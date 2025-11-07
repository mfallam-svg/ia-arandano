#!/usr/bin/env python3
"""
Script para probar el modelo YOLO de detección de arándanos
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

# Agregar el directorio src al path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def test_yolo_model():
    """Probar el modelo YOLO con una imagen de ejemplo"""
    try:
        from src.web_app.models.blueberry_detector import BlueberryDetector
        
        print("🧪 Probando modelo YOLO...")
        print("=" * 50)
        
        # Inicializar detector
        detector = BlueberryDetector()
        
        if not detector.model_loaded or detector.model is None:
            print("❌ Modelo YOLO no se pudo cargar")
            return False
        
        print("✅ Modelo YOLO cargado correctamente")
        
        # Crear una imagen de prueba (arándanos simulados)
        test_image = create_test_image()
        
        # Realizar detección
        print("🔍 Realizando detección...")
        detections = detector.detect(test_image)
        
        print(f"📊 Resultados:")
        print(f"   - Objetos detectados: {len(detections)}")
        
        for i, detection in enumerate(detections):
            print(f"   - Objeto {i+1}:")
            print(f"     * Clase: {detection.get('class', 'unknown')}")
            print(f"     * Confianza: {detection.get('confidence', 0):.2f}")
            print(f"     * Bbox: {detection.get('bbox', [])}")
        
        # Probar análisis de madurez
        print("\n🍇 Analizando madurez...")
        maturity_analysis = detector.analyze_maturity(detections, test_image)
        
        print(f"📈 Análisis de madurez:")
        print(f"   - Tiempo de procesamiento: {maturity_analysis.get('processing_time', 0):.2f}ms")
        print(f"   - Resolución de imagen: {maturity_analysis.get('image_resolution', 'Unknown')}")
        print(f"   - Total detectado: {maturity_analysis.get('total_detected', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando modelo: {str(e)}")
        return False

def create_test_image():
    """Crear una imagen de prueba con círculos que simulan arándanos"""
    # Crear imagen de 640x480
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Fondo verde (plantas)
    image[:, :] = [34, 139, 34]  # Verde bosque
    
    # Dibujar círculos que simulan arándanos
    circles = [
        (150, 120, 30, [139, 69, 19]),   # Marrón (no maduro)
        (300, 150, 35, [75, 0, 130]),    # Morado (maduro)
        (450, 200, 25, [138, 43, 226]),  # Violeta (maduro)
        (200, 300, 40, [0, 100, 0]),     # Verde (no maduro)
        (350, 350, 30, [128, 0, 128]),   # Púrpura (maduro)
    ]
    
    for x, y, radius, color in circles:
        cv2.circle(image, (x, y), radius, color, -1)
        # Agregar brillo
        cv2.circle(image, (x-5, y-5), radius//3, [255, 255, 255], -1)
    
    return image

def main():
    """Función principal"""
    print("🫐 Prueba del Modelo YOLO - Detector de Arándanos")
    print("=" * 60)
    
    success = test_yolo_model()
    
    print("=" * 60)
    if success:
        print("🎉 ¡Prueba exitosa! Tu modelo YOLO está funcionando correctamente.")
        print("💡 Ahora puedes usar tu aplicación web con el modelo real.")
    else:
        print("⚠️ La prueba falló. Revisa los errores arriba.")
        print("💡 Asegúrate de que:")
        print("   - El archivo best.pt esté en models/weights/")
        print("   - Las dependencias estén instaladas (ultralytics)")
        print("   - El modelo sea compatible con YOLO v8+")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
