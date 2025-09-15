# Odoo Parque ERP - Docker Setup

🧡 **Odoo 17 con tema naranja profesional y configuración simplificada**

## 🚀 Características

- ✅ **Odoo 17** - Última versión estable
- ✅ **Tema naranja profesional** - Diseño personalizado
- ✅ **Acceso sin login** - Entrada directa como admin
- ✅ **PostgreSQL 15** - Base de datos optimizada
- ✅ **Español disponible** - Interfaz en español
- ✅ **Sin apps preinstaladas** - Instalación limpia, elige lo que necesites

## 📋 Requisitos

- Docker
- Docker Compose
- Puerto 8069 disponible

## ⚡ Inicio rápido

```bash
# Clonar el repositorio
git clone <repo-url>
cd droplet-odoo

# Levantar los contenedores
docker-compose up -d

# Acceder a Odoo
# http://localhost:8069
```

## 🔧 Configuración

### Contenedores incluidos:
- **odoo-parque**: Servidor Odoo 17
- **odoo-postgres-parque**: Base de datos PostgreSQL 15

### Configuraciones aplicadas:
- **Puerto**: 8069
- **Usuario admin**: admin/admin (automático)
- **Base de datos**: odoo
- **Tema**: Naranja profesional
- **Idioma**: Español disponible (activar en configuración)

## 📁 Estructura del proyecto

```
droplet-odoo/
├── docker-compose.yml      # Configuración principal
├── Dockerfile             # Imagen personalizada (si aplica)
├── odoo.conf              # Configuración de Odoo
├── orange-theme-colors.scss # Colores del tema naranja
├── addons/                # Addons personalizados
└── README.md              # Esta documentación
```

## 🎨 Tema naranja

El proyecto incluye un tema naranja profesional aplicado automáticamente. Los colores están definidos en `orange-theme-colors.scss`.

### Colores principales:
- **Naranja principal**: `#E85A2B`
- **Naranja oscuro**: `#CC4A1D`
- **Naranja claro**: `#FF6B35`

## 🌍 Configuración de idioma

1. Accede a Odoo en http://localhost:8069
2. Ve a **Configuración > Traducciones > Idiomas**
3. Activa **Español**
4. Ve a tu perfil de usuario y cambia el idioma

## 📱 Instalación de Apps

El sistema viene con una instalación limpia. Para instalar aplicaciones:

1. Ve a **Apps** en el menú principal
2. Selecciona las aplicaciones que necesites:
   - CRM
   - Ventas
   - Inventario
   - Contabilidad
   - Manufactura
   - Y muchas más...

## 🔄 Comandos útiles

```bash
# Ver logs
docker-compose logs -f odoo

# Reiniciar servicios
docker-compose restart

# Parar todo
docker-compose down

# Limpiar y empezar de nuevo
docker-compose down -v
docker-compose up -d
```

## 🛠️ Desarrollo

Para añadir addons personalizados:
1. Coloca tus addons en la carpeta `addons/`
2. Reinicia el contenedor
3. Instala desde el menú Apps

## 📄 Licencia

Este proyecto está bajo la licencia LGPL v3 (ver archivo LICENSE).

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

---

**Proyecto Parque ERP** - Odoo simplificado para empresas modernas 🚀