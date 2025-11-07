"""
🫐 Sistema de Evaluación de Madurez de Arándanos con IA
Aplicación web principal para análisis de imágenes de arándanos
"""

import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image
import json

# Importar módulos personalizados
from .models.blueberry_detector import BlueberryDetector
from .utils.image_processor import ImageProcessor
from .utils.report_generator import ReportGenerator
from .utils.simple_database import SimpleDatabase
import uuid

app = Flask(__name__)
CORS(app)

# Configuración
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEFAULT_UPLOAD = os.path.join(BASE_DIR, 'data', 'uploads')
DEFAULT_PROCESSED = os.path.join(BASE_DIR, 'data', 'processed')
DEFAULT_EXPORTS = os.path.join(BASE_DIR, 'data', 'exports')
app.config['UPLOAD_FOLDER'] = os.path.abspath(os.environ.get('UPLOAD_FOLDER', DEFAULT_UPLOAD))
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))  # 16MB
app.config['ALLOWED_EXTENSIONS'] = os.environ.get('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,bmp,tiff').split(',')
app.config['PROCESSED_FOLDER'] = os.path.abspath(os.environ.get('PROCESSED_FOLDER', DEFAULT_PROCESSED))
app.config['EXPORTS_FOLDER'] = os.path.abspath(os.environ.get('EXPORTS_FOLDER', DEFAULT_EXPORTS))

# Asegurar que los directorios existen
for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER'], app.config['EXPORTS_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Asegurar que los directorios de uploads y processed existen
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Inicializar componentes
detector = BlueberryDetector()
image_processor = ImageProcessor()
report_generator = ReportGenerator()

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Página principal de la aplicación"""
    return render_template('index.html')

@app.route('/history')
def get_history():
    """Obtener historial de análisis"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page
        
        db = SimpleDatabase()
        results = db.get_history(limit=per_page, offset=offset)
        
        return jsonify({
            'success': True,
            'data': results,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': f'Error obteniendo historial: {str(e)}'}), 500

@app.route('/history/<int:id>', methods=['DELETE'])
def delete_record(id):
    """Eliminar un registro del historial"""
    try:
        db = SimpleDatabase()
        if db.delete_record(id):
            return jsonify({'success': True, 'message': 'Registro eliminado correctamente'})
        else:
            return jsonify({'error': 'No se pudo eliminar el registro'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Error eliminando registro: {str(e)}'}), 500

@app.route('/export')
def export_history():
    """Exportar historial a CSV"""
    try:
        # Generar nombre único para el archivo
        filename = f"analisis_arandanos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(app.config['EXPORTS_FOLDER'], filename)
        
        # Exportar usando la clase SimpleDatabase
        db = SimpleDatabase()
        if db.export_to_csv(filepath):
            return send_from_directory(
                app.config['EXPORTS_FOLDER'],
                filename,
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': 'Error generando archivo CSV'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error exportando historial: {str(e)}'}), 500

@app.route('/export/<int:id>')
def export_single_record(id):
    """Exportar un registro individual a CSV"""
    try:
        # Generar nombre único para el archivo
        filename = f"analisis_arandano_{id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(app.config['EXPORTS_FOLDER'], filename)
        
        # Exportar usando la clase SimpleDatabase
        db = SimpleDatabase()
        if db.export_to_csv(filepath, record_id=id):
            return send_from_directory(
                app.config['EXPORTS_FOLDER'],
                filename,
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': 'Error generando archivo CSV'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error exportando registro: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Endpoint para subir y procesar imágenes"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se encontró archivo'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        if file and allowed_file(file.filename):
            # Generar nombre único para el archivo
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Guardar archivo
            file.save(filepath)

            # Validar que el archivo sea una imagen válida
            try:
                with Image.open(filepath) as im:
                    im.verify()
            except Exception:
                # Eliminar archivo inválido
                try:
                    os.remove(filepath)
                except Exception:
                    pass
                return jsonify({'error': 'Archivo de imagen inválido'}), 400

            # Procesar imagen
            results = process_image(filepath)

            # Guardar resultados en base de datos
            db = SimpleDatabase()
            analysis_id = db.save_analysis(results)
            
            if analysis_id:
                results['analysis_id'] = analysis_id
            
            return jsonify({
                'success': True,
                'filename': unique_filename,
                'results': results
            })
        
        return jsonify({'error': 'Tipo de archivo no permitido'}), 400
    
    except Exception as e:
        return jsonify({'error': f'Error en el procesamiento: {str(e)}'}), 500

@app.route('/batch_upload', methods=['POST'])
def batch_upload():
    """Endpoint para subir múltiples imágenes"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No se encontraron archivos'}), 400
        
        files = request.files.getlist('files[]')
        results = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                file.save(filepath)
                result = process_image(filepath)
                result['filename'] = unique_filename
                # Guardar en base de datos
                batch_id = str(uuid.uuid4())
                db = SimpleDatabase()
                analysis_id = db.save_analysis(result, batch_id=batch_id)
                if analysis_id:
                    result['analysis_id'] = analysis_id
                results.append(result)
        
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': f'Error en el procesamiento por lotes: {str(e)}'}), 500

def process_image(image_path):
    """Procesar una imagen y retornar resultados de análisis"""
    try:
        # Cargar imagen
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("No se pudo cargar la imagen")
        
        # Preprocesar imagen
        processed_image = image_processor.preprocess(image)
        
        # Detectar arándanos
        detections = detector.detect(processed_image)
        
        # Analizar madurez
        maturity_analysis = detector.analyze_maturity(detections, processed_image)
        
        # Generar reporte
        report = report_generator.generate_report(maturity_analysis, image_path)
        
        # Guardar imagen procesada
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_dir = app.config.get('PROCESSED_FOLDER', app.config['UPLOAD_FOLDER'])
        os.makedirs(output_dir, exist_ok=True)
        ext_out = '.jpg'
        output_path = os.path.join(output_dir, f"{base_name}_processed{ext_out}")
        try:
            image_processor.save_processed_image(processed_image, maturity_analysis.get('detections', detections), output_path)
        except Exception as e:
            print(f"Error guardando imagen procesada: {e}")
        processed_filename = os.path.basename(output_path) if os.path.exists(output_path) else None

        return {
            'detections': maturity_analysis.get('total_detected', len(detections)),
            'maturity_analysis': maturity_analysis,
            'report': report,
            'processed_image': processed_filename
        }
    
    except Exception as e:
        raise Exception(f"Error procesando imagen: {str(e)}")

@app.route('/results/<filename>')
def get_results(filename):
    """Obtener resultados de una imagen procesada"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        results = process_image(filepath)
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': f'Error obteniendo resultados: {str(e)}'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Servir archivos subidos"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processed/<filename>')
def processed_file(filename):
    """Servir archivos procesados"""
    return send_from_directory(app.config.get('PROCESSED_FOLDER', app.config['UPLOAD_FOLDER']), filename)

@app.route('/api/health')
def health_check():
    """Endpoint de verificación de salud de la aplicación"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/model_info')
def model_info():
    """Información del modelo YOLO y umbrales actuales"""
    try:
        info = detector.get_model_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': f'Error obteniendo información del modelo: {str(e)}'}), 500

@app.route('/api/stats')
def get_stats():
    """Obtener estadísticas de la aplicación"""
    try:
        upload_dir = app.config['UPLOAD_FOLDER']
        total_files = len([f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))])
        
        return jsonify({
            'total_processed_images': total_files,
            'model_status': 'active',
            'last_processed': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': f'Error obteniendo estadísticas: {str(e)}'}), 500

@app.route('/manifest.json')
def serve_manifest():
    """Servir el archivo manifest.json"""
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'manifest.json',
        mimetype='application/json'
    )

@app.route('/service-worker.js')
def service_worker():
    """Servir el service worker desde la raíz para que tenga scope de la app"""
    try:
        # Enviar el archivo JS del service worker ubicado en static/js/
        return app.send_static_file('js/service-worker.js')
    except Exception as e:
        return ('', 404)

@app.route('/offline.html')
def offline():
    """Página para mostrar cuando no hay conexión"""
    return render_template('offline.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
