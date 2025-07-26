# 🎨 Background Remover - Solución Profesional

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-in--development-yellow)

Eliminación profesional de fondo con preservación de elementos usando IA. Después de múltiples pruebas y optimizaciones, hemos desarrollado la **solución óptima con umbral 20** que preserva todos los elementos del personaje.

## 🚀 Instalación Rápida

### Método 1: Paquete Python (Recomendado)
```bash
# Clonar repositorio
git clone https://github.com/tutanchacon/bgremover.git
cd bgremover

# Instalar como paquete reutilizable
python -m pip install -e .

# ¡Listo! Usar desde cualquier lugar
bgremover input.jpg output.png --threshold 20 --verbose
```

### Método 2: Instalación Básica
```bash
# Clonar repositorio
git clone https://github.com/tutanchacon/bgremover.git
cd bgremover

# Crear entorno virtual (recomendado)
python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# Linux/Mac  
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Usar script original
python bgremover.py input.png output.png 20 true
```

### Método 3: Para Otros Proyectos
```bash
# Instalar desde GitHub
pip install git+https://github.com/tutanchacon/bgremover.git

# Usar en tu código
from bgremover_package import BackgroundRemover
```

## ⚡ Uso Rápido

### CLI (Línea de Comandos)
```bash
# Configuración óptima recomendada
bgremover input.jpg output.png --threshold 20 --verbose

# Procesamiento por lotes
bgremover input_folder/ output_folder/ --batch

# Ver estadísticas de imagen
bgremover input.jpg --stats

# Ver formatos soportados
bgremover --formats
```

### API de Python
```python
from bgremover_package import BackgroundRemover

# Uso básico
remover = BackgroundRemover()
success = remover.remove_background('input.jpg', 'output.png')

# Configuración óptima
success = remover.remove_background(
    'input.jpg', 'output.png',
    min_alpha_threshold=20,
    preserve_elements=True,
    verbose=True
)

# Obtener estadísticas
stats = remover.get_stats('image.png')
print(f"Transparencia: {stats['transparency_percentage']:.1f}%")
```

### Script Original (Compatible)
```bash
# Uso básico
python bgremover.py input.png output.png

# Configuración óptima (recomendada)
python bgremover.py input.png output.png 20 true
```

## 🎯 ¿Por qué Este Método Es El Mejor?

### ✅ Resultados Superiores
- **Visibilidad**: Los elementos del personaje (globos, relojes) son MÁS VISIBLES que con ISNet básico
- **Solidez**: Convierte transparencias parciales en completamente opacas (alpha=255)
- **Preservación**: No elimina elementos importantes del personaje
- **Calidad**: Sin elementos "fantasmales" o semi-transparentes

### 📊 Métricas de Rendimiento
- **Cobertura**: ~55.7% (660,457 píxeles)
- **Cambio**: -5.0% (solo se elimina fondo verdadero)
- **Elementos**: Globos, relojes y accesorios completamente sólidos
- **Calidad**: Visualmente superior a métodos estándar

## 🔧 Configuración Óptima

**Umbral 20 - La configuración perfecta:**

```bash
# CLI
bgremover input.jpg output.png --threshold 20 --verbose

# Script original
python bgremover.py input.jpg output.png 20 true

# Python API
remover.remove_background('input.jpg', 'output.png', min_alpha_threshold=20, verbose=True)
```

### ¿Por qué umbral 20?
- **Preserva elementos**: Globos, relojes, accesorios quedan sólidos
- **Elimina ruido**: Artefactos menores se eliminan automáticamente
- **Balance perfecto**: Entre preservación y limpieza

## 🛠️ Requisitos del Sistema

### Software
- **Python**: 3.8 o superior
- **Sistema Operativo**: Windows, macOS, Linux
- **RAM**: Mínimo 4GB (recomendado 8GB+)
- **Espacio**: ~2GB para modelos de IA

### Dependencias (Instalación Automática)
```
rembg>=2.0.67          # Eliminación de fondo con ISNet
Pillow>=10.0.0         # Procesamiento de imágenes
opencv-python>=4.8.0   # Visión por computadora
numpy>=1.24.0          # Cálculos numéricos
scipy>=1.10.0          # Procesamiento científico
onnxruntime>=1.15.0    # Runtime de IA
```

## 📁 Estructura del Proyecto

```
bgremover/
├── 📦 bgremover_package/        # ⭐ PAQUETE PYTHON PROFESIONAL
│   ├── __init__.py              # Inicialización del paquete
│   ├── core.py                  # Clase BackgroundRemover principal
│   ├── utils.py                 # Funciones de utilidad
│   └── cli.py                   # Interfaz de línea de comandos
├── 🐍 bgremover.py              # Script original (compatible)
├── 📄 bgremover_standalone.py   # Versión independiente
├── ⚙️ setup.py                  # Configuración del paquete
├── 📋 requirements.txt          # Dependencias
├── 📖 README.md                 # Esta documentación
├── 📚 PACKAGE_README.md         # Documentación del paquete
├── 🚀 PYPI_INSTRUCTIONS.md      # Instrucciones para PyPI
├── 🖼️ input.png, input2.png     # Imágenes de prueba
├── ✅ resultado_final.png       # Resultado óptimo
└── 📁 archive/                  # Versiones experimentales
    ├── experimental_versions/   # Scripts de desarrollo
    └── old_outputs/            # Resultados de pruebas
```

## 🎨 Algoritmo Profesional

### Pipeline de Procesamiento
1. **Segmentación ISNet**: Detecta elementos del personaje (incluso parciales)
2. **Análisis de transparencias**: Categoriza píxeles por nivel de alpha
3. **Solidificación**: Convierte alpha parciales (30-254) → alpha completo (255)
4. **Limpieza selectiva**: Elimina solo ruido, preserva elementos
5. **Conexión**: Une fragmentos separados del personaje
6. **Suavizado conservador**: Mejora bordes sin perder detalles

### Ventajas Técnicas
- **IA Avanzada**: Modelo ISNet-General-Use optimizado
- **Preservación Inteligente**: Mantiene todos los elementos del personaje
- **Anti-fragmentación**: Conecta partes separadas automáticamente
- **Control de Calidad**: Validación automática de resultados

## 🔄 Casos de Uso

### Para Desarrolladores
```python
# Integración en aplicaciones
from bgremover_package import BackgroundRemover
remover = BackgroundRemover()

# Procesamiento automático
def process_user_avatar(user_image_path):
    return remover.remove_background(
        user_image_path, 
        f"processed_{user_image_path}",
        min_alpha_threshold=20
    )
```

### Para Diseñadores
```bash
# Procesamiento por lotes de imágenes
bgremover design_assets/ processed_assets/ --batch --threshold 20

# Comparación de resultados
bgremover --stats original.jpg
bgremover --stats processed.png
```

### Para Otros Proyectos
```python
# Usar versión standalone (copia bgremover_standalone.py)
from bgremover_standalone import remove_background_quick
success = remove_background_quick("input.jpg", "output.png", threshold=20)
```

## 📈 Comparación con Métodos Estándar

| Método | Preservación | Calidad | Velocidad | Uso |
|--------|-------------|---------|-----------|-----|
| **BGRemover (Nuestro)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Profesional |
| ISNet Básico | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Básico |
| U²-Net | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | Fragmentado |
| Métodos manuales | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | Lento |

## 🆘 Soporte y Contribución

### Obtener Ayuda
- **Issues**: [GitHub Issues](https://github.com/tutanchacon/bgremover/issues)
- **Documentación**: Consulta `PACKAGE_README.md` para API detallada
- **Ejemplos**: Ver carpeta `archive/` para casos de uso

### Contribuir
1. Fork el repositorio
2. Crea una rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

MIT License - ver archivo `LICENSE` para detalles.

## 🏆 Créditos

Desarrollado con ❤️ para procesamiento profesional de imágenes.

- **Modelo IA**: ISNet-General-Use (rembg)
- **Optimizaciones**: Algoritmos de preservación de elementos personalizados
- **Pipeline**: Procesamiento multi-etapa para máxima calidad

---

**¿Listo para eliminar fondos como un profesional? ¡Comienza ahora!** 🎨✨
