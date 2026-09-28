#!/usr/bin/env python3
"""
scid_export.py - builds 1-second and 1-minute bar CSV files from Sierra Chart .scid contract files.

Source of truth: per-contract Sierra Chart intraday files <SYMBOL><MONTH><YY>-<EXCHANGE>.scid
(tick records, time in UTC). Output (in --out):

  <SYMBOL>-1-sec.csv          1-second bars
  <SYMBOL>-1-min.csv          1-minute bars (same records, same days as the 1-second file)
  <SYMBOL>-rolls.csv          roll table (when the front contract changes and the measured price spread)
  <SYMBOL>-export-report.json source files, rules, included/excluded days, checks

Rules (fixed, documented in the report):
  * time zone: --tz (default Europe/Prague); a bar is labelled by the local time of its START;
    a trading day is the local calendar day
  * bar prices are trade prices (Close field of the record) rounded to the price grid --tick (Sierra stores float32
    and some records are off by ~0.001, e.g. 13422.499 instead of 13422.5); whole day, no session filter
  * record order: timestamp truncated to the second, stable sort. Within a second the file (arrival) order is kept
    (FDAXM16 stamps trades of one second alternately .000/.001 ms, sorting by the full timestamp would reorder them);
    a record stamped 1-5 s earlier than the record before it (2013-2016 files) goes to the second of its own timestamp.
    Counts per contract are in the report (out_of_order)
  * only complete days: the local day of the export run and later days are skipped (--include-today overrides)
  * front contract by volume: roll to the next contract at the start of the first local day
    (within 21 days before the expiry of the current one) on which the next contract has the higher volume;
    fallback = expiry day. Prices are NOT back-adjusted; column Contract says which contract a bar comes from
  * roll spread = median of (close_next - close_current) over the last 60 one-minute bars traded in both
    contracts on the last day before the roll, rounded to --tick
  * a day is exported only if its front-contract records are real ticks with bid/ask classification:
    (BidVolume + AskVolume) / Volume >= --min-bidask (default 0.999) and records >= --min-records (default 100).
    Everything before the first such day is skipped; later days that fail are listed as excluded.

Usage:
  python scid_export.py all --data E:\\SierraChart\\Data --symbol FDAX --exchange EUREX --out C:\\...\\data
  (the phases plan / build / finalize can be run separately; build is resumable, --budget limits seconds per run)

Requires: Python 3.9+, numpy, pandas.
"""
import argparse, glob, json, os, re, sys, time
import numpy as np
import pandas as pd

VERSION = '1.2'
TICKS = {'FDAX': 0.5, 'FDXM': 1.0, 'FDXS': 1.0, 'FESX': 1.0, 'NQ': 0.25, 'MNQ': 0.25, 'ES': 0.25, 'MES': 0.25, 'YM': 1.0, 'MYM': 1.0}
REC = np.dtype([('t', '<i8'), ('o', '<f4'), ('h', '<f4'), ('l', '<f4'), ('c', '<f4'),
                ('n', '<u4'), ('v', '<u4'), ('bv', '<u4'), ('av', '<u4')])
MONTHS = 'FGHJKMNQUVXZ'
EPOCH = pd.Timestamp('1899-12-30')
COLS = ['Date', 'Time', 'Open', 'High', 'Low', 'Last', 'Volume', 'NumberOfTrades', 'BidVolume', 'AskVolume', 'Contract']


# ------------------------------------------------------------------ helpers

def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def third_friday(y, m):
    d = pd.Timestamp(y, m, 15)
    return d + pd.Timedelta(days=(4 - d.dayofweek) % 7)


def open_scid(path):
    with open(path, 'rb') as f:
        hdr = f.read(56)
    if len(hdr) < 12 or hdr[:4] != b'SCID':
        raise ValueError('not a SCID file: ' + path)
    hsize = int(np.frombuffer(hdr[4:8], '<u4')[0]); rsize = int(np.frombuffer(hdr[8:12], '<u4')[0])
    if rsize != 40:
        raise ValueError('unsupported record size %d in %s' % (rsize, path))
    n = (os.path.getsize(path) - hsize) // rsize
    if n <= 0:
        return None
    return np.memmap(path, dtype=REC, mode='r', offset=hsize, shape=(n,))


def local_times(r, tz):
    t = pd.to_datetime(np.asarray(r['t']), unit='us', origin=EPOCH)
    return t.tz_localize('UTC').tz_convert(tz).tz_localize(None)


def list_contracts(data, symbol, exchange):
    rx = re.compile(r'^%s([%s])(\d{2})-%s\.scid$' % (re.escape(symbol), MONTHS, re.escape(exchange)), re.I)
    out = []
    for p in glob.glob(os.path.join(data, '*.scid')):
        m = rx.match(os.path.basename(p))
        if not m:
            continue
        mon = MONTHS.index(m.group(1).upper()) + 1; yy = int(m.group(2))
        year = 2000 + yy if yy < 80 else 1900 + yy
        out.append(dict(name='%s%s%02d' % (symbol, m.group(1).upper(), yy), file=p, year=year, month=mon,
                        expiry=third_friday(year, mon), size=os.path.getsize(p), mtime=os.path.getmtime(p)))
    out.sort(key=lambda c: (c['year'], c['month']))
    return out


def daily_stats(c, tz, cache_dir):
    key = os.path.join(cache_dir, '%s_%d_%d.pkl' % (os.path.basename(c['file']), c['size'], int(c['mtime'])))
    if os.path.exists(key):
        return pd.read_pickle(key)
    r = open_scid(c['file'])
    if r is None:
        g = pd.DataFrame(columns=['recs', 'vol', 'ba', 'first', 'last'])
    else:
        loc = local_times(r, tz); d = loc.normalize()
        v = np.asarray(r['v']).astype(np.int64)
        ba = np.asarray(r['bv']).astype(np.int64) + np.asarray(r['av']).astype(np.int64)
        df = pd.DataFrame({'d': d, 'v': v, 'ba': ba, 'loc': loc})
        g = df.groupby('d').agg(recs=('v', 'size'), vol=('v', 'sum'), ba=('ba', 'sum'), first=('loc', 'min'), last=('loc', 'max'))
    g.to_pickle(key)
    return g


def sc_us(ts_local, tz):
    """local naive midnight -> Sierra time (microseconds since 1899-12-30 UTC)"""
    u = pd.Timestamp(ts_local).tz_localize(tz).tz_convert('UTC').tz_localize(None)
    return int((u - EPOCH) / pd.Timedelta(microseconds=1))


def ordered(t_us):
    """index order by timestamp truncated to the second, stable (file order kept within a second); None = already ordered"""
    s = np.asarray(t_us) // 10**6
    return np.argsort(s, kind='stable') if np.any(np.diff(s) < 0) else None


def minute_closes(c, tz, day, tick):
    r = open_scid(c['file'])
    t = np.asarray(r['t'])
    idx = np.flatnonzero((t >= sc_us(day, tz)) & (t < sc_us(day + pd.Timedelta(days=1), tz)))
    if len(idx) == 0:
        return pd.Series(dtype=float)
    o = ordered(t[idx])
    part = r[idx if o is None else idx[o]]
    loc = local_times(part, tz)
    s = pd.Series(np.round(np.asarray(part['c']).astype(np.float64) / tick) * tick, index=loc)
    s = s[s > 0]
    return s.groupby(s.index.floor('min')).last()


# ------------------------------------------------------------------ plan

def plan(a):
    out = a.out; cache = os.path.join(out, '.scid_export_cache'); os.makedirs(cache, exist_ok=True)
    cons = list_contracts(a.data, a.symbol, a.exchange)
    if not cons:
        raise SystemExit('no %s*-%s.scid files in %s' % (a.symbol, a.exchange, a.data))
    for c in cons:
        c['daily'] = daily_stats(c, a.tz, cache)
    have = [c for c in cons if len(c['daily'])]
    empty = [c['name'] for c in cons if not len(c['daily'])]
    log('contracts with data:', len(have), '| empty:', len(empty))
    # roll schedule by volume
    rolls, holes = [], []
    for A, B in zip(have, have[1:]):
        va, vb = A['daily'].vol, B['daily'].vol
        skipped = [c['name'] for c in cons if A['expiry'] < c['expiry'] < B['expiry']]
        win = [d for d in va.index if A['expiry'] - pd.Timedelta(days=21) <= d <= A['expiry'] and d in vb.index]
        day = next((d for d in win if vb[d] > va[d]), None); rule = 'volume'
        if day is None:
            if skipped or not win:
                # missing contract(s) between A and B: front A ends with its data, B starts with its first day
                day = vb.index.min() if vb.index.min() > va.index.max() else va.index.max() + pd.Timedelta(days=1)
                rule = 'hole'
                holes.append(dict(after=A['name'], before=B['name'], missing=skipped,
                                  last_day_with_data=str(va.index.max().date()), next_day_with_data=str(vb.index.min().date())))
            else:
                day = A['expiry']; rule = 'expiry-fallback'
        rolls.append(dict(frm=A['name'], to=B['name'], day=day, rule=rule))
    # front contract per day
    fronts = []
    starts = [pd.Timestamp('1900-01-01')] + [r['day'] for r in rolls]
    ends = [r['day'] for r in rolls] + [pd.Timestamp('2200-01-01')]
    for c, s, e in zip(have, starts, ends):
        g = c['daily']; g = g[(g.index >= s) & (g.index < e)]
        for d, x in g.iterrows():
            fronts.append(dict(date=d, contract=c['name'], recs=int(x.recs), vol=int(x.vol),
                               ba_share=float(x.ba / x.vol) if x.vol else 0.0))
    F = pd.DataFrame(fronts).set_index('date').sort_index()
    today = pd.Timestamp.now(tz=a.tz).normalize().tz_localize(None)
    incomplete = [] if a.include_today else [str(d.date()) for d in F.index[F.index >= today]]
    if not a.include_today:
        F = F[F.index < today]
    F['reason'] = ''
    F.loc[F.ba_share < a.min_bidask, 'reason'] = 'no tick data with bid/ask (bid+ask < %.1f%% of volume)' % (100 * a.min_bidask)
    F.loc[(F.reason == '') & (F.recs < a.min_records), 'reason'] = 'fewer than %d records (non-trading day artefact)' % a.min_records
    ok = F.reason == ''
    first = F[ok].index.min()
    excluded = F[(F.index >= first) & ~ok]
    included = F[(F.index >= first) & ok]
    # roll spreads
    byname = {c['name']: c for c in have}
    roll_rows = []
    for r in rolls:
        if r['day'] < first:
            continue
        A, B = byname[r['frm']], byname[r['to']]
        common = [d for d in A['daily'].index if d < r['day'] and d in B['daily'].index]
        spread, n, ref = None, 0, None
        if common and r['rule'] != 'hole':
            ref = common[-1]
            ca, cb = minute_closes(A, a.tz, ref, a.tick), minute_closes(B, a.tz, ref, a.tick)
            j = pd.concat([ca, cb], axis=1, keys=['a', 'b']).dropna().tail(60)
            if len(j):
                spread = float(np.round(np.median(j.b - j.a) / a.tick) * a.tick); n = int(len(j))
        first_bar = included[included.contract == r['to']].index.min()
        roll_rows.append(dict(roll_day=str(r['day'].date()), from_contract=r['frm'], to_contract=r['to'], rule=r['rule'],
                              first_day_of_new_contract=str(first_bar.date()) if pd.notna(first_bar) else '',
                              spread_to_minus_from=spread, spread_minutes=n, spread_measured_on=str(ref.date()) if ref is not None else ''))
    P = dict(version=VERSION, symbol=a.symbol, exchange=a.exchange, tz=a.tz, data=a.data, tick=a.tick,
             rules=dict(bar_label='start of interval, local time', prices='trade price (record Close) rounded to the tick grid %s' % a.tick,
                        session='whole day, no filter',
                        record_order='timestamp truncated to the second, stable (file order within a second)',
                        complete_days='days from the local export date on are skipped' if not a.include_today else 'export date included (may be incomplete)',
                        roll='volume crossover within 21 days before expiry, at start of local day; fallback expiry day; no back-adjustment',
                        spread='median(close_to - close_from) over the last 60 common 1-min bars of the last day before the roll, rounded to tick',
                        include_day='front-contract (BidVolume+AskVolume)/Volume >= %s and records >= %d' % (a.min_bidask, a.min_records)),
             sources=[dict(file=os.path.basename(c['file']), size=c['size'], mtime=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c['mtime'])),
                           first_day=str(c['daily'].index.min().date()) if len(c['daily']) else None,
                           last_day=str(c['daily'].index.max().date()) if len(c['daily']) else None) for c in cons],
             empty_files=empty, holes=holes, skipped_incomplete_days=incomplete,
             first_day=str(first.date()), last_day=str(included.index.max().date()),
             days_included=int(len(included)), days_skipped_before_start=int((F.index < first).sum()),
             excluded_days=[dict(date=str(d.date()), contract=x.contract, records=x.recs, volume=x.vol,
                                 bidask_share=round(x.ba_share, 4), reason=x.reason) for d, x in excluded.iterrows()],
             rolls=roll_rows,
             days={c: [str(d.date()) for d in included[included.contract == c].index] for c in included.contract.unique()})
    json.dump(P, open(os.path.join(out, '.%s-plan.json' % a.symbol), 'w'), indent=1)
    log('plan: first day', P['first_day'], '| last day', P['last_day'], '| days', P['days_included'],
        '| excluded', len(P['excluded_days']), '| rolls', len(roll_rows), '| holes', len(holes))
    return P


# ------------------------------------------------------------------ build

_TIMES = None


def time_strings():
    global _TIMES
    if _TIMES is None:
        s = np.arange(86400)
        _TIMES = np.array(['%02d:%02d:%02d' % (x // 3600, x // 60 % 60, x % 60) for x in s], dtype=object)
    return _TIMES


def bars(key, c, v, n, bv, av):
    idx = np.r_[0, np.flatnonzero(np.diff(key)) + 1]
    last = np.r_[idx[1:] - 1, len(key) - 1]
    return dict(k=key[idx], o=c[idx], h=np.maximum.reduceat(c, idx), l=np.minimum.reduceat(c, idx), cl=c[last],
                v=np.add.reduceat(v, idx), n=np.add.reduceat(n, idx), bv=np.add.reduceat(bv, idx), av=np.add.reduceat(av, idx))


def write_bars(f, b, unit_us, contract):
    k = b['k']
    day_us = 86400 * 10**6
    day = k // day_us; sod = (k % day_us) // 10**6
    ud = np.unique(day)
    dstr = {d: '%d/%d/%d' % (t.year, t.month, t.day) for d, t in zip(ud, pd.to_datetime(ud * day_us, unit='us'))}
    df = pd.DataFrame({'Date': pd.Series(day).map(dstr).values, 'Time': time_strings()[sod],
                       'Open': b['o'], 'High': b['h'], 'Low': b['l'], 'Last': b['cl'],
                       'Volume': b['v'], 'NumberOfTrades': b['n'], 'BidVolume': b['bv'], 'AskVolume': b['av'], 'Contract': contract})
    df.to_csv(f, header=False, index=False, float_format='%.10g', lineterminator='\n')
    return len(df)


def build(a, P):
    out = a.out; t0 = time.time()
    names = {'sec': os.path.join(out, '%s-1-sec.csv.part' % a.symbol), 'min': os.path.join(out, '%s-1-min.csv.part' % a.symbol)}
    stf = os.path.join(out, '.%s-build-state.json' % a.symbol)
    st = json.load(open(stf)) if os.path.exists(stf) else None
    if st is None or st.get('plan_first_day') != P['first_day'] or st.get('plan_last_day') != P['last_day']:
        for p in names.values():
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write(','.join(COLS) + '\n')
        st = dict(plan_first_day=P['first_day'], plan_last_day=P['last_day'], done=[], sizes={}, rows={'sec': 0, 'min': 0}, volume=0, records=0)
    order = list(P['days'].keys())
    files = {s['file'].split('-')[0].upper(): s['file'] for s in P['sources']}
    for cname in order:
        if cname in st['done']:
            continue
        if time.time() - t0 > a.budget:
            json.dump(st, open(stf, 'w'), indent=1)
            log('budget reached, resume with the same command'); return False
        # truncate partial output of an interrupted run
        for kind, p in names.items():
            want = st['sizes'].get(kind)
            if want is not None and os.path.getsize(p) != want:
                with open(p, 'r+b') as f:
                    f.truncate(want)
        r = open_scid(os.path.join(a.data, files[cname]))
        tus = np.asarray(r['t'])
        loc = local_times(r, a.tz)
        days = pd.to_datetime(P['days'][cname])
        m = np.asarray(loc.normalize().isin(days))
        c = np.round(np.asarray(r['c']).astype(np.float64) / a.tick) * a.tick
        m &= c > 0
        loc_us = (loc.values.astype('datetime64[us]').astype(np.int64))[m]
        order_ = ordered(loc_us)
        dsec = np.diff(loc_us // 10**6)
        st.setdefault('out_of_order', {})[cname] = dict(back_within_second=int(((np.diff(loc_us) < 0) & (dsec == 0)).sum()),
                                                        back_across_seconds=int((dsec < 0).sum()))
        cc = c[m]; v = np.asarray(r['v'])[m].astype(np.int64); n = np.asarray(r['n'])[m].astype(np.int64)
        bv = np.asarray(r['bv'])[m].astype(np.int64); av = np.asarray(r['av'])[m].astype(np.int64)
        if order_ is not None:
            loc_us, cc, v, n, bv, av = loc_us[order_], cc[order_], v[order_], n[order_], bv[order_], av[order_]
        epoch_us = np.int64(pd.Timestamp('1970-01-01').value // 1000)
        res = {}
        for kind, unit in (('sec', 10**6), ('min', 60 * 10**6)):
            key = (loc_us - epoch_us) // unit * unit + epoch_us
            b = bars(key, cc, v, n, bv, av)
            with open(names[kind], 'a', encoding='utf-8', newline='\n') as f:
                res[kind] = write_bars(f, b, unit, cname)
            st['rows'][kind] += res[kind]
            st['sizes'][kind] = os.path.getsize(names[kind])
        st['volume'] += int(v.sum()); st['records'] += int(m.sum())
        st['done'].append(cname)
        json.dump(st, open(stf, 'w'), indent=1)
        log(cname, 'records', int(m.sum()), '| 1s rows', res['sec'], '| 1m rows', res['min'], '| %.0fs' % (time.time() - t0))
    return True


# ------------------------------------------------------------------ finalize

def finalize(a, P):
    out = a.out
    stf = os.path.join(out, '.%s-build-state.json' % a.symbol); st = json.load(open(stf))
    if st['done'] != list(P['days'].keys()):
        raise SystemExit('build not complete')
    for kind in ('sec', 'min'):
        part = os.path.join(out, '%s-1-%s.csv.part' % (a.symbol, kind)); final = part[:-5]
        os.replace(part, final)
    pd.DataFrame(P['rolls']).to_csv(os.path.join(out, '%s-rolls.csv' % a.symbol), index=False, lineterminator='\n')
    rep = {k: v for k, v in P.items() if k != 'days'}
    rep.update(rows_1sec=st['rows']['sec'], rows_1min=st['rows']['min'], total_volume=st['volume'], total_records=st['records'],
               created=time.strftime('%Y-%m-%d %H:%M:%S'), columns=COLS,
               out_of_order={k: v for k, v in st.get('out_of_order', {}).items() if v['back_within_second'] or v['back_across_seconds']})
    json.dump(rep, open(os.path.join(out, '%s-export-report.json' % a.symbol), 'w'), indent=1, ensure_ascii=False)
    os.remove(stf)
    pf = os.path.join(out, '.%s-plan.json' % a.symbol)
    if os.path.exists(pf):
        os.remove(pf)
    log('done:', os.path.join(out, '%s-1-sec.csv' % a.symbol), st['rows']['sec'], 'rows |', os.path.join(out, '%s-1-min.csv' % a.symbol), st['rows']['min'], 'rows')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('phase', choices=['plan', 'build', 'finalize', 'all'])
    ap.add_argument('--data', required=True, help='Sierra Chart Data folder with .scid files')
    ap.add_argument('--symbol', required=True, help='e.g. FDAX, NQ, ES, YM')
    ap.add_argument('--exchange', required=True, help='e.g. EUREX, CME, CBOT')
    ap.add_argument('--out', required=True, help='output folder')
    ap.add_argument('--tz', default='Europe/Prague')
    ap.add_argument('--tick', type=float, default=None, help='price grid; default by symbol: %s' % TICKS)
    ap.add_argument('--min-bidask', type=float, default=0.999)
    ap.add_argument('--min-records', type=int, default=100)
    ap.add_argument('--budget', type=float, default=1e9, help='seconds per build run (resumable)')
    ap.add_argument('--include-today', action='store_true', help='also export the (possibly incomplete) local day of the run')
    a = ap.parse_args()
    if a.tick is None:
        if a.symbol.upper() not in TICKS:
            raise SystemExit('unknown tick size for %s, pass --tick' % a.symbol)
        a.tick = TICKS[a.symbol.upper()]
    os.makedirs(a.out, exist_ok=True)
    pf = os.path.join(a.out, '.%s-plan.json' % a.symbol)
    if a.phase in ('plan', 'all'):
        P = plan(a)
    else:
        P = json.load(open(pf))
        if P.get('tick') != a.tick:
            raise SystemExit('plan was made with tick %s, run plan again' % P.get('tick'))
    if a.phase in ('build', 'all'):
        if not build(a, P):
            sys.exit(3)
    if a.phase in ('finalize', 'all'):
        finalize(a, P)


if __name__ == '__main__':
    main()
