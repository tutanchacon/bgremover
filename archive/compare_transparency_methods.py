#!/usr/bin/env python3
"""
Comparador de Resultados - Análisis de Transparencias
====================================================

Script para generar múltiples versiones y comparar la efectividad
en la eliminación de objetos semi-transparentes problemáticos.
"""

import subprocess
import sys
import os

def generate_comparison(input_image):
    """Genera múltiples versiones para comparación."""
    
    print("🎨 Generando Comparación de Métodos de Limpieza")
    print("=" * 55)
    
    # Configuraciones de prueba
    tests = [
        {
            'script': 'bg_remover.py',
            'output': 'comparacion_original.png',
            'args': [input_image, 'comparacion_original.png', 'true'],
            'description': 'Método original (43.3%)'
        },
        {
            'script': 'bg_remover_clean.py', 
            'output': 'comparacion_balanceado.png',
            'args': [input_image, 'comparacion_balanceado.png', '150', 'true'],
            'description': 'Limpieza balanceada (umbral 150)'
        },
        {
            'script': 'bg_remover_clean.py',
            'output': 'comparacion_agresivo.png', 
            'args': [input_image, 'comparacion_agresivo.png', '120', 'true'],
            'description': 'Limpieza agresiva (umbral 120)'
        },
        {
            'script': 'bg_remover_clean.py',
            'output': 'comparacion_ultra.png',
            'args': [input_image, 'comparacion_ultra.png', '100', 'true'], 
            'description': 'Limpieza ultra (umbral 100)'
        }
    ]
    
    results = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n📋 {i}/4: {test['description']}")
        print("-" * 40)
        
        try:
            # Ejecutar el comando
            result = subprocess.run(
                ['python', test['script']] + test['args'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                # Buscar el porcentaje en la salida
                output_lines = result.stdout.split('\n')
                percentage = "No detectado"
                
                for line in output_lines:
                    if 'Píxeles finales:' in line:
                        # Extraer porcentaje de líneas como "📈 Píxeles finales: 32.7%"
                        try:
                            percentage = line.split(':')[1].strip().split('%')[0].strip() + '%'
                        except:
                            pass
                    elif 'Píxeles capturados:' in line:
                        # Para el método original
                        try:
                            percentage = line.split(':')[1].strip().split('%')[0].strip() + '%'
                        except:
                            pass
                
                results.append({
                    'method': test['description'],
                    'file': test['output'],
                    'percentage': percentage,
                    'status': '✅ Éxito'
                })
                print(f"✅ Completado: {test['output']} - {percentage}")
                
            else:
                results.append({
                    'method': test['description'], 
                    'file': test['output'],
                    'percentage': 'Error',
                    'status': '❌ Error'
                })
                print(f"❌ Error en {test['script']}")
                print(result.stderr)
                
        except Exception as e:
            results.append({
                'method': test['description'],
                'file': test['output'], 
                'percentage': 'Error',
                'status': f'❌ Excepción: {str(e)}'
            })
            print(f"❌ Excepción: {str(e)}")
    
    # Mostrar resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE COMPARACIÓN")
    print("="*70)
    
    print(f"{'Método':<35} {'Archivo':<25} {'Captura':<10} {'Estado'}")
    print("-" * 70)
    
    for result in results:
        method = result['method'][:34]
        file_name = result['file'][:24] 
        percentage = result['percentage'][:9]
        status = result['status'][:15]
        print(f"{method:<35} {file_name:<25} {percentage:<10} {status}")
    
    print("\n💡 INTERPRETACIÓN:")
    print("- Menor % = Menos objetos semi-transparentes problemáticos")
    print("- Mayor % = Más contenido preservado (incluye objetos dudosos)")
    print("- Balanceado (150): Buen equilibrio")
    print("- Agresivo (120): Para casos con muchos objetos problemáticos") 
    print("- Ultra (100): Máxima limpieza, puede eliminar detalles válidos")
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Uso: python compare_transparency_methods.py <imagen_entrada>")
        print("Ejemplo: python compare_transparency_methods.py input.png")
        sys.exit(1)
    
    input_image = sys.argv[1]
    
    if not os.path.exists(input_image):
        print(f"❌ Error: No se encuentra el archivo {input_image}")
        sys.exit(1)
    
    generate_comparison(input_image)

if __name__ == "__main__":
    main()
