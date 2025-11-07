"""
Utilidades de base de datos para almacenar histórico de análisis usando SQLite directamente
"""

import sqlite3
import json
import os
import csv
from datetime import datetime
from pathlib import Path

class SimpleDatabase:
    """Clase para manejar operaciones de base de datos sin dependencias externas"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            # Crear base de datos en carpeta data
            base_dir = Path(__file__).resolve().parents[3]
            db_dir = base_dir / 'data'
            os.makedirs(db_dir, exist_ok=True)
            db_path = db_dir / 'analysis_history.db'
        
        self.db_path = str(db_path)
        self.init_db()
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Inicializar esquema de base de datos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    processed_filename TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_detections INTEGER,
                    maturity_score REAL,
                    maturity_distribution TEXT,
                    batch_id TEXT
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON analysis_history(created_at)')
            conn.commit()
    
    def save_analysis(self, result, batch_id=None):
        """Guardar resultado de análisis en la base de datos"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                filename = result.get('filename', '')
                processed_filename = result.get('processed_image', '')
                
                maturity_analysis = result.get('maturity_analysis', {})
                total_detected = maturity_analysis.get('total_detected', 0)
                
                distribution = {}
                if 'report' in result and 'maturity_analysis' in result['report']:
                    dist_data = result['report']['maturity_analysis']
                    distribution = {
                        'counts': dist_data.get('counts', {}),
                        'percentages': dist_data.get('percentages', {}),
                        'maturity_score': dist_data.get('maturity_score', 0)
                    }
                
                cursor.execute('''
                    INSERT INTO analysis_history 
                    (filename, processed_filename, total_detections, 
                     maturity_score, maturity_distribution, batch_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    filename,
                    processed_filename,
                    total_detected,
                    distribution.get('maturity_score', 0),
                    json.dumps(distribution),
                    batch_id
                ))
                
                analysis_id = cursor.lastrowid
                conn.commit()
                return analysis_id
                
        except Exception as e:
            print(f"Error guardando análisis: {e}")
            return None
    
    def get_history(self, limit=100, offset=0):
        """Obtener historial de análisis"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, filename, processed_filename, created_at,
                           total_detections, maturity_score, maturity_distribution,
                           batch_id
                    FROM analysis_history
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    
                    if result['maturity_distribution']:
                        result['maturity_distribution'] = json.loads(result['maturity_distribution'])
                    
                    if result['created_at']:
                        dt = datetime.strptime(result['created_at'], '%Y-%m-%d %H:%M:%S')
                        result['created_at'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    results.append(result)
                
                return results
                
        except Exception as e:
            print(f"Error obteniendo historial: {e}")
            return []
    
    def export_to_csv(self, output_path, record_id=None):
        """
        Exportar historial a CSV. Si se proporciona record_id, solo exporta ese registro.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Construir la consulta según si es un registro individual o todos
                query = '''
                    SELECT id, filename, created_at, total_detections,
                           maturity_score, maturity_distribution
                    FROM analysis_history
                '''
                params = []
                
                if record_id is not None:
                    query += ' WHERE id = ?'
                    params = [record_id]
                
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                
                rows = cursor.fetchall()
                if not rows:
                    return False
                
                # Escribir CSV
                with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Encabezados
                    writer.writerow([
                        'ID', 'Fecha', 'Archivo', 'Total Detectados',
                        'Maduros', 'Semimaduros', 'No Maduros',
                        'Puntuación Madurez'
                    ])
                    
                    # Datos
                    for row in rows:
                        id_, filename, created_at, total_detections, maturity_score, maturity_dist = row
                        
                        # Parsear distribución JSON
                        dist = json.loads(maturity_dist) if maturity_dist else {}
                        counts = dist.get('counts', {})
                        
                        writer.writerow([
                            id_,
                            created_at,
                            filename,
                            total_detections,
                            counts.get('maduro', 0),
                            counts.get('semimaduro', 0),
                            counts.get('no_maduro', 0),
                            f"{maturity_score:.1f}%"
                        ])
                
                return True
                
        except Exception as e:
            print(f"Error exportando a CSV: {e}")
            return False

    def delete_record(self, record_id):
        """
        Eliminar un registro del historial
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Primero verificar si el registro existe
                cursor.execute('SELECT filename, processed_filename FROM analysis_history WHERE id = ?', (record_id,))
                record = cursor.fetchone()
                
                if not record:
                    return False
                
                # Eliminar el registro
                cursor.execute('DELETE FROM analysis_history WHERE id = ?', (record_id,))
                conn.commit()
                
                # Intentar eliminar los archivos asociados
                filename, processed_filename = record
                base_dir = Path(self.db_path).parent.parent
                
                if filename:
                    file_path = base_dir / 'uploads' / filename
                    try:
                        if file_path.exists():
                            file_path.unlink()
                    except Exception as e:
                        print(f"Error eliminando archivo original: {e}")
                
                if processed_filename:
                    processed_path = base_dir / 'processed' / processed_filename
                    try:
                        if processed_path.exists():
                            processed_path.unlink()
                    except Exception as e:
                        print(f"Error eliminando archivo procesado: {e}")
                
                return True
                
        except Exception as e:
            print(f"Error eliminando registro: {e}")
            return False