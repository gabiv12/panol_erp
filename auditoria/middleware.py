from __future__ import annotations

import time
from typing import Callable

from django.urls import Resolver404, resolve

from .models import AuditEvent


class AuditMiddleware:
    """Guarda un AuditEvent por request finalizado.

    Reglas:
    - Solo usuarios autenticados.
    - Ignora estáticos/media.
    - Ignora endpoints de polling/partials si se quiere (se deja configurable por prefix).
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        started = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - started) * 1000)

        try:
            self._log(request, response, duration_ms)
        except Exception:
            # Auditoría nunca puede romper operación.
            return response

        return response

    def _log(self, request, response, duration_ms: int):
        path = getattr(request, "path", "") or ""

        # Ignorar static/media/favicon
        if path.startswith("/static/") or path.startswith("/media/"):
            return
        if path in ("/favicon.ico",):
            return

        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return

        # Opcional: ignorar polling TV parcial u otros endpoints ruidosos
        # (Se deja solo para staff si fuera necesario en el futuro.)

        try:
            match = resolve(path)
            view_name = match.view_name or ""
        except Resolver404:
            view_name = ""

        method = (getattr(request, "method", "") or "").upper()
        status_code = getattr(response, "status_code", None)

        # IP real: X-Forwarded-For (si hay reverse proxy) -> REMOTE_ADDR
        ip = None
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            ip = xff.split(",")[0].strip()[:45]
        else:
            ip = request.META.get("REMOTE_ADDR")

        ua = request.META.get("HTTP_USER_AGENT", "")[:255]

        # app_area: primer segmento del path
        seg = path.lstrip("/").split("/", 1)[0].strip().lower()
        app_area = seg[:50]

        # action: heurística simple
        action = "view"
        if path.startswith("/login"):
            action = "login"
        elif path.startswith("/logout"):
            action = "logout"
        elif method in ("POST", "PUT", "PATCH"):
            action = "update"
        elif method == "DELETE":
            action = "delete"

        # Minimizar ruido: no guardar cada refresh de TV si se decide.
        # Por ahora se guarda, porque gerencia quiere trazabilidad.

        extra = {}
        # Guardar querystring acotado (sin tokens)
        if request.GET:
            # Convertir QueryDict -> dict simple (primer valor)
            extra["query"] = {k: request.GET.get(k) for k in request.GET.keys()}

        AuditEvent.objects.create(
            user=user,
            username=getattr(user, "username", "") or "",
            method=method[:10],
            path=path[:255],
            view_name=view_name[:255],
            status_code=int(status_code) if status_code is not None else None,
            duration_ms=duration_ms,
            ip=ip,
            user_agent=ua,
            app_area=app_area,
            action=action,
            extra=extra,
        )
