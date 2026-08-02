from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LAMBDA = RAIZ / "lambda"
PROXY = RAIZ / "local_proxy"
sys.path.insert(0, str(LAMBDA))
sys.path.insert(0, str(PROXY))
