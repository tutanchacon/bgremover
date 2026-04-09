# BGRemover - Eliminador de Fondos con Preservacion de Elementos

Herramienta profesional para eliminar fondos de imagenes usando IA (ISNet), con un algoritmo especializado que preserva todos los elementos del personaje y corrige transparencias parciales.

## Caracteristicas

- Usa el modelo ISNet-General-Use para segmentacion precisa
- Preserva elementos semi-transparentes convirtiendolos a opacos
- Conecta componentes fragmentados del personaje
- Elimina solo el fondo verdadero, no accesorios
- Suavizado de bordes conservador

## Requisitos

- Python 3.8+
- Windows, macOS o Linux
- 4GB RAM minimo (8GB recomendado)

## Instalacion

### Opcion 1: Uso directo (recomendado para uso rapido)

```bash
git clone https://github.com/tutanchacon/bgremover.git
cd bgremover

# Crear entorno virtual
python -m venv venv

# Activar (Windows)
.\venv\Scripts\Activate.ps1

# Activar (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Opcion 2: Instalar como paquete

```bash
git clone https://github.com/tutanchacon/bgremover.git
cd bgremover
pip install -e .
```

## Uso

### Script directo

```bash
# Basico
python bgremover.py entrada.png salida.png

# Con umbral personalizado y modo verbose
python bgremover.py entrada.png salida.png 20 true
```

**Parametros:**
- `entrada`: Imagen de entrada (jpg, png, etc.)
- `salida`: Imagen de salida (PNG con transparencia)
- `umbral` (opcional): Umbral minimo de alpha para preservar (default: 50, recomendado: 20-50)
- `verbose` (opcional): Mostrar informacion detallada (true/false)

### CLI del paquete

```bash
# Basico
bgremover entrada.jpg salida.png

# Con opciones
bgremover entrada.jpg salida.png --threshold 20 --verbose

# Procesamiento por lotes
bgremover carpeta_entrada/ carpeta_salida/ --batch

# Ver estadisticas de imagen
bgremover imagen.png --stats

# Ver formatos soportados
bgremover --formats
```

### API de Python

```python
from bgremover_package import BackgroundRemover

remover = BackgroundRemover()

# Uso basico
success = remover.remove_background('entrada.jpg', 'salida.png')

# Con opciones
success = remover.remove_background(
    'entrada.jpg',
    'salida.png',
    min_alpha_threshold=20,
    preserve_elements=True,
    smooth_edges=True,
    verbose=True
)

# Obtener estadisticas
stats = remover.get_stats('imagen.png')
```

### Version standalone (para integrar en otros proyectos)

Copia `bgremover_standalone.py` a tu proyecto:

```python
from bgremover_standalone import BackgroundRemoverStandalone

remover = BackgroundRemoverStandalone()
success = remover.process('entrada.jpg', 'salida.png', threshold=20)
```

## Pipeline de procesamiento

1. **Segmentacion ISNet**: Detecta el personaje y sus elementos
2. **Analisis de transparencias**: Categoriza pixeles por nivel de alpha
3. **Correccion de transparencias**: Convierte semi-transparentes (>umbral) a opacos (alpha=255)
4. **Conexion de elementos**: Une componentes fragmentados usando morfologia
5. **Limpieza de blancos**: Elimina pixeles blancos residuales del fondo
6. **Suavizado**: Aplica suavizado conservador en los bordes

## Estructura del proyecto

```
bgremover/
├── bgremover.py              # Script principal
├── bgremover_standalone.py   # Version independiente para otros proyectos
├── bgremover_package/        # Paquete instalable
│   ├── __init__.py
│   ├── core.py               # Clase BackgroundRemover
│   ├── cli.py                # Interfaz de linea de comandos
│   └── utils.py              # Funciones auxiliares
├── setup.py                  # Configuracion del paquete
├── requirements.txt          # Dependencias
├── clean_project.py          # Script de limpieza
└── archive/                  # Versiones experimentales y resultados antiguos
    ├── experimental_versions/
    └── old_outputs/
```

## Dependencias

```
rembg>=2.0.67          # Motor de eliminacion de fondo con ISNet
Pillow>=10.0.0         # Procesamiento de imagenes
opencv-python>=4.8.0   # Vision por computadora
numpy>=1.24.0          # Calculos numericos
scipy>=1.10.0          # Procesamiento cientifico
onnxruntime>=1.15.0    # Runtime de IA
scikit-learn>=1.3.0    # Analisis de colores
```

## Umbral recomendado

- **20-30**: Preserva casi todo (ideal para personajes con accesorios)
- **50**: Balanceado (default)
- **80-100**: Mas restrictivo (elimina mas ruido pero puede perder detalles)

## Licencia

MIT License
