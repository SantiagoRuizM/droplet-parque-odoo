# 📚 Documentación - Proceso de Login en Odoo 17

## 🎯 Propósito

Esta documentación explica el funcionamiento interno del sistema de autenticación de Odoo 17, basada en el análisis del código fuente y la implementación exitosa del bypass de login en el proyecto Parque ERP.

---

## 🏗️ Arquitectura del Sistema de Login

### 📁 Estructura de Archivos Clave

```
odoo/addons/web/controllers/
├── home.py           # Controlador principal de autenticación
├── session.py        # Manejo de sesiones y APIs JSON
└── utils.py          # Funciones utilitarias de login
```

---

## 🔐 Flujo de Autenticación Completo

### 1. **Punto de Entrada** - `index()` (Ruta: `/`)

**Archivo:** `home.py:31-35`

```python
@http.route('/', type='http', auth="none")
def index(self, s_action=None, db=None, **kw):
    if request.db and request.session.uid and not is_user_internal(request.session.uid):
        return request.redirect_query('/web/login_successful', query=request.params)
    return request.redirect_query('/web', query=request.params)
```

**Función:**
- Detecta si hay sesión activa (`request.session.uid`)
- Verifica tipo de usuario (`is_user_internal()`)
- **Usuario externo** → `/web/login_successful`
- **Usuario interno o sin sesión** → `/web`

### 2. **Cliente Web** - `web_client()` (Ruta: `/web`)

**Archivo:** `home.py:38-63`

```python
@http.route('/web', type='http', auth="none")
def web_client(self, s_action=None, **kw):
    ensure_db()
    if not request.session.uid:
        return request.redirect_query('/web/login', query=request.params, code=303)
    # ... validaciones de sesión ...
    return request.render('web.webclient_bootstrap', qcontext=context)
```

**Validaciones clave:**
1. **`ensure_db()`** - Garantiza base de datos disponible
2. **`request.session.uid`** - Verifica usuario autenticado
3. **`security.check_session()`** - Valida sesión no expirada
4. **`is_user_internal()`** - Confirma permisos de usuario interno

### 3. **Formulario de Login** - `web_login()` (Ruta: `/web/login`)

**Archivo:** `home.py:89-136`

#### 🔄 Flujo GET (Mostrar formulario)

```python
# Verificación de sesión existente
if request.httprequest.method == 'GET' and redirect and request.session.uid:
    return request.redirect(redirect)

# Preparación de valores para template
values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
```

#### 🔄 Flujo POST (Procesar login)

```python
if request.httprequest.method == 'POST':
    try:
        uid = request.session.authenticate(request.db, request.params['login'], request.params['password'])
        request.params['login_success'] = True
        return request.redirect(self._login_redirect(uid, redirect=redirect))
    except odoo.exceptions.AccessDenied as e:
        values['error'] = _("Wrong login/password")
```

**Proceso de autenticación:**
1. **`request.session.authenticate(db, login, password)`** - Validación core
2. **`login_success = True`** - Marcador de éxito
3. **`_login_redirect(uid, redirect)`** - Redirección inteligente

---

## 🔧 Funciones Utilitarias Críticas

### 🛡️ `ensure_db()` - Gestión de Base de Datos

**Archivo:** `utils.py:55-107`

```python
def ensure_db(redirect='/web/database/selector', db=None):
    # Detectar DB desde parámetros
    db = request.params.get('db') and request.params.get('db').strip()

    # Validar DB contra filtros de seguridad
    if db and db not in http.db_filter([db]):
        db = None

    # Modo monodb - detectar automáticamente
    if not db:
        all_dbs = http.db_list(force=True)
        if len(all_dbs) == 1:
            db = all_dbs[0]
```

**Funciones:**
- Detecta base de datos disponible
- Aplica filtros de seguridad (`http.db_filter`)
- Maneja modo mono-base vs multi-base
- Redirige a selector si es necesario

### 🎯 `_get_login_redirect_url()` - Redirección Inteligente

**Archivo:** `utils.py:184-200`

```python
def _get_login_redirect_url(uid, redirect=None):
    if request.session.uid:  # Sesión completa
        return redirect or ('/web' if is_user_internal(request.session.uid)
                            else '/web/login_successful')

    # Sesión parcial (MFA pendiente)
    url = request.env(user=uid)['res.users'].browse(uid)._mfa_url()
    # ... manejo de MFA ...
```

**Lógica de redirección:**
1. **Sesión completa** → Verifica tipo de usuario
   - **Usuario interno** → `/web` (dashboard)
   - **Usuario externo** → `/web/login_successful`
2. **Sesión parcial** → URL de MFA (autenticación multi-factor)

### 👤 `is_user_internal()` - Verificación de Permisos

**Archivo:** `utils.py:203-204`

```python
def is_user_internal(uid):
    return request.env['res.users'].browse(uid)._is_internal()
```

**Determina:**
- **Usuario interno**: Empleados, administradores
- **Usuario externo**: Clientes del portal, usuarios públicos

---

## 🔄 API de Sesión JSON

### 📡 `/web/session/authenticate` - Autenticación Programática

**Archivo:** `session.py:29-51`

```python
@http.route('/web/session/authenticate', type='json', auth="none")
def authenticate(self, db, login, password, base_location=None):
    if not http.db_filter([db]):
        raise AccessError("Database not found.")

    pre_uid = request.session.authenticate(db, login, password)
    if pre_uid != request.session.uid:
        return {'uid': None}  # Fallo de MFA

    return env['ir.http'].session_info()
```

**Para APIs y aplicaciones móviles:**
- Autenticación via JSON
- Manejo de MFA integrado
- Retorna información completa de sesión

---

## 🎨 Bypass de Login - Implementación Exitosa

### 💡 Estrategia Implementada

**Modificación en múltiples puntos del flujo:**

#### 1. **Index Page** (`/`)
```python
@http.route('/', type='http', auth="none")
def index(self, s_action=None, db=None, **kw):
    # AUTO-LOGIN BYPASS
    ensure_db()
    if not request.session.uid:
        try:
            uid = request.session.authenticate(request.db, 'admin', 'admin')
            if uid:
                request.update_env(user=uid)
        except:
            pass
    # ... flujo original ...
```

#### 2. **Web Client** (`/web`)
```python
if not request.session.uid:
    # AUTO-LOGIN BYPASS
    try:
        uid = request.session.authenticate(request.db, 'admin', 'admin')
        if uid:
            request.update_env(user=uid)
        else:
            return request.redirect_query('/web/login', query=request.params, code=303)
    except:
        return request.redirect_query('/web/login', query=request.params, code=303)
```

#### 3. **Login Form** (`/web/login`)
```python
@http.route('/web/login', type='http', auth="none")
def web_login(self, redirect=None, **kw):
    ensure_db()

    # AUTO-LOGIN BYPASS
    if not request.session.uid:
        try:
            uid = request.session.authenticate(request.db, 'admin', 'admin')
            if uid:
                request.params['login_success'] = True
                return request.redirect(self._login_redirect(uid, redirect=redirect))
        except:
            pass  # Continuar con flujo normal
```

### ✅ Ventajas de esta Implementación

1. **Respeta el flujo original completo**
   - Usa `request.session.authenticate()` oficial
   - Mantiene `_login_redirect()` para MFA
   - Preserva validaciones de seguridad

2. **Manejo de errores robusto**
   - Fallback al login normal si falla
   - No rompe funcionalidad existente

3. **Cobertura completa**
   - Intercepta en todos los puntos de entrada
   - Funciona para URLs directas y navegación

---

## 🛠️ Implementación Técnica

### 📦 Deployment con Volúmenes Docker

```yaml
# docker-compose.yml
volumes:
  - ./custom_home_bypass.py:/usr/lib/python3/dist-packages/odoo/addons/web/controllers/home.py:ro
```

**Ventajas:**
- ✅ **Portable** - Funciona en cualquier servidor
- ✅ **Reversible** - Quitar volumen restaura original
- ✅ **Mantenible** - Cambios en archivo local se reflejan
- ✅ **Seguro** - No modifica imagen base de Odoo

### 🔍 Verificación de Funcionamiento

```bash
# Test 1: Verificar redirección automática
curl -I http://localhost:8069
# Esperado: HTTP 303 → Location: /web

# Test 2: Verificar sesión establecida
curl -s http://localhost:8069/web | grep '"uid"'
# Esperado: "uid": 2, "is_admin": true, "username": "admin"

# Test 3: Verificar ausencia de formulario login
curl -s http://localhost:8069/web | grep -i "password\|login\|username"
# Esperado: Solo información de sesión, NO campos de formulario
```

---

## 📋 Parámetros y Variables Clave

### 🔑 Variables de Sesión

- **`request.session.uid`** - ID del usuario autenticado (None si no autenticado)
- **`request.session.db`** - Base de datos de la sesión
- **`request.session.context`** - Contexto de usuario (idioma, timezone, etc.)

### 📝 Parámetros de Request

```python
SIGN_UP_REQUEST_PARAMS = {
    'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
    'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
    'password', 'confirm_password', 'city', 'country_id', 'lang', 'signup_email'
}
```

### 🏷️ Estados de Login

- **`login_success`** - Marcador de autenticación exitosa
- **`error`** - Mensaje de error de login
- **`redirect`** - URL de redirección post-login

---

## 🔒 Consideraciones de Seguridad

### ⚠️ Implicaciones del Bypass

1. **Acceso sin credenciales** - Cualquier usuario puede acceder como admin
2. **Ideal para desarrollo** - Entornos de testing y desarrollo
3. **NO para producción** - Eliminar en entornos públicos

### 🛡️ Medidas de Seguridad Recomendadas

```python
# Condicional por entorno
if os.environ.get('ODOO_ENV') == 'development':
    # Aplicar bypass solo en desarrollo
    uid = request.session.authenticate(request.db, 'admin', 'admin')
```

### 🔐 Alternativas Seguras

1. **Token de acceso** - API tokens para automatización
2. **OAuth/LDAP** - Integración con sistemas de autenticación corporativos
3. **Usuario demo** - Cuenta específica para demos con permisos limitados

---

## 📊 Flujo Completo Visualizado

```mermaid
graph TD
    A[Usuario accede /] --> B{¿Tiene sesión?}
    B -->|No| C[Auto-login admin/admin]
    B -->|Sí| D{¿Usuario interno?}

    C --> E{¿Login exitoso?}
    E -->|Sí| F[Establecer sesión]
    E -->|No| G[Continuar flujo normal]

    D -->|Sí| H[Redirigir a /web]
    D -->|No| I[Redirigir a /web/login_successful]

    F --> H
    G --> J[Mostrar formulario login]
    H --> K[Cargar dashboard]

    J --> L[Usuario ingresa credenciales]
    L --> M[request.session.authenticate()]
    M --> N{¿Autenticación exitosa?}
    N -->|Sí| O[_login_redirect()]
    N -->|No| P[Mostrar error]

    O --> Q{¿MFA requerido?}
    Q -->|Sí| R[Redirigir a MFA]
    Q -->|No| S{¿Usuario interno?}
    S -->|Sí| H
    S -->|No| I
```

---

## 🚀 Casos de Uso

### 1. **Desarrollo Local**
- Bypass para testing rápido
- Evitar login repetitivo en desarrollo

### 2. **Demos y Presentaciones**
- Acceso inmediato para demostraciones
- URL directa para clientes

### 3. **Entornos de Testing**
- Automatización de tests
- CI/CD sin intervención manual

### 4. **Kioscos y Pantallas**
- Dispositivos dedicados sin teclado
- Acceso automático en puntos de venta

---

## 🔧 Personalización Avanzada

### 🎨 Modificar Usuario de Auto-login

```python
# En lugar de admin/admin, usar credenciales específicas
uid = request.session.authenticate(request.db, 'demo_user', 'demo_pass')
```

### 🌐 Auto-login Condicional por IP

```python
# Solo aplicar bypass desde IPs específicas
allowed_ips = ['127.0.0.1', '192.168.1.0/24']
if request.httprequest.remote_addr in allowed_ips:
    uid = request.session.authenticate(request.db, 'admin', 'admin')
```

### ⏰ Auto-login con Expiración

```python
# Bypass solo durante horario específico
from datetime import datetime
current_hour = datetime.now().hour
if 9 <= current_hour <= 17:  # 9 AM a 5 PM
    uid = request.session.authenticate(request.db, 'admin', 'admin')
```

---

## 📖 Referencias y Recursos

### 📚 Documentación Oficial
- [Odoo Web Controllers](https://www.odoo.com/documentation/17.0/developer/reference/backend/controllers.html)
- [Odoo Authentication](https://www.odoo.com/documentation/17.0/developer/reference/backend/security.html)

### 🔍 Archivos Fuente Analizados
- `odoo/addons/web/controllers/home.py`
- `odoo/addons/web/controllers/session.py`
- `odoo/addons/web/controllers/utils.py`

### 🎯 Implementación de Referencia
- Repositorio: `droplet-parque-odoo`
- Archivo: `custom_home_bypass.py`
- Commit: `e451055a`

---

## 📝 Conclusiones

El sistema de autenticación de Odoo 17 está bien estructurado y permite modificaciones quirúrgicas para casos de uso específicos. La implementación del bypass demuestra:

1. **Flexibilidad del framework** - Permite overrides controlados
2. **Mantenimiento de seguridad** - Respeta validaciones existentes
3. **Portabilidad** - Deployment con Docker volúmenes
4. **Escalabilidad** - Base para funcionalidades avanzadas de autenticación

Esta documentación sirve como referencia para futuras modificaciones del sistema de login y desarrollo de features relacionados con autenticación en el proyecto Parque ERP.

---

**🏷️ Versión:** 1.0
**📅 Fecha:** Septiembre 2025
**👨‍💻 Autor:** Claude Code + Santiago Ruiz
**🎯 Proyecto:** Parque ERP - Odoo 17