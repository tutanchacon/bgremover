#!/usr/bin/env python3
"""
Comparación: Eliminar vs Preservar Elementos del Personaje
=========================================================

Genera una comparación lado a lado mostrando:
1. Método que ELIMINA elementos semi-transparentes
2. Método que PRESERVA elementos corrigiendo transparencias
"""

import subprocess
import sys
import os

def compare_elimination_vs_preservation(input_image):
    """Compara eliminación vs preservación de elementos del personaje."""
    
    print("🎨 Comparación: Eliminar vs Preservar Elementos")
    print("=" * 55)
    print("💡 Determinando cuál enfoque es mejor para tu caso...")
    
    # Configuraciones de prueba
    tests = [
        {
            'script': 'bg_remover.py',
            'output': 'comparacion_original.png',
            'args': [input_image, 'comparacion_original.png', 'true'],
            'description': 'Original ISNet (incluye semi-transparentes)',
            'approach': 'Base'
        },
        {
            'script': 'bg_remover_clean.py',
            'output': 'comparacion_elimina.png',
            'args': [input_image, 'comparacion_elimina.png', '150', 'true'],
            'description': 'ELIMINA elementos semi-transparentes',
            'approach': 'Eliminación'
        },
        {
            'script': 'bg_remover_preserve.py',
            'output': 'comparacion_preserva.png',
            'args': [input_image, 'comparacion_preserva.png', '30', 'true'],
            'description': 'PRESERVA elementos, corrige transparencias',
            'approach': 'Preservación'
        },
        {
            'script': 'bg_remover_preserve.py',
            'output': 'comparacion_conservador.png',
            'args': [input_image, 'comparacion_conservador.png', '20', 'true'],
            'description': 'Ultra-conservador (preserva todo)',
            'approach': 'Ultra-Preservación'
        }
    ]
    
    results = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n📋 {i}/4: {test['description']}")
        print("-" * 50)
        
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
                    if 'Píxeles finales:' in line or 'Píxeles capturados:' in line:
                        try:
                            percentage = line.split(':')[1].strip().split('%')[0].strip() + '%'
                            break
                        except:
                            pass
                
                results.append({
                    'approach': test['approach'],
                    'description': test['description'],
                    'file': test['output'],
                    'percentage': percentage,
                    'status': '✅ Éxito'
                })
                print(f"✅ Completado: {test['output']} - {percentage}")
                
            else:
                results.append({
                    'approach': test['approach'],
                    'description': test['description'], 
                    'file': test['output'],
                    'percentage': 'Error',
                    'status': '❌ Error'
                })
                print(f"❌ Error en {test['script']}")
                
        except Exception as e:
            results.append({
                'approach': test['approach'],
                'description': test['description'],
                'file': test['output'], 
                'percentage': 'Error',
                'status': f'❌ Excepción: {str(e)}'
            })
            print(f"❌ Excepción: {str(e)}")
    
    # Mostrar análisis comparativo
    print("\n" + "="*80)
    print("📊 ANÁLISIS COMPARATIVO: ¿ELIMINAR O PRESERVAR?")
    print("="*80)
    
    print(f"{'Enfoque':<20} {'Descripción':<35} {'Captura':<10} {'Estado'}")
    print("-" * 80)
    
    for result in results:
        approach = result['approach'][:19]
        description = result['description'][:34]
        percentage = result['percentage'][:9]
        status = result['status'][:15]
        print(f"{approach:<20} {description:<35} {percentage:<10} {status}")
    
    print("\n" + "="*80)
    print("🎯 INTERPRETACIÓN DE RESULTADOS")
    print("="*80)
    
    print("\n📈 PORCENTAJES DE CAPTURA:")
    print("• Mayor % = Más elementos preservados")
    print("• Menor % = Más elementos eliminados")
    
    print("\n🎨 ENFOQUES:")
    print("• ELIMINACIÓN: Quita globos/relojes semi-transparentes")
    print("• PRESERVACIÓN: Mantiene globos/relojes, corrige transparencias")
    
    print("\n💡 RECOMENDACIÓN SEGÚN TU CASO:")
    print("Si los globos y relojes SON PARTE del personaje → Usar PRESERVACIÓN")
    print("Si los globos y relojes NO SON PARTE del personaje → Usar ELIMINACIÓN")
    
    print("\n🎯 COMANDOS RECOMENDADOS:")
    print("# Para PRESERVAR elementos del personaje:")
    print("python bg_remover_preserve.py input.png resultado.png 30 true")
    print("\n# Para ELIMINAR elementos no deseados:")
    print("python bg_remover_clean.py input.png resultado.png 120 true")
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Uso: python compare_eliminate_vs_preserve.py <imagen_entrada>")
        print("Ejemplo: python compare_eliminate_vs_preserve.py input.png")
        sys.exit(1)
    
    input_image = sys.argv[1]
    
    if not os.path.exists(input_image):
        print(f"❌ Error: No se encuentra el archivo {input_image}")
        sys.exit(1)
    
    compare_elimination_vs_preservation(input_image)

if __name__ == "__main__":
    main()
