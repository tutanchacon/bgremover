# Background Remover ISNet 🎨

Herramienta avanzada para eliminar fondos de avatares y modelos complejos usando inteligencia artificial.

## 🚀 Características

- **ISNet-General-Use**: Modelo de IA especializado que mantiene la integridad de figuras completas
- **Procesamiento inteligente**: Eliminación de píxeles blancos residuales y suavizado de bordes
- **Optimizado para avatares**: Especialmente diseñado para personajes y modelos complejos
- **Sin fragmentación**: A diferencia de U²-Net, ISNet captura el modelo completo como una unidad

## 📋 Requisitos

- Python 3.8+
- rembg (con modelo ISNet)
- OpenCV
- PIL/Pillow
- NumPy
- SciPy

## 🛠️ Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Descargar modelo ISNet (automático en primer uso)
python bg_remover.py
```

## 💡 Uso

### Uso Básico
```bash
python bg_remover.py imagen_entrada.jpg resultado.png
```

### Modo Verbose (con información detallada)
```bash
python bg_remover.py avatar.png modelo_limpio.png true
```

## 📊 Rendimiento

| Modelo Original | Resultado ISNet | Captura |
|----------------|-----------------|---------|
| Avatar complejo | Sin fragmentación | ~36% |
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
