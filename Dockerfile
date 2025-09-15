FROM odoo:17

USER root

# Replace home controller with better no-login version
COPY simple_home.py /usr/lib/python3/dist-packages/odoo/addons/web/controllers/home.py

USER odoo