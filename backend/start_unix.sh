#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3.12 >/dev/null 2>&1; then
  echo "Python 3.12 is required. Install Python 3.12 and try again." >&2
  exit 1
fi
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
python create_tables.py
python seed_roles.py
python -m uvicorn app.main:app --reload
