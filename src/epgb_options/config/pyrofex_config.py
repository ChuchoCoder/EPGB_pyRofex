"""
Módulo de Configuración de API de pyRofex

Este módulo contiene todos los valores de configuración relacionados a la API de pyRofex.
Las variables de entorno tienen prioridad sobre estos valores por defecto.

⚠️  ADVERTENCIA CRÍTICA DE SEGURIDAD ⚠️
=====================================
Este archivo contiene credenciales sensibles de API almacenadas como TEXTO PLANO.

MEDIDAS DE SEGURIDAD REQUERIDAS:
1. Configurá permisos restrictivos de archivo (sólo lectura/escritura del propietario):
   Windows: icacls pyRofex_config.py /grant:r %USERNAME%:F /inheritance:r
   
2. Asegurate de que este archivo NO sea commiteado al control de versiones
   (Verificá que tu .gitignore incluya archivos de config *.py si es necesario)
   
3. Para despliegues en producción, usá variables de entorno en su lugar:
   - Configurá PYROFEX_USER, PYROFEX_PASSWORD, PYROFEX_ACCOUNT en tu entorno
   - Este archivo usará automáticamente las variables de entorno cuando estén disponibles
   
4. Rotá las credenciales regularmente y monitoreá accesos no autorizados

ALTERNATIVA: Usá variables de entorno exclusivamente configurando todos los 
valores PYROFEX_* en tu archivo .env y dejando los valores por defecto como placeholders.
=====================================
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

# Configuración de API de pyRofex - Las variables de entorno sobrescriben estos valores por defecto
ENVIRONMENT = os.getenv('PYROFEX_ENVIRONMENT', 'LIVE')
API_URL = os.getenv('PYROFEX_API_URL', 'https://api.cocos.xoms.com.ar/')
WS_URL = os.getenv('PYROFEX_WS_URL', 'wss://api.cocos.xoms.com.ar/')

# CREDENCIALES - Reemplazá con valores reales o usá variables de entorno
USER = os.getenv('PYROFEX_USER', 'REPLACE_WITH_YOUR_USERNAME')
PASSWORD = os.getenv('PYROFEX_PASSWORD', 'REPLACE_WITH_YOUR_PASSWORD')
ACCOUNT = os.getenv('PYROFEX_ACCOUNT', 'REPLACE_WITH_YOUR_ACCOUNT')


def validate_pyRofex_config():
    """
    Validar valores de configuración de pyRofex.
    Devuelve lista de errores, lista vacía si todos son válidos.
    """
    errors = []
    
    # Verificar que las URLs tengan el protocolo adecuado
    if not API_URL.startswith(('http://', 'https://')):
        errors.append(f"Protocolo de API_URL inválido: {API_URL}. Se esperaba http:// o https://")
    
    if not WS_URL.startswith(('ws://', 'wss://')):
        errors.append(f"Protocolo de WS_URL inválido: {WS_URL}. Se esperaba ws:// o wss://")
    
    # Verificar que las credenciales no sean placeholders
    placeholder_values = ['REPLACE_WITH_YOUR_USERNAME', 'REPLACE_WITH_YOUR_PASSWORD', 'REPLACE_WITH_YOUR_ACCOUNT']
    
    if USER in placeholder_values:
        errors.append("USER todavía contiene valor placeholder. Reemplazá con el nombre de usuario real o configurá la variable de entorno PYROFEX_USER")
    
    if PASSWORD in placeholder_values:
        errors.append("PASSWORD todavía contiene valor placeholder. Reemplazá con la contraseña real o configurá la variable de entorno PYROFEX_PASSWORD")
        
    if ACCOUNT in placeholder_values:
        errors.append("ACCOUNT todavía contiene valor placeholder. Reemplazá con la cuenta real o configurá la variable de entorno PYROFEX_ACCOUNT")
    
    # Verificar que las credenciales no estén vacías
    if not USER.strip():
        errors.append("USER no puede estar vacío")
        
    if not PASSWORD.strip():
        errors.append("PASSWORD no puede estar vacío")
        
    if not ACCOUNT.strip():
        errors.append("ACCOUNT no puede estar vacío")
    
    # Verificar que el entorno sea válido
    valid_environments = ['LIVE', 'REMARKET', 'DEMO']
    if ENVIRONMENT not in valid_environments:
        errors.append(f"ENVIRONMENT inválido: {ENVIRONMENT}. Se esperaba uno de: {', '.join(valid_environments)}")
    
    return errors


if __name__ == "__main__":
    # Probar configuración cuando se ejecuta directamente
    errors = validate_pyRofex_config()
    if errors:
        print("❌ Errores de configuración de pyRofex:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ La configuración de pyRofex es válida")
