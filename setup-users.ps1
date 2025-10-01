# Script para crear usuarios en Odoo
# Uso: .\setup-users.ps1

Write-Host "=================================================="
Write-Host "  🧡 Parque ERP - Creador de Usuarios"
Write-Host "=================================================="
Write-Host ""

# 1. Verificar que Docker esté corriendo
Write-Host "[1/4] Verificando contenedores..." -ForegroundColor Cyan
$odooContainer = docker ps --filter "name=odoo-parque" --format "{{.Names}}"

if (-not $odooContainer) {
    Write-Host "❌ Error: Contenedor odoo-parque no está corriendo" -ForegroundColor Red
    Write-Host "   Ejecuta primero: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "   ✓ Contenedor odoo-parque está corriendo" -ForegroundColor Green
Write-Host ""

# 2. Esperar a que Odoo esté listo
Write-Host "[2/4] Esperando a que Odoo esté listo..." -ForegroundColor Cyan
Write-Host "   Esto puede tomar 30-60 segundos..." -ForegroundColor Yellow

$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    $attempt++
    Start-Sleep -Seconds 2

    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8069/web/database/selector" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 303) {
            $ready = $true
        }
    }
    catch {
        # Continuar intentando
    }

    if ($attempt % 5 -eq 0) {
        Write-Host "   Intento $attempt/$maxAttempts..." -ForegroundColor Gray
    }
}

if (-not $ready) {
    Write-Host "   ⚠️  Advertencia: No se pudo verificar que Odoo esté listo" -ForegroundColor Yellow
    Write-Host "   Continuando de todas formas..." -ForegroundColor Yellow
} else {
    Write-Host "   ✓ Odoo está listo" -ForegroundColor Green
}

Write-Host ""

# 3. Ejecutar script de creación de usuarios
Write-Host "[3/4] Creando usuarios desde users.json..." -ForegroundColor Cyan
Write-Host ""

docker exec odoo-parque python3 /mnt/extra-addons/create_users.py

$exitCode = $LASTEXITCODE

Write-Host ""

# 4. Resultado
Write-Host "[4/4] Resultado final" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "   ✓ Usuarios creados exitosamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "  📝 Cómo usar los usuarios:"
    Write-Host "=================================================="
    Write-Host ""
    Write-Host "Edita custom_home_bypass.py línea 18 con uno de estos:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   # Para Oscar Gomez (interno):" -ForegroundColor Cyan
    Write-Host "   uid = request.session.authenticate(request.db, 'dato.calidad@parque-e.co', '123456')"
    Write-Host ""
    Write-Host "   # Para Santiago Ruiz (interno):" -ForegroundColor Cyan
    Write-Host "   uid = request.session.authenticate(request.db, 'dato.indicadores@parque-e.co', '123456')"
    Write-Host ""
    Write-Host "   # Para Juan (portal):" -ForegroundColor Cyan
    Write-Host "   uid = request.session.authenticate(request.db, 'juan@parque-e.co', '123456')"
    Write-Host ""
    Write-Host "Luego reinicia Odoo:" -ForegroundColor Yellow
    Write-Host "   docker-compose restart odoo"
    Write-Host ""
} else {
    Write-Host "   ❌ Error al crear usuarios (código: $exitCode)" -ForegroundColor Red
    Write-Host "   Revisa los logs arriba para más detalles" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "=================================================="
