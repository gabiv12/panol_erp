import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXTS = {".py",".html",".htm",".js",".css",".md",".txt"}
SKIP = {".venv","node_modules","media","staticfiles","__pycache__",".pytest_cache",".git"}

REPL = {
  "·":"·",
  "Próx.":"Próx.",
  "Sesión":"Sesión",
  "Pañol":"Pañol",
  "Órdenes":"Órdenes",
  "revisión":"revisión",
  "técnica":"técnica",
  "último":"último",
  "Número":"Número",
}

def should_skip(p: pathlib.Path) -> bool:
  return any(part in SKIP for part in p.parts)

changed = 0
for p in ROOT.rglob("*"):
  if p.is_dir() or should_skip(p) or p.suffix.lower() not in EXTS:
    continue
  try:
    txt = p.read_text(encoding="utf-8")
  except Exception:
    continue
  new = txt
  for a,b in REPL.items():
    new = new.replace(a,b)
  if new != txt:
    p.write_text(new, encoding="utf-8", newline="\n")
    changed += 1
print(f"Done. Files changed: {changed}")
