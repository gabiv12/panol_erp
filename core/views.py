from __future__ import annotations

from datetime import timedelta
import logging

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Value, Q, DecimalField
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import requires_csrf_token

from flota.models import Colectivo
from inventario.models import Producto, StockActual, MovimientoStock, Ubicacion


_csrf_logger = logging.getLogger("django.security.csrf")

# Tipo Decimal consistente con tu inventario (12,3)
QTY_FIELD = DecimalField(max_digits=12, decimal_places=3)
ZERO_QTY = Value(0, output_field=QTY_FIELD)


@login_required
def dashboard_view(request):
    today = timezone.localdate()
    limit_30 = today + timedelta(days=30)
    limit_7 = today + timedelta(days=7)
    desde_7 = today - timedelta(days=6)

    # =====================
    # FLOTA (real)
    # =====================
    total_unidades = Colectivo.objects.filter(is_active=True).count()
    activos = Colectivo.objects.filter(is_active=True, estado=Colectivo.Estado.ACTIVO).count()
    en_taller = Colectivo.objects.filter(is_active=True, estado=Colectivo.Estado.TALLER).count()
    bajas = Colectivo.objects.filter(is_active=True, estado=Colectivo.Estado.BAJA).count()
    flota_operativo_pct = round((activos / total_unidades) * 100) if total_unidades else 0

    vtv_vencidos_qs = Colectivo.objects.filter(
        is_active=True,
        revision_tecnica_vto__isnull=False,
        revision_tecnica_vto__lt=today,
    ).order_by("revision_tecnica_vto", "interno")

    vtv_hoy_qs = Colectivo.objects.filter(
        is_active=True,
        revision_tecnica_vto__isnull=False,
        revision_tecnica_vto=today,
    ).order_by("interno")

    vtv_por_vencer_7_qs = Colectivo.objects.filter(
        is_active=True,
        revision_tecnica_vto__isnull=False,
        revision_tecnica_vto__gt=today,
        revision_tecnica_vto__lte=limit_7,
    ).order_by("revision_tecnica_vto", "interno")

    vtv_por_vencer_30_qs = Colectivo.objects.filter(
        is_active=True,
        revision_tecnica_vto__isnull=False,
        revision_tecnica_vto__gte=today,
        revision_tecnica_vto__lte=limit_30,
    ).order_by("revision_tecnica_vto", "interno")

    vtv_sin_fecha_qs = Colectivo.objects.filter(
        is_active=True,
        revision_tecnica_vto__isnull=True,
    ).order_by("interno")

    vencimientos_vtv = []
    for c in Colectivo.objects.filter(is_active=True).only("interno", "dominio", "revision_tecnica_vto").order_by("interno"):
        vto = c.revision_tecnica_vto
        if not vto:
            vencimientos_vtv.append({
                "tipo": "VTV",
                "interno": c.interno,
                "dominio": c.dominio,
                "fecha": None,
                "dias": None,
                "estado": "Pendiente",
                "badge": "muted",
            })
            continue

        dias = (vto - today).days
        if dias < 0:
            estado = "Vencido"
            badge = "critical"
        elif dias == 0:
            estado = "Hoy"
            badge = "critical"
        elif 1 <= dias <= 7:
            estado = "Por vencer"
            badge = "high"
        else:
            estado = "OK"
            badge = "ok"

        vencimientos_vtv.append({
            "tipo": "VTV",
            "interno": c.interno,
            "dominio": c.dominio,
            "fecha": vto,
            "dias": dias,
            "estado": estado,
            "badge": badge,
        })

    def _sort_key(row):
        prio = {"critical": 0, "high": 1, "ok": 3, "muted": 4}.get(row.get("badge"), 9)
        dias = row.get("dias")
        dias_sort = dias if dias is not None else 10**9
        return (prio, dias_sort)

    vencimientos_vtv.sort(key=_sort_key)

    # =====================
    # INVENTARIO (real) - FIX DECIMAL
    # =====================
    inv_total_ubicaciones = Ubicacion.objects.filter(is_active=True).count()
    inv_total_stock_rows = StockActual.objects.count()

    # ✅ Sum(Decimal) + Coalesce con ZERO_QTY (Decimal) => sin FieldError
    prod_qs = Producto.objects.filter(is_active=True).annotate(
        stock_total=Coalesce(Sum("stocks__cantidad"), ZERO_QTY, output_field=QTY_FIELD)
    )

    inv_total_productos = prod_qs.count()
    inv_productos_con_stock = prod_qs.filter(stock_total__gt=0).count()
    inv_productos_sin_stock = prod_qs.filter(stock_total__lte=0).count()
    inv_productos_bajo_min = prod_qs.filter(stock_minimo__gt=0, stock_total__lt=F("stock_minimo")).count()
    inv_disponibilidad_pct = round((inv_productos_con_stock / inv_total_productos) * 100) if inv_total_productos else 0

    inv_stock_rows_low = StockActual.objects.filter(cantidad__lt=F("producto__stock_minimo")).count()

    inv_mov_hoy = MovimientoStock.objects.filter(fecha__date=today).count()
    inv_mov_7 = MovimientoStock.objects.filter(fecha__date__gte=desde_7, fecha__date__lte=today).count()

    inv_mov_hoy_ing = MovimientoStock.objects.filter(fecha__date=today, tipo=MovimientoStock.Tipo.INGRESO).count()
    inv_mov_hoy_egr = MovimientoStock.objects.filter(fecha__date=today, tipo=MovimientoStock.Tipo.EGRESO).count()
    inv_mov_hoy_ajs = MovimientoStock.objects.filter(fecha__date=today, tipo=MovimientoStock.Tipo.AJUSTE).count()
    inv_mov_hoy_trf = MovimientoStock.objects.filter(fecha__date=today, tipo=MovimientoStock.Tipo.TRANSFERENCIA).count()

    movimientos_recientes = (
        MovimientoStock.objects
        .select_related("producto", "ubicacion", "ubicacion_destino", "usuario")
        .order_by("-fecha", "-id")[:20]
    )

    crit_qs = (
        prod_qs.filter(
            Q(stock_total__lte=0) | Q(stock_minimo__gt=0, stock_total__lt=F("stock_minimo"))
        )
        .order_by("stock_total", "codigo")
    )[:12]

    criticos_inventario = []
    crit_ids = [p.id for p in crit_qs]
    stocks_map = {}
    for s in (
        StockActual.objects
        .filter(producto_id__in=crit_ids)
        .select_related("ubicacion", "producto")
        .order_by("producto_id", "-cantidad", "ubicacion__codigo")
    ):
        stocks_map.setdefault(s.producto_id, []).append(s)

    for p in crit_qs:
        st_list = stocks_map.get(p.id, [])
        ubic_res = []
        for s in st_list:
            if len(ubic_res) >= 2:
                break
            ubic_res.append(f"{s.ubicacion.codigo} ({s.cantidad})")
        ubic_resumen = ", ".join(ubic_res) if ubic_res else "—"

        if p.stock_total <= 0:
            estado = "Sin stock"
            badge = "critical"
        else:
            estado = "Bajo mínimo"
            badge = "high"

        criticos_inventario.append({
            "id": p.id,
            "codigo": p.codigo,
            "nombre": p.nombre,
            "stock_total": p.stock_total,
            "stock_minimo": p.stock_minimo,
            "ubicaciones": ubic_resumen,
            "estado": estado,
            "badge": badge,
        })

    alert_crit_vtv = vtv_vencidos_qs.count() + vtv_hoy_qs.count()
    alert_crit_unidad = bajas
    alert_crit_inv_sin_stock = inv_productos_sin_stock
    alert_total_critico = alert_crit_vtv + alert_crit_unidad + alert_crit_inv_sin_stock
    colectivos_quick = (
    Colectivo.objects.filter(is_active=True)
    .only("id", "interno", "dominio", "estado", "revision_tecnica_vto")
    .order_by("interno")[:20]
)

    ctx = {
        "today": today,
        "limit_7": limit_7,
        "limit_30": limit_30,

        "header_status_text": f"Críticos: {alert_total_critico}",

        "kpi_total_unidades": total_unidades,
        "kpi_activos": activos,
        "kpi_taller": en_taller,
        "kpi_baja": bajas,
        "kpi_flota_operativo_pct": flota_operativo_pct,

        "kpi_vtv_vencidos": vtv_vencidos_qs.count(),
        "kpi_vtv_hoy": vtv_hoy_qs.count(),
        "kpi_vtv_por_vencer_7": vtv_por_vencer_7_qs.count(),
        "kpi_vtv_por_vencer": vtv_por_vencer_30_qs.count(),
        "kpi_vtv_sin_fecha": vtv_sin_fecha_qs.count(),
        "vencimientos_vtv": vencimientos_vtv[:80],

        
        "inv_total_productos": inv_total_productos,
        "inv_productos_con_stock": inv_productos_con_stock,
        "inv_productos_sin_stock": inv_productos_sin_stock,
        "inv_productos_bajo_min": inv_productos_bajo_min,
        "inv_disponibilidad_pct": inv_disponibilidad_pct,
        "inv_total_ubicaciones": inv_total_ubicaciones,
        "inv_total_stock_rows": inv_total_stock_rows,
        "inv_stock_rows_low": inv_stock_rows_low,

        "inv_mov_hoy": inv_mov_hoy,
        "inv_mov_7": inv_mov_7,
        "inv_mov_hoy_ing": inv_mov_hoy_ing,
        "inv_mov_hoy_egr": inv_mov_hoy_egr,
        "inv_mov_hoy_ajs": inv_mov_hoy_ajs,
        "inv_mov_hoy_trf": inv_mov_hoy_trf,

        "movimientos_recientes": movimientos_recientes,
        "colectivos_quick": colectivos_quick,
        "criticos_inventario": criticos_inventario,

        "alert_crit_vtv": alert_crit_vtv,
        "alert_crit_unidad": alert_crit_unidad,
        "alert_crit_inv_sin_stock": alert_crit_inv_sin_stock,
    }

    return render(request, "core/dashboard.html", ctx)


@requires_csrf_token
def csrf_failure(request, reason=""):
    _csrf_logger.error(
        "CSRF failure: %s | host=%s | secure=%s | origin=%s | referer=%s | xfp=%s | xfh=%s",
        reason,
        request.get_host(),
        request.is_secure(),
        request.META.get("HTTP_ORIGIN"),
        request.META.get("HTTP_REFERER"),
        request.META.get("HTTP_X_FORWARDED_PROTO"),
        request.META.get("HTTP_X_FORWARDED_HOST"),
    )
    return HttpResponseForbidden(f"CSRF verification failed. {reason}")

@login_required
def home_view(request):
    # Si tiene permiso de ver flota, lo llevamos a colectivos.
    if request.user.has_perm("flota.view_colectivo"):
        return redirect("flota:colectivo_list")

    # Caso contrario, no lo castigamos con 403: lo mandamos al dashboard
    return redirect("core:dashboard")