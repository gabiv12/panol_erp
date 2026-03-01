from __future__ import annotations

import csv
from datetime import timedelta
from typing import Any, Dict, Optional

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import AuditEvent


def _parse_date(s: str) -> Optional[timezone.datetime]:
    s = (s or "").strip()
    if not s:
        return None
    try:
        dt = timezone.datetime.strptime(s, "%Y-%m-%d")
        return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
    except Exception:
        return None


def _qs_filtered(request: HttpRequest):
    qs = AuditEvent.objects.all().select_related("user")

    q = (request.GET.get("q") or "").strip()
    username = (request.GET.get("username") or "").strip()
    app = (request.GET.get("app") or "").strip()
    action = (request.GET.get("action") or "").strip()
    status = (request.GET.get("status") or "").strip()
    days = (request.GET.get("days") or "").strip()
    from_s = (request.GET.get("from") or "").strip()
    to_s = (request.GET.get("to") or "").strip()

    if days:
        try:
            n = int(days)
            if n > 0:
                since = timezone.now() - timedelta(days=n)
                qs = qs.filter(created_at__gte=since)
        except Exception:
            pass

    dt_from = _parse_date(from_s)
    if dt_from:
        qs = qs.filter(created_at__gte=dt_from)

    dt_to = _parse_date(to_s)
    if dt_to:
        qs = qs.filter(created_at__lt=dt_to + timedelta(days=1))

    if username:
        qs = qs.filter(username__icontains=username)

    if app:
        qs = qs.filter(app_area=app)

    if action:
        qs = qs.filter(action=action)

    if status:
        st = status.lower()
        if st.endswith("xx") and len(st) == 3 and st[0].isdigit():
            base = int(st[0]) * 100
            qs = qs.filter(status_code__gte=base, status_code__lt=base + 100)
        else:
            try:
                code = int(st)
                qs = qs.filter(status_code=code)
            except Exception:
                pass

    if q:
        qs = qs.filter(
            Q(path__icontains=q)
            | Q(view_name__icontains=q)
            | Q(action__icontains=q)
            | Q(method__icontains=q)
            | Q(ip__icontains=q)
            | Q(username__icontains=q)
        )

    return qs.order_by("-created_at")


@login_required
@permission_required("auditoria.view_auditevent", raise_exception=True)
def audit_list(request: HttpRequest) -> HttpResponse:
    qs = _qs_filtered(request)

    paginator = Paginator(qs, 50)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    ctx: Dict[str, Any] = {
        "page_obj": page_obj,
        "q": request.GET.get("q", ""),
        "username": request.GET.get("username", ""),
        "app": request.GET.get("app", ""),
        "action": request.GET.get("action", ""),
        "status": request.GET.get("status", ""),
        "from": request.GET.get("from", ""),
        "to": request.GET.get("to", ""),
        "days": request.GET.get("days", "7") or "7",
        "apps": list(AuditEvent.objects.values_list("app_area", flat=True).distinct().order_by("app_area")),
        "actions": list(AuditEvent.objects.values_list("action", flat=True).distinct().order_by("action")),
        "usernames": list(AuditEvent.objects.values_list("username", flat=True).distinct().order_by("username")[:200]),
    }
    return render(request, "auditoria/audit_list.html", ctx)


@login_required
@permission_required("auditoria.view_auditevent", raise_exception=True)
def audit_export_csv(request: HttpRequest) -> HttpResponse:
    qs = _qs_filtered(request)

    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="auditoria.csv"'
    # BOM para Excel
    resp.write("\ufeff")

    w = csv.writer(resp, delimiter=";")
    w.writerow(
        [
            "fecha_hora",
            "usuario",
            "area",
            "accion",
            "metodo",
            "ruta",
            "vista",
            "status",
            "duracion_ms",
            "ip",
        ]
    )
    for e in qs[:20000]:
        w.writerow(
            [
                timezone.localtime(e.created_at).strftime("%Y-%m-%d %H:%M:%S"),
                e.username or "",
                e.app_area or "",
                e.action or "",
                e.method or "",
                e.path or "",
                e.view_name or "",
                e.status_code or "",
                e.duration_ms or "",
                e.ip or "",
            ]
        )
    return resp
