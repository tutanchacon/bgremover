# 🎨 Background Remover - Solución Profesional

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Eliminación profesional de fondo con preservación de elementos. Después de múltiples pruebas y optimizaciones, el **método preserve con umbral 20** ha sido identificado como la solución óptima.

## 🚀 Instalación Rápida

### Opción 1: Paquete Python (Recomendado)
```bash
# Instalar como paquete reutilizable
python -m pip install -e .

# Usar desde cualquier lugar
bgremover input.jpg output.png --threshold 20 --verbose
```

### Opción 2: Dependencias Básicas
```bash
# Activar entorno virtual (opcional pero recomendado)
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

### Opción 3: Instalación desde GitHub
```bash
# Para usar en otros proyectos
pip install git+https://github.com/tutanchacon/bgremover.git
```

## 🎯 ¿Por qué este método es el mejor?

1. **Visibilidad superior**: Los elementos del personaje (globos, relojes) son MÁS VISIBLES que con ISNet básico
2. **Elementos sólidos**: Convierte transparencias parciales en completamente opacas (alpha=255)
3. **Preserva todo**: No elimina elementos importantes del personaje
4. **Calidad visual óptima**: Prioriza la apariencia visual sobre la cobertura numérica

## 📊 Resultados Finales

- **Cobertura**: ~55.7% (660,457 píxeles)
- **Cambio**: -5.0% (solo se elimina fondo verdadero)
- **Elementos**: Globos, relojes y accesorios completamente sólidos
- **Calidad**: Sin elementos "fantasmales" o semi-transparentes

## 📋 Requisitos del Sistema

- **Python**: 3.8 o superior
- **Sistema Operativo**: Windows, macOS, Linux
- **RAM**: Mínimo 4GB (recomendado 8GB)
- **Espacio**: ~2GB para modelos de IA

### Dependencias Automáticas
```
rembg>=2.0.67          # Eliminación de fondo con ISNet
Pillow>=10.0.0         # Procesamiento de imágenes
opencv-python>=4.8.0   # Visión por computadora
numpy>=1.24.0          # Cálculos numéricos
scipy>=1.10.0          # Procesamiento científico
onnxruntime>=1.15.0    # Runtime de IA
```

## 🔧 Uso del Software

### Método 1: Paquete Python (Recomendado)

Después de instalar con `python -m pip install -e .`:

```bash
# Comando básico
bgremover input.jpg output.png

# Configuración óptima (recomendada)
bgremover input.jpg output.png --threshold 20 --verbose

# Procesamiento por lotes
bgremover input_folder/ output_folder/ --batch

# Ver estadísticas de imagen
bgremover input.jpg --stats

# Ver formatos soportados
bgremover --formats
```

#### API de Python:
```python
from bgremover_package import BackgroundRemover

# Uso básico
remover = BackgroundRemover()
success = remover.remove_background('input.jpg', 'output.png')

# Uso avanzado
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

### Método 2: Script Original

**`bgremover.py`** - Script clásico compatible:

```bash
# Uso básico
python bgremover.py input.png output.png

# Configuración óptima (recomendada)
python bgremover.py input2.png resultado_final.png 20 true
```

#### Parámetros del Script:
- **input**: Imagen de entrada (JPG, PNG, BMP, TIFF, WebP)
- **output**: Imagen de salida (recomendado PNG para transparencia)
- **umbral**: (opcional) 20-50, menor = más conservador
- **verbose**: (opcional) `true` para ver detalles del proceso

### Método 3: Librería Standalone

Para proyectos que necesitan una sola dependencia:

```python
# Copiar bgremover_standalone.py a tu proyecto
from bgremover_standalone import remove_background_quick

# Uso simple
success = remove_background_quick("input.jpg", "output.png", threshold=20)

# Uso avanzado
from bgremover_standalone import BackgroundRemoverStandalone
remover = BackgroundRemoverStandalone()
success = remover.process("input.jpg", "output.png", threshold=20, verbose=True)
```

## 🎨 Configuración Recomendada

**Para mejores resultados, usa estos parámetros:**

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
- **Calidad óptima**: Balance perfecto entre preservación y limpieza

## 📁 Estructura del Proyecto

```
bgremover/
├── bgremover.py              # ⭐ SCRIPT PRINCIPAL
├── input.png                 # Imagen de prueba 1
├── input2.png                # Imagen de prueba 2
├── resultado_final.png       # Resultado óptimo generado
├── README.md                 # Esta documentación
├── requirements.txt          # Dependencias
├── archive/                  # Scripts experimentales archivados
└── venv/                     # Entorno virtual
```

## � Uso Rápido

### 1. Activar entorno virtual:
```bash
cd bgremover
.\venv\Scripts\Activate.ps1
```

### 2. Ejecutar script principal:
```bash
python bgremover.py input2.png mi_resultado.png 20 true
```

### 3. Resultado:
- ✅ Fondo eliminado completamente
- ✅ Personaje y elementos (globos, relojes) sólidos y visibles
- ✅ Sin transparencias parciales
- ✅ Calidad visual óptima

## 🎨 ¿Qué hace el algoritmo?

1. **Segmentación ISNet**: Detecta elementos del personaje (incluso parcialmente)
2. **Análisis de transparencias**: Categoriza píxeles por nivel de alpha
3. **Solidificación**: Convierte alpha parciales (30-254) → alpha completo (255)
4. **Limpieza selectiva**: Elimina solo ruido, preserva elementos
5. **Conexión**: Une fragmentos separados del personaje
6. **Suavizado conservador**: Mejora bordes sin perder detalles

## 🏆 Ventajas del Método Final

- **Sin pérdida de elementos**: Globos y relojes ya no desaparecen
- **Calidad visual superior**: Elementos sólidos vs "fantasmales"
- **Configuración óptima**: Umbral 20 = balance perfecto
- **Proceso automatizado**: Un solo comando para resultados profesionales

## 🔄 Historial del Proyecto

El proyecto evolucionó a través de múltiples enfoques:
- ISNet básico → elementos semi-transparentes
- Métodos de eliminación → perdía elementos importantes
- **Método preserve** → ⭐ SOLUCIÓN ÓPTIMA

Todos los scripts experimentales están archivados en `archive/` para referencia.

---

**🎯 COMANDO FINAL RECOMENDADO:**
```bash
python bgremover.py input2.png resultado_final.png 20 true
```

**🎉 Este método garantiza la mejor calidad visual con elementos del personaje completamente sólidos y visibles.**
| Figura humana | Bordes suaves | ~35% |
| Personaje 3D | Modelo unificado | ~38% |

## 🔧 Parámetros de Optimización

El algoritmo incluye varios pasos de optimización:

1. **Segmentación ISNet**: Captura completa del modelo
2. **Conexión de componentes**: Une partes separadas del modelo
3. **Limpieza de blancos**: Elimina píxeles blancos residuales (umbral >240)
4. **Suavizado de bordes**: Gaussian blur suave (kernel 3x3, σ=0.5)

## 📁 Estructura del Proyecto

```
bgremover/
├── bg_remover.py              # Script principal optimizado
├── input.png                  # Imagen de prueba
├── modelo_final_definitivo.png # Mejor resultado actual
├── requirements.txt           # Dependencias
├── README.md                 # Esta documentación
├── AVATAR_GUIDE.md           # Guía técnica detallada
└── archive/                  # Versiones experimentales
    ├── experimental_versions/ # Scripts de desarrollo
    └── old_outputs/          # Resultados anteriores
```

## � Resultados de Referencia

- **modelo_balanceado.png**: 47.6% captura (base excelente, con borde blanco)
- **modelo_isnet.png**: 36.5% captura (ISNet puro, sin fragmentación)  
- **modelo_final_definitivo.png**: 36.3% captura (versión final optimizada)

## ⚡ Mejoras Implementadas

### Problema Resuelto: Fragmentación de Modelos
- **Antes (U²-Net)**: Modelos complejos se fragmentaban en ~15-17% de captura
- **Después (ISNet)**: Modelos completos capturados como unidad ~36% de captura
- **Mejora**: >100% de incremento en calidad de captura

### Optimizaciones Adicionales
- ✅ Eliminación de bordes blancos (~30px problema resuelto)
- ✅ Suavizado anti-dentado en bordes
- ✅ Conexión inteligente de componentes
- ✅ Limpieza de píxeles blancos residuales

## 🧪 Desarrollo y Testing

Para experimentar con nuevos parámetros:

```bash
# Probar diferentes umbrales de limpieza
python bg_remover.py test.png resultado.png true

# Comparar con versiones anteriores
ls archive/old_outputs/
```

## � Roadmap

- [ ] Interfaz web para uso fácil
- [ ] Soporte para procesamiento batch  
- [ ] Perfiles de optimización por tipo de imagen
- [ ] Integración con otras herramientas de edición

## 🏆 Créditos

Desarrollado como solución definitiva para procesamiento de avatares complejos.
Basado en investigación de modelos de segmentación semántica avanzados.

## 💡 Ejemplos de uso

### Para logos o gráficos (sin difuminado):
```bash
python bg_remove_final.py logo.png logo_clean.png binary
```

### Para fotos con bordes nítidos:
```bash
python bg_remove_final.py photo.jpg photo_sharp.png sharp
```

### Para retratos equilibrados:
```bash
python bg_remove_final.py portrait.jpg portrait_clean.png clean
```

### Control manual del umbral:
```bash
python remove_bg_enhanced.py photo.jpg output.png 200 isnet-general-use
```

## 📊 Valores de umbral recomendados

- **240-255**: Bordes muy duros, casi binarios
- **200-220**: Bordes nítidos con mínimo anti-aliasing
- **150-180**: Equilibrio entre nitidez y suavidad  
- **100-130**: Bordes suaves con anti-aliasing
- **50-90**: Muy suave, preserva difuminado original

## 🚀 Comando rápido para diferentes necesidades

```bash
# Para máxima nitidez (sin difuminado)
python bg_remove_final.py input.png output.png binary

# Para uso general con bordes limpios  
python bg_remove_final.py input.png output.png sharp

# Para comparar todas las opciones
python compare_versions.py input.png
```

## 📁 Archivos generados

En tu carpeta ahora tienes:
- `input_binary.png` - Sin anti-aliasing
- `input_sharp.png` - Bordes nítidos
- `input_clean.png` - Equilibrado
- `input_soft.png` - Bordes suaves
- Otros archivos de prueba: `ultra_sharp.png`, `sharp.png`, etc.

## ⚡ Nota sobre rendimiento

- Los avisos de CUDA son normales si no tienes GPU NVIDIA
- El procesamiento funciona perfectamente en CPU
- Los modelos se descargan automáticamente la primera vez

## 🔧 Instalación y configuración

### Requisitos
```bash
# Instalar dependencias
pip install -r requirements.txt
```

### Estructura del proyecto
```
bgremover/
├── bg_remove_final.py      # Script principal (recomendado)
├── compare_versions.py     # Comparación automática
├── remove_bg_enhanced.py   # Control manual fino
├── remove_bg.py           # Script básico original
├── requirements.txt       # Dependencias del proyecto
├── README.md             # Esta documentación
├── .gitignore           # Archivos ignorados por Git
└── input.png           # Imagen de ejemplo
```

## 📦 Gestión del proyecto con Git

### Inicializar repositorio
```bash
git init
git add .
git commit -m "Initial commit: Background removal tool"
```

### Archivos incluidos en el repositorio
- ✅ Código fuente Python (.py)
- ✅ Documentación (README.md)
- ✅ Dependencias (requirements.txt)
- ✅ Configuración (.gitignore)

### Archivos excluidos automáticamente
- ❌ Imágenes procesadas (output_*, *_clean.png, etc.)
- ❌ Modelos AI descargados (.onnx files)
- ❌ Cache de Python (__pycache__)
- ❌ Entornos virtuales (venv/)
- ❌ Archivos temporales y logs
