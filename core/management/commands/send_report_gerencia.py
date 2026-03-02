from __future__ import annotations

import csv
import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Max, Min, Q
from django.utils import timezone

from auditoria.models import AuditEvent


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    user: str | None
    password: str | None
    use_tls: bool
    mail_from: str
    mail_to: list[str]


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if not v:
        return default
    try:
        return int(v.strip())
    except ValueError:
        return default


def _period_range(period: str) -> tuple[datetime, datetime]:
    """
    Returns (start, end) in timezone-aware datetimes.
    end is 'now'. start depends on period.
    """
    now = timezone.now()
    if period == "daily":
        start = now - timedelta(days=1)
    elif period == "weekly":
        start = now - timedelta(days=7)
    elif period == "monthly":
        start = now - timedelta(days=30)
    else:
        raise CommandError("period inválido. Usar: daily|weekly|monthly")
    return start, now


def _safe_outdir(outdir: str | None) -> Path:
    if not outdir:
        outdir = "reports"
    p = Path(outdir).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def _utf8sig_write_csv(path: Path, header: list[str], rows: Iterable[list[str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def _smtp_from_env() -> SmtpConfig:
    host = os.getenv("ERP_SMTP_HOST", "").strip()
    port = _env_int("ERP_SMTP_PORT", 587)
    user = os.getenv("ERP_SMTP_USER", "").strip() or None
    password = os.getenv("ERP_SMTP_PASS", "").strip() or None
    use_tls = _env_bool("ERP_SMTP_TLS", True)

    mail_from = os.getenv("ERP_REPORT_FROM", "").strip()
    if not mail_from:
        # si no se define explícito, usar el usuario SMTP
        mail_from = user or ""
    if not mail_from:
        raise CommandError("Falta ERP_REPORT_FROM (o ERP_SMTP_USER) para enviar correo.")

    to_raw = os.getenv("ERP_REPORT_TO", "").strip()
    mail_to = [x.strip() for x in to_raw.split(",") if x.strip()]
    if not mail_to:
        raise CommandError("Falta ERP_REPORT_TO (destinatarios, separados por coma).")

    if not host:
        raise CommandError("Falta ERP_SMTP_HOST.")
    return SmtpConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        use_tls=use_tls,
        mail_from=mail_from,
        mail_to=mail_to,
    )


def _send_email(cfg: SmtpConfig, subject: str, body_text: str, attachments: list[Path]) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.mail_from
    msg["To"] = ", ".join(cfg.mail_to)
    msg.set_content(body_text)

    for p in attachments:
        data = p.read_bytes()
        maintype = "text"
        subtype = "plain" if p.suffix.lower() in (".txt", ".md") else "csv"
        msg.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=p.name,
        )

    with smtplib.SMTP(cfg.host, cfg.port, timeout=30) as s:
        s.ehlo()
        if cfg.use_tls:
            s.starttls()
            s.ehlo()
        if cfg.user and cfg.password:
            s.login(cfg.user, cfg.password)
        s.send_message(msg)


class Command(BaseCommand):
    help = "Genera informe gerencial (auditoría) y opcionalmente lo envía por email."

    def add_arguments(self, parser):
        parser.add_argument(
            "--period",
            choices=["daily", "weekly", "monthly"],
            default="daily",
            help="Rango: daily (24h), weekly (7d), monthly (30d).",
        )
        parser.add_argument(
            "--outdir",
            default="reports",
            help="Carpeta de salida para los archivos (por defecto: ./reports).",
        )
        parser.add_argument(
            "--send",
            action="store_true",
            help="Enviar por email usando variables de entorno ERP_SMTP_* y ERP_REPORT_*.",
        )
        parser.add_argument(
            "--slow-ms",
            type=int,
            default=_env_int("ERP_SLOW_MS", 1500),
            help="Umbral de request lento (ms). Default 1500 o ERP_SLOW_MS.",
        )

    def handle(self, *args, **opts):
        period: str = opts["period"]
        outdir = _safe_outdir(opts["outdir"])
        slow_ms: int = int(opts["slow_ms"])

        start, end = _period_range(period)

        qs = AuditEvent.objects.filter(created_at__gte=start, created_at__lte=end)

        total = qs.count()
        err = qs.filter(status_code__gte=400).count()
        slow = qs.filter(duration_ms__gte=slow_ms).count()

        # resumen por empleado (username)
        by_user = (
            qs.values("username")
            .annotate(
                total=Count("id"),
                errores=Count("id", filter=Q(status_code__gte=400)),
                lentos=Count("id", filter=Q(duration_ms__gte=slow_ms)),
                primero=Min("created_at"),
                ultimo=Max("created_at"),
            )
            .order_by("-total", "username")
        )

        # top áreas
        by_area = (
            qs.values("app_area")
            .annotate(total=Count("id"))
            .order_by("-total", "app_area")
        )

        # dispositivos (ip + user_agent)
        by_device = (
            qs.values("ip", "user_agent")
            .annotate(
                total=Count("id"),
                primero=Min("created_at"),
                ultimo=Max("created_at"),
                usuarios=Count("username", distinct=True),
                errores=Count("id", filter=Q(status_code__gte=400)),
            )
            .order_by("-total")
        )

        # Archivos
        now_local = timezone.localtime(timezone.now())
        stamp = now_local.strftime("%Y%m%d_%H%M")
        base = f"informe_{period}_{stamp}"

        txt_path = outdir / f"{base}.txt"
        usuarios_csv = outdir / f"{base}_empleados.csv"
        device_csv = outdir / f"{base}_dispositivos.csv"
        area_csv = outdir / f"{base}_areas.csv"

        # Texto simple para gerente (sin tecnicismos)
        start_str = timezone.localtime(start).strftime("%d/%m/%Y %H:%M")
        end_str = timezone.localtime(end).strftime("%d/%m/%Y %H:%M")

        top_areas_txt = ", ".join([f"{r['app_area'] or '—'} ({r['total']})" for r in list(by_area)[:5]]) or "—"
        top_users_txt = ", ".join([f"{(r['username'] or 'anon')} ({r['total']})" for r in list(by_user)[:5]]) or "—"

        lines = [
            "LA TERMAL ERP — INFORME GERENCIAL (AUDITORÍA)",
            f"Período: {period} | Desde: {start_str} | Hasta: {end_str}",
            "",
            f"Actividad total: {total}",
            f"Errores del sistema o accesos fallidos: {err}",
            f"Acciones lentas (>{slow_ms} ms): {slow}",
            "",
            f"Top módulos usados: {top_areas_txt}",
            f"Top usuarios con actividad: {top_users_txt}",
            "",
            "Archivos adjuntos:",
            f"- {usuarios_csv.name} (resumen por empleado)",
            f"- {device_csv.name} (dispositivos conectados: IP + navegador)",
            f"- {area_csv.name} (uso por módulo/área)",
            "",
            "Nota:",
            "Si hay errores repetidos (status 500/403/404) conviene revisarlos con el administrador.",
        ]
        txt_path.write_text("\n".join(lines), encoding="utf-8")

        # CSV empleados
        emp_rows = []
        for r in by_user:
            emp_rows.append([
                (r["username"] or "anon"),
                str(r["total"]),
                str(r["errores"]),
                str(r["lentos"]),
                timezone.localtime(r["primero"]).strftime("%d/%m/%Y %H:%M") if r["primero"] else "",
                timezone.localtime(r["ultimo"]).strftime("%d/%m/%Y %H:%M") if r["ultimo"] else "",
            ])
        _utf8sig_write_csv(
            usuarios_csv,
            ["usuario", "eventos", "errores", "lentos", "primera_vez", "ultima_vez"],
            emp_rows,
        )

        # CSV dispositivos
        dev_rows = []
        for r in by_device:
            dev_rows.append([
                (r["ip"] or ""),
                (r["user_agent"] or ""),
                str(r["total"]),
                str(r["usuarios"]),
                str(r["errores"]),
                timezone.localtime(r["primero"]).strftime("%d/%m/%Y %H:%M") if r["primero"] else "",
                timezone.localtime(r["ultimo"]).strftime("%d/%m/%Y %H:%M") if r["ultimo"] else "",
            ])
        _utf8sig_write_csv(
            device_csv,
            ["ip", "user_agent", "eventos", "usuarios_distintos", "errores", "primera_vez", "ultima_vez"],
            dev_rows,
        )

        # CSV áreas
        area_rows = []
        for r in by_area:
            area_rows.append([
                (r["app_area"] or "—"),
                str(r["total"]),
            ])
        _utf8sig_write_csv(
            area_csv,
            ["area", "eventos"],
            area_rows,
        )

        self.stdout.write(self.style.SUCCESS(f"OK: informe generado en {outdir}"))
        self.stdout.write(f"- {txt_path.name}")
        self.stdout.write(f"- {usuarios_csv.name}")
        self.stdout.write(f"- {device_csv.name}")
        self.stdout.write(f"- {area_csv.name}")

        if opts["send"]:
            cfg = _smtp_from_env()
            prefix = os.getenv("ERP_REPORT_SUBJECT_PREFIX", "La Termal ERP").strip() or "La Termal ERP"
            subject = f"{prefix} - Informe {period} - {now_local.strftime('%d/%m/%Y')}"
            body = txt_path.read_text(encoding="utf-8")

            try:
                _send_email(cfg, subject, body, [txt_path, usuarios_csv, device_csv, area_csv])
            except Exception as e:
                # No fallar la ejecución: el informe local ya fue generado.
                err_path = outdir / f"{base}_envio_error.txt"
                err_path.write_text(str(e), encoding="utf-8")
                self.stderr.write(self.style.WARNING(f"WARN: no se pudo enviar el correo ({e}). Se guardó: {err_path.name}")) 
                return

            self.stdout.write(self.style.SUCCESS("OK: correo enviado"))
