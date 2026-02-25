import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXTS = {".py", ".html", ".htm", ".js", ".css", ".md", ".txt"}
SKIP = {".venv", "node_modules", "media", "staticfiles", "__pycache__", ".pytest_cache", ".git"}

REPL = {
    # Acentos comunes
    "á":"á","é":"é","í":"í","ó":"ó","ú":"ú","ñ":"ñ",
    "Á":"Á","É":"É","Í":"Í","Ó":"Ó","Ú":"Ú","Ñ":"Ñ",
    "ü":"ü","Ü":"Ü",

    # Puntuación / símbolos típicos de UTF8 mal decodificado
    "–":"–","—":"—","“":"“","”":"”","’":"’","‘":"‘",
    "°":"°","º":"º","·":"·"," ":" ",  # NBSP

    # Casos específicos que te aparecen (corregimos a español correcto)
    "Número":"Número",
    "Número":"Número",
}

def should_skip(p: pathlib.Path) -> bool:
    return any(part in SKIP for part in p.parts)

def fix_text(s: str) -> str:
    for a, b in REPL.items():
        s = s.replace(a, b)
    return s

changed = 0
scanned = 0

for p in ROOT.rglob("*"):
    if p.is_dir() or should_skip(p) or p.suffix.lower() not in EXTS:
        continue

    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        continue

    scanned += 1
    new = fix_text(txt)
    if new != txt:
        p.write_text(new, encoding="utf-8", newline="\n")
        changed += 1
        print(f"FIXED: {p}")

print(f"Done. Files scanned: {scanned}. Files changed: {changed}.")
