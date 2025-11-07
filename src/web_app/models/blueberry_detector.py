"""
Detector de arándanos y analizador de madurez usando YOLO
"""

import cv2
import numpy as np
import time
from typing import List, Dict, Any
import os
from ultralytics import YOLO

class BlueberryDetector:
    """Clase para detectar arándanos y analizar su madurez"""
    
    def __init__(self):
        self.confidence_threshold = 0.15
        self.iou_threshold = 0.45
        self.model_loaded = False
        self.model_path = os.environ.get('MODEL_PATH', 'models/weights/best_model.pt')
        self.model = None
        
        # Inicializar modelo YOLO
        self._initialize_model()
    
    def _initialize_model(self):
        """Inicializar modelo YOLO de detección"""
        try:
            # Resolver mejor ruta de pesos disponible
            candidates = []
            if self.model_path:
                candidates.append(self.model_path)
            candidates += [
                os.path.join('models', 'weights', 'best_model.pt'),
                os.path.join('models', 'weights', 'best.pt'),
                'best.pt',
                'last.pt'
            ]

            selected = None
            for p in candidates:
                if p and os.path.exists(p):
                    selected = p
                    break

            if selected:
                self.model = YOLO(selected)
                self.model_loaded = True
                self.model_path = selected
                print(f"✅ Modelo YOLO cargado desde: {selected}")
                try:
                    print(f"📊 Información del modelo: {self.model.info()}")
                except Exception:
                    pass
            else:
                # Fallback: detección por color
                self.model = None
                self.model_loaded = False
                print("⚠️ Pesos de YOLO no encontrados. Usando detección por color como fallback.")
                print("💡 Coloca best.pt en la raíz del proyecto o en models/weights/.")
        except Exception as e:
            print(f"❌ Error inicializando modelo YOLO: {str(e)}")
            print("🔄 Usando detección por color como fallback")
            self.model = None
            self.model_loaded = False
    
    def detect(self, image):
        """
        Detectar arándanos en la imagen usando YOLO
        
        Args:
            image: Imagen preprocesada (numpy array)
            
        Returns:
            detections: Lista de detecciones
        """
        try:
            if self.model_loaded and self.model is not None:
                # Usar modelo YOLO real
                yolo_dets = self._yolo_detection(image)
                # Si YOLO no detecta nada, intentar por color
                if not yolo_dets:
                    color_dets = self._color_based_detection(image)
                    if color_dets:
                        print("ℹ️ YOLO no detectó, pero detección por color encontró objetos.")
                        return color_dets
                return yolo_dets
            else:
                # Usar detección por color como fallback
                return self._color_based_detection(image)
            
        except Exception as e:
            print(f"❌ Error en detección YOLO: {str(e)}")
            print("🔄 Usando detección por color como fallback")
            return self._color_based_detection(image)
    
    def _color_based_detection(self, image):
        """
        Detección basada en color mejorada para arándanos (azul/morado)
        """
        try:
            # Convertir a HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

            # Rangos de tono ampliados para azul y morado (OpenCV H: 0-179)
            # Permitir menor saturación/valor para condiciones de iluminación variables
            lower_blue = np.array([85, 20, 30])
            upper_blue = np.array([140, 255, 255])
            lower_purple = np.array([140, 20, 30])
            upper_purple = np.array([170, 255, 255])

            # Máscaras y combinación
            mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
            mask_purple = cv2.inRange(hsv, lower_purple, upper_purple)
            mask = cv2.bitwise_or(mask_blue, mask_purple)

            # Suavizado y morfología para reducir ruido y unir regiones
            mask = cv2.medianBlur(mask, 5)
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

            # Encontrar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detections = []
            img_h, img_w = image.shape[:2]
            img_area = img_h * img_w
            min_area = max(100, int(0.0005 * img_area))  # umbral relativo al tamaño

            for contour in contours:
                area = cv2.contourArea(contour)
                if area < min_area:
                    continue

                x, y, w, h = cv2.boundingRect(contour)
                # Filtrar por razón de aspecto (arándanos ~circulares)
                aspect_ratio = w / float(h) if h > 0 else 0
                if aspect_ratio < 0.5 or aspect_ratio > 1.8:
                    continue

                # Confianza basada en área (heurística)
                confidence = float(min(0.99, area / (0.02 * img_area)))

                detections.append({
                    'bbox': [int(x), int(y), int(x + w), int(y + h)],
                    'confidence': confidence,
                    'class': 'blueberry',
                    'area': float(area)
                })

            # Si no hay detecciones por color, intentar un fallback con HoughCircles
            if not detections:
                try:
                    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                    gray = cv2.medianBlur(gray, 5)
                    circles = cv2.HoughCircles(
                        gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=20,
                        param1=60, param2=30,
                        minRadius=max(5, int(min(img_h, img_w) * 0.01)),
                        maxRadius=int(min(img_h, img_w) * 0.15)
                    )
                    if circles is not None:
                        for c in np.uint16(np.around(circles))[0, :]:
                            cx, cy, r = c
                            x1, y1 = int(cx - r), int(cy - r)
                            x2, y2 = int(cx + r), int(cy + r)
                            detections.append({
                                'bbox': [max(0, x1), max(0, y1), min(img_w-1, x2), min(img_h-1, y2)],
                                'confidence': 0.5,
                                'class': 'blueberry',
                                'area': float((x2 - x1) * (y2 - y1))
                            })
                except Exception as he:
                    # Ignorar errores de Hough para no romper flujo
                    pass

            return detections

        except Exception as e:
            print(f"Error en detección por color: {str(e)}")
            return []
    
    def _yolo_detection(self, image):
        """
        Detección usando modelo YOLO real
        
        Args:
            image: Imagen preprocesada
            
        Returns:
            detections: Lista de detecciones YOLO
        """
        try:
            # Realizar predicción con YOLO
            results = self.model(image, conf=self.confidence_threshold, iou=self.iou_threshold)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Obtener coordenadas del bounding box
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Obtener confianza y clase
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Obtener nombre de la clase de manera robusta
                        names = getattr(result, 'names', None) or getattr(self.model, 'names', None) or {}
                        if isinstance(names, (list, tuple)):
                            class_name = names[class_id] if 0 <= class_id < len(names) else f"class_{class_id}"
                        elif isinstance(names, dict):
                            class_name = names.get(class_id, f"class_{class_id}")
                        else:
                            class_name = f"class_{class_id}"
                        
                        # Normalizar clase a etiquetas de madurez si aplica
                        norm_name = str(class_name).strip().lower().replace(' ', '_').replace('-', '_')
                        if norm_name in ('maduro', 'semimaduro', 'no_maduro'):
                            maturity_cls = norm_name
                        elif norm_name in ('ripe',):
                            maturity_cls = 'maduro'
                        elif norm_name in ('semi_ripe', 'semi-ripe', 'semi_maduro'):
                            maturity_cls = 'semimaduro'
                        elif norm_name in ('unripe', 'no_maduro', 'inmaduro'):
                            maturity_cls = 'no_maduro'
                        else:
                            maturity_cls = None

                        detection = {
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': float(confidence),
                            'class': class_name,
                            'class_id': int(class_id),
                            'area': float((x2 - x1) * (y2 - y1)),
                            'maturity': maturity_cls if maturity_cls else None
                        }
                        detections.append(detection)
            
            print(f"🔍 YOLO detectó {len(detections)} objetos")
            return detections
            
        except Exception as e:
            print(f"❌ Error en detección YOLO: {str(e)}")
            return []
    
    def analyze_maturity(self, detections, image):
        """
        Analizar madurez de los arándanos detectados
        
        Args:
            detections: Lista de detecciones
            image: Imagen original
            
        Returns:
            maturity_analysis: Análisis completo de madurez
        """
        try:
            start_time = time.time()
            
            maturity_results = []
            for detection in detections:
                bbox = detection.get('bbox', [])
                if len(bbox) == 4:
                    x1, y1, x2, y2 = bbox
                    
                    # Normalizar bbox a límites de la imagen y garantizar caja válida
                    img_h, img_w = image.shape[:2]
                    x1n = max(0, min(int(x1), img_w - 1))
                    y1n = max(0, min(int(y1), img_h - 1))
                    x2n = max(0, min(int(x2), img_w - 1))
                    y2n = max(0, min(int(y2), img_h - 1))

                    if x2n <= x1n:
                        x2n = min(img_w - 1, x1n + 1)
                    if y2n <= y1n:
                        y2n = min(img_h - 1, y1n + 1)

                    detection['bbox'] = [x1n, y1n, x2n, y2n]

                    # Extraer región del arándano con bbox ajustado
                    berry_region = image[y1n:y2n, x1n:x2n]

                    if berry_region is not None and berry_region.size > 0:
                        # Analizar madurez respetando la etiqueta del modelo si existe
                        if detection.get('maturity') in ('maduro', 'semimaduro', 'no_maduro'):
                            maturity = detection['maturity']
                        else:
                            maturity = self._analyze_berry_maturity(berry_region)
                        detection['maturity'] = maturity
                        detection['maturity_confidence'] = self._calculate_maturity_confidence(berry_region)
                    else:
                        # Incluir detección aunque no se pudo extraer región válida para evitar desajustes
                        detection['maturity'] = detection.get('maturity', 'unknown')
                        detection['maturity_confidence'] = detection.get('maturity_confidence', 0.0)

                    maturity_results.append(detection)
            
            processing_time = (time.time() - start_time) * 1000  # en milisegundos
            
            return {
                'detections': maturity_results,
                'processing_time': processing_time,
                'image_resolution': f"{image.shape[1]}x{image.shape[0]}",
                'total_detected': len(maturity_results)
            }
            
        except Exception as e:
            print(f"Error analizando madurez: {str(e)}")
            return {
                'detections': [],
                'processing_time': 0,
                'image_resolution': 'Unknown',
                'total_detected': 0
            }
    
    def _analyze_berry_maturity(self, berry_region):
        """
        Analizar madurez de un arándano individual
        
        Args:
            berry_region: Región de la imagen del arándano
            
        Returns:
            maturity: Estado de madurez ('maduro', 'semimaduro', 'no_maduro')
        """
        try:
            # Convertir a HSV
            hsv = cv2.cvtColor(berry_region, cv2.COLOR_RGB2HSV)
            
            # Calcular estadísticas de color
            mean_hue = np.mean(hsv[:, :, 0])
            mean_saturation = np.mean(hsv[:, :, 1])
            mean_value = np.mean(hsv[:, :, 2])
            
            # Clasificar madurez basado en color
            # Azul oscuro/morado = maduro
            # Azul claro = semimaduro
            # Verde/rojo = no maduro
            
            if mean_hue < 120 and mean_saturation > 100:  # Azul/morado
                if mean_value > 150:  # Claro
                    return 'semimaduro'
                else:  # Oscuro
                    return 'maduro'
            elif mean_hue > 120:  # Verde
                return 'no_maduro'
            else:  # Otros colores
                return 'unknown'
                
        except Exception as e:
            print(f"Error analizando madurez individual: {str(e)}")
            return 'unknown'
    
    def _calculate_maturity_confidence(self, berry_region):
        """
        Calcular confianza del análisis de madurez
        
        Args:
            berry_region: Región del arándano
            
        Returns:
            confidence: Valor de confianza (0-1)
        """
        try:
            # Calcular varianza de color como medida de confianza
            hsv = cv2.cvtColor(berry_region, cv2.COLOR_RGB2HSV)
            color_variance = np.var(hsv[:, :, 0])  # Varianza en tono
            
            # Normalizar confianza
            confidence = min(1.0, max(0.0, 1.0 - (color_variance / 1000)))
            return confidence
            
        except Exception:
            return 0.5  # Confianza neutral si hay error
    
    def get_model_info(self):
        """Obtener información del modelo"""
        return {
            'model_loaded': self.model_loaded,
            'model_path': self.model_path,
            'confidence_threshold': self.confidence_threshold,
            'iou_threshold': self.iou_threshold,
            'version': '1.0.0'
        }
    
    def update_thresholds(self, confidence_threshold=None, iou_threshold=None):
        """Actualizar umbrales de detección"""
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
        if iou_threshold is not None:
            self.iou_threshold = iou_threshold
    
    def preprocess_for_model(self, image):
        """
        Preprocesar imagen para el modelo (placeholder)
        
        Args:
            image: Imagen original
            
        Returns:
            processed_image: Imagen preprocesada
        """
        try:
            # Redimensionar a tamaño estándar
            resized = cv2.resize(image, (640, 640))
            
            # Normalizar
            normalized = resized.astype(np.float32) / 255.0
            
            # Agregar dimensión de batch
            batched = np.expand_dims(normalized, axis=0)
            
            return batched
            
        except Exception as e:
            print(f"Error en preprocesamiento para modelo: {str(e)}")
            return None
