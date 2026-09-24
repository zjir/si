#!/usr/bin/env bash
# Lokální smyčka review: každé kolo = nový proces claude -p = nezávislý recenzent.
# Konec: verdikt APPROVED, strop kol, dvě kola bez změny, nebo opakované selhání.
set -uo pipefail

cd "$(dirname "$0")"

MAX_ROUNDS="${MAX_ROUNDS:-8}"
MODELS=(${MODELS:-opus sonnet opus sonnet})   # střídání modelů mezi koly
RETRIES="${RETRIES:-3}"                       # pokusy při selhání (např. vyčerpaný limit)
RETRY_SLEEP="${RETRY_SLEEP:-3600}"            # pauza mezi pokusy v sekundách
TOOLS="${TOOLS:-Read,Edit,Write,Glob,Grep}"   # agent nepotřebuje Bash ani síť

mkdir -p logs
command -v claude >/dev/null || { echo "claude CLI nenalezeno"; exit 1; }
[ -f spec.md ] || { echo "chybí spec.md"; exit 1; }
[ -f input/pat-system.txt ] || { echo "chybí input/pat-system.txt (spusť ./setup.sh)"; exit 1; }
[ -d .git ] || { echo "chybí git repozitář (spusť ./setup.sh)"; exit 1; }

no_change_streak=0

for (( round=1; round<=MAX_ROUNDS; round++ )); do
  model="${MODELS[$(( (round-1) % ${#MODELS[@]} ))]}"
  log="logs/round_$(printf '%02d' "$round")_${model}.log"
  echo "=== kolo $round, model $model, $(date '+%Y-%m-%d %H:%M:%S') ==="

  rm -f verdict.json
  attempt=1
  while : ; do
    claude -p "$(cat prompts/review.md)" \
      --bare \
      --model "$model" \
      --allowedTools "$TOOLS" \
      --permission-mode acceptEdits \
      >"$log" 2>&1
    rc=$?
    [ $rc -eq 0 ] && break
    echo "  běh selhal (rc=$rc), pokus $attempt/$RETRIES, viz $log"
    if [ "$attempt" -ge "$RETRIES" ]; then
      echo "  smyčka končí kvůli opakovanému selhání"
      exit "$rc"
    fi
    attempt=$(( attempt + 1 ))
    sleep "$RETRY_SLEEP"
  done

  if [ ! -f verdict.json ]; then
    echo "  agent nezapsal verdict.json, viz $log; smyčka končí"
    exit 2
  fi

  read -r blocking medium minor verdict summary < <(python3 - <<'PY'
import json
v = json.load(open("verdict.json"))
print(v.get("blocking", -1), v.get("medium", -1), v.get("minor", -1),
      v.get("verdict", "?"), v.get("summary", "").replace("\n", " "))
PY
  )
  echo "  nálezy B/S/D: $blocking/$medium/$minor, verdikt: $verdict"
  echo "  $summary"

  git add -A
  if git diff --cached --quiet; then
    no_change_streak=$(( no_change_streak + 1 ))
    echo "  beze změn v dokumentu ($no_change_streak v řadě)"
  else
    no_change_streak=0
    git commit -q -m "review kolo $round ($model): B=$blocking S=$medium D=$minor $verdict"
    echo "  změny commitnuty"
  fi

  if [ "$verdict" = "APPROVED" ]; then
    echo "=== SCHVÁLENO v kole $round ==="
    exit 0
  fi
  if [ "$no_change_streak" -ge 2 ]; then
    echo "=== konec: dvě kola bez jediné změny, smyčka nekonverguje ==="
    exit 3
  fi
done

echo "=== konec: vyčerpán strop $MAX_ROUNDS kol bez schválení ==="
exit 4
