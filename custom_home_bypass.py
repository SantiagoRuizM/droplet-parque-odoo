# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import os
import psycopg2
from hashlib import sha512


import odoo
import odoo.modules.registry
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.service import security
from odoo.tools import ustr
from odoo.tools.translate import _
from .utils import ensure_db, _get_login_redirect_url, is_user_internal


_logger = logging.getLogger(__name__)

# 🔐 AUTO-LOGIN BYPASS CONFIGURATION
# Credenciales por defecto - pueden ser actualizadas vía API
BYPASS_CREDENTIALS = {
    'user': 'usuario_generico',
    'password': 'XXXXXXX'
}

# Bearer Token for API security (must be set in environment variable)
BYPASS_API_TOKEN = os.getenv('BYPASS_API_TOKEN')

# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang', 'signup_email'}
LOGIN_SUCCESSFUL_PARAMS = set()


class Home(http.Controller):

    # ideally, this route should be `auth="user"` but that don't work in non-monodb mode.
    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):

        # Ensure we have both a database and a user
        ensure_db()
        if not request.session.uid:
            # AUTO-LOGIN BYPASS - Try to authenticate as admin
            try:
                uid = request.session.authenticate(request.db, BYPASS_CREDENTIALS['user'], BYPASS_CREDENTIALS['password'])
                if uid:
                    request.update_env(user=uid)
                else:
                    return request.redirect_query('/web/login', query=request.params, code=303)
            except:
                return request.redirect_query('/web/login', query=request.params, code=303)
        if kw.get('redirect'):
            return request.redirect(kw.get('redirect'), 303)
        if not security.check_session(request.session, request.env):
            raise http.SessionExpiredException("Session expired")
        if not is_user_internal(request.session.uid):
            return request.redirect('/web/login_successful', 303)

        # Side-effect, refresh the session lifetime
        request.session.touch()

        # Restore the user on the environment, it was lost due to auth="none"
        request.update_env(user=request.session.uid)
        try:
            context = request.env['ir.http'].webclient_rendering_context()
            response = request.render('web.webclient_bootstrap', qcontext=context)
            response.headers['X-Frame-Options'] = 'DENY'
            return response
        except AccessError:
            return request.redirect('/web/login?error=access')

    @http.route('/web/webclient/load_menus/<string:unique>', type='http', auth='user', methods=['GET'])
    def web_load_menus(self, unique, lang=None):
        """
        Loads the menus for the webclient
        :param unique: this parameters is not used, but mandatory: it is used by the HTTP stack to make a unique request
        :param lang: language in which the menus should be loaded (only works if language is installed)
        :return: the menus (including the images in Base64)
        """
        if lang:
            request.update_context(lang=lang)

        menus = request.env["ir.ui.menu"].load_web_menus(request.session.debug)
        body = json.dumps(menus, default=ustr)
        response = request.make_response(body, [
            # this method must specify a content-type application/json instead of using the default text/html set because
            # the type of the route is set to HTTP, but the rpc is made with a get and expects JSON
            ('Content-Type', 'application/json'),
            ('Cache-Control', 'public, max-age=' + str(http.STATIC_CACHE_LONG)),
        ])
        return response

    @http.route('/apps', type='http', auth="none")
    def apps_page(self, **kw):
        """Static navbar that looks exactly like Odoo's but without JavaScript redirects"""
        try:
            # Ensure database connection and auto-login
            ensure_db()
            if not request.session.uid:
                try:
                    uid = request.session.authenticate(request.db, BYPASS_CREDENTIALS['user'], BYPASS_CREDENTIALS['password'])
                    if uid:
                        request.update_env(user=uid)
                except:
                    return request.redirect('/web/login')

            # Restore the user on the environment
            request.update_env(user=request.session.uid)

            user = request.env.user
            company = user.company_id

            # Get user's avatar color using the same algorithm as Odoo
            # (same as avatar_mixin.py get_hsl_from_seed function)
            seed = user.name + str(user.partner_id.create_date.timestamp() if user.partner_id.create_date else "")
            hashed_seed = sha512(seed.encode()).hexdigest()
            hue = int(hashed_seed[0:2], 16) * 360 / 255
            sat = int(hashed_seed[2:4], 16) * ((70 - 40) / 255) + 40
            lig = 45
            user_avatar_color = f'hsl({hue:.0f}, {sat:.0f}%, {lig:.0f}%)'

            # Get installed applications (using sudo to bypass ACL restrictions)
            installed_apps = request.env['ir.module.module'].sudo().search([
                ('state', '=', 'installed'),
                ('application', '=', True)
            ])

            # External IDs mapping (estático entre instalaciones)
            external_id_mapping = {
                'crm': 'crm.crm_lead_all_leads',
                'calendar': 'calendar.action_calendar_event',
                'contacts': 'base.action_partner_form',
                'sale_management': 'sale.action_orders',
                'website': None,  # Special case: redirect to /
                'hr': 'hr.open_view_employee_list_my',
                'stock': 'stock.stock_picking_type_action',
                'point_of_sale': 'point_of_sale.action_pos_config_kanban',
                'project': 'project.open_view_project_all',
                'maintenance': 'maintenance.hr_equipment_action',
                'purchase': 'purchase.purchase_rfq',
                'mrp': 'mrp.mrp_production_action',
                'website_sale': None,  # Special case: redirect to /shop
                'mass_mailing': 'mass_mailing.action_mailing_mass_mail',
                'hr_expense': 'hr_expense.hr_expense_actions_all',
                'hr_holidays': 'hr_holidays.hr_leave_action_my',
                'hr_recruitment': 'hr_recruitment.hr_job_action',
                'website_event': 'website_event.website_event_menu_action',
                'fleet': 'fleet.fleet_vehicle_action',
                'survey': 'survey.action_survey_form',
                'pos_restaurant': 'pos_restaurant.action_pos_config_kanban',
                'account': 'account.action_move_out_invoice_type',
                'mail': 'mail.action_discuss',
                'website_hr_recruitment': 'website_hr_recruitment.action_hr_job_website',
                'project_todo': 'project_todo.project_task_action_todo',
                'repair': 'repair.action_repair_order_tree',
            }

            # Función para obtener URL dinámica basada en external ID
            def get_action_url(external_id, model=None):
                if external_id is None:
                    return '/apps'
                try:
                    action = request.env.ref(external_id)
                    if hasattr(action, 'id'):
                        return f'/web#action={action.id}&model={model or action.res_model}&view_type=list&cids=1'
                except:
                    pass
                return '/apps'

            # Format apps data for template
            apps_data = []
            for app in installed_apps:
                # Casos especiales
                if app.name == 'website':
                    app_url = '/'
                elif app.name == 'website_sale':
                    app_url = '/shop'
                else:
                    # Usar external ID para obtener URL dinámica
                    external_id = external_id_mapping.get(app.name)
                    app_url = get_action_url(external_id, app.name)

                app_data = {
                    'name': app.name,
                    'display_name': app.shortdesc or app.name,
                    'summary': app.summary or app.shortdesc or app.name,
                    'icon_url': f'/web/image/ir.module.module/{app.id}/icon_image' if app.icon else '/web/static/img/placeholder.png',
                    'url': app_url
                }
                apps_data.append(app_data)

            apps_dropdown_html = ''.join([f'<a href="{app["url"]}" class="apps-dropdown-item">{app["display_name"]}</a>'for app in apps_data])

            # Create static HTML that looks exactly like Odoo navbar
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no"/>
                <title>Odoo - Aplicaciones</title>
                <link type="image/x-icon" rel="shortcut icon" href="/web/static/img/icon-parque.png"/>

                <!-- Load Odoo UI Icons -->
                <link rel="stylesheet" type="text/css" href="/web/static/lib/odoo_ui_icons/style.css"/>

                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

                    body {{
                        font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", Arial, sans-serif;
                        background: #f2f5f6;
                    }}

                    /* EXACT Odoo navbar styles with orange theme */
                    .o_navbar {{
                        background-color: #e85a2b;
                        border-bottom: 1px solid rgba(0,0,0,0.1);
                        height: 48px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        position: relative;
                        z-index: 1000;
                    }}

                    .o_main_navbar {{
                        display: flex;
                        align-items: center;
                        height: 100%;
                        padding: 0 16px;
                        max-width: 100%;
                    }}

                    .o_navbar_apps_menu {{
                        margin-right: 12px;
                    }}

                    .o_navbar_apps_menu button {{
                        background: none;
                        border: none;
                        color: white;
                        font-size: 18px;
                        padding: 8px 12px;
                        cursor: pointer;
                        border-radius: 4px;
                        transition: background-color 0.2s;
                    }}

                    .o_navbar_apps_menu button:hover {{
                        background-color: rgba(255,255,255,0.1);
                    }}

                    /* User avatar styles - square with rounded corners */
                    .o_user_avatar {{
                        width: 28px;
                        height: 28px;
                        border-radius: 3px;
                        background-color: {user_avatar_color};
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 14px;
                        text-transform: uppercase;
                    }}

                    .o_menu_brand {{
                        color: white;
                        font-family: "Segoe UI", sans-serif;
                        font-weight: 400;
                        margin-right: auto;
                        font-size: 16px;
                        text-decoration: none;
                        padding: 8px 12px;
                        border-radius: 4px;
                        transition: background-color 0.2s;
                    }}

                    .o_menu_brand:hover {{
                        background-color: rgba(255,255,255,0.1);
                        color: white;
                        text-decoration: none;
                    }}

                    .o_menu_systray {{
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }}

                    .o_menu_systray button {{
                        background: none;
                        border: none;
                        color: white;
                        padding: 8px 12px;
                        cursor: pointer;
                        border-radius: 4px;
                        font-size: 14px;
                        transition: background-color 0.2s;
                    }}

                    .o_menu_systray button:hover {{
                        background-color: rgba(255,255,255,0.1);
                    }}

                    .main-content {{
                        background: #f2f5f6;
                        min-height: calc(100vh - 48px);
                        padding: 20px;
                    }}

                    .apps-container {{
                        max-width: 1200px;
                        margin: 0 auto;
                    }}

                    .apps-header {{
                        margin-bottom: 40px;
                        text-align: center;
                        padding: 20px 0;
                    }}

                    .apps-header h1 {{
                        color: #2c3e50;
                        font-family: "Segoe UI", sans-serif;
                        font-size: 2.2rem;
                        font-weight: 300;
                        margin-bottom: 8px;
                        letter-spacing: -0.5px;
                        line-height: 1.2;
                    }}

                    .apps-header .subtitle {{
                        color: #7f8c8d;
                        font-family: "Segoe UI", sans-serif;
                        font-size: 1rem;
                        font-weight: 400;
                        margin-top: 5px;
                        opacity: 0.8;
                    }}

                    .apps-grid {{
                        display: flex;
                        flex-wrap: wrap;
                        gap: 20px;
                        justify-content: center;
                    }}

                    .app-card {{
                        background: white;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 20px;
                        width: 200px;
                        text-align: center;
                        transition: all 0.2s;
                        cursor: pointer;
                    }}

                    .app-card:hover {{
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        transform: translateY(-2px);
                    }}

                    .app-icon {{
                        width: 64px;
                        height: 64px;
                        margin: 0 auto 15px;
                        border-radius: 8px;
                        overflow: hidden;
                    }}

                    .app-icon img {{
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                    }}

                    .app-name {{
                        font-size: 1.1rem;
                        font-weight: 600;
                        color: #333;
                        margin-bottom: 8px;
                    }}

                    .app-summary {{
                        font-size: 0.9rem;
                        color: #666;
                        line-height: 1.4;
                    }}

                    /* Logos en las esquinas */
                    .corner-logos {{
                        position: fixed;
                        top: 58px;
                        z-index: 100;
                    }}

                    .logo-parque {{
                        left: 20px;
                    }}

                    .logo-fua {{
                        right: 20px;
                    }}

                    .corner-logos img {{
                        height: auto;
                        opacity: 1;
                        transition: opacity 0.3s ease;
                    }}

                    .logo-parque img {{
                        width: 35px;
                    }}

                    .logo-fua img {{
                        width: 150px;
                    }}

                    .corner-logos img:hover {{
                        opacity: 0.9;
                    }}

                    /* Dropdown styles */
                    .apps-dropdown {{
                        position: absolute;
                        top: 48px;
                        left: 0;
                        background: white;
                        border-radius: 4px;
                        border: 1px solid #d1d5db;
                        box-shadow: none;
                        min-width: 160px;
                        max-width: 180px;
                        max-height: 400px;
                        overflow-y: auto;
                        display: none;
                        z-index: 1001;
                        padding: 4px 0;
                    }}

                    .apps-dropdown.show {{
                        display: block;
                    }}

                    .apps-dropdown-item {{
                        display: block;
                        padding: 8px 12px;
                        color: #2c3e50;
                        text-decoration: none;
                        font-size: 14px;
                        font-family: "Segoe UI", sans-serif;
                        transition: background-color 0.2s;
                        cursor: pointer;
                        border: none;
                        background: none;
                        width: 100%;
                        text-align: left;
                    }}

                    
                    .apps-dropdown-item:hover {{
                        background-color: #ebebeb;
                    }}

                    /* Scrollbar personalizado para el dropdown */
                    .apps-dropdown::-webkit-scrollbar {{
                        width: 6px;
                    }}

                    .apps-dropdown::-webkit-scrollbar-track {{
                        background: #f1f1f1;
                    }}

                    .apps-dropdown::-webkit-scrollbar-thumb {{
                        background: #888;
                        border-radius: 3px;
                    }}

                    .apps-dropdown::-webkit-scrollbar-thumb:hover {{
                        background: #555;
                    }}

                    /* User dropdown styles */
                    .o_user_menu {{
                        position: relative;
                    }}

                    .user-dropdown {{
                        position: fixed;
                        top: 48px;
                        right: 16px;
                        background: white;
                        border-radius: 4px;
                        border: 1px solid #d1d5db;
                        box-shadow: none;
                        min-width: 160px;
                        max-width: 180px;
                        display: none;
                        z-index: 1001;
                        padding: 4px 0;
                    }}

                    .user-dropdown.show {{
                        display: block;
                    }}

                    .user-dropdown-item {{
                        display: block;
                        padding: 8px 12px;
                        color: #2c3e50;
                        text-decoration: none;
                        font-size: 14px;
                        font-family: "Segoe UI", sans-serif;
                        transition: background-color 0.2s;
                        cursor: pointer;
                        border: none;
                        background: none;
                        width: 100%;
                        text-align: left;
                    }}

                    .user-dropdown-item:hover {{
                        background-color: #ebebeb;
                    }}

                    .o_user_menu button {{
                        position: relative;
                    }}

                </style>
            </head>
            <body>
                <!-- Static Odoo-style navbar -->
                <header class="o_navbar">
                    <nav class="o_main_navbar">
                        <!-- Apps Menu -->
                        <div class="o_navbar_apps_menu">
                            <button id="appsMenuBtn">
                                <i class="oi oi-apps"></i>
                            </button>
                            <div class="apps-dropdown" id="appsDropdown">
                                {apps_dropdown_html}
                            </div>
                        </div>

                        <!-- Brand -->
                        <a class="o_menu_brand">
                            Aplicaciones
                        </a>

                        <!-- Systray -->
                        <div class="o_menu_systray">
                            <div class="o_user_menu">
                                <button id="userMenuBtn">
                                    <div class="o_user_avatar">
                                        {user.name[0] if user.name else 'U'}
                                    </div>
                                </button>
                                <div class="user-dropdown" id="userDropdown">
                                    <a href="#" class="user-dropdown-item" id="profileBtn">Perfil</a>
                                    <a href="#" class="user-dropdown-item" id="logoutBtn">Cerrar sesión</a>
                                </div>
                            </div>
                        </div>
                    </nav>
                </header>

                <!-- Logos en las esquinas -->
                <div class="corner-logos logo-parque">
                    <img src="/web/static/img/icon-parque.png" alt="Parque" />
                </div>

                <div class="corner-logos logo-fua">
                    <img src="/web/static/img/logo-fua.png" alt="FUA" />
                </div>

                <!-- Main content -->
                <div class="main-content">
                    <div class="apps-container">
                        <div class="apps-header">
                            <h1>Bienvenido, {user.name}</h1>
                            <div class="subtitle">Potencia tu negocio con herramientas inteligentes</div>
                        </div>

                        <div class="apps-grid">''' + ''.join([f'''
                            <div class="app-card" onclick="window.location.href='{app["url"]}'">
                                <div class="app-icon">
                                    <img src="{app["icon_url"]}" alt="{app["display_name"]}" />
                                </div>
                                <div class="app-name">{app["display_name"]}</div>
                                <div class="app-summary">{app["summary"]}</div>
                            </div>''' for app in apps_data]) + '''
                        </div>
                    </div>
                </div>
                <script>
                    // Toggle apps dropdown menu
                    const appsMenuBtn = document.getElementById('appsMenuBtn');
                    const appsDropdown = document.getElementById('appsDropdown');

                    appsMenuBtn.addEventListener('click', function(e) {
                        e.stopPropagation();
                        appsDropdown.classList.toggle('show');
                        // Close user dropdown if open
                        userDropdown.classList.remove('show');
                    });

                    // Toggle user dropdown menu
                    const userMenuBtn = document.getElementById('userMenuBtn');
                    const userDropdown = document.getElementById('userDropdown');

                    userMenuBtn.addEventListener('click', function(e) {
                        e.stopPropagation();
                        userDropdown.classList.toggle('show');
                        // Close apps dropdown if open
                        appsDropdown.classList.remove('show');
                    });

                    // Close dropdowns when clicking outside
                    document.addEventListener('click', function(e) {
                        if (!appsMenuBtn.contains(e.target) && !appsDropdown.contains(e.target)) {
                            appsDropdown.classList.remove('show');
                        }
                        if (!userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
                            userDropdown.classList.remove('show');
                        }
                    });

                    // Close dropdowns on ESC key
                    document.addEventListener('keydown', function(e) {
                        if (e.key === 'Escape') {
                            appsDropdown.classList.remove('show');
                            userDropdown.classList.remove('show');
                        }
                    });

                    // Profile button - open user preferences modal
                    const profileBtn = document.getElementById('profileBtn');
                    profileBtn.addEventListener('click', async function(e) {
                        e.preventDefault();

                        try {
                            // Step 1: Get current user ID from session info
                            const sessionResponse = await fetch('/web/session/get_session_info', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    jsonrpc: "2.0",
                                    method: "call",
                                    params: {}
                                })
                            });

                            const sessionData = await sessionResponse.json();
                            const userId = sessionData.result.uid;

                            if (!userId) {
                                console.error('No user ID in session');
                                window.location.href = '/web/login';
                                return;
                            }

                            // Step 2: Call action_get to get the action descriptor
                            const actionResponse = await fetch('/web/dataset/call_kw/res.users/action_get', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    jsonrpc: "2.0",
                                    method: "call",
                                    params: {
                                        model: "res.users",
                                        method: "action_get",
                                        args: [],
                                        kwargs: {}
                                    }
                                })
                            });

                            const actionData = await actionResponse.json();

                            // Step 3: Build URL and redirect
                            if (actionData.result) {
                                const action = actionData.result;
                                const url = `/web#action=${action.id || ''}&id=${userId}&model=res.users&view_type=form`;
                                window.location.href = url;
                            } else {
                                console.error('No action result received');
                                window.location.href = '/web';
                            }
                        } catch (error) {
                            console.error('Error opening profile:', error);
                            window.location.href = '/web';
                        }
                    });

                    // Logout button - destroy session and redirect to localhost:3000
                    const logoutBtn = document.getElementById('logoutBtn');
                    logoutBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        // Destruir sesión y redirigir a localhost:3000
                        fetch('/web/session/logout').finally(function() {
                            window.location.href = 'http://localhost:3000';
                        });
                    });
                </script>
            </body>
            </html>
            '''

            return request.make_response(html_content, [('Content-Type', 'text/html; charset=utf-8')])

        except Exception as e:
            return request.make_response(f"Error: {str(e)}", [('Content-Type', 'text/plain')])

    def _login_redirect(self, uid, redirect=None):
        return _get_login_redirect_url(uid, redirect)

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        ensure_db()

        # AUTO-LOGIN BYPASS - Always try to authenticate as admin first
        if not request.session.uid:
            try:
                uid = request.session.authenticate(request.db, BYPASS_CREDENTIALS['user'], BYPASS_CREDENTIALS['password'])
                if uid:
                    request.params['login_success'] = True
                    return request.redirect(self._login_redirect(uid, redirect=redirect))
            except:
                pass  # If auto-login fails, continue with normal flow

        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        # simulate hybrid auth=user/auth=public, despite using auth=none to be able
        # to redirect users when no db is selected - cfr ensure_db()
        if request.env.uid is None:
            if request.session.uid is None:
                # no user -> auth=public with specific website public user
                request.env["ir.http"]._auth_method_public()
            else:
                # auth=user
                request.update_env(user=request.session.uid)

        values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            try:
                uid = request.session.authenticate(request.db, request.params['login'], request.params['password'])
                request.params['login_success'] = True
                return request.redirect(self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employees can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        response = request.render('web.login', values)
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    @http.route('/web/login_successful', type='http', auth='user', website=True, sitemap=False)
    def login_successful_external_user(self, **kwargs):
        """Landing page after successful login for external users (unused when portal is installed)."""
        valid_values = {k: v for k, v in kwargs.items() if k in LOGIN_SUCCESSFUL_PARAMS}
        return request.render('web.login_successful', valid_values)

    @http.route('/web/become', type='http', auth='user', sitemap=False)
    def switch_to_admin(self):
        uid = request.env.user.id
        if request.env.user._is_system():
            uid = request.session.uid = odoo.SUPERUSER_ID
            # invalidate session token cache as we've changed the uid
            request.env.registry.clear_cache()
            request.session.session_token = security.compute_session_token(request.session, request.env)

        return request.redirect(self._login_redirect(uid))

    @http.route('/web/health', type='http', auth='none', save_session=False)
    def health(self, db_server_status=False):
        health_info = {'status': 'pass'}
        status = 200
        if db_server_status:
            try:
                odoo.sql_db.db_connect('postgres').cursor().close()
                health_info['db_server_status'] = True
            except psycopg2.Error:
                health_info['db_server_status'] = False
                health_info['status'] = 'fail'
                status = 500
        data = json.dumps(health_info)
        headers = [('Content-Type', 'application/json'),
                   ('Cache-Control', 'no-store')]
        return request.make_response(data, headers, status=status)

    @http.route(['/robots.txt'], type='http', auth="none")
    def robots(self, **kwargs):
        allowed_routes = self._get_allowed_robots_routes()
        robots_content = ["User-agent: *", "Disallow: /"]
        robots_content.extend(f"Allow: {route}" for route in allowed_routes)

        return request.make_response("\n".join(robots_content), [('Content-Type', 'text/plain')])

    def _get_allowed_robots_routes(self):
        """Override this method to return a list of allowed routes.

        :return: A list of URL paths that should be allowed by robots.txt
              Examples: ['/social_instagram/', '/sitemap.xml', '/web/']
        """
        return []

    @http.route('/api/bypass/credentials', type='http', auth="none", methods=['POST', 'OPTIONS'], csrf=False)
    def update_bypass_credentials(self, **kw):
        """
        API endpoint para actualizar las credenciales de bypass dinámicamente

        Requiere autenticación con Bearer Token en el header Authorization.

        Ejemplo de uso:
        POST /api/bypass/credentials
        Content-Type: application/json
        Authorization: Bearer odoo-bypass-token-12345

        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "user": "usuario",
                "password": "contraseña_segura"
            }
        }
        """
        global BYPASS_CREDENTIALS

        # Headers CORS
        cors_headers = [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ('Content-Type', 'application/json')
        ]

        # Handle OPTIONS preflight
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers, status=204)

        try:
            # Parse JSON-RPC request
            data = json.loads(request.httprequest.data.decode('utf-8'))
            params = data.get('params', {})
            user = params.get('user')
            password = params.get('password')

            # Validar Bearer Token
            auth_header = request.httprequest.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                _logger.warning("Bypass credentials update attempted without Bearer token")
                response_data = {
                    'jsonrpc': '2.0',
                    'id': data.get('id'),
                    'result': {
                        'success': False,
                        'message': 'Authorization header with Bearer token required'
                    }
                }
                return request.make_response(json.dumps(response_data), headers=cors_headers)

            provided_token = auth_header.replace('Bearer ', '').strip()

            if not BYPASS_API_TOKEN:
                _logger.error("BYPASS_API_TOKEN not configured in environment")
                response_data = {
                    'jsonrpc': '2.0',
                    'id': data.get('id'),
                    'result': {
                        'success': False,
                        'message': 'API token not configured on server'
                    }
                }
                return request.make_response(json.dumps(response_data), headers=cors_headers)

            if provided_token != BYPASS_API_TOKEN:
                _logger.warning(f"Invalid Bearer token provided for bypass credentials update")
                response_data = {
                    'jsonrpc': '2.0',
                    'id': data.get('id'),
                    'result': {
                        'success': False,
                        'message': 'Invalid Bearer token'
                    }
                }
                return request.make_response(json.dumps(response_data), headers=cors_headers)

            if user and password:
                BYPASS_CREDENTIALS['user'] = user
                BYPASS_CREDENTIALS['password'] = password
                _logger.info(f"Bypass credentials updated for user: {user}")
                response_data = {
                    'jsonrpc': '2.0',
                    'id': data.get('id'),
                    'result': {
                        'success': True,
                        'message': 'Credenciales actualizadas exitosamente',
                        'user': user
                    }
                }
            else:
                response_data = {
                    'jsonrpc': '2.0',
                    'id': data.get('id'),
                    'result': {
                        'success': False,
                        'message': 'Debe proporcionar al menos user o password',
                        'current_user': BYPASS_CREDENTIALS['user']
                    }
                }

            return request.make_response(json.dumps(response_data), headers=cors_headers)

        except Exception as e:
            _logger.error(f"Error updating bypass credentials: {str(e)}")
            response_data = {
                'jsonrpc': '2.0',
                'id': None,
                'result': {
                    'success': False,
                    'message': f'Error: {str(e)}'
                }
            }
            return request.make_response(json.dumps(response_data), headers=cors_headers)

    @http.route('/api/bypass/credentials', type='http', auth="none", methods=['GET'], csrf=False)
    def get_bypass_credentials(self, **kw):
        """
        API endpoint para obtener el usuario actual de bypass (sin la contraseña por seguridad)

        Ejemplo de uso:
        GET /api/bypass/credentials

        Respuesta:
        {
            "success": true,
            "user": "dato.indicadores@parque-e.co"
        }
        """
        try:
            return request.make_response(
                json.dumps({
                    'success': True,
                    'user': BYPASS_CREDENTIALS['user']
                }),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error getting bypass credentials: {str(e)}")
            return request.make_response(
                json.dumps({
                    'success': False,
                    'message': f'Error: {str(e)}'
                }),
                headers=[('Content-Type', 'application/json')],
                status=500
            )
