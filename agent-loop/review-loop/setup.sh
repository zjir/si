#!/usr/bin/env bash
# Jednorázová příprava: převod PDF systému na text, git repozitář, kontrola nástrojů.
set -euo pipefail
cd "$(dirname "$0")"

PDF="${PDF:-input/Popis_OS_P_A_T.pdf}"

command -v claude >/dev/null || { echo "chybí claude CLI: https://code.claude.com"; exit 1; }
command -v python3 >/dev/null || { echo "chybí python3"; exit 1; }
command -v git >/dev/null || { echo "chybí git"; exit 1; }

if [ ! -f input/pat-system.txt ]; then
  [ -f "$PDF" ] || { echo "vlož PDF systému P.A.T. jako $PDF a spusť znovu"; exit 1; }
  if command -v pdftotext >/dev/null; then
    pdftotext -layout "$PDF" input/pat-system.txt
  else
    python3 - "$PDF" <<'PY'
import sys
try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("chybí pdftotext i pypdf: brew install poppler   nebo   pip install pypdf")
r = PdfReader(sys.argv[1])
with open("input/pat-system.txt", "w", encoding="utf-8") as f:
    for i, p in enumerate(r.pages, 1):
        f.write(f"\n\n=== strana {i} ===\n\n")
        f.write(p.extract_text() or "")
PY
  fi
  echo "text systému: input/pat-system.txt ($(wc -c < input/pat-system.txt) B)"
  echo "POZNÁMKA: z PDF se vytáhne jen text, obrázky grafů ne."
fi

chmod +x run_review_loop.sh

if [ ! -d .git ]; then
  git init -q
  git add -A
  git commit -q -m "výchozí zadání komponenty (kolo 0)"
  echo "git repozitář založen"
fi

echo "hotovo. Spuštění jednoho průběhu: ./run_review_loop.sh"
