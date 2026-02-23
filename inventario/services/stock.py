from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
from decimal import Decimal

from django.db import transaction
from django.db.models import F

from inventario.models import MovimientoStock, StockActual


@dataclass(frozen=True)
class MovimientoSnapshot:
    producto_id: int
    ubicacion_id: int
    tipo: str
    cantidad: Decimal
    ubicacion_destino_id: int | None = None


def _get_qty(val) -> Decimal:
    try:
        return Decimal(val)
    except Exception:
        return Decimal("0")


def _stock_row(producto_id: int, ubicacion_id: int) -> StockActual:
    obj, _ = StockActual.objects.select_for_update().get_or_create(
        producto_id=producto_id,
        ubicacion_id=ubicacion_id,
        defaults={"cantidad": Decimal("0")},
    )
    return obj


def _apply_ingreso(producto_id: int, ubicacion_id: int, qty: Decimal) -> None:
    st = _stock_row(producto_id, ubicacion_id)
    StockActual.objects.filter(pk=st.pk).update(
        cantidad=F("cantidad") + qty,
        last_movement_at=timezone.now(),
    )


def _apply_egreso(producto_id: int, ubicacion_id: int, qty: Decimal) -> None:
    st = _stock_row(producto_id, ubicacion_id)
    # Validación: no dejar stock negativo
    st.refresh_from_db(fields=["cantidad"])
    if st.cantidad - qty < 0:
        raise ValueError("Stock insuficiente para registrar el egreso.")

    StockActual.objects.filter(pk=st.pk).update(
        cantidad=F("cantidad") - qty,
        last_movement_at=timezone.now(),
    )


def _apply_ajuste(producto_id: int, ubicacion_id: int, qty: Decimal) -> None:
    # Ajuste suma (puede ser negativo)
    st = _stock_row(producto_id, ubicacion_id)
    st.refresh_from_db(fields=["cantidad"])
    if st.cantidad + qty < 0:
        raise ValueError("El ajuste dejaría el stock en negativo.")

    StockActual.objects.filter(pk=st.pk).update(
        cantidad=F("cantidad") + qty,
        last_movement_at=timezone.now(),
    )


def _apply_transferencia(producto_id: int, ub_origen_id: int, ub_destino_id: int, qty: Decimal) -> None:
    # Origen egreso, destino ingreso
    _apply_egreso(producto_id, ub_origen_id, qty)
    _apply_ingreso(producto_id, ub_destino_id, qty)


def aplicar_movimiento_creado(mov: MovimientoStock) -> None:
    qty = _get_qty(mov.cantidad)

    if mov.tipo == MovimientoStock.Tipo.INGRESO:
        _apply_ingreso(mov.producto_id, mov.ubicacion_id, qty)
    elif mov.tipo == MovimientoStock.Tipo.EGRESO:
        _apply_egreso(mov.producto_id, mov.ubicacion_id, qty)
    elif mov.tipo == MovimientoStock.Tipo.AJUSTE:
        _apply_ajuste(mov.producto_id, mov.ubicacion_id, qty)
    elif mov.tipo == MovimientoStock.Tipo.TRANSFERENCIA:
        if not mov.ubicacion_destino_id:
            raise ValueError("La transferencia requiere una ubicación destino.")
        _apply_transferencia(mov.producto_id, mov.ubicacion_id, mov.ubicacion_destino_id, qty)
    else:
        raise ValueError("Tipo de movimiento inválido.")


@transaction.atomic
def aplicar_movimiento_actualizado(old: MovimientoSnapshot, mov: MovimientoStock) -> None:
    """Reversa el efecto del movimiento viejo y aplica el nuevo."""

    # 1) revertir viejo
    qty_old = _get_qty(old.cantidad)

    if old.tipo == MovimientoStock.Tipo.INGRESO:
        _apply_egreso(old.producto_id, old.ubicacion_id, qty_old)
    elif old.tipo == MovimientoStock.Tipo.EGRESO:
        _apply_ingreso(old.producto_id, old.ubicacion_id, qty_old)
    elif old.tipo == MovimientoStock.Tipo.AJUSTE:
        _apply_ajuste(old.producto_id, old.ubicacion_id, -qty_old)
    elif old.tipo == MovimientoStock.Tipo.TRANSFERENCIA:
        if not old.ubicacion_destino_id:
            raise ValueError("Movimiento viejo inconsistente: falta destino.")
        # revertir transferencia = ingreso en origen + egreso en destino
        _apply_ingreso(old.producto_id, old.ubicacion_id, qty_old)
        _apply_egreso(old.producto_id, old.ubicacion_destino_id, qty_old)

    # 2) aplicar nuevo
    aplicar_movimiento_creado(mov)


@transaction.atomic
def aplicar_movimiento_eliminado(mov: MovimientoStock) -> None:
    """Reversa el efecto del movimiento eliminado."""

    qty = _get_qty(mov.cantidad)

    if mov.tipo == MovimientoStock.Tipo.INGRESO:
        _apply_egreso(mov.producto_id, mov.ubicacion_id, qty)
    elif mov.tipo == MovimientoStock.Tipo.EGRESO:
        _apply_ingreso(mov.producto_id, mov.ubicacion_id, qty)
    elif mov.tipo == MovimientoStock.Tipo.AJUSTE:
        _apply_ajuste(mov.producto_id, mov.ubicacion_id, -qty)
    elif mov.tipo == MovimientoStock.Tipo.TRANSFERENCIA:
        if not mov.ubicacion_destino_id:
            raise ValueError("La transferencia requiere una ubicación destino.")
        # revertir transferencia = ingreso en origen + egreso en destino
        _apply_ingreso(mov.producto_id, mov.ubicacion_id, qty)
        _apply_egreso(mov.producto_id, mov.ubicacion_destino_id, qty)
    else:
        raise ValueError("Tipo de movimiento inválido.")
