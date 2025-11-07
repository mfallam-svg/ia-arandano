"""
Procesador de imágenes para el análisis de arándanos
"""

import cv2
import numpy as np
from PIL import Image
import os

class ImageProcessor:
    """Clase para procesamiento de imágenes de arándanos"""
    
    def __init__(self):
        self.target_size = (640, 640)  # Tamaño estándar para YOLO
        self.normalization_factor = 255.0
    
    def preprocess(self, image):
        """
        Preprocesar imagen para detección
        
        Args:
            image: Imagen en formato numpy array (BGR)
            
        Returns:
            processed_image: Imagen preprocesada
        """
        try:
            # Convertir BGR a RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Para YOLO, no necesitamos redimensionar aquí ya que YOLO lo hace internamente
            # Solo retornamos la imagen en RGB
            return rgb_image
            
        except Exception as e:
            raise Exception(f"Error en preprocesamiento: {str(e)}")
    
    def _enhance_image(self, image):
        """
        Mejorar imagen para mejor detección
        
        Args:
            image: Imagen normalizada
            
        Returns:
            enhanced_image: Imagen mejorada
        """
        try:
            # Convertir a escala de grises para análisis
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Aplicar filtro Gaussiano para reducir ruido
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Aplicar ecualización de histograma para mejorar contraste
            enhanced = cv2.equalizeHist(blurred)
            
            # Convertir de vuelta a RGB
            enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
            
            return enhanced_rgb
            
        except Exception as e:
            # Si falla el mejoramiento, retornar imagen original
            return image
    
    def save_processed_image(self, image, detections, output_path):
        """
        Guardar imagen procesada con detecciones
        
        Args:
            image: Imagen procesada
            detections: Lista de detecciones
            output_path: Ruta de salida
        """
        try:
            # Convertir imagen de vuelta a formato de visualización
            if isinstance(image, np.ndarray):
                if image.dtype in (np.float32, np.float64):
                    # Escalar si está normalizada [0,1]
                    if image.max() <= 1.0:
                        display_image = (image * self.normalization_factor).clip(0, 255).astype(np.uint8)
                    else:
                        display_image = np.clip(image, 0, 255).astype(np.uint8)
                else:
                    # Ya está en uint8
                    display_image = image
            else:
                raise ValueError("Formato de imagen no soportado para guardar")
            
            # Dibujar bounding boxes y etiquetas
            annotated_image = self._draw_detections(display_image, detections)
            
            # Guardar imagen
            cv2.imwrite(output_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
            
        except Exception as e:
            raise Exception(f"Error guardando imagen procesada: {str(e)}")
    
    def _draw_detections(self, image, detections):
        """
        Dibujar detecciones en la imagen
        
        Args:
            image: Imagen para dibujar
            detections: Lista de detecciones
            
        Returns:
            annotated_image: Imagen con detecciones dibujadas
        """
        try:
            annotated_image = image.copy()
            
            for detection in detections:
                # Extraer información de la detección
                bbox = detection.get('bbox', [])
                confidence = detection.get('confidence', 0)
                class_name = detection.get('class', 'blueberry')
                maturity = detection.get('maturity', 'unknown')
                
                if len(bbox) == 4:
                    x1, y1, x2, y2 = bbox
                    
                    # Color según madurez (RGB)
                    color = self._get_maturity_color(maturity)

                    # Dibujar bounding box (rectángulo)
                    x1i, y1i, x2i, y2i = int(x1), int(y1), int(x2), int(y2)
                    cv2.rectangle(annotated_image, (x1i, y1i), (x2i, y2i), color, 2)

                    # Dibujar silueta circular centrada en el bbox
                    w = max(0, x2i - x1i)
                    h = max(0, y2i - y1i)
                    cx, cy = x1i + w // 2, y1i + h // 2
                    radius = max(1, min(w, h) // 2)
                    cv2.circle(annotated_image, (int(cx), int(cy)), int(radius), color, 2)

                    # Etiqueta con fondo del mismo color y texto blanco
                    label = f"{maturity} ({float(confidence)*100:.1f}%)"
                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    pad = 3
                    y_top = max(0, y1i - th - 2*pad)
                    y_bottom = y_top + th + 2*pad
                    x_right = x1i + tw + 2*pad
                    cv2.rectangle(annotated_image, (x1i, y_top), (x_right, y_bottom), color, -1)
                    cv2.putText(annotated_image, label, (x1i + pad, y_bottom - pad),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
            return annotated_image
            
        except Exception as e:
            return image
    
    def _get_maturity_color(self, maturity):
        """
        Obtener color según el estado de madurez (RGB)
        
        - maduro: azul
        - semimaduro: rojo
        - no_maduro: verde
        """
        color_map = {
            'maduro': (0, 123, 255),      # Azul (Bootstrap primary)
            'semimaduro': (220, 53, 69),  # Rojo (Bootstrap danger)
            'no_maduro': (40, 167, 69),   # Verde (Bootstrap success)
            'unknown': (128, 128, 128)    # Gris
        }
        return color_map.get(maturity, (128, 128, 128))
    
    def extract_features(self, image):
        """
        Extraer características de la imagen para análisis
        
        Args:
            image: Imagen procesada
            
        Returns:
            features: Diccionario con características extraídas
        """
        try:
            features = {}
            
            # Convertir a HSV para análisis de color
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Estadísticas de color
            features['mean_hue'] = np.mean(hsv[:, :, 0])
            features['mean_saturation'] = np.mean(hsv[:, :, 1])
            features['mean_value'] = np.mean(hsv[:, :, 2])
            
            # Histograma de color
            features['color_histogram'] = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
            
            # Textura (usando GLCM simplificado)
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            features['texture_variance'] = np.var(gray)
            
            return features
            
        except Exception as e:
            raise Exception(f"Error extrayendo características: {str(e)}")
