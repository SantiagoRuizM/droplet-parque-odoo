# Assets - Elementos Gráficos

Estructura organizada para elementos gráficos del proyecto Parque ERP.

## 📁 Estructura

```
assets/
├── images/
│   ├── logos/          # Logotipos de la empresa y marca
│   ├── icons/          # Iconos personalizados y favicon
│   ├── backgrounds/    # Imágenes de fondo
│   └── banners/        # Banners y headers
└── fonts/              # Fuentes personalizadas
```

## 🎨 Uso recomendado

### Logos (`logos/`)
- Logo principal de Parque ERP
- Variaciones (horizontal, vertical, monocromo)
- Formatos: PNG, SVG (preferible)

### Iconos (`icons/`)
- Favicon para el navegador
- Iconos de aplicación móvil
- Iconos personalizados para módulos
- Formatos: ICO, PNG, SVG

### Backgrounds (`backgrounds/`)
- Imágenes de fondo para login
- Patterns o texturas
- Formatos: JPG, PNG, WebP

### Banners (`banners/`)
- Headers para reportes
- Banners promocionales
- Imágenes para dashboards
- Formatos: JPG, PNG, SVG

### Fuentes (`fonts/`)
- Fuentes corporativas
- Fuentes web personalizadas
- Formatos: WOFF2, WOFF, TTF

## 🔧 Integración con Odoo

Para usar estos assets en Odoo:

1. **Montar en Docker**:
   ```yaml
   volumes:
     - ./assets:/mnt/assets:ro
   ```

2. **Referenciar en templates**:
   ```xml
   <img src="/mnt/assets/images/logos/logo-principal.png"/>
   ```

3. **CSS personalizado**:
   ```scss
   .company-logo {
     background-image: url('/mnt/assets/images/logos/logo.svg');
   }
   ```