"""
Generador de reportes para análisis de madurez de arándanos
"""

import json
from datetime import datetime
import os

class ReportGenerator:
    """Clase para generar reportes de análisis de madurez"""
    
    def __init__(self):
        self.report_template = {
            'timestamp': '',
            'image_info': {},
            'detection_summary': {},
            'maturity_analysis': {},
            'recommendations': {},
            'technical_details': {}
        }
    
    def generate_report(self, maturity_analysis, image_path):
        """
        Generar reporte completo de análisis
        
        Args:
            maturity_analysis: Resultados del análisis de madurez
            image_path: Ruta de la imagen analizada
            
        Returns:
            report: Diccionario con el reporte completo
        """
        try:
            report = self.report_template.copy()
            
            # Información básica
            report['timestamp'] = datetime.now().isoformat()
            report['image_info'] = self._get_image_info(image_path)
            
            # Resumen de detecciones
            report['detection_summary'] = self._generate_detection_summary(maturity_analysis)
            
            # Análisis de madurez
            maturity_dist = self._analyze_maturity_distribution(maturity_analysis)
            report['maturity_analysis'] = maturity_dist
            
            # Recomendaciones (basadas en la distribución ya calculada)
            report['recommendations'] = self._generate_recommendations(maturity_dist)
            
            # Detalles técnicos
            report['technical_details'] = self._get_technical_details(maturity_analysis)
            
            return report
            
        except Exception as e:
            raise Exception(f"Error generando reporte: {str(e)}")
    
    def _get_image_info(self, image_path):
        """Obtener información de la imagen"""
        try:
            file_info = os.stat(image_path)
            return {
                'filename': os.path.basename(image_path),
                'file_size_mb': round(file_info.st_size / (1024 * 1024), 2),
                'created_date': datetime.fromtimestamp(file_info.st_ctime).isoformat(),
                'modified_date': datetime.fromtimestamp(file_info.st_mtime).isoformat()
            }
        except Exception:
            return {'filename': os.path.basename(image_path), 'error': 'No se pudo obtener información del archivo'}
    
    def _generate_detection_summary(self, maturity_analysis):
        """Generar resumen de detecciones"""
        try:
            total_detections = len(maturity_analysis.get('detections', []))
            
            summary = {
                'total_blueberries': total_detections,
                'detection_confidence_avg': 0,
                'detection_confidence_min': 0,
                'detection_confidence_max': 0
            }
            
            if total_detections > 0:
                confidences = [det.get('confidence', 0) for det in maturity_analysis.get('detections', [])]
                summary['detection_confidence_avg'] = round(sum(confidences) / len(confidences), 3)
                summary['detection_confidence_min'] = round(min(confidences), 3)
                summary['detection_confidence_max'] = round(max(confidences), 3)
            
            return summary
            
        except Exception as e:
            return {'error': f'Error generando resumen: {str(e)}'}
    
    def _analyze_maturity_distribution(self, maturity_analysis):
        """Analizar distribución de madurez"""
        try:
            detections = maturity_analysis.get('detections', [])
            
            # Contar por categoría de madurez
            maturity_counts = {
                'maduro': 0,
                'semimaduro': 0,
                'no_maduro': 0,
                'unknown': 0
            }
            
            for detection in detections:
                maturity = detection.get('maturity', 'unknown')
                maturity_counts[maturity] = maturity_counts.get(maturity, 0) + 1
            
            total = sum(maturity_counts.values())
            
            # Calcular porcentajes
            maturity_percentages = {}
            if total > 0:
                for maturity, count in maturity_counts.items():
                    maturity_percentages[maturity] = round((count / total) * 100, 1)
            
            return {
                'counts': maturity_counts,
                'percentages': maturity_percentages,
                'total_analyzed': total,
                'maturity_score': self._calculate_maturity_score(maturity_counts, total)
            }
            
        except Exception as e:
            return {'error': f'Error analizando distribución: {str(e)}'}
    
    def _calculate_maturity_score(self, maturity_counts, total):
        """Calcular puntuación de madurez general"""
        try:
            if total == 0:
                return 0
            
            # Ponderación: maduro=1.0, semimaduro=0.5, no_maduro=0.0
            weighted_sum = (
                maturity_counts.get('maduro', 0) * 1.0 +
                maturity_counts.get('semimaduro', 0) * 0.5 +
                maturity_counts.get('no_maduro', 0) * 0.0
            )
            
            return round((weighted_sum / total) * 100, 1)
            
        except Exception:
            return 0
    
    def _generate_recommendations(self, maturity_dist):
        """Generar recomendaciones basadas en el análisis"""
        try:
            maturity_score = maturity_dist.get('maturity_score', 0)
            counts = maturity_dist.get('counts', {})
            
            recommendations = {
                'harvest_recommendation': self._get_harvest_recommendation(maturity_score),
                'timing_recommendation': self._get_timing_recommendation(maturity_score),
                'quality_assessment': self._get_quality_assessment(counts),
                'next_steps': self._get_next_steps(maturity_score)
            }
            
            return recommendations
            
        except Exception as e:
            return {'error': f'Error generando recomendaciones: {str(e)}'}
    
    def _get_harvest_recommendation(self, maturity_score):
        """Obtener recomendación de cosecha"""
        if maturity_score >= 80:
            return "Cosecha inmediata recomendada - Alta proporción de frutos maduros"
        elif maturity_score >= 60:
            return "Cosecha en 2-3 días - Buena proporción de frutos maduros"
        elif maturity_score >= 40:
            return "Cosecha en 5-7 días - Proporción moderada de frutos maduros"
        elif maturity_score >= 20:
            return "Cosecha en 10-14 días - Mayoría de frutos aún inmaduros"
        else:
            return "No cosechar aún - Frutos predominantemente inmaduros"
    
    def _get_timing_recommendation(self, maturity_score):
        """Obtener recomendación de timing"""
        if maturity_score >= 80:
            return "Urgente - Cosechar dentro de 24-48 horas"
        elif maturity_score >= 60:
            return "Pronto - Cosechar dentro de 3-5 días"
        elif maturity_score >= 40:
            return "Moderado - Cosechar dentro de 1 semana"
        elif maturity_score >= 20:
            return "Paciente - Cosechar dentro de 2 semanas"
        else:
            return "Esperar - Continuar monitoreo semanal"
    
    def _get_quality_assessment(self, counts):
        """Evaluar calidad del cultivo"""
        total = sum(counts.values())
        if total == 0:
            return "No se detectaron frutos"
        
        maduro_pct = (counts.get('maduro', 0) / total) * 100
        
        if maduro_pct >= 70:
            return "Excelente - Alta calidad de maduración"
        elif maduro_pct >= 50:
            return "Buena - Calidad de maduración aceptable"
        elif maduro_pct >= 30:
            return "Regular - Calidad de maduración moderada"
        else:
            return "Baja - Calidad de maduración deficiente"
    
    def _get_next_steps(self, maturity_score):
        """Obtener próximos pasos recomendados"""
        if maturity_score >= 80:
            return [
                "Preparar equipos de cosecha",
                "Organizar personal de cosecha",
                "Verificar condiciones de almacenamiento",
                "Programar transporte para venta inmediata"
            ]
        elif maturity_score >= 60:
            return [
                "Continuar monitoreo diario",
                "Preparar equipos de cosecha",
                "Evaluar condiciones climáticas",
                "Planificar logística de cosecha"
            ]
        elif maturity_score >= 40:
            return [
                "Continuar monitoreo cada 2-3 días",
                "Evaluar condiciones de riego",
                "Verificar nutrición de plantas",
                "Preparar plan de cosecha"
            ]
        else:
            return [
                "Continuar monitoreo semanal",
                "Evaluar condiciones de cultivo",
                "Verificar nutrición y riego",
                "Mantener control de plagas"
            ]
    
    def _get_technical_details(self, maturity_analysis):
        """Obtener detalles técnicos del análisis"""
        try:
            return {
                'model_version': '1.0.0',
                'analysis_method': 'CNN + Color Analysis',
                'confidence_threshold': 0.5,
                'processing_time_ms': maturity_analysis.get('processing_time', 0),
                'image_resolution': maturity_analysis.get('image_resolution', 'Unknown'),
                'detection_algorithm': 'YOLO + Custom Maturity Classifier'
            }
        except Exception:
            return {'error': 'No se pudieron obtener detalles técnicos'}
    
    def save_report(self, report, output_path):
        """Guardar reporte en archivo JSON"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            raise Exception(f"Error guardando reporte: {str(e)}")
    
    def generate_summary_report(self, reports_list):
        """Generar reporte resumen de múltiples análisis"""
        try:
            summary = {
                'total_images_analyzed': len(reports_list),
                'average_maturity_score': 0,
                'harvest_recommendations': [],
                'quality_trends': {}
            }
            
            if reports_list:
                # Calcular promedio de puntuación de madurez
                maturity_scores = [
                    report.get('maturity_analysis', {}).get('maturity_score', 0)
                    for report in reports_list
                ]
                summary['average_maturity_score'] = round(sum(maturity_scores) / len(maturity_scores), 1)
                
                # Agregar recomendaciones únicas
                recommendations = set()
                for report in reports_list:
                    rec = report.get('recommendations', {}).get('harvest_recommendation', '')
                    if rec:
                        recommendations.add(rec)
                summary['harvest_recommendations'] = list(recommendations)
            
            return summary
            
        except Exception as e:
            return {'error': f'Error generando reporte resumen: {str(e)}'}
