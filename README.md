# Odoo Parque ERP - Docker Setup

🧡 **Odoo 17 con tema naranja profesional y configuración empresarial**

## 🚀 Características

- ✅ **Odoo 17** - Última versión estable
- ✅ **Tema naranja profesional** - Diseño personalizado integrado
- ✅ **Imagen Docker personalizada** - Lista para producción
- ✅ **PostgreSQL 15** - Base de datos optimizada
- ✅ **Configuración colombiana** - Timezone y localización
- ✅ **Instalación limpia** - Sin demos, elige las apps que necesites

## 📋 Requisitos

- Docker Engine 20.10+
- Docker Compose v2.0+
- 2GB RAM mínimo
- Puerto 80 o 8069 disponible

## ⚡ Inicio rápido

### Opción 1: Imagen estándar (requiere login)
```bash
# Clonar el repositorio
git clone https://github.com/SantiagoRuizM/droplet-parque-odoo.git
cd droplet-parque-odoo

# Levantar los contenedores
docker-compose up -d

# Acceder a Odoo
# http://localhost:8069
# Credenciales: admin/admin
```

### Opción 2: Imagen personalizada con tema naranja
```bash
# Usar la configuración con tema naranja
docker-compose -f docker-compose.orange.yml up -d

# Acceder a Odoo con tema naranja
# http://localhost
```

## 🎨 Tema Naranja Profesional

### 🏗️ Arquitectura del tema
El tema naranja está implementado como una **imagen Docker personalizada** que modifica:

1. **Variables SCSS** (`primary_variables.scss`)
   - Color principal: `#E85A2B` (Naranja profesional)
   - Botones, enlaces y elementos de acción
   - Paleta de colores complementaria

2. **Meta tags HTML** (`webclient_templates.xml`)
   - Theme-color para navegadores móviles
   - Favicon y iconos de aplicación

### 🔧 Archivos del tema
```
theme/
├── primary_variables_orange.scss    # Variables de color SCSS
├── webclient_templates_orange.xml   # Templates HTML
└── Dockerfile.orange               # Imagen personalizada
```

### 🎯 Colores principales
- **Naranja principal**: `#E85A2B`
- **Naranja hover**: `#CC4A1D` (10% más oscuro)
- **Naranja activo**: `#B8421A` (20% más oscuro)
- **Complementarios**: Grises profesionales y colores de estado

## 🐳 Docker Images

### Imagen estándar
- **Base**: `odoo:17`
- **Tema**: Púrpura estándar de Odoo
- **Uso**: Desarrollo y testing

### Imagen personalizada
- **Tag**: `parque-erp/odoo:17-orange`
- **Base**: `odoo:17` + modificaciones de tema
- **Uso**: Producción con identidad de marca

### Construcción de imagen personalizada
```bash
# Construir la imagen localmente
docker build -f Dockerfile.orange -t parque-erp/odoo:17-orange .

# Verificar la construcción
docker run --rm parque-erp/odoo:17-orange cat /usr/lib/python3/dist-packages/odoo/PARQUE_THEME_INFO
```

## 🔧 Configuración

### Contenedores incluidos
- **odoo-parque**: Servidor Odoo 17
- **odoo-postgres-parque**: Base de datos PostgreSQL 15

### Variables de entorno
```yaml
environment:
  HOST: postgres              # Host de la base de datos
  USER: odoo                 # Usuario de la base de datos
  PASSWORD: odoo             # Contraseña de la base de datos
  TZ: America/Bogota         # Timezone Colombia
```

### Puertos y volúmenes
- **Puerto**: 80:8069 (externo:interno)
- **Volúmenes persistentes**:
  - `postgres_data`: Datos de PostgreSQL
  - `odoo_data`: Filestore y assets de Odoo

## 📁 Estructura del proyecto

```
droplet-parque-odoo/
├── docker-compose.yml          # Configuración estándar
├── docker-compose.orange.yml   # Configuración con tema naranja
├── Dockerfile.orange           # Imagen personalizada
├── theme/                      # Archivos del tema naranja
│   ├── primary_variables_orange.scss
│   ├── webclient_templates_orange.xml
│   └── ...
├── orange-theme-colors.scss    # Referencia de colores
├── nginx.conf                  # Configuración de proxy (opcional)
├── COPYRIGHT                   # Información de copyright
├── LICENSE                     # Licencia LGPL v3
└── README.md                   # Esta documentación
```

## 🌍 Configuración colombiana

El sistema incluye configuración específica para Colombia:

1. **Timezone**: `America/Bogota`
2. **Localización**: Soporte para español
3. **Moneda**: Configuración para COP (Peso colombiano)

### Activar idioma español
1. Accede a **Configuración > Traducciones > Idiomas**
2. Activa **Español**
3. Ve a tu perfil de usuario y cambia el idioma

## 📱 Gestión de aplicaciones

### Instalación limpia
El sistema se inicia solo con el módulo `base`, sin aplicaciones demo:
```yaml
command: ["odoo", "-i", "base", "-d", "odoo", "--without-demo=all"]
```

### Apps recomendadas para empresas
1. **CRM** - Gestión de clientes
2. **Ventas** - Proceso de ventas
3. **Inventario** - Control de stock
4. **Contabilidad** - Gestión financiera
5. **Facturación** - Emisión de facturas
6. **RRHH** - Recursos humanos

## 🔄 Comandos útiles

### Gestión básica
```bash
# Ver logs en tiempo real
docker-compose logs -f odoo

# Reiniciar solo Odoo
docker-compose restart odoo

# Parar todo el stack
docker-compose down

# Limpiar y empezar de nuevo
docker-compose down -v
docker-compose up -d
```

### Desarrollo y debugging
```bash
# Acceder al contenedor de Odoo
docker exec -it odoo-parque bash

# Ver configuración de Odoo
docker exec odoo-parque cat /etc/odoo/odoo.conf

# Verificar tema aplicado
docker exec odoo-parque cat /usr/lib/python3/dist-packages/odoo/PARQUE_THEME_INFO
```

### Backup y restauración
```bash
# Backup de la base de datos
docker exec odoo-postgres-parque pg_dump -U odoo odoo > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker exec -i odoo-postgres-parque psql -U odoo odoo < backup_20241215.sql
```

## 🚀 Despliegue en producción

### Usando Docker Hub (recomendado)
```bash
# Pull de la imagen desde Docker Hub
docker pull parque-erp/odoo:17-orange

# Usar en docker-compose
services:
  odoo:
    image: parque-erp/odoo:17-orange
    # ... resto de configuración
```

### Construcción local
```bash
# Clonar y construir
git clone https://github.com/SantiagoRuizM/droplet-parque-odoo.git
cd droplet-parque-odoo
docker-compose -f docker-compose.orange.yml up -d --build
```

### Variables de entorno para producción
```yaml
environment:
  - ODOO_RC=/etc/odoo/odoo.conf
  - DB_MAXCONN=64
  - DB_TEMPLATE=template1
```

## 🔒 Seguridad

### Recomendaciones para producción
1. Cambiar contraseñas por defecto
2. Usar variables de entorno para secretos
3. Implementar SSL/TLS con reverse proxy
4. Configurar backup automático
5. Limitar acceso por IP si es necesario

### Configuración con nginx (opcional)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🛠️ Desarrollo y personalización

### Añadir módulos personalizados
1. Crear carpeta `addons/` en el proyecto
2. Colocar módulos en la carpeta
3. Montar volumen en docker-compose:
   ```yaml
   volumes:
     - ./addons:/mnt/extra-addons
   ```

### Modificar tema
1. Editar archivos en `theme/`
2. Reconstruir imagen:
   ```bash
   docker-compose -f docker-compose.orange.yml up -d --build
   ```

### Testing
```bash
# Ejecutar tests de Odoo
docker exec odoo-parque odoo -d odoo --test-enable --test-tags=base --stop-after-init
```

## 📊 Monitoreo

### Logs importantes
```bash
# Logs de aplicación
docker logs odoo-parque

# Logs de base de datos
docker logs odoo-postgres-parque

# Métricas de uso
docker stats odoo-parque odoo-postgres-parque
```

### Health checks
```bash
# Verificar estado de servicios
curl -I http://localhost/web/health

# Verificar base de datos
docker exec odoo-postgres-parque pg_isready -U odoo
```

## 🆘 Solución de problemas

### Problemas comunes

#### Puerto ocupado
```bash
# Verificar puertos en uso
netstat -tlnp | grep :80
# o cambiar puerto en docker-compose.yml
ports: ["8069:8069"]
```

#### Tema no aplicado
```bash
# Limpiar cache de assets
docker exec odoo-parque rm -rf /var/lib/odoo/filestore/*/assets/*
docker-compose restart odoo
```

#### Base de datos corrupta
```bash
# Reiniciar con base de datos limpia
docker-compose down -v
docker-compose up -d
```

## 📄 Licencia

Este proyecto está bajo la licencia **LGPL v3**. Ver archivo [LICENSE](LICENSE) para más detalles.

### Componentes incluidos
- **Odoo Community**: LGPL v3
- **PostgreSQL**: PostgreSQL License
- **Tema personalizado**: LGPL v3

## 🤝 Contribuir

### Proceso de contribución
1. Fork el proyecto
2. Crear rama para feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m 'Añadir nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Abrir Pull Request

### Guías de desarrollo
- Seguir estándares de código de Odoo
- Documentar cambios en README
- Incluir tests cuando sea posible
- Usar commits semánticos

## 📞 Soporte

### Canales de soporte
- **Issues**: [GitHub Issues](https://github.com/SantiagoRuizM/droplet-parque-odoo/issues)
- **Documentación**: Este README
- **Comunidad Odoo**: [Odoo Community](https://www.odoo.com/forum)

### Información del sistema
- **Versión Odoo**: 17.0
- **Versión PostgreSQL**: 15
- **Versión tema**: 1.0
- **Última actualización**: Diciembre 2024

---

## 🚀 Tecnologías utilizadas

![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Odoo](https://img.shields.io/badge/Odoo-714B67?style=flat&logo=odoo&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![SCSS](https://img.shields.io/badge/SCSS-CF649A?style=flat&logo=sass&logoColor=white)

**Proyecto Parque ERP** - Odoo profesional para empresas modernas 🧡