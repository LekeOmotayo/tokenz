"""
Root delegator for Leke Local Token Cache.
Delegates to backend.cmd.main for senior standard modularity.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.cmd.main import main

if __name__ == "__main__":
    main()
