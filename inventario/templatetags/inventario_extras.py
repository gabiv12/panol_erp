from __future__ import annotations

from decimal import Decimal

from django import template
from django.utils.formats import number_format

register = template.Library()

from django.http import QueryDict

@register.simple_tag(takes_context=True)
def qs_replace(context, **kwargs):
    """Reemplaza/agrega parámetros de querystring preservando el resto.

    Para eliminar un parámetro, pasá valor vacío ("") o None.
    """
    request = context.get("request")
    if not request:
        return ""
    qd = request.GET.copy()
    for k, v in kwargs.items():
        if v is None or v == "":
            if k in qd:
                qd.pop(k)
        else:
            qd[k] = str(v)
    return qd.urlencode()


@register.filter
def qty(value, unidad=None) -> str:
    """Formatea cantidades de stock de forma "humana".

    - Si la unidad NO permite decimales (permite_decimales=False) -> 0 decimales.
    - Si permite decimales -> hasta 3 decimales, pero **recorta ceros**.

    Importante: en locale es-AR el separador decimal es ",".
    """

    if value is None:
        return "—"

    try:
        val = Decimal(str(value))
    except Exception:
        return str(value)

    # Por defecto permitimos hasta 3 decimales
    max_dec = 3
    if unidad is not None and getattr(unidad, "permite_decimales", True) is False:
        max_dec = 0

    if max_dec == 0:
        return number_format(val, decimal_pos=0, use_l10n=True, force_grouping=False)

    q = Decimal("0." + "0" * (max_dec - 1) + "1")
    val_q = val.quantize(q)

    # Si quedó entero -> mostrar sin decimales
    if val_q == val_q.to_integral():
        return number_format(val_q, decimal_pos=0, use_l10n=True, force_grouping=False)

    # Calcular decimales realmente necesarios (recortando ceros)
    s = format(val_q, "f")  # usa '.' como decimal
    if "." in s:
        s2 = s.rstrip("0").rstrip(".")
        dec = len(s2.split(".")[1]) if "." in s2 else 0
    else:
        dec = 0

    return number_format(val_q, decimal_pos=dec, use_l10n=True, force_grouping=False)
@register.filter
def qty_auto(value, unidad=None) -> str:
    """Alias de `qty` (para que el template sea más legible)."""
    return qty(value, unidad)


@register.filter
def ubic_path(ubicacion, sep: str = " / ") -> str:
    """Devuelve la ruta jerárquica de códigos de una ubicación."""
    if not ubicacion:
        return "—"
    if hasattr(ubicacion, "path_codigos"):
        try:
            return ubicacion.path_codigos(sep=sep)
        except TypeError:
            # por si el método no acepta sep por nombre
            return ubicacion.path_codigos(sep)
    return getattr(ubicacion, "codigo", str(ubicacion))
