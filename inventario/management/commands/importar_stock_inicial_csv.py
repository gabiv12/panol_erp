from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from inventario.models import Producto, Proveedor, Ubicacion, MovimientoStock
from inventario.services import stock as stock_service


def _sniff_delimiter(sample: str) -> str:
    # Heurística simple (Excel AR suele usar ;)
    if sample.count(";") >= sample.count(",") and sample.count(";") > 0:
        return ";"
    if sample.count(",") > 0:
        return ","
    return ";"


class Command(BaseCommand):
    help = (
        "Importa un CSV de stock inicial y genera movimientos INGRESO (aplicando StockActual). "
        "Ideal para el primer inventario del depósito."
    )

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Ruta del CSV a importar.")
        parser.add_argument(
            "--username",
            default="",
            help="Usuario responsable (username). Si se omite, queda vacío.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="No guarda nada; sólo valida y muestra totales.",
        )
        parser.add_argument(
            "--delimiter",
            default="",
            help="Separador CSV. Si se omite, se autodetecta.",
        )
        parser.add_argument(
            "--default-ref",
            default="Stock inicial",
            help="Referencia por defecto si la columna 'referencia' viene vacía.",
        )

    def handle(self, *args, **opts):
        file_path = Path(opts["file"])
        if not file_path.exists():
            raise CommandError(f"No existe el archivo: {file_path}")

        username = (opts.get("username") or "").strip()
        dry = bool(opts.get("dry_run"))
        default_ref = (opts.get("default_ref") or "Stock inicial").strip()

        user = None
        if username:
            U = get_user_model()
            try:
                user = U.objects.get(username=username)
            except U.DoesNotExist:
                raise CommandError(f"No existe el usuario: {username}")

        raw = file_path.read_text(encoding="utf-8-sig")
        delim = (opts.get("delimiter") or "").strip() or _sniff_delimiter(raw[:2048])

        r = csv.DictReader(raw.splitlines(), delimiter=delim)
        required = {"producto_codigo", "ubicacion_codigo", "cantidad"}
        missing = required - set(r.fieldnames or [])
        if missing:
            raise CommandError(f"Faltan columnas requeridas: {', '.join(sorted(missing))}")

        total_rows = 0
        ok_rows = 0
        skipped_zero = 0
        created = 0

        errors = []

        with transaction.atomic():
            for i, row in enumerate(r, start=2):  # 1 = header
                total_rows += 1
                try:
                    p_code = (row.get("producto_codigo") or row.get("codigo") or "").strip().upper()
                    u_code = (row.get("ubicacion_codigo") or row.get("ubicacion") or "").strip().upper()
                    qty_raw = (row.get("cantidad") or "0").strip().replace(",", ".")

                    if not p_code or not u_code:
                        raise ValueError("producto_codigo y ubicacion_codigo son obligatorios.")

                    qty = Decimal(qty_raw)
                    if qty == 0:
                        skipped_zero += 1
                        continue
                    if qty < 0:
                        raise ValueError("cantidad no puede ser negativa (para stock inicial).")

                    producto = Producto.objects.get(codigo=p_code)
                    ubic = Ubicacion.objects.get(codigo=u_code)

                    ref = (row.get("referencia") or "").strip() or default_ref
                    obs = (row.get("observaciones") or row.get("obs") or "").strip()

                    proveedor = None
                    prov_raw = (row.get("proveedor") or "").strip()
                    if prov_raw:
                        # Intento: CUIT exacto -> nombre exacto
                        proveedor = Proveedor.objects.filter(cuit=prov_raw).first() or Proveedor.objects.filter(nombre__iexact=prov_raw).first()

                    mov = MovimientoStock(
                        producto=producto,
                        ubicacion=ubic,
                        tipo=MovimientoStock.Tipo.INGRESO,
                        cantidad=qty,
                        proveedor=proveedor,
                        referencia=ref,
                        observaciones=obs,
                        usuario=user,
                    )

                    mov.full_clean()
                    ok_rows += 1

                    if not dry:
                        mov.save()
                        stock_service.aplicar_movimiento_creado(mov)
                        created += 1

                except Exception as e:
                    errors.append(f"Fila {i}: {e}")

            if dry:
                transaction.set_rollback(True)

        if errors:
            msg = "Errores:\n" + "\n".join(errors[:30])
            if len(errors) > 30:
                msg += f"\n... ({len(errors) - 30} más)"
            raise CommandError(msg)

        if dry:
            self.stdout.write(self.style.WARNING(f"DRY-RUN OK. Filas: {total_rows}. Validadas: {ok_rows}. Omitidas por 0: {skipped_zero}."))
        else:
            self.stdout.write(self.style.SUCCESS(f"OK: filas {total_rows}. Movimientos creados: {created}. Omitidas por 0: {skipped_zero}."))
