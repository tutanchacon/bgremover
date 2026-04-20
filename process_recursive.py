#!/usr/bin/env python3
"""
BGRemover - Procesamiento Recursivo de Directorios
=================================================

Procesa recursivamente todas las imágenes en subdirectorios,
manteniendo la estructura de carpetas original.

Uso:
    python process_recursive.py input_dir output_dir [threshold] [verbose]
    
Ejemplos:
    python process_recursive.py input_folder output_folder
    python process_recursive.py input_folder output_folder 20 true
    python process_recursive.py "C:/Images" "C:/Processed" 30
"""

import os
import sys
from pathlib import Path
import time
from typing import List, Tuple, Optional

# Importar desde el paquete local
from bgremover_package import BackgroundRemover


class RecursiveProcessor:
    """Procesador recursivo de imágenes con preservación de estructura."""
    
    def __init__(self, threshold: int = 20, verbose: bool = False):
        self.threshold = threshold
        self.verbose = verbose
        self.remover = BackgroundRemover()
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
        
        # Estadísticas
        self.stats = {
            'total_found': 0,
            'processed': 0,
            'errors': 0,
            'skipped': 0,
            'start_time': None,
            'directories_created': 0
        }
    
    def find_images_recursive(self, input_dir: Path) -> List[Tuple[Path, Path]]:
        """
        Encuentra todas las imágenes recursivamente y calcula rutas de salida.
        
        Returns:
            List of (input_path, output_path) tuples
        """
        image_pairs = []
        directories_scanned = 0
        files_scanned = 0
        
        if self.verbose:
            print(f"🔍 Escaneando directorios recursivamente desde: {input_dir}")
        
        for root, dirs, files in os.walk(input_dir):
            root_path = Path(root)
            directories_scanned += 1
            
            if self.verbose and files:
                rel_root = root_path.relative_to(input_dir) if root_path != input_dir else "."
                print(f"📁 Escaneando: {rel_root} ({len(files)} archivos)")
            
            for file in files:
                files_scanned += 1
                file_path = root_path / file
                
                # Verificar extensión
                if file_path.suffix.lower() not in self.supported_extensions:
                    if self.verbose:
                        print(f"⏭️  Saltando (extensión no soportada): {file}")
                    continue
                
                # Calcular ruta relativa desde input_dir
                relative_path = file_path.relative_to(input_dir)
                
                # Cambiar extensión a .png y agregar sufijo
                output_name = f"{file_path.stem}_no_bg.png"
                output_path = Path(sys.argv[2]) / relative_path.parent / output_name
                
                image_pairs.append((file_path, output_path))
                
                if self.verbose:
                    print(f"✅ Encontrada: {relative_path}")
        
        if self.verbose or len(image_pairs) == 0:
            print(f"📊 Resumen del escaneo:")
            print(f"   📁 Directorios escaneados: {directories_scanned}")
            print(f"   📄 Archivos totales: {files_scanned}")
            print(f"   🖼️  Imágenes válidas: {len(image_pairs)}")
        
        return image_pairs
    
    def create_output_directories(self, image_pairs: List[Tuple[Path, Path]]) -> None:
        """Crea todos los directorios de salida necesarios."""
        directories_to_create = set()
        
        for _, output_path in image_pairs:
            directories_to_create.add(output_path.parent)
        
        for directory in directories_to_create:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                self.stats['directories_created'] += 1
                if self.verbose:
                    print(f"📁 Directorio creado: {directory}")
    
    def process_image(self, input_path: Path, output_path: Path) -> bool:
        """Procesa una sola imagen."""
        try:
            success = self.remover.remove_background(
                str(input_path),
                str(output_path),
                min_alpha_threshold=self.threshold,
                preserve_elements=True,
                smooth_edges=True,
                verbose=False  # No verbose por imagen individual
            )
            
            if success:
                self.stats['processed'] += 1
                if self.verbose:
                    rel_input = input_path.relative_to(Path(sys.argv[1]))
                    rel_output = output_path.relative_to(Path(sys.argv[2]))
                    print(f"✅ {rel_input} → {rel_output}")
            else:
                self.stats['errors'] += 1
                if self.verbose:
                    print(f"❌ Error procesando: {input_path}")
            
            return success
            
        except Exception as e:
            self.stats['errors'] += 1
            if self.verbose:
                print(f"❌ Excepción en {input_path}: {e}")
            return False
    
    def process_all(self, input_dir: str, output_dir: str) -> None:
        """Procesa todas las imágenes recursivamente."""
        self.stats['start_time'] = time.time()
        
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # Validaciones
        if not input_path.exists():
            print(f"❌ Error: Directorio de entrada no existe: {input_dir}")
            return
        
        if not input_path.is_dir():
            print(f"❌ Error: La ruta de entrada no es un directorio: {input_dir}")
            return
        
        # Encontrar todas las imágenes
        print(f"🎨 BGRemover - Procesamiento Recursivo")
        print(f"=" * 50)
        print(f"📂 Entrada: {input_path.absolute()}")
        print(f"📂 Salida: {output_path.absolute()}")
        print(f"🎯 Umbral: {self.threshold} (preserva elementos del personaje)")
        print(f"🔍 Extensiones: {', '.join(sorted(self.supported_extensions))}")
        print()
        
        image_pairs = self.find_images_recursive(input_path)
        self.stats['total_found'] = len(image_pairs)
        
        if not image_pairs:
            print("❌ No se encontraron imágenes para procesar")
            print(f"🔍 Extensiones buscadas: {', '.join(sorted(self.supported_extensions))}")
            print(f"📂 Directorios escaneados recursivamente desde: {input_path}")
            print("💡 Verifica que haya imágenes en el directorio o sus subdirectorios")
            return
        
        print(f"📊 Imágenes encontradas: {self.stats['total_found']}")
        
        # Crear directorios de salida
        if self.verbose:
            print(f"\n📁 Creando estructura de directorios...")
        self.create_output_directories(image_pairs)
        
        print(f"📁 Directorios creados: {self.stats['directories_created']}")
        print()
        
        # Procesar imágenes
        print("🚀 Iniciando procesamiento...")
        if not self.verbose:
            print("💡 Usa 'verbose=true' para ver progreso detallado")
        print()
        
        for i, (input_img, output_img) in enumerate(image_pairs, 1):
            if not self.verbose:
                # Mostrar progreso simple
                progress = (i / len(image_pairs)) * 100
                print(f"\r🔄 Progreso: {i}/{len(image_pairs)} ({progress:.1f}%) - {input_img.name}", end='', flush=True)
            
            success = self.process_image(input_img, output_img)
            
            if not success:
                self.stats['errors'] += 1
        
        # Estadísticas finales
        elapsed_time = time.time() - self.stats['start_time']
        self.print_final_stats(elapsed_time)
    
    def print_final_stats(self, elapsed_time: float) -> None:
        """Imprime estadísticas finales."""
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE PROCESAMIENTO")
        print("=" * 50)
        print(f"⏱️  Tiempo total: {elapsed_time:.1f} segundos")
        print(f"📂 Directorios creados: {self.stats['directories_created']}")
        print(f"🔍 Imágenes encontradas: {self.stats['total_found']}")
        print(f"✅ Procesadas exitosamente: {self.stats['processed']}")
        print(f"❌ Errores: {self.stats['errors']}")
        
        if self.stats['total_found'] > 0:
            success_rate = (self.stats['processed'] / self.stats['total_found']) * 100
            print(f"📈 Tasa de éxito: {success_rate:.1f}%")
            
            if self.stats['processed'] > 0:
                avg_time = elapsed_time / self.stats['processed']
                print(f"⚡ Tiempo promedio por imagen: {avg_time:.2f} segundos")
        
        if self.stats['processed'] > 0:
            print(f"\n🎉 ¡Procesamiento completado!")
            print(f"📁 Revisa los resultados en: {sys.argv[2]}")
            print(f"✨ Configuración óptima aplicada (umbral {self.threshold})")
        else:
            print(f"\n❌ No se procesaron imágenes exitosamente")


def main():
    """Función principal."""
    # Verificar argumentos
    if len(sys.argv) < 3:
        print("🎨 BGRemover - Procesamiento Recursivo")
        print("=" * 40)
        print("Uso:")
        print("  python process_recursive.py <directorio_entrada> <directorio_salida> [umbral] [verbose]")
        print()
        print("Ejemplos:")
        print("  python process_recursive.py input_folder output_folder")
        print("  python process_recursive.py input_folder output_folder 20 true")
        print("  python process_recursive.py \"C:/Images\" \"C:/Processed\" 30")
        print()
        print("Parámetros:")
        print("  umbral (opcional): 10-50 (20 recomendado para preservar elementos)")
        print("  verbose (opcional): true/false - mostrar progreso detallado")
        print()
        print("🎯 Configuración recomendada: umbral 20 (preserva globos, relojes, etc.)")
        sys.exit(1)
    
    # Parsear argumentos
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Umbral opcional (default: 20)
    threshold = 20
    if len(sys.argv) > 3 and sys.argv[3].isdigit():
        threshold = int(sys.argv[3])
        verbose_arg = 4
    else:
        verbose_arg = 3
    
    # Verbose opcional
    verbose = False
    if len(sys.argv) > verbose_arg:
        verbose = sys.argv[verbose_arg].lower() in ['true', '1', 'yes', 'v']
    
    # Crear procesador y ejecutar
    processor = RecursiveProcessor(threshold=threshold, verbose=verbose)
    processor.process_all(input_dir, output_dir)


if __name__ == "__main__":
    main()