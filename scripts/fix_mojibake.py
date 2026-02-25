import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

EXTS = {".py", ".html", ".htm", ".js", ".css", ".md", ".txt"}
SKIP_DIRS = {".venv", "node_modules", "media", "staticfiles", "__pycache__", ".pytest_cache", ".git"}

MARKERS = ["Ã", "Â", "â€", "’", "“", "”", "–", "—"]

def marker_count(s: str) -> int:
    return sum(s.count(m) for m in MARKERS)

def looks_mojibake(s: str) -> bool:
    return marker_count(s) > 0

def fix_latin1_to_utf8(s: str) -> str | None:
    # típico caso: UTF-8 bytes leídos como Latin-1 → "Número"
    try:
        return s.encode("latin-1").decode("utf-8")
    except Exception:
        return None

def should_skip(path: pathlib.Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)

fixed = 0
checked = 0

for p in ROOT.rglob("*"):
    if p.is_dir():
        continue
    if should_skip(p):
        continue
    if p.suffix.lower() not in EXTS:
        continue

    try:
        txt = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # si algún archivo estuviera en cp1252, lo leemos así
        try:
            txt = p.read_text(encoding="cp1252")
        except Exception:
            continue

    if not looks_mojibake(txt):
        continue

    checked += 1
    before = marker_count(txt)
    new = fix_latin1_to_utf8(txt)
    if not new:
        continue

    after = marker_count(new)

    # solo aceptamos si mejora fuerte y elimina markers
    if after == 0 and before > 0:
        p.write_text(new, encoding="utf-8", newline="\n")
        fixed += 1
        print(f"FIXED: {p}")

print(f"Done. Files fixed: {fixed}. Files with mojibake checked: {checked}.")
