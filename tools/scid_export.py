#!/usr/bin/env python3
"""
scid_export.py - 1-second and 1-minute bar CSV files from Sierra Chart .scid contract files.

Full documentation for people and agents: data/README.md (repository root). Summary:

Input:  per-contract Sierra Chart files <SYMBOL><MONTH><YY>-<EXCHANGE>.scid (tick records, time in UTC).
Output (--out, by convention data/<SYMBOL>/):
  <SYMBOL>-1-sec.csv            1-second bars
  <SYMBOL>-1-min.csv            1-minute bars (same records and days as the 1-second file)
  <SYMBOL>-rolls.csv            roll table (front contract changes and the measured price spread)
  <SYMBOL>-export-report.json   sources, rules, included/excluded days, checks, verification, gaps

Rules (also written to the report):
  * a bar is labelled by the local time (--tz, default Europe/Prague) of its START; only bars with trades
  * trading day = exchange trading day (EXCHANGES): CME/CBOT day D runs from 17:00 America/Chicago on D-1 to
    17:00 on D, EUREX day = calendar day Europe/Berlin; Saturday/Sunday trading days are dropped
  * price = trade price (record Close) rounded to the tick grid --tick (Sierra stores float32; some records are
    off by ~0.001); whole trading day, no session filter
  * record order: timestamp truncated to the second, stable sort (file = arrival order kept within a second)
  * front contract by volume: roll at the start of the first trading day within 21 days before the expiry of the
    current contract on which the next contract has the higher volume (only weekdays with >= --min-records
    records in both contracts count); fallback = expiry day; a missing contract = 'hole'. Prices are NOT
    adjusted; the column Contract names the source contract
  * roll spread = median(close_next - close_current) over the last 60 one-minute bars traded in both contracts
    on the last trading day before the roll, rounded to --tick
  * a trading day is exported only if its front-contract records are real ticks with bid/ask classification:
    (BidVolume + AskVolume) / Volume >= --min-bidask and records >= --min-records; everything before the first
    such day is skipped, later failing days are listed as excluded
  * only complete days: the trading day of the run and later days are skipped (--include-today overrides)

Phases: plan | build | finalize | verify | all. plan, build and verify are resumable: --budget limits the
seconds of one run, exit code 3 = run the same command again.

Example (Windows, repository root):
  python tools\\scid_export.py all --data E:\\SierraChart\\Data --symbol NQ --exchange CME --out data\\NQ

Requires Python 3.9+, numpy, pandas.
"""
import argparse, glob, io, json, os, re, shutil, sys, time
import numpy as np
import pandas as pd

VERSION = '1.3'
TICKS = {'FDAX': 0.5, 'FDXM': 1.0, 'FDXS': 1.0, 'FESX': 1.0, 'NQ': 0.25, 'MNQ': 0.25, 'ES': 0.25, 'MES': 0.25,
         'YM': 1.0, 'MYM': 1.0}
# tz = exchange time zone; day_start = local time at which the trading day starts (on the previous calendar day
# when not 00:00); rth = main session in exchange time, used only by the gap report (equity index futures)
EXCHANGES = {
    'CME': dict(tz='America/Chicago', day_start='17:00', rth=('08:30', '15:00')),
    'CBOT': dict(tz='America/Chicago', day_start='17:00', rth=('08:30', '15:00')),
    'EUREX': dict(tz='Europe/Berlin', day_start='00:00', rth=('09:00', '17:30')),
}
REC = np.dtype([('t', '<i8'), ('o', '<f4'), ('h', '<f4'), ('l', '<f4'), ('c', '<f4'),
                ('n', '<u4'), ('v', '<u4'), ('bv', '<u4'), ('av', '<u4')])
MONTHS = 'FGHJKMNQUVXZ'
EPOCH = pd.Timestamp('1899-12-30')      # Sierra time = microseconds since EPOCH, UTC
DAY_US = 86_400_000_000
UNIX0_US = 25569 * DAY_US               # 1970-01-01 in Sierra microseconds
CHUNK = 4_000_000                       # records per processing chunk
COLS = ['Date', 'Time', 'Open', 'High', 'Low', 'Last', 'Volume', 'NumberOfTrades', 'BidVolume', 'AskVolume', 'Contract']
FIELDS = ('k', 'o', 'h', 'l', 'cl', 'v', 'n', 'bv', 'av', 'con', 'con2')


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


def day_shift(ex):
    """added to exchange local time, turns the trading day into a calendar day"""
    h, m = map(int, ex['day_start'].split(':'))
    return pd.Timedelta(0) if h == 0 and m == 0 else pd.Timedelta(days=1) - pd.Timedelta(hours=h, minutes=m)


_TZ = {}


def tz_table(tz):
    """UTC -> tz: (instants of offset changes in Sierra microseconds, offset in microseconds from that instant)"""
    if tz not in _TZ:
        rng = pd.date_range('1990-01-01', '2100-01-01', freq='h')
        off = (rng.tz_localize('UTC').tz_convert(tz).tz_localize(None) - rng).asi8 // 1000
        ch = np.flatnonzero(np.r_[True, off[1:] != off[:-1]])
        _TZ[tz] = (((rng[ch] - EPOCH).asi8 // 1000).astype(np.int64), off[ch].astype(np.int64))
    return _TZ[tz]


def to_local(t_us, tz):
    """Sierra UTC microseconds -> local wall-clock microseconds (same epoch)"""
    tr, off = tz_table(tz)
    return t_us + off[np.clip(np.searchsorted(tr, t_us, side='right') - 1, 0, None)]


def trade_day(t_us, ex):
    """exchange trading day of each record, as a day number since EPOCH"""
    return (to_local(t_us, ex['tz']) + int(day_shift(ex) / pd.Timedelta(microseconds=1))) // DAY_US


def day_num(d):
    return int((pd.Timestamp(d) - EPOCH) / pd.Timedelta(days=1))


def num_day(n):
    return EPOCH + pd.Timedelta(days=int(n))


def utc_us(ts_local, tz):
    u = pd.Timestamp(ts_local).tz_localize(tz).tz_convert('UTC').tz_localize(None)
    return int((u - EPOCH) / pd.Timedelta(microseconds=1))


def day_bounds(day, ex):
    """[lo, hi) of an exchange trading day in Sierra UTC microseconds"""
    s = day_shift(ex); d = pd.Timestamp(day)
    return utc_us(d - s, ex['tz']), utc_us(d + pd.Timedelta(days=1) - s, ex['tz'])


def now_trade_day(ex):
    t = int((pd.Timestamp.now(tz='UTC').tz_localize(None) - EPOCH) / pd.Timedelta(microseconds=1))
    return num_day(trade_day(np.array([t], dtype=np.int64), ex)[0])


def ordered(t_us):
    """index order by timestamp truncated to the second, stable; None = already in order"""
    s = np.asarray(t_us) // 10**6
    return np.argsort(s, kind='stable') if np.any(np.diff(s) < 0) else None


def bsearch(r, value):
    """first index with r['t'] >= value in a (nearly) time-ordered memmap; reads only ~log2(n) records"""
    lo, hi = 0, len(r)
    while lo < hi:
        mid = (lo + hi) // 2
        if int(r[mid]['t']) < value:
            lo = mid + 1
        else:
            hi = mid
    return lo


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


def daily_stats(c, ex, cache_dir):
    """records, volume and bid+ask volume per exchange trading day (cached per file size, mtime and day rule)"""
    tag = re.sub(r'[^A-Za-z0-9]+', '-', '%s %s' % (ex['tz'], ex['day_start']))
    key = os.path.join(cache_dir, '%s_%d_%d_%s.pkl' % (os.path.basename(c['file']), c['size'], int(c['mtime']), tag))
    if os.path.exists(key):
        return pd.read_pickle(key)
    r = open_scid(c['file'])
    cols = ['recs', 'vol', 'ba']
    if r is None:
        g = pd.DataFrame(columns=cols, dtype=np.int64)
    else:
        parts = []
        for a0 in range(0, len(r), CHUNK):
            x = np.array(r[a0:a0 + CHUNK])
            d = trade_day(x['t'], ex)
            br = np.flatnonzero(np.r_[True, d[1:] != d[:-1]])
            parts.append(pd.DataFrame({'d': d[br], 'recs': np.diff(np.r_[br, len(d)]),
                                       'vol': np.add.reduceat(x['v'], br, dtype=np.int64),
                                       'ba': np.add.reduceat(x['bv'].astype(np.int64) + x['av'], br)}))
        g = pd.concat(parts).groupby('d')[cols].sum()
        g.index = pd.DatetimeIndex([num_day(n) for n in g.index])
    g.to_pickle(key)
    return g


def minute_closes(c, ex, day, tick, tz):
    """last trade price of each local minute of one trading day"""
    r = open_scid(c['file'])
    lo, hi = day_bounds(day, ex)
    i0 = max(0, bsearch(r, lo - DAY_US)); i1 = min(len(r), bsearch(r, hi + DAY_US))
    x = np.array(r[i0:i1]); x = x[(x['t'] >= lo) & (x['t'] < hi)]
    if not len(x):
        return pd.Series(dtype=float)
    o = ordered(x['t'])
    if o is not None:
        x = x[o]
    cc = np.round(x['c'].astype(np.float64) / tick) * tick
    k = (to_local(x['t'], tz) - UNIX0_US) // 60_000_000
    s = pd.Series(cc, index=k)
    s = s[s > 0]
    return s.groupby(level=0).last()


# ------------------------------------------------------------------ plan

def plan(a, ex):
    t0 = time.time()
    out = a.out; cache = os.path.join(out, '.scid_export_cache'); os.makedirs(cache, exist_ok=True)
    cons = list_contracts(a.data, a.symbol, a.exchange)
    if not cons:
        raise SystemExit('no %s*-%s.scid files in %s' % (a.symbol, a.exchange, a.data))
    for c in cons:
        if time.time() - t0 > a.budget:
            log('budget reached while reading daily statistics, run the same command again')
            return None
        c['daily'] = daily_stats(c, ex, cache)
    have = [c for c in cons if len(c['daily'])]
    empty = [c['name'] for c in cons if not len(c['daily'])]
    log('contracts with data:', len(have), '| empty:', len(empty))
    mr = a.min_records
    rolls, holes = [], []
    for A, B in zip(have, have[1:]):
        da, db = A['daily'], B['daily']
        skipped = [c['name'] for c in cons if A['expiry'] < c['expiry'] < B['expiry']]
        win = [d for d in da.index if A['expiry'] - pd.Timedelta(days=21) <= d <= A['expiry'] and d in db.index
               and d.dayofweek < 5 and da.recs[d] >= mr and db.recs[d] >= mr]
        day = next((d for d in win if db.vol[d] > da.vol[d]), None); rule = 'volume'
        if day is None:
            if skipped or not win:
                day = db.index.min() if db.index.min() > da.index.max() else da.index.max() + pd.Timedelta(days=1)
                rule = 'hole'
                holes.append(dict(after=A['name'], before=B['name'], missing=skipped,
                                  last_day_with_data=str(da.index.max().date()), next_day_with_data=str(db.index.min().date())))
            else:
                day = A['expiry']; rule = 'expiry-fallback'
        rolls.append(dict(frm=A['name'], to=B['name'], day=day, rule=rule))
    fronts = []
    starts = [pd.Timestamp('1900-01-01')] + [r['day'] for r in rolls]
    ends = [r['day'] for r in rolls] + [pd.Timestamp('2200-01-01')]
    for c, s, e in zip(have, starts, ends):
        g = c['daily']; g = g[(g.index >= s) & (g.index < e)]
        for d, x in g.iterrows():
            fronts.append(dict(date=d, contract=c['name'], recs=int(x.recs), vol=int(x.vol),
                               ba_share=float(x.ba / x.vol) if x.vol else 0.0))
    F = pd.DataFrame(fronts).set_index('date').sort_index()
    today = now_trade_day(ex)
    incomplete = [] if a.include_today else [str(d.date()) for d in F.index[F.index >= today]]
    if not a.include_today:
        F = F[F.index < today]
    F['reason'] = ''
    F.loc[F.index.dayofweek >= 5, 'reason'] = 'weekend (exchange closed)'
    F.loc[(F.reason == '') & (F.ba_share < a.min_bidask), 'reason'] = 'no tick data with bid/ask (bid+ask < %.1f%% of volume)' % (100 * a.min_bidask)
    F.loc[(F.reason == '') & (F.recs < mr), 'reason'] = 'fewer than %d records' % mr
    ok = F.reason == ''
    first = F[ok].index.min()
    excluded = F[(F.index >= first) & ~ok]
    included = F[(F.index >= first) & ok]
    byname = {c['name']: c for c in have}
    roll_rows = []
    for r in rolls:
        if r['day'] < first:
            continue
        A, B = byname[r['frm']], byname[r['to']]
        common = [d for d in A['daily'].index if d < r['day'] and d in B['daily'].index and d.dayofweek < 5
                  and A['daily'].recs[d] >= mr and B['daily'].recs[d] >= mr]
        spread, n, ref = None, 0, None
        if common and r['rule'] != 'hole':
            ref = common[-1]
            ca, cb = minute_closes(A, ex, ref, a.tick, a.tz), minute_closes(B, ex, ref, a.tick, a.tz)
            j = pd.concat([ca, cb], axis=1, keys=['a', 'b']).dropna().tail(60)
            if len(j):
                spread = float(np.round(np.median(j.b - j.a) / a.tick) * a.tick); n = int(len(j))
        first_bar = included[included.contract == r['to']].index.min()
        roll_rows.append(dict(roll_day=str(r['day'].date()), from_contract=r['frm'], to_contract=r['to'], rule=r['rule'],
                              first_day_of_new_contract=str(first_bar.date()) if pd.notna(first_bar) else '',
                              spread_to_minus_from=spread, spread_minutes=n, spread_measured_on=str(ref.date()) if ref is not None else ''))
    P = dict(version=VERSION, symbol=a.symbol, exchange=a.exchange, exchange_rules=ex, tz=a.tz, data=a.data, tick=a.tick,
             min_bidask=a.min_bidask, min_records=mr,
             rules=dict(bar_label='start of the bar, local time %s; only bars with trades' % a.tz,
                        trading_day='exchange trading day, starts %s %s (on the previous calendar day if not 00:00); Saturday/Sunday dropped' % (ex['day_start'], ex['tz']),
                        prices='trade price (record Close) rounded to the tick grid %s' % a.tick,
                        record_order='timestamp truncated to the second, stable (file order within a second)',
                        session='whole trading day, no session filter',
                        roll='volume crossover within 21 days before expiry (weekdays with >= %d records in both contracts), at the start of the trading day; fallback expiry day; no price adjustment' % mr,
                        spread='median(close_to - close_from) over the last 60 common 1-min bars of the last trading day before the roll, rounded to tick',
                        include_day='front-contract (BidVolume+AskVolume)/Volume >= %s and records >= %d; days before the first such day skipped' % (a.min_bidask, mr),
                        complete_days='the trading day of the run and later days are skipped' if not a.include_today else 'trading day of the run included (may be incomplete)'),
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
    idx = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    last = np.r_[idx[1:] - 1, len(key) - 1]
    return dict(k=key[idx], o=c[idx], h=np.maximum.reduceat(c, idx), l=np.minimum.reduceat(c, idx), cl=c[last],
                v=np.add.reduceat(v, idx, dtype=np.int64), n=np.add.reduceat(n, idx, dtype=np.int64),
                bv=np.add.reduceat(bv, idx, dtype=np.int64), av=np.add.reduceat(av, idx, dtype=np.int64))


def merge_carry(b, c):
    """joins the last bar of the previous chunk; returns (bars to write, new carry = last bar)"""
    if c is not None:
        if c['k'][0] > b['k'][0]:
            raise RuntimeError('bar keys not increasing across chunks')
        if c['k'][0] == b['k'][0]:
            b['o'][0] = c['o'][0]; b['h'][0] = max(b['h'][0], c['h'][0]); b['l'][0] = min(b['l'][0], c['l'][0])
            for f in ('v', 'n', 'bv', 'av'):
                b[f][0] += c[f][0]
        else:
            b = {f: np.r_[c[f], b[f]] for f in b}
    return {f: b[f][:-1] for f in b}, {f: b[f][-1:].copy() for f in b}


def write_bars(f, b, contract):
    k = b['k']                                     # local microseconds since 1970
    day = k // DAY_US; sod = (k % DAY_US) // 10**6
    ud = np.unique(day)
    dstr = {d: '%d/%d/%d' % (t.year, t.month, t.day) for d, t in zip(ud, pd.to_datetime(ud * DAY_US, unit='us'))}
    df = pd.DataFrame({'Date': pd.Series(day).map(dstr).values, 'Time': time_strings()[sod],
                       'Open': b['o'], 'High': b['h'], 'Low': b['l'], 'Last': b['cl'],
                       'Volume': b['v'], 'NumberOfTrades': b['n'], 'BidVolume': b['bv'], 'AskVolume': b['av'], 'Contract': contract})
    df.to_csv(f, header=False, index=False, float_format='%.10g', lineterminator='\n')
    return len(df)


def build(a, P, ex):
    out = a.out; t0 = time.time()
    names = {'sec': os.path.join(out, '%s-1-sec.csv.part' % a.symbol), 'min': os.path.join(out, '%s-1-min.csv.part' % a.symbol)}
    stf = os.path.join(out, '.%s-build-state.json' % a.symbol)
    st = json.load(open(stf)) if os.path.exists(stf) else None
    if (st is None or st.get('version') != VERSION or st.get('plan_first_day') != P['first_day']
            or st.get('plan_last_day') != P['last_day']):
        for p in names.values():
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write(','.join(COLS) + '\n')
        st = dict(version=VERSION, plan_first_day=P['first_day'], plan_last_day=P['last_day'], done=[],
                  sizes={k: os.path.getsize(p) for k, p in names.items()}, rows={'sec': 0, 'min': 0},
                  volume=0, records=0, out_of_order={}, off_grid={})
    files = {s['file'].split('-')[0].upper(): s['file'] for s in P['sources']}
    rate = None
    for cname in P['days']:
        if cname in st['done']:
            continue
        path = os.path.join(a.data, files[cname])
        est = rate * os.path.getsize(path) / 40 if rate else 0
        if time.time() - t0 + est > a.budget:
            json.dump(st, open(stf, 'w'), indent=1)
            log('budget reached, run the same command again'); return False
        tc = time.time()
        for kind, p in names.items():           # drop the output of an interrupted run
            if os.path.getsize(p) != st['sizes'][kind]:
                with open(p, 'r+b') as f:
                    f.truncate(st['sizes'][kind])
        r = open_scid(path); n = len(r)
        days = np.array(sorted(day_num(d) for d in P['days'][cname]), dtype=np.int64)
        t = np.asarray(r['t'])
        back = np.diff(t) < 0
        s = t // 10**6
        del t
        ds = np.diff(s)
        st['out_of_order'][cname] = dict(back_within_second=int((back & (ds == 0)).sum()), back_across_seconds=int((ds < 0).sum()))
        del back, ds
        order = np.argsort(s, kind='stable') if st['out_of_order'][cname]['back_across_seconds'] else None
        del s
        carry = {'sec': None, 'min': None}; res = {'sec': 0, 'min': 0}; vol = recs = offg = 0
        tgt = {k: os.path.join(a.stage, os.path.basename(p)) for k, p in names.items()} if a.stage else names
        fh = {k: open(p, 'w' if a.stage else 'a', encoding='utf-8', newline='\n') for k, p in tgt.items()}
        try:
            for a0 in range(0, n, CHUNK):
                x = r[order[a0:a0 + CHUNK]] if order is not None else np.array(r[a0:a0 + CHUNK])
                x = x[np.isin(trade_day(x['t'], ex), days)]
                if not len(x):
                    continue
                q = x['c'].astype(np.float64) / a.tick; qr = np.round(q)
                good = qr > 0
                offg += int((np.abs(q - qr) > 1e-4)[good].sum())
                x = x[good]; cc = qr[good] * a.tick
                if not len(x):
                    continue
                loc = to_local(x['t'], a.tz) - UNIX0_US
                vol += int(x['v'].sum(dtype=np.int64)); recs += len(x)
                for kind, unit in (('sec', 10**6), ('min', 60 * 10**6)):
                    b = bars(loc // unit * unit, cc, x['v'], x['n'], x['bv'], x['av'])
                    b, carry[kind] = merge_carry(b, carry[kind])
                    if len(b['k']):
                        res[kind] += write_bars(fh[kind], b, cname)
            for kind in carry:
                if carry[kind] is not None:
                    res[kind] += write_bars(fh[kind], carry[kind], cname)
        finally:
            for f in fh.values():
                f.close()
        if a.stage:                              # append the staged contract to the output in large blocks
            for kind, p in names.items():
                with open(tgt[kind], 'rb') as src, open(p, 'ab') as dst:
                    shutil.copyfileobj(src, dst, 16 << 20)
                os.remove(tgt[kind])
        for kind, p in names.items():
            st['rows'][kind] += res[kind]; st['sizes'][kind] = os.path.getsize(p)
        st['volume'] += vol; st['records'] += recs; st['off_grid'][cname] = offg
        st['done'].append(cname)
        json.dump(st, open(stf, 'w'), indent=1)
        rate = (time.time() - tc) / max(n, 1)
        log(cname, 'records', recs, '| 1s rows', res['sec'], '| 1m rows', res['min'], '| %.0fs' % (time.time() - t0))
    return True


# ------------------------------------------------------------------ finalize

def finalize(a, P):
    out = a.out
    stf = os.path.join(out, '.%s-build-state.json' % a.symbol); st = json.load(open(stf))
    if st['done'] != list(P['days'].keys()):
        raise SystemExit('build not complete')
    for kind in ('sec', 'min'):
        part = os.path.join(out, '%s-1-%s.csv.part' % (a.symbol, kind))
        os.replace(part, part[:-5])
    pd.DataFrame(P['rolls']).to_csv(os.path.join(out, '%s-rolls.csv' % a.symbol), index=False, lineterminator='\n')
    rep = {k: v for k, v in P.items() if k != 'days'}
    rep.update(rows_1sec=st['rows']['sec'], rows_1min=st['rows']['min'], total_volume=st['volume'], total_records=st['records'],
               created=time.strftime('%Y-%m-%d %H:%M:%S'), columns=COLS,
               out_of_order={k: v for k, v in st['out_of_order'].items() if v['back_within_second'] or v['back_across_seconds']},
               off_grid_records={k: v for k, v in st['off_grid'].items() if v})
    json.dump(rep, open(os.path.join(out, '%s-export-report.json' % a.symbol), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    os.remove(stf)
    pf = os.path.join(out, '.%s-plan.json' % a.symbol)
    if os.path.exists(pf):
        os.remove(pf)
    log('done:', st['rows']['sec'], '1-sec rows |', st['rows']['min'], '1-min rows in', out)


# ------------------------------------------------------------------ verify

def csv_keys(df):
    """Date and Time columns (categories) -> local seconds since 1970"""
    d = df['Date'].cat; t = df['Time'].cat
    dd = pd.to_datetime(pd.Series(d.categories), format='%Y/%m/%d')
    days = ((dd - pd.Timestamp('1970-01-01')) // pd.Timedelta(days=1)).to_numpy(np.int64)
    tp = pd.Series(t.categories).str.split(':', expand=True).astype(np.int64)
    sod = (tp[0] * 3600 + tp[1] * 60 + tp[2]).to_numpy(np.int64)
    return days[d.codes.to_numpy()] * 86400 + sod[t.codes.to_numpy()]


def read_bars_csv(src, header):
    df = pd.read_csv(src, header=0 if header else None, names=COLS,
                     dtype={'Date': 'category', 'Time': 'category', 'Contract': 'category'})
    return dict(k=csv_keys(df), o=df.Open.to_numpy(float), h=df.High.to_numpy(float), l=df.Low.to_numpy(float),
                cl=df.Last.to_numpy(float), v=df.Volume.to_numpy(np.int64), n=df.NumberOfTrades.to_numpy(np.int64),
                bv=df.BidVolume.to_numpy(np.int64), av=df.AskVolume.to_numpy(np.int64), con=df.Contract.astype(str).to_numpy())


def to_minutes(S):
    mk = S['k'] // 60 * 60
    idx = np.flatnonzero(np.r_[True, mk[1:] != mk[:-1]]); last = np.r_[idx[1:] - 1, len(mk) - 1]
    return dict(k=mk[idx], o=S['o'][idx], h=np.maximum.reduceat(S['h'], idx), l=np.minimum.reduceat(S['l'], idx),
                cl=S['cl'][last], v=np.add.reduceat(S['v'], idx), n=np.add.reduceat(S['n'], idx),
                bv=np.add.reduceat(S['bv'], idx), av=np.add.reduceat(S['av'], idx), con=S['con'][idx], con2=S['con'][last])


def gap_report(M, a, ex, rep):
    """gaps without trades, weekdays without data and contract changes, from the 1-minute bars"""
    loc = pd.to_datetime(M['k'], unit='s')
    exl = loc.tz_localize(a.tz, ambiguous='NaT', nonexistent='NaT').tz_convert(ex['tz']).tz_localize(None)
    if exl.isna().any():
        raise SystemExit('bar times that do not exist or are ambiguous in %s' % a.tz)
    td = (exl + day_shift(ex)).normalize()
    one = pd.Timedelta(minutes=1)
    r0 = pd.Timedelta(ex['rth'][0] + ':00'); r1 = pd.Timedelta(ex['rth'][1] + ':00')
    back = lambda x: x.tz_localize(ex['tz']).tz_convert(a.tz).tz_localize(None)
    fmt = lambda x: x.strftime('%Y-%m-%d %H:%M')
    gaps = []
    exv, tdv = exl.values, td.values
    gm = (exv[1:] - exv[:-1]) / np.timedelta64(1, 'm') - 1
    for i in np.flatnonzero((tdv[1:] == tdv[:-1]) & (gm >= min(a.gap_rth, a.gap_other))):
        s, e, d = exl[i] + one, exl[i + 1], td[i]
        rth = s < d + r1 and e > d + r0
        if gm[i] >= (a.gap_rth if rth else a.gap_other):
            gaps.append(dict(trading_day=str(d.date()), kind='main session' if rth else 'outside main session',
                             from_local=fmt(loc[i] + one), to_local=fmt(loc[i + 1]), from_exchange=fmt(s), to_exchange=fmt(e),
                             minutes=int(gm[i])))
    g = pd.DataFrame({'td': td, 'ex': exl}).groupby('td').ex.agg(['min', 'max'])
    has = pd.Series(np.asarray((exl >= td + r0) & (exl < td + r1)), index=td).groupby(level=0).any()
    for d, x in g.iterrows():
        rs, re_ = d + r0, d + r1
        if not has[d]:
            gaps.append(dict(trading_day=str(d.date()), kind='no main session', from_local=fmt(back(rs)), to_local=fmt(back(re_)),
                             from_exchange=fmt(rs), to_exchange=fmt(re_), minutes=int((re_ - rs) / one)))
            continue
        if x['min'] - rs >= pd.Timedelta(minutes=a.gap_rth):
            e = min(x['min'], re_)
            gaps.append(dict(trading_day=str(d.date()), kind='main session starts late', from_local=fmt(back(rs)), to_local=fmt(back(e)),
                             from_exchange=fmt(rs), to_exchange=fmt(e), minutes=int((e - rs) / one)))
        if re_ - (x['max'] + one) >= pd.Timedelta(minutes=a.gap_rth) and x['max'] + one > rs:
            s = x['max'] + one
            gaps.append(dict(trading_day=str(d.date()), kind='main session ends early', from_local=fmt(back(s)), to_local=fmt(back(re_)),
                             from_exchange=fmt(s), to_exchange=fmt(re_), minutes=int((re_ - s) / one)))
    gaps.sort(key=lambda z: (z['trading_day'], z['from_exchange']))
    present = set(g.index)
    excl = {e['date']: e['reason'] for e in rep.get('excluded_days', [])}
    missing = [dict(date=str(d.date()), weekday=d.day_name()[:3], reason=excl.get(str(d.date()), 'no data (exchange holiday or missing data)'))
               for d in pd.bdate_range(rep['first_day'], rep['last_day']) if d not in present]
    ch = np.flatnonzero(M['con'][1:] != M['con'][:-1]) + 1
    roll_days = {r['roll_day'] for r in rep.get('rolls', [])}
    first_bar = np.r_[True, tdv[1:] != tdv[:-1]]
    bad_changes = [str(td[i].date()) for i in ch if not first_bar[i] or str(td[i].date()) not in roll_days]
    return gaps, missing, int(len(ch)), bad_changes, int(len(g))


def verify(a, ex):
    out = a.out; t0 = time.time()
    fsec = os.path.join(out, '%s-1-sec.csv' % a.symbol); fmin = os.path.join(out, '%s-1-min.csv' % a.symbol)
    repf = os.path.join(out, '%s-export-report.json' % a.symbol)
    rep = json.load(open(repf, encoding='utf-8'))
    stf = os.path.join(out, '.%s-verify-state.json' % a.symbol)
    sizes = [os.path.getsize(fsec), os.path.getsize(fmin)]
    M = read_bars_csv(fmin, True)
    st = json.load(open(stf)) if os.path.exists(stf) else None
    if st is None or st['sizes'] != sizes:
        with open(fsec, 'rb') as f:
            hdr = f.readline()
        st = dict(sizes=sizes, offset=len(hdr), ptr=0, carry=None, last=None, rows=0, not_increasing=0, ohlc=0,
                  off_tick=0, nonpos=0, ba_ne_volume=0, volume_le0=0, minute_mismatch=0, examples=[])
    tick = rep['tick']

    def compare(B):
        L = len(B['k']); p = st['ptr']; q = min(p + L, len(M['k']))
        bad = np.ones(L, bool)
        m = q - p
        if m > 0:
            ok = np.ones(m, bool)
            for f in ('k', 'o', 'h', 'l', 'cl', 'v', 'n', 'bv', 'av', 'con'):
                ok &= B[f][:m] == M[f][p:q]
            ok &= B['con2'][:m] == M['con'][p:q]
            bad[:m] = ~ok
        st['minute_mismatch'] += int(bad.sum())
        for i in np.flatnonzero(bad)[:max(0, 5 - len(st['examples']))]:
            st['examples'].append(str(pd.to_datetime(int(B['k'][i]), unit='s')))
        st['ptr'] = p + L

    with open(fsec, 'rb') as f:
        while st['offset'] < sizes[0]:
            if time.time() - t0 > a.budget:
                json.dump(st, open(stf, 'w')); log('budget reached, run the same command again'); return False
            f.seek(st['offset']); data = f.read(64 << 20)
            if st['offset'] + len(data) < sizes[0]:
                data = data[:data.rfind(b'\n') + 1]
            st['offset'] += len(data)
            S = read_bars_csv(io.BytesIO(data), False)
            k = S['k']; st['rows'] += len(k)
            prev = st['last'] if st['last'] is not None else k[0] - 1
            st['not_increasing'] += int((np.diff(np.r_[prev, k]) <= 0).sum()); st['last'] = int(k[-1])
            o, h, l, c = S['o'], S['h'], S['l'], S['cl']
            st['ohlc'] += int(((h < np.maximum(o, c)) | (l > np.minimum(o, c)) | (h < l)).sum())
            P4 = np.stack([o, h, l, c])
            st['off_tick'] += int((np.abs(P4 / tick - np.round(P4 / tick)) > 1e-6).any(axis=0).sum())
            st['nonpos'] += int((P4 <= 0).any(axis=0).sum())
            st['ba_ne_volume'] += int((S['bv'] + S['av'] != S['v']).sum()); st['volume_le0'] += int((S['v'] <= 0).sum())
            A = to_minutes(S)
            cr = st['carry']
            if cr is not None:
                if cr['k'] == A['k'][0]:
                    A['o'][0] = cr['o']; A['h'][0] = max(A['h'][0], cr['h']); A['l'][0] = min(A['l'][0], cr['l'])
                    for fl in ('v', 'n', 'bv', 'av'):
                        A[fl][0] += cr[fl]
                    A['con'][0] = cr['con']
                else:
                    A = {fl: np.r_[np.array([cr[fl]], dtype=A[fl].dtype), A[fl]] for fl in FIELDS}
            st['carry'] = {fl: (A[fl][-1].item() if hasattr(A[fl][-1], 'item') else str(A[fl][-1])) for fl in FIELDS}
            compare({fl: A[fl][:-1] for fl in FIELDS})
            json.dump(st, open(stf, 'w'))
    if st['carry'] is not None:
        compare({fl: np.array([st['carry'][fl]]) for fl in FIELDS})
    nmin = len(M['k'])
    gaps, missing, nchanges, bad_changes, ndays = gap_report(M, a, ex, rep)
    ver = dict(tool_version=VERSION, verified=time.strftime('%Y-%m-%d %H:%M:%S'),
               rows_1sec=st['rows'], rows_1min=nmin, trading_days=ndays,
               rows_equal_report=bool(st['rows'] == rep.get('rows_1sec') and nmin == rep.get('rows_1min')),
               minutes_from_1sec_equal_1min=bool(st['minute_mismatch'] == 0 and st['ptr'] == nmin),
               minute_mismatches=st['minute_mismatch'] + abs(st['ptr'] - nmin), mismatch_examples=st['examples'],
               seconds_not_increasing=st['not_increasing'], ohlc_violations=st['ohlc'], prices_off_tick=st['off_tick'],
               nonpositive_prices=st['nonpos'], volume_le0=st['volume_le0'],
               bidask_ne_volume_1sec=st['ba_ne_volume'], bidask_ne_volume_1min=int((M['bv'] + M['av'] != M['v']).sum()),
               contract_changes=nchanges, contract_changes_not_at_roll=bad_changes,
               gap_rules=dict(main_session=list(ex['rth']), exchange_tz=ex['tz'], main_session_min_minutes=a.gap_rth,
                              other_min_minutes=a.gap_other),
               gaps=len(gaps), missing_weekdays=len(missing))
    ver['passed'] = bool(ver['rows_equal_report'] and ver['minutes_from_1sec_equal_1min'] and not ver['seconds_not_increasing']
                         and not ver['ohlc_violations'] and not ver['prices_off_tick'] and not ver['nonpositive_prices']
                         and not ver['volume_le0'] and not bad_changes)
    rep['verification'] = ver; rep['gaps'] = gaps; rep['missing_weekdays'] = missing
    json.dump(rep, open(repf, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if os.path.exists(stf):
        os.remove(stf)
    log('verify:', 'PASSED' if ver['passed'] else 'FAILED',
        {k: v for k, v in ver.items() if k not in ('gap_rules', 'mismatch_examples', 'contract_changes_not_at_roll')})
    return True


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('phase', choices=['plan', 'build', 'finalize', 'verify', 'all'])
    ap.add_argument('--data', help='Sierra Chart Data folder with the .scid files (plan, build)')
    ap.add_argument('--symbol', required=True, help='e.g. FDAX, NQ, ES, YM')
    ap.add_argument('--exchange', required=True, help='one of %s (file name suffix)' % ', '.join(sorted(EXCHANGES)))
    ap.add_argument('--out', required=True, help='output folder, by convention data/<SYMBOL>')
    ap.add_argument('--tz', default='Europe/Prague', help='time zone of the bar labels')
    ap.add_argument('--tick', type=float, default=None, help='price grid; default by symbol: %s' % TICKS)
    ap.add_argument('--min-bidask', type=float, default=0.999)
    ap.add_argument('--min-records', type=int, default=100)
    ap.add_argument('--include-today', action='store_true', help='also export the (possibly incomplete) trading day of the run')
    ap.add_argument('--gap-rth', type=int, default=5, help='verify: report gaps of >= N minutes touching the main session')
    ap.add_argument('--gap-other', type=int, default=60, help='verify: report other gaps of >= N minutes')
    ap.add_argument('--budget', type=float, default=1e9, help='seconds per run of plan/build/verify (resumable, exit code 3)')
    ap.add_argument('--stage', help='build: write each contract to this local folder first, then append it to --out in '
                                    'large blocks (faster when --out is a slow network or synced folder)')
    a = ap.parse_args()
    a.symbol = a.symbol.upper()
    ex = EXCHANGES.get(a.exchange.upper())
    if ex is None:
        raise SystemExit('unknown exchange %s: add it to EXCHANGES' % a.exchange)
    if a.tick is None:
        if a.symbol not in TICKS:
            raise SystemExit('unknown tick size for %s, pass --tick' % a.symbol)
        a.tick = TICKS[a.symbol]
    if a.phase in ('plan', 'build', 'all') and not a.data:
        raise SystemExit('--data is required for %s' % a.phase)
    os.makedirs(a.out, exist_ok=True)
    if a.stage:
        os.makedirs(a.stage, exist_ok=True)
    pf = os.path.join(a.out, '.%s-plan.json' % a.symbol)
    P = None
    if a.phase in ('plan', 'all'):
        P = plan(a, ex)
        if P is None:
            sys.exit(3)
    elif a.phase in ('build', 'finalize'):
        P = json.load(open(pf))
        if P.get('tick') != a.tick or P.get('version') != VERSION:
            raise SystemExit('the plan was made with another tick or tool version, run plan again')
    if a.phase in ('build', 'all'):
        if not build(a, P, ex):
            sys.exit(3)
    if a.phase in ('finalize', 'all'):
        finalize(a, P)
    if a.phase in ('verify', 'all'):
        if not verify(a, ex):
            sys.exit(3)


if __name__ == '__main__':
    main()
