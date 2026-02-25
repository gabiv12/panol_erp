from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from inventario.models import Producto, Ubicacion, MovimientoStock, StockActual
from inventario.services import stock as stock_service


class StockServiceTests(TestCase):
    def setUp(self):
        self.prod = Producto.objects.create(codigo="P-001", nombre="Producto X")
        self.u1 = Ubicacion.objects.create(codigo="U-01", nombre="Ubicación 1")
        self.u2 = Ubicacion.objects.create(codigo="U-02", nombre="Ubicación 2")

    def _stock(self, ubic: Ubicacion) -> StockActual:
        obj, _ = StockActual.objects.get_or_create(producto=self.prod, ubicacion=ubic)
        obj.refresh_from_db()
        return obj

    def test_ingreso_actualiza_stock_y_last_movement_at(self):
        mov = MovimientoStock.objects.create(
            producto=self.prod,
            ubicacion=self.u1,
            tipo=MovimientoStock.Tipo.INGRESO,
            cantidad=Decimal("10"),
        )
        stock_service.aplicar_movimiento_creado(mov)

        st = self._stock(self.u1)
        self.assertEqual(st.cantidad, Decimal("10"))
        self.assertIsNotNone(st.last_movement_at)
        self.assertTrue(timezone.is_aware(st.last_movement_at))

    def test_egreso_valida_stock_suficiente(self):
        mov_in = MovimientoStock.objects.create(
            producto=self.prod,
            ubicacion=self.u1,
            tipo=MovimientoStock.Tipo.INGRESO,
            cantidad=Decimal("5"),
        )
        stock_service.aplicar_movimiento_creado(mov_in)

        mov_out = MovimientoStock.objects.create(
            producto=self.prod,
            ubicacion=self.u1,
            tipo=MovimientoStock.Tipo.EGRESO,
            cantidad=Decimal("3"),
        )
        stock_service.aplicar_movimiento_creado(mov_out)

        st = self._stock(self.u1)
        self.assertEqual(st.cantidad, Decimal("2"))

    def test_egreso_insuficiente_levanta_error_y_no_modifica(self):
        mov_out = MovimientoStock.objects.create(
            producto=self.prod,
            ubicacion=self.u1,
            tipo=MovimientoStock.Tipo.EGRESO,
            cantidad=Decimal("1"),
        )

        with self.assertRaises(ValueError):
            stock_service.aplicar_movimiento_creado(mov_out)

        st = self._stock(self.u1)
        self.assertEqual(st.cantidad, Decimal("0"))

    def test_transferencia_mueve_stock(self):
        mov_in = MovimientoStock.objects.create(
            producto=self.prod,
            ubicacion=self.u1,
            tipo=MovimientoStock.Tipo.INGRESO,
            cantidad=Decimal("10"),
        )
        stock_service.aplicar_movimiento_creado(mov_in)

        mov_tr = MovimientoStock.objects.create(
            producto=self.prod,
            ubicacion=self.u1,
            ubicacion_destino=self.u2,
            tipo=MovimientoStock.Tipo.TRANSFERENCIA,
            cantidad=Decimal("4"),
        )
        stock_service.aplicar_movimiento_creado(mov_tr)

        st1 = self._stock(self.u1)
        st2 = self._stock(self.u2)
        self.assertEqual(st1.cantidad, Decimal("6"))
        self.assertEqual(st2.cantidad, Decimal("4"))

    def test_actualizar_movimiento_aplica_delta(self):
        mov = MovimientoStock.objects.create(
            producto=self.prod,
            ubicacion=self.u1,
            tipo=MovimientoStock.Tipo.INGRESO,
            cantidad=Decimal("10"),
        )
        stock_service.aplicar_movimiento_creado(mov)

        old = stock_service.MovimientoSnapshot(
            producto_id=mov.producto_id,
            ubicacion_id=mov.ubicacion_id,
            tipo=mov.tipo,
            cantidad=mov.cantidad,
            ubicacion_destino_id=mov.ubicacion_destino_id,
        )

        # Simulamos edición: cambia cantidad de 10 a 6
        mov.cantidad = Decimal("6")
        mov.save(update_fields=["cantidad"])

        stock_service.aplicar_movimiento_actualizado(old, mov)

        st = self._stock(self.u1)
        self.assertEqual(st.cantidad, Decimal("6"))

    def test_eliminar_movimiento_revierte(self):
        mov = MovimientoStock.objects.create(
            producto=self.prod,
            ubicacion=self.u1,
            tipo=MovimientoStock.Tipo.INGRESO,
            cantidad=Decimal("3"),
        )
        stock_service.aplicar_movimiento_creado(mov)
        self.assertEqual(self._stock(self.u1).cantidad, Decimal("3"))

        stock_service.aplicar_movimiento_eliminado(mov)
        self.assertEqual(self._stock(self.u1).cantidad, Decimal("0"))
