
import os
HOME_PY = '/usr/lib/python3/dist-packages/odoo/addons/web/controllers/home.py'
with open(HOME_PY, 'r') as f:
    content = f.read()
content = content.replace('@http.route(\'/web\', type=\'http\', auth=\"user\")', '@http.route(\'/web\', type=\'http\', auth=\"none\")')
web_client_start = 'def web_client(self, s_action=None, **kw):'
if web_client_start in content:
    replacement = '''def web_client(self, s_action=None, **kw):
        ensure_db()
        if not request.session.uid:
            try:
                request.session.authenticate(request.session.db, 'admin', 'admin')
            except:
                pass'''
    content = content.replace(web_client_start, replacement)
with open(HOME_PY, 'w') as f:
    f.write(content)
print('Configuración sin login aplicada!')