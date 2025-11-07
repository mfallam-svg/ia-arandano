#!/usr/bin/env python3
"""
Script principal para ejecutar la aplicación web de evaluación de madurez de arándanos
"""

import os
import sys
from pathlib import Path

# Agregar el directorio src al path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Configurar variables de entorno por defecto
os.environ.setdefault('FLASK_APP', 'web_app.app')
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('SECRET_KEY', 'dev-secret-key-change-in-production')

# Exponer la aplicación Flask a nivel de módulo para que servidores WSGI (p. ej. gunicorn)
# puedan importarla. Esto permite usar `gunicorn run:app` como comando de inicio
# cuando se despliega con un servidor WSGI.
try:
    # Intentamos importar la aplicación desde el paquete `web_app`
    from web_app.app import app as app  # noqa: F401
except Exception:
    # Si falla la importación no interrumpimos; el script `main()` intentará importar
    app = None

def main():
    """Función principal para ejecutar la aplicación"""
    try:
        # Importar la aplicación Flask
        from web_app.app import app
        
        print("🫐 Sistema de Evaluación de Madurez de Arándanos")
        print("=" * 50)
        print("🚀 Iniciando aplicación web...")
        print(f"📁 Directorio de trabajo: {os.getcwd()}")
        print(f"🌐 URL: http://localhost:5000")
        print(f"🔧 Modo: {os.environ.get('FLASK_ENV', 'development')}")
        print("=" * 50)
        
        # Ejecutar la aplicación
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
        
    except ImportError as e:
        print(f"❌ Error importando la aplicación: {e}")
        print("💡 Asegúrate de que todas las dependencias estén instaladas:")
        print("   pip install -r requirements/requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error ejecutando la aplicación: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
