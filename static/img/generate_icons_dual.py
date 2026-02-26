import io
import json
from pathlib import Path

from PIL import Image
import cairosvg


SIZES = [16, 32, 48, 64, 96, 128, 144, 150, 180, 192, 256, 384, 512]
ICO_SIZES = [16, 32, 48, 64, 256]


def svg_to_square_png(svg_bytes: bytes, size: int, out_path: Path):
    """
    Renderiza SVG -> PNG y lo centra en canvas cuadrado (size x size) con fondo transparente.
    Renderizamos por altura para evitar desbordes si el SVG no es perfectamente cuadrado.
    """
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_height=size)
    im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    if im.width > size or im.height > size:
        im.thumbnail((size, size), Image.LANCZOS)

    x = (size - im.width) // 2
    y = (size - im.height) // 2
    canvas.paste(im, (x, y), im)
    canvas.save(out_path, format="PNG", optimize=True)


def make_ico(icons_dir: Path, out_path: Path):
    imgs = [Image.open(icons_dir / f"icon-{s}.png").convert("RGBA") for s in ICO_SIZES]
    imgs[0].save(out_path, format="ICO", sizes=[(s, s) for s in ICO_SIZES])


def make_og_images(svg_bytes: bytes, out_dir: Path, bg_rgb=(11, 11, 11)):
    # OG 1200x630
    og_w, og_h = 1200, 630
    logo_png = Image.open(
        io.BytesIO(cairosvg.svg2png(bytestring=svg_bytes, output_height=520))
    ).convert("RGBA")

    bg = Image.new("RGBA", (og_w, og_h), (*bg_rgb, 255))
    logo = logo_png.copy()
    logo.thumbnail((int(og_w * 0.8), int(og_h * 0.8)), Image.LANCZOS)
    bg.paste(logo, ((og_w - logo.width) // 2, (og_h - logo.height) // 2), logo)
    bg.convert("RGB").save(out_dir / "og-image-1200x630.png", format="PNG", optimize=True)

    # Square social 1024
    sq = Image.new("RGBA", (1024, 1024), (*bg_rgb, 255))
    logo2 = logo_png.copy()
    logo2.thumbnail((820, 820), Image.LANCZOS)
    sq.paste(logo2, ((1024 - logo2.width) // 2, (1024 - logo2.height) // 2), logo2)
    sq.convert("RGB").save(out_dir / "social-1024.png", format="PNG", optimize=True)


def build_set(svg_path: Path, icons_out: Path, set_name: str):
    svg_bytes = svg_path.read_bytes()

    # Guardar el svg tal cual
    (icons_out / "favicon.svg").write_bytes(svg_bytes)

    # PNGs
    for s in SIZES:
        svg_to_square_png(svg_bytes, s, icons_out / f"icon-{s}.png")

    # Alias esperados por plataformas
    (icons_out / "apple-touch-icon.png").write_bytes((icons_out / "icon-180.png").read_bytes())
    (icons_out / "icon-192.png").write_bytes((icons_out / "icon-192.png").read_bytes())
    (icons_out / "icon-512.png").write_bytes((icons_out / "icon-512.png").read_bytes())

    # ICO multi-size
    make_ico(icons_out, icons_out / "favicon.ico")

    # OG images (para compartir)
    # Fondo: si es set oscuro, fondo oscuro. Si es claro, fondo claro.
    bg = (11, 11, 11) if set_name == "dark" else (245, 245, 245)
    make_og_images(svg_bytes, icons_out, bg_rgb=bg)


def main():
    pictures = Path(r"C:\Users\gabi\Pictures")
    svg_light = pictures / "fondo_blanco.svg"
    svg_dark = pictures / "fondo_oscuro.svg"

    if not svg_light.exists():
        raise FileNotFoundError(f"No encuentro: {svg_light}")
    if not svg_dark.exists():
        raise FileNotFoundError(f"No encuentro: {svg_dark}")

    out_root = pictures / "django_icon_pack"
    static_dir = out_root / "static"
    icons_dir = static_dir / "icons"
    light_dir = icons_dir / "light"
    dark_dir = icons_dir / "dark"
    light_dir.mkdir(parents=True, exist_ok=True)
    dark_dir.mkdir(parents=True, exist_ok=True)

    # Generar ambos sets
    build_set(svg_light, light_dir, "light")
    build_set(svg_dark, dark_dir, "dark")

    # manifest (PWA): OJO: normalmente NO cambia con dark mode. Elegimos DARK por defecto.
    manifest = {
        "name": "Mi Sistema",
        "short_name": "Sistema",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0b0b0b",
        "theme_color": "#0b0b0b",
        "icons": [
            {"src": "/static/icons/dark/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/dark/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/static/icons/dark/icon-144.png", "sizes": "144x144", "type": "image/png"},
        ],
    }
    (static_dir / "manifest.webmanifest").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # browserconfig.xml (Windows tiles, opcional) -> dark
    (static_dir / "browserconfig.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
  <msapplication>
    <tile>
      <square150x150logo src="/static/icons/dark/icon-150.png"/>
      <TileColor>#0b0b0b</TileColor>
    </tile>
  </msapplication>
</browserconfig>
""",
        encoding="utf-8",
    )

    # Acceso directo Windows descargable (.url) -> usa ICO dark
    # (esto crea un archivo en Pictures; luego lo podés copiar a escritorio)
    url_shortcut = pictures / "MiSistema.url"
    content = "\n".join([
        "[InternetShortcut]",
        "URL=https://TU-DOMINIO/",  # <-- CAMBIAR
        "IconFile=https://TU-DOMINIO/static/icons/dark/favicon.ico",  # <-- CAMBIAR
        "IconIndex=0",
        "",
    ])
    url_shortcut.write_text(content, encoding="utf-8")

    print("✅ Listo.")
    print(f"Generado en: {out_root}")
    print(f"Acceso directo Windows (plantilla): {url_shortcut}")


if __name__ == "__main__":
    main()