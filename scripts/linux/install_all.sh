#!/usr/bin/env bash
set -euo pipefail

INSTALL_ROOT="${INSTALL_ROOT:-/opt/la_termalerp}"
REPO_URL="${REPO_URL:-https://github.com/gabiv12/panol_erp.git}"
REF="${REF:-v0.1.1}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

APP_DIR="${INSTALL_ROOT}/app"
DATA_DIR="${INSTALL_ROOT}/data"
LOG_DIR="${INSTALL_ROOT}/logs"
BACKUP_DIR="${INSTALL_ROOT}/backups"
REPORTS_DIR="${DATA_DIR}/reportes"

ENV_FILE="/etc/la_termalerp.env"
SERVICE_FILE="/etc/systemd/system/la-termalerp.service"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Ejecutar como root: sudo $0"
  exit 1
fi

apt-get update -y
apt-get install -y git python3 python3-venv python3-pip

mkdir -p "$APP_DIR" "$DATA_DIR" "$LOG_DIR" "$BACKUP_DIR" "$REPORTS_DIR"

if [[ ! -d "$APP_DIR/.git" ]]; then
  git clone "$REPO_URL" "$APP_DIR"
else
  (cd "$APP_DIR" && git fetch --all --tags)
fi

cd "$APP_DIR"
git fetch --all --tags
git checkout "$REF"

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

python manage.py migrate
python manage.py init_roles || true
python manage.py init_auditoria || true

if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<EOF
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=CAMBIAR_ESTA_CLAVE_LARGA
ERP_REPORT_TO=gerente@empresa.com
ERP_REPORT_FROM=erp@empresa.com
# SMTP opcional:
# ERP_SMTP_HOST=smtp.gmail.com
# ERP_SMTP_PORT=587
# ERP_SMTP_TLS=1
# ERP_SMTP_USER=correo@empresa.com
# ERP_SMTP_PASS=APP_PASSWORD
EOF
  chmod 600 "$ENV_FILE"
fi

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=La Termal ERP (Gunicorn)
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$APP_DIR/.venv/bin/gunicorn config.wsgi:application --bind $HOST:$PORT --workers 2 --timeout 60
Restart=always
RestartSec=3
StandardOutput=append:$LOG_DIR/server.log
StandardError=append:$LOG_DIR/server.err.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now la-termalerp.service

echo "OK. Servicio activo: http://IP_DEL_SERVIDOR:$PORT/dashboard/"
