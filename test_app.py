#!/usr/bin/env python3
"""
Script de prueba para verificar que la aplicación funciona correctamente
"""

import os
import sys
import requests
import time
from pathlib import Path

# Agregar el directorio src al path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def test_app_health():
    """Probar el endpoint de salud de la aplicación"""
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ Endpoint de salud funcionando")
            return True
        else:
            print(f"❌ Error en endpoint de salud: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ No se puede conectar a la aplicación: {e}")
        return False

def test_upload_endpoint():
    """Probar el endpoint de subida de archivos"""
    try:
        # Crear un archivo de prueba simple
        test_file_path = "test_image.txt"
        with open(test_file_path, 'w') as f:
            f.write("Test image content")
        
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test.jpg', f, 'image/jpeg')}
            response = requests.post('http://localhost:5000/upload', files=files, timeout=10)
        
        # Limpiar archivo de prueba
        os.remove(test_file_path)
        
        if response.status_code in [200, 400]:  # 400 es esperado para archivo inválido
            print("✅ Endpoint de subida funcionando")
            return True
        else:
            print(f"❌ Error en endpoint de subida: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error probando endpoint de subida: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🧪 Iniciando pruebas de la aplicación...")
    print("=" * 50)
    
    # Esperar un poco para que la aplicación se inicie
    print("⏳ Esperando que la aplicación se inicie...")
    time.sleep(3)
    
    # Probar endpoints
    health_ok = test_app_health()
    upload_ok = test_upload_endpoint()
    
    print("=" * 50)
    if health_ok and upload_ok:
        print("🎉 ¡Todas las pruebas pasaron! La aplicación está funcionando correctamente.")
        print("🌐 Puedes acceder a tu aplicación en: http://localhost:5000")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
    
    print("=" * 50)

if __name__ == '__main__':
    main()
