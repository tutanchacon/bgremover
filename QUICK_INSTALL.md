# 🚀 Guía de Instalación Rápida - BGRemover

## 🎯 Instalación en 3 Pasos

### 1️⃣ Clonar el Repositorio
```bash
git clone https://github.com/tutanchacon/bgremover.git
cd bgremover
```

### 2️⃣ Elegir Método de Instalación

#### 🏆 **Opción A: Paquete Profesional (Recomendado)**
```bash
# Instalar como paquete
python -m pip install -e .

# ¡Listo! Usar desde cualquier lugar
bgremover input.jpg output.png --threshold 20 --verbose
```

#### 📦 **Opción B: Instalación Clásica**
```bash
# Crear entorno virtual (opcional)
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate   # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Usar script original
python bgremover.py input.jpg output.png 20 true
```

### 3️⃣ ¡Probar!
```bash
# Si instalaste como paquete
bgremover input.png output.png --threshold 20 --verbose

# Si usas el script original
python bgremover.py input.png output.png 20 true
```

## 🔧 Para Otros Proyectos

### Opción 1: Instalar desde GitHub
```bash
pip install git+https://github.com/tutanchacon/bgremover.git
```

### Opción 2: Archivo Standalone
```bash
# Copiar bgremover_standalone.py a tu proyecto
# No requiere instalación del paquete completo
```

## ⚡ Verificar Instalación

### Test del Paquete
```bash
bgremover --formats
bgremover --help
```

### Test del Script
```bash
python bgremover.py --help
# O simplemente probar con una imagen
python bgremover.py input.png test_output.png 20 true
```

## 🆘 Problemas Comunes

### "pip no se reconoce"
```bash
# Usar en su lugar:
python -m pip install -e .
```

### "bgremover command not found"
```bash
# Asegúrate de que Python Scripts esté en PATH
# O usar directamente:
python -m bgremover_package.cli input.jpg output.png
```

### Error de dependencias
```bash
# Actualizar pip primero
python -m pip install --upgrade pip
# Luego instalar
pip install -r requirements.txt
```

## ✅ Instalación Exitosa Si:

- ✅ `bgremover --help` muestra ayuda (método paquete)
- ✅ `python bgremover.py input.png output.png 20 true` funciona (método clásico)
- ✅ Se genera imagen con fondo transparente
- ✅ Los elementos del personaje quedan sólidos (no semi-transparentes)

---
**¿Problemas? Crea un [issue en GitHub](https://github.com/tutanchacon/bgremover/issues)**
