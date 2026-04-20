# Instrucciones para publicar en PyPI

## Pasos para publicar tu paquete en PyPI:

### 1. Preparar el paquete
```bash
# Instalar herramientas de construcción
pip install build twine

# Construir el paquete
python -m build
```

### 2. Subir a PyPI de prueba (TestPyPI)
```bash
# Crear cuenta en https://test.pypi.org/
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

### 3. Probar instalación
```bash
pip install --index-url https://test.pypi.org/simple/ bgremover-preserve
```

### 4. Subir a PyPI oficial
```bash
# Crear cuenta en https://pypi.org/
twine upload dist/*
```

### 5. Usar en cualquier proyecto
```bash
pip install bgremover-preserve
```

## Ventajas:
- ✅ Instalación global con `pip install`
- ✅ Gestión automática de dependencias
- ✅ Versionado profesional
- ✅ Accesible desde cualquier proyecto Python
- ✅ Documentación integrada
