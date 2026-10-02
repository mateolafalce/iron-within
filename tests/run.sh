#!/bin/bash
# Logic tests, JavaScript syntax, and the shader pixel contract.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv
fi

cjs tests/grade_logic_test.js
cjs tests/syntax_check.js
.venv/bin/python -m unittest discover -s tests -v
