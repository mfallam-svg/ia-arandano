"""
Utilidades de base de datos para almacenar histórico de análisis
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

class Database:
    """Clase para manejar operaciones de base de datos"""
    
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
            
            # Tabla principal de análisis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    processed_filename TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_detections INTEGER,
                    maturity_score REAL,
                    maturity_distribution TEXT,
                    analysis_data TEXT,
                    batch_id TEXT
                )
            ''')
            
            # Índices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON analysis_history(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch_id ON analysis_history(batch_id)')
            
            conn.commit()
    
    def save_analysis(self, result, batch_id=None):
        """
        Guardar resultado de análisis en la base de datos
        
        Args:
            result: Diccionario con resultados del análisis
            batch_id: ID opcional del lote (para subidas múltiples)
            
        Returns:
            id: ID del registro creado
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Extraer datos relevantes
                filename = result.get('filename', '')
                processed_filename = result.get('processed_image', '')
                
                maturity_analysis = result.get('maturity_analysis', {})
                total_detected = maturity_analysis.get('total_detected', 0)
                
                # Extraer distribución de madurez
                distribution = {}
                if 'report' in result and 'maturity_analysis' in result['report']:
                    dist_data = result['report']['maturity_analysis']
                    distribution = {
                        'counts': dist_data.get('counts', {}),
                        'percentages': dist_data.get('percentages', {}),
                        'maturity_score': dist_data.get('maturity_score', 0)
                    }
                
                # Insertar registro
                cursor.execute('''
                    INSERT INTO analysis_history 
                    (filename, processed_filename, total_detections, 
                     maturity_score, maturity_distribution, analysis_data, batch_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    filename,
                    processed_filename,
                    total_detected,
                    distribution.get('maturity_score', 0),
                    json.dumps(distribution),
                    json.dumps(result),
                    batch_id
                ))
                
                analysis_id = cursor.lastrowid
                conn.commit()
                return analysis_id
                
        except Exception as e:
            print(f"Error guardando análisis: {e}")
            return None
    
    def get_history(self, limit=100, offset=0):
        """
        Obtener historial de análisis
        
        Args:
            limit: Límite de registros a retornar
            offset: Offset para paginación
            
        Returns:
            list: Lista de registros de análisis
        """
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
                    
                    # Parsear JSON
                    if result['maturity_distribution']:
                        result['maturity_distribution'] = json.loads(result['maturity_distribution'])
                    
                    # Formatear fecha
                    if result['created_at']:
                        dt = datetime.strptime(result['created_at'], '%Y-%m-%d %H:%M:%S')
                        result['created_at'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    results.append(result)
                
                return results
                
        except Exception as e:
            print(f"Error obteniendo historial: {e}")
            return []
    
    def get_analysis_by_id(self, analysis_id):
        """
        Obtener un análisis específico por ID
        
        Args:
            analysis_id: ID del análisis
            
        Returns:
            dict: Datos del análisis o None si no existe
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, filename, processed_filename, created_at,
                           total_detections, maturity_score, maturity_distribution,
                           analysis_data, batch_id
                    FROM analysis_history
                    WHERE id = ?
                ''', (analysis_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                columns = [col[0] for col in cursor.description]
                result = dict(zip(columns, row))
                
                # Parsear campos JSON
                if result['maturity_distribution']:
                    result['maturity_distribution'] = json.loads(result['maturity_distribution'])
                if result['analysis_data']:
                    result['analysis_data'] = json.loads(result['analysis_data'])
                
                return result
                
        except Exception as e:
            print(f"Error obteniendo análisis {analysis_id}: {e}")
            return None
    
    def export_to_excel(self, output_path):
        """
        Exportar historial a Excel
        
        Args:
            output_path: Ruta donde guardar el archivo Excel
            
        Returns:
            bool: True si se exportó correctamente
        """
        try:
            import pandas as pd
            
            with self.get_connection() as conn:
                # Obtener datos básicos
                df_basic = pd.read_sql_query('''
                    SELECT id, filename, processed_filename, created_at,
                           total_detections, maturity_score, batch_id
                    FROM analysis_history
                    ORDER BY created_at DESC
                ''', conn)
                
                # Obtener distribución de madurez
                df_distribution = pd.read_sql_query('''
                    SELECT id, maturity_distribution
                    FROM analysis_history
                ''', conn)
                
                # Parsear distribución JSON
                distributions = df_distribution['maturity_distribution'].apply(json.loads)
                counts = distributions.apply(lambda x: x.get('counts', {}))
                
                # Crear columnas de conteo
                df_basic['maduros'] = counts.apply(lambda x: x.get('maduro', 0))
                df_basic['semimaduros'] = counts.apply(lambda x: x.get('semimaduro', 0))
                df_basic['no_maduros'] = counts.apply(lambda x: x.get('no_maduro', 0))
                
                # Reordenar columnas
                columns = [
                    'id', 'created_at', 'filename', 'total_detections',
                    'maduros', 'semimaduros', 'no_maduros',
                    'maturity_score', 'batch_id'
                ]
                df_basic = df_basic[columns]
                
                # Renombrar columnas para el Excel
                column_names = {
                    'id': 'ID',
                    'created_at': 'Fecha',
                    'filename': 'Archivo',
                    'total_detections': 'Total Detectados',
                    'maduros': 'Maduros',
                    'semimaduros': 'Semimaduros',
                    'no_maduros': 'No Maduros',
                    'maturity_score': 'Puntuación Madurez',
                    'batch_id': 'ID de Lote'
                }
                df_basic.rename(columns=column_names, inplace=True)
                
                # Crear archivo Excel con formato
                with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                    df_basic.to_excel(writer, sheet_name='Análisis', index=False)
                    
                    # Obtener objeto workbook/worksheet
                    workbook = writer.book
                    worksheet = writer.sheets['Análisis']
                    
                    # Formatos
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'bg_color': '#D9EAD3',
                        'border': 1
                    })
                    
                    # Aplicar formato a encabezados
                    for col_num, value in enumerate(df_basic.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Ajustar anchos de columna
                    worksheet.set_column('A:A', 8)   # ID
                    worksheet.set_column('B:B', 20)  # Fecha
                    worksheet.set_column('C:C', 30)  # Archivo
                    worksheet.set_column('D:H', 15)  # Columnas numéricas
                    worksheet.set_column('I:I', 20)  # ID de Lote
                
                return True
                
        except Exception as e:
            print(f"Error exportando a Excel: {e}")
            return False