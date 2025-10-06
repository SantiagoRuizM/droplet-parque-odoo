# API de Credenciales de Bypass

Esta API permite actualizar dinámicamente las credenciales de auto-login (bypass) sin necesidad de reiniciar el contenedor de Odoo.

## Endpoints Disponibles

### 1. Obtener usuario actual de bypass

**GET** `/api/bypass/credentials`

Retorna el usuario actual configurado para el auto-login (no incluye la contraseña por seguridad).

#### Ejemplo con cURL:
```bash
curl -X GET http://localhost:8069/api/bypass/credentials
```

#### Ejemplo con JavaScript (fetch):
```javascript
fetch('http://localhost:8069/api/bypass/credentials')
  .then(response => response.json())
  .then(data => console.log(data));
```

#### Respuesta:
```json
{
  "success": true,
  "user": "dato.indicadores@parque-e.co"
}
```

---

### 2. Actualizar credenciales de bypass

**POST** `/api/bypass/credentials`
**Content-Type:** `application/json`

Actualiza el usuario y/o contraseña para el auto-login.

#### Parámetros:
- `user` (opcional): Nuevo usuario/email para auto-login
- `password` (opcional): Nueva contraseña para auto-login

**Nota:** Debes proporcionar al menos uno de los dos parámetros.

#### Ejemplo 1: Actualizar ambos (usuario y contraseña)

```bash
curl -X POST http://localhost:8069/api/bypass/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "user": "nuevo.usuario@parque-e.co",
      "password": "nueva_contraseña"
    }
  }'
```

#### Ejemplo 2: Actualizar solo el usuario

```bash
curl -X POST http://localhost:8069/api/bypass/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "user": "otro.usuario@parque-e.co"
    }
  }'
```

#### Ejemplo 3: Actualizar solo la contraseña

```bash
curl -X POST http://localhost:8069/api/bypass/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "password": "super_segura_123"
    }
  }'
```

#### Ejemplo con JavaScript (fetch):

```javascript
fetch('http://localhost:8069/api/bypass/credentials', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    jsonrpc: "2.0",
    method: "call",
    params: {
      user: "nuevo.usuario@parque-e.co",
      password: "nueva_contraseña"
    }
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

#### Respuesta exitosa:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "message": "Credenciales actualizadas exitosamente",
    "user": "nuevo.usuario@parque-e.co"
  }
}
```

#### Respuesta de error:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": false,
    "message": "Debe proporcionar al menos user o password",
    "current_user": "dato.indicadores@parque-e.co"
  }
}
```

---

## Credenciales por Defecto

Al iniciar el contenedor, las credenciales por defecto son:
- **Usuario:** `dato.indicadores@parque-e.co`
- **Contraseña:** `123456`

---

## Notas Importantes

1. **Los cambios son temporales**: Las credenciales actualizadas vía API se mantienen solo mientras el contenedor esté corriendo. Si se reinicia el contenedor (`docker-compose restart` o `docker-compose down && up`), las credenciales volverán a los valores por defecto.

2. **Sin autenticación**: Estos endpoints no requieren autenticación (`auth="none"`), lo que permite cambiar las credenciales sin estar logueado. **Considerar agregar autenticación en producción.**

3. **CSRF deshabilitado**: El CSRF está deshabilitado (`csrf=False`) para permitir llamadas desde clientes externos.

4. **El usuario debe existir en Odoo**: Las credenciales configuradas deben corresponder a un usuario válido en la base de datos de Odoo.

---

## Casos de Uso

### Integración con sistema externo de autenticación
```javascript
// Después de autenticar en tu sistema (ej: Supabase)
async function syncOdooBypass(userEmail, userPassword) {
  const response = await fetch('http://localhost:8069/api/bypass/credentials', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: "2.0",
      method: "call",
      params: { user: userEmail, password: userPassword }
    })
  });

  const result = await response.json();
  if (result.result.success) {
    console.log('Odoo bypass sincronizado con usuario:', userEmail);
  }
}
```

### Script de inicialización
```bash
#!/bin/bash
# init_odoo_bypass.sh

# Esperar a que Odoo esté listo
sleep 10

# Configurar credenciales desde variables de entorno
curl -X POST http://localhost:8069/api/bypass/credentials \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"method\": \"call\",
    \"params\": {
      \"user\": \"$ODOO_BYPASS_USER\",
      \"password\": \"$ODOO_BYPASS_PASSWORD\"
    }
  }"
```

---

## Seguridad

⚠️ **Advertencias de seguridad:**

1. Esta API está diseñada para ambientes de desarrollo/staging
2. En producción, considerar:
   - Agregar autenticación (API key, token, etc.)
   - Restringir acceso por IP
   - Usar HTTPS
   - Agregar rate limiting
   - Logs de auditoría para cambios de credenciales
