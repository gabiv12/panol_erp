import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXTS = {".py", ".html", ".htm", ".js", ".css", ".md", ".txt"}
SKIP = {".venv", "node_modules", "media", "staticfiles", "__pycache__", ".pytest_cache", ".git"}

MARKERS = ["Ã", "Â", "â€", "’", "“", "”", "–", "—", "°", "º"]

def marker_count(s: str) -> int:
    return sum(s.count(m) for m in MARKERS)

def try_convert(s: str, src_enc: str) -> str | None:
    try:
        return s.encode(src_enc).decode("utf-8")
    except Exception:
        return None

def best_fix(s: str) -> tuple[str, int] | None:
    before = marker_count(s)
    if before == 0:
        return None

    candidates = []
    for enc in ("latin-1", "cp1252"):
        c = try_convert(s, enc)
        if c:
            candidates.append(c)

    if not candidates:
        return None

    # Elegimos el que más reduce markers
    best = min(candidates, key=lambda x: marker_count(x))
    after = marker_count(best)

    # Aceptamos si mejora claramente
    if after < before:
        return best, after
    return None

def should_skip(p: pathlib.Path) -> bool:
    return any(part in SKIP for part in p.parts)

fixed = 0
touched = 0

for p in ROOT.rglob("*"):
    if p.is_dir() or should_skip(p) or p.suffix.lower() not in EXTS:
        continue

    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        # si no lo podemos leer, lo saltamos
        continue

    before = marker_count(txt)
    if before == 0:
        continue

    original = txt
    # Aplicamos hasta 2 pasadas (por si hay doble mojibake)
    for _ in range(2):
        res = best_fix(txt)
        if not res:
            break
        txt, after = res

    if txt != original and marker_count(txt) < marker_count(original):
        p.write_text(txt, encoding="utf-8", newline="\n")
        fixed += 1
        print(f"FIXED: {p}")
    touched += 1

print(f"Done. Files fixed: {fixed}. Files scanned with markers: {touched}.")
