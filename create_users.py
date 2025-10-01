#!/usr/bin/env python3
"""
Script para crear usuarios automáticamente en Odoo desde users.json
Se ejecuta después de que Odoo termine de inicializar la base de datos
"""

import xmlrpc.client
import json
import time
import sys
import os

# Configuración de conexión a Odoo
ODOO_URL = "http://localhost:8069"
ODOO_DB = "odoo"
ODOO_ADMIN_USER = "admin"
ODOO_ADMIN_PASSWORD = "admin"
USERS_JSON_PATH = "/mnt/extra-addons/users.json"

# Colores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(message, color=Colors.BLUE):
    """Imprimir mensaje con color"""
    print(f"{color}[CREATE-USERS]{Colors.END} {message}")

def wait_for_odoo(max_attempts=30):
    """Esperar a que Odoo esté disponible"""
    log("Esperando a que Odoo esté disponible...", Colors.YELLOW)

    for attempt in range(max_attempts):
        try:
            common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
            version = common.version()
            log(f"✓ Odoo está listo! Versión: {version['server_version']}", Colors.GREEN)
            return True
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(2)
            else:
                log(f"✗ Error: No se pudo conectar a Odoo después de {max_attempts} intentos", Colors.RED)
                log(f"  Detalle: {str(e)}", Colors.RED)
                return False
    return False

def authenticate():
    """Autenticarse como admin en Odoo"""
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_ADMIN_USER, ODOO_ADMIN_PASSWORD, {})

        if uid:
            log(f"✓ Autenticado como admin (uid: {uid})", Colors.GREEN)
            return uid
        else:
            log("✗ Error: Autenticación fallida", Colors.RED)
            return None
    except Exception as e:
        log(f"✗ Error en autenticación: {str(e)}", Colors.RED)
        return None

def load_users_config():
    """Cargar configuración de usuarios desde JSON"""
    try:
        if not os.path.exists(USERS_JSON_PATH):
            log(f"✗ Error: Archivo {USERS_JSON_PATH} no encontrado", Colors.RED)
            return None

        with open(USERS_JSON_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)

        users = config.get('users', [])
        log(f"✓ Configuración cargada: {len(users)} usuarios", Colors.GREEN)
        return users
    except Exception as e:
        log(f"✗ Error al cargar JSON: {str(e)}", Colors.RED)
        return None

def get_group_id(models, uid, group_xml_id):
    """Obtener ID del grupo por su XML ID"""
    try:
        group_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_ADMIN_PASSWORD,
            'ir.model.data', 'search_read',
            [[['module', '=', 'base'], ['name', '=', group_xml_id.split('.')[1]]]],
            {'fields': ['res_id']}
        )
        if group_ids:
            return group_ids[0]['res_id']
        return None
    except Exception as e:
        log(f"  ⚠ Warning: No se pudo obtener grupo {group_xml_id}: {str(e)}", Colors.YELLOW)
        return None

def user_exists(models, uid, login):
    """Verificar si un usuario ya existe"""
    try:
        user_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_ADMIN_PASSWORD,
            'res.users', 'search',
            [[['login', '=', login]]]
        )
        return len(user_ids) > 0
    except Exception as e:
        log(f"  ✗ Error al verificar usuario: {str(e)}", Colors.RED)
        return False

def create_user(models, uid, user_data):
    """Crear un usuario en Odoo"""
    try:
        login = user_data['login']

        # Verificar si el usuario ya existe
        if user_exists(models, uid, login):
            log(f"  ⊘ Usuario '{login}' ya existe, omitiendo...", Colors.YELLOW)
            return None

        # Preparar datos del usuario
        is_internal = user_data.get('is_internal', False)

        # Grupos base
        groups = []

        if is_internal:
            # Usuario interno: grupo base.group_user
            group_id = get_group_id(models, uid, 'base.group_user')
            if group_id:
                groups.append((4, group_id))  # (4, id) = link
        else:
            # Usuario portal: grupo base.group_portal
            group_id = get_group_id(models, uid, 'base.group_portal')
            if group_id:
                groups.append((4, group_id))

        # Datos del usuario
        user_vals = {
            'login': login,
            'name': user_data['name'],
            'email': user_data['email'],
            'password': user_data['password'],
            'lang': user_data.get('lang', 'es_ES'),
            'tz': user_data.get('tz', 'America/Bogota'),
            'active': True,
        }

        if groups:
            user_vals['groups_id'] = groups

        # Crear usuario
        new_user_id = models.execute_kw(
            ODOO_DB, uid, ODOO_ADMIN_PASSWORD,
            'res.users', 'create',
            [user_vals]
        )

        user_type = "interno" if is_internal else "portal"
        log(f"  ✓ Usuario '{login}' creado exitosamente (ID: {new_user_id}, tipo: {user_type})", Colors.GREEN)
        return new_user_id

    except Exception as e:
        log(f"  ✗ Error al crear usuario '{user_data.get('login', 'unknown')}': {str(e)}", Colors.RED)
        return None

def main():
    """Función principal"""
    log("=" * 60, Colors.BLUE)
    log("Iniciando creación automática de usuarios", Colors.BLUE)
    log("=" * 60, Colors.BLUE)

    # 1. Esperar a que Odoo esté disponible
    if not wait_for_odoo():
        log("Abortando script por falta de conexión con Odoo", Colors.RED)
        sys.exit(1)

    # 2. Autenticarse
    uid = authenticate()
    if not uid:
        log("Abortando script por fallo en autenticación", Colors.RED)
        sys.exit(1)

    # 3. Cargar configuración de usuarios
    users_config = load_users_config()
    if not users_config:
        log("Abortando script por fallo al cargar configuración", Colors.RED)
        sys.exit(1)

    # 4. Conectar a models API
    try:
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    except Exception as e:
        log(f"✗ Error al conectar a API de modelos: {str(e)}", Colors.RED)
        sys.exit(1)

    # 5. Crear usuarios
    log(f"\nCreando {len(users_config)} usuarios...", Colors.BLUE)
    created_count = 0
    skipped_count = 0
    error_count = 0

    for user_data in users_config:
        result = create_user(models, uid, user_data)
        if result:
            created_count += 1
        elif result is None and user_exists(models, uid, user_data['login']):
            skipped_count += 1
        else:
            error_count += 1

    # 6. Resumen
    log("\n" + "=" * 60, Colors.BLUE)
    log("Resumen de creación de usuarios:", Colors.BLUE)
    log(f"  ✓ Creados: {created_count}", Colors.GREEN)
    log(f"  ⊘ Omitidos (ya existían): {skipped_count}", Colors.YELLOW)
    if error_count > 0:
        log(f"  ✗ Errores: {error_count}", Colors.RED)
    log("=" * 60, Colors.BLUE)

    log("\n✓ Script completado exitosamente!", Colors.GREEN)
    log("\nPara usar un usuario en el bypass, edita custom_home_bypass.py línea 18:", Colors.BLUE)
    log("  uid = request.session.authenticate(request.db, 'dato.calidad@parque-e.co', '123456')", Colors.YELLOW)

if __name__ == "__main__":
    main()
