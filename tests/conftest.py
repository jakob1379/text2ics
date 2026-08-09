import sys
from pathlib import Path

# app/ uses flat imports (`from utils import ...`), the layout Streamlit runs it
# with, so it is importable only with app/ on the path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
