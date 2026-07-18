import sys
import os

# Agrega el directorio raíz del proyecto al PYTHONPATH para que 'import src...' funcione
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
