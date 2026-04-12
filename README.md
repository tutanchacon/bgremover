# BGRemover

Eliminador de fondos con IA usando **BiRefNet** y alpha matting. Calidad profesional similar a remove.bg, 100% local.

## Requisitos

- Python 3.8+
- 4 GB RAM mínimo (8 GB recomendado)

## Instalación

```bash
# Clonar el repositorio
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

> La primera ejecución descarga el modelo BiRefNet (~1.5 GB) automáticamente.

## Uso

### Python

```python
from bgremover import remove_background

remove_background('foto.jpg', 'resultado.png')
remove_background('foto.jpg', 'resultado.png', verbose=True)
```

### Línea de comandos

```bash
python bgremover.py entrada.jpg salida.png
python bgremover.py entrada.jpg salida.png true
```

### Windows (lanzador .bat)

```bat
procesaImagen.bat foto.jpg resultado.png
procesaImagen.bat foto.jpg resultado.png true
```

## Dependencias

| Paquete | Versión | Función |
|---|---|---|
| rembg | >=2.0.67 | Motor AI con BiRefNet |
| onnxruntime | >=1.15.0 | Inferencia en CPU |
| Pillow | >=10.0.0 | I/O de imágenes |
| opencv-python | >=4.8.0 | Procesamiento de bordes |
| numpy | >=1.24.0 | Operaciones numéricas |

## Licencia

MIT License
