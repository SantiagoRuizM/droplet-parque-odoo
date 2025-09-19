# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import psycopg2


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


# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang', 'signup_email'}
LOGIN_SUCCESSFUL_PARAMS = set()


class Home(http.Controller):

    @http.route('/', type='http', auth="none")
    def index(self, s_action=None, db=None, **kw):
        # AUTO-LOGIN BYPASS on index page
        ensure_db()
        if not request.session.uid:
            try:
                uid = request.session.authenticate(request.db, 'admin', 'admin')
                if uid:
                    request.update_env(user=uid)
            except:
                pass

        if request.db and request.session.uid and not is_user_internal(request.session.uid):
            return request.redirect_query('/web/login_successful', query=request.params)
        # CUSTOM: Redirect to our apps page instead of /web
        if request.db and request.session.uid and is_user_internal(request.session.uid):
            return request.redirect('/apps')
        return request.redirect_query('/web', query=request.params)

    # ideally, this route should be `auth="user"` but that don't work in non-monodb mode.
    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):

        # Ensure we have both a database and a user
        ensure_db()
        if not request.session.uid:
            # AUTO-LOGIN BYPASS - Try to authenticate as admin
            try:
                uid = request.session.authenticate(request.db, 'admin', 'admin')
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
                    uid = request.session.authenticate(request.db, 'admin', 'admin')
                    if uid:
                        request.update_env(user=uid)
                except:
                    return request.redirect('/web/login')

            # Restore the user on the environment
            request.update_env(user=request.session.uid)

            user = request.env.user
            company = user.company_id

            # Create static HTML that looks exactly like Odoo navbar
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no"/>
                <title>Test Navbar - {company.name}</title>
                <link type="image/x-icon" rel="shortcut icon" href="/web/static/img/favicon.ico"/>

                <!-- Load Odoo UI Icons -->
                <link rel="stylesheet" type="text/css" href="/web/static/lib/odoo_ui_icons/style.css"/>

                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
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
                        width: 24px;
                        height: 24px;
                        border-radius: 4px;
                        background-color: #b44931;
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 12px;
                        font-weight: 600;
                        text-transform: uppercase;
                    }}

                    .o_menu_brand {{
                        color: white;
                        font-weight: 600;
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

                    .test-content {{
                        padding: 40px 20px;
                        text-align: center;
                        font-size: 1.5rem;
                        color: #666;
                        background: #f2f5f6;
                        min-height: calc(100vh - 48px);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        flex-direction: column;
                    }}

                    .success-message {{
                        background: #d4edda;
                        color: #155724;
                        padding: 20px;
                        border-radius: 8px;
                        border: 1px solid #c3e6cb;
                        margin-bottom: 20px;
                        max-width: 600px;
                    }}
                </style>
            </head>
            <body>
                <!-- Static Odoo-style navbar -->
                <header class="o_navbar">
                    <nav class="o_main_navbar">
                        <!-- Apps Menu -->
                        <div class="o_navbar_apps_menu">
                            <button onclick="window.location.href='/web'">
                                <i class="oi oi-apps"></i>
                            </button>
                        </div>

                        <!-- Brand -->
                        <a href="/web" class="o_menu_brand">
                            Aplicaciones
                        </a>

                        <!-- Systray -->
                        <div class="o_menu_systray">
                            <button onclick="window.location.href='/web/session/logout'">
                                <div class="o_user_avatar">
                                    {user.name[0] if user.name else 'U'}
                                </div>
                            </button>
                        </div>
                    </nav>
                </header>

                <!-- Custom content -->
                <div class="test-content">
                    <div class="success-message">
                        ✅ <strong>¡NAVBAR FUNCIONANDO!</strong><br>
                        Este es el navbar de Odoo recreado sin JavaScript que cause redirecciones.<br>
                        Se ve igual al original pero es HTML/CSS estático.
                    </div>

                    <p>Usuario: <strong>{user.name}</strong></p>
                    <p>Empresa: <strong>{company.name}</strong></p>
                </div>
            </body>
            </html>
            '''

            return request.make_response(html_content, [('Content-Type', 'text/html; charset=utf-8')])

        except Exception as e:
            return request.make_response(f"Error: {{str(e)}}", [('Content-Type', 'text/plain')])

    def _login_redirect(self, uid, redirect=None):
        return _get_login_redirect_url(uid, redirect)

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        ensure_db()

        # AUTO-LOGIN BYPASS - Always try to authenticate as admin first
        if not request.session.uid:
            try:
                uid = request.session.authenticate(request.db, 'admin', 'admin')
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
