#!/usr/bin/env bash
# deploy/setup.sh
# Configura bgremover en Ubuntu 24.04 con Gunicorn + nginx existente.
# Ejecutar como root: sudo bash deploy/setup.sh
#
# Clonar primero el repo en APP_DIR antes de correr este script.

set -euo pipefail

# ---------------------------------------------------------------------------
# CONFIG — ajustar antes de correr
# ---------------------------------------------------------------------------
APP_DIR="/opt/bgremover"
APP_USER="bgremover"
APP_PORT=8001                      # 8000 está ocupado por lab.service
APP_WORKERS=2                      # gunicorn workers — 1 por ahora es suficiente;
                                   # con 2 se puede atender una request mientras
                                   # otra está procesando. No poner más de 3:
                                   # cada worker carga el modelo en RAM (~800 MB).
APP_MODEL="isnet-general-use"      # cambiar a "birefnet-general" para mejor calidad
PYTHON_BIN="python3"

# ---------------------------------------------------------------------------
# 1. Dependencias del sistema (solo lo que puede faltar en Ubuntu 24.04)
# ---------------------------------------------------------------------------
echo ">>> Instalando dependencias del sistema..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    python3-venv \
    libglib2.0-0 \
    libgl1

# libgl1 y libglib2.0-0 son requeridos por opencv-python-headless en Linux.
# nginx, python3 y pip ya están instalados en este servidor.

# ---------------------------------------------------------------------------
# 2. Usuario dedicado
# ---------------------------------------------------------------------------
if ! id "$APP_USER" &>/dev/null; then
    echo ">>> Creando usuario $APP_USER..."
    useradd --system \
        --home-dir "/var/lib/$APP_USER" \
        --create-home \
        --shell /usr/sbin/nologin \
        "$APP_USER"
fi

# ---------------------------------------------------------------------------
# 3. Permisos del directorio de la app
# ---------------------------------------------------------------------------
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

# ---------------------------------------------------------------------------
# 4. Entorno virtual
# ---------------------------------------------------------------------------
echo ">>> Creando entorno virtual..."
sudo -u "$APP_USER" "$PYTHON_BIN" -m venv "$APP_DIR/.venv"

echo ">>> Instalando dependencias Python..."
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --upgrade pip -q
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install gunicorn -q
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install \
    -r "$APP_DIR/requirements-server.txt" -q

# ---------------------------------------------------------------------------
# 5. Pre-descarga del modelo de IA
# ---------------------------------------------------------------------------
echo ">>> Pre-descargando modelo $APP_MODEL..."
sudo -u "$APP_USER" HOME="/var/lib/$APP_USER" \
    "$APP_DIR/.venv/bin/python" -c "
from rembg import new_session
print('  Descargando $APP_MODEL...')
new_session('$APP_MODEL')
print('  Modelo listo.')
"

# ---------------------------------------------------------------------------
# 6. Servicio systemd
# ---------------------------------------------------------------------------
echo ">>> Instalando servicio systemd..."
sed \
    -e "s|{{APP_DIR}}|$APP_DIR|g" \
    -e "s|{{APP_USER}}|$APP_USER|g" \
    -e "s|{{APP_PORT}}|$APP_PORT|g" \
    -e "s|{{APP_WORKERS}}|$APP_WORKERS|g" \
    -e "s|{{APP_MODEL}}|$APP_MODEL|g" \
    "$APP_DIR/deploy/bgremover.service.template" \
    > /etc/systemd/system/bgremover.service

systemctl daemon-reload
systemctl enable bgremover
systemctl restart bgremover

# ---------------------------------------------------------------------------
# 7. Nginx — agrega el site sin tocar la config existente
# ---------------------------------------------------------------------------
echo ">>> Configurando Nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/bgremover
ln -sf /etc/nginx/sites-available/bgremover /etc/nginx/sites-enabled/bgremover

nginx -t && systemctl reload nginx

# ---------------------------------------------------------------------------
echo ""
echo "======================================================"
echo "  Despliegue completado."
echo "  Servicio: $(systemctl is-active bgremover)"
echo "  Health check interno:"
sleep 3
curl -s http://127.0.0.1:$APP_PORT/api/v1/health || echo "  (aún iniciando...)"
echo ""
echo "  Logs en vivo:  journalctl -u bgremover -f"
echo "======================================================"
