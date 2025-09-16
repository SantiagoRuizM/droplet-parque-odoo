#!/bin/bash

echo "🚀 Desplegando Odoo Parque ERP en droplet fresco..."

# Actualizar sistema
echo "📦 Actualizando sistema..."
apt update && apt upgrade -y

# Instalar Docker y Docker Compose
echo "🐳 Instalando Docker..."
apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Instalar Docker Compose clásico
echo "📋 Instalando Docker Compose..."
apt install -y docker-compose

# Iniciar y habilitar Docker
systemctl start docker
systemctl enable docker

# Configurar firewall
echo "🛡️ Configurando firewall..."
ufw allow OpenSSH
ufw allow 8069
ufw --force enable

# Clonar repositorio
echo "📥 Clonando repositorio Odoo..."
cd /root
git clone https://github.com/SantiagoRuizM/droplet-parque-odoo.git
cd droplet-parque-odoo

# Crear archivo de bypass de login
echo "🔓 Creando archivo de bypass de login..."
cat > simple_home.py << 'EOF'
import functools
import logging
import werkzeug

import odoo
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.web.controllers import home
from odoo.addons.base.models.ir_http import ModelConverter
from odoo.osv import expression
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

def ensure_db(redirect='/web/database/selector'):
    db = request.params.get('db') and request.params.get('db').strip()
    if db and db not in http.db_filter([db]):
        db = None
    if not db and request.session.db and http.db_filter([request.session.db]):
        db = request.session.db
    if not db:
        db = http.db_monodb(request.httprequest)
    if not db:
        werkzeug.exceptions.abort(http.redirect_with_hash(redirect))
    if db != request.session.db:
        request.session.logout()
        werkzeug.exceptions.abort(http.redirect_with_hash('/web', 303))
    request.session.db = db

class Home(home.Home):

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        ensure_db()
        if not request.session.uid:
            try:
                request.session.authenticate(request.session.db, 'admin', 'admin')
            except:
                pass
        if not request.session.uid:
            return http.redirect_with_hash('/web/login')

        if kw.get('debug') is not None:
            request.session.debug = kw.get('debug')

        request.session.context = dict(request.session.context, iap_company_enrich=False)

        try:
            context = request.env['ir.http'].webclient_rendering_context()
            response = request.render('web.webclient_bootstrap', qcontext=context)
            response.headers['X-Frame-Options'] = 'DENY'
            return response
        except AccessError:
            return http.redirect_with_hash('/web/login?error=access')
EOF

# Levantar contenedores
echo "🔄 Levantando contenedores de Odoo..."
docker-compose up -d

# Esperar a que los contenedores se inicien
echo "⏱️ Esperando a que Odoo se inicie..."
sleep 60

# Aplicar bypass de login
echo "🔓 Aplicando bypass de login..."
docker cp simple_home.py odoo-parque:/usr/lib/python3/dist-packages/odoo/addons/web/controllers/home.py

# Aplicar tema naranja
echo "🧡 Aplicando tema naranja..."
docker exec -u root odoo-parque sed -i 's/#71639e/#E85A2B/g' /usr/lib/python3/dist-packages/odoo/addons/web/static/src/scss/primary_variables.scss

# Reiniciar contenedor de Odoo
echo "🔄 Reiniciando Odoo para aplicar cambios..."
docker-compose restart odoo

# Esperar a que reinicie
echo "⏱️ Esperando reinicio..."
sleep 30

echo "✅ Odoo Parque ERP desplegado exitosamente!"
echo "🌐 Accede en: http://$(curl -s ifconfig.me):8069"
echo "🔓 Sin login requerido - Acceso directo como admin"
echo "🧡 Tema naranja profesional aplicado"