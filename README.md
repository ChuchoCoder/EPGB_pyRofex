# EPGB_pyRofex - Datos de Mercado en Tiempo Real

Aplicación Python para obtener datos de mercado en tiempo real y gestionar opciones desde tu planilla de Excel.

## 📊 ¿Qué hace esta aplicación?

EPGB_pyRofex te permite:

- Obtener datos de mercado en tiempo real de opciones usando la API de Matba Rofex
- Integración directa con Excel para visualizar y analizar los datos
- Actualización automática de precios, volúmenes y otros datos de mercado
- Gestión de símbolos de opciones desde tu planilla de Excel
- Caché inteligente de instrumentos para mejor rendimiento

## 🚀 Inicio Rápido

### Requisitos previos

- Python 3.9 o superior
- Microsoft Excel (para la integración con xlwings)
- Windows (recomendado para la integración con Excel)

### Instalación

#### Opción 1: Instalación moderna (recomendada)

```bash
# Clonar el repositorio
git clone https://github.com/ChuchoCoder/EPGB_pyRofex.git
cd EPGB_pyRofex

# Crear y activar un entorno virtual (Windows)
python -m venv .venv
.venv\Scripts\activate

# Instalar el paquete en modo editable
pip install -e .
```

#### Opción 2: Instalación manual

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual (Windows)
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración

1. Copiá la plantilla y creá el archivo de configuración:

```bash
copy .env.example .env
```

2. Editá el archivo `.env` con tus credenciales:

```env
PYROFEX_USER=tu_usuario
PYROFEX_PASSWORD=tu_contraseña
PYROFEX_ACCOUNT=tu_cuenta
```

> **Importante:** Nunca compartas ni subas tu archivo `.env` con credenciales reales.

3. (Opcional) Generá módulos de configuración faltantes:

```bash
python tools/create_configs.py
```

### Ejecutar la aplicación

```bash
# Ejecutar mediante el comando instalado
epgb-options

# O en forma de módulo (equivalente)
python -m epgb_options.main
```

## 🧪 Validación del sistema

Verificá que tu instalación esté correcta ejecutando:

```bash
# Validación completa del sistema (estructura, importaciones, entry points)
python tools/validate_system.py

# Validación del quickstart (dependencias, transformaciones, integración)
python tools/validate_quickstart.py
```

`validate_system.py` verifica:
- ✅ Importaciones y estructura del paquete `src.epgb_options`
- ✅ Disponibilidad del comando `epgb-options`
- ✅ Presencia de módulos de configuración y archivos necesarios

`validate_quickstart.py` verifica:
- ✅ Instalación de dependencias (pyRofex, xlwings, pandas)
- ✅ Acceso al archivo Excel `EPGB OC-DI - Python.xlsb`
- ✅ Configuración del entorno y credenciales
- ✅ Lógica de transformación de símbolos (18 casos de prueba)
- ✅ Validación de datos de mercado
- ✅ Integración de módulos Excel y Market Data
- ✅ Cache inteligente de instrumentos para mejor rendimiento

## 📁 Estructura de archivos

Los archivos y recursos principales se encuentran en la raíz del proyecto o en las subcarpetas indicadas:

```text
EPGB_pyRofex/
├── .env.example                ← Plantilla de configuración
├── .env                        ← Tu configuración (creala a partir de la plantilla)
├── "EPGB OC-DI - Python.xlsb"  ← Planilla de Excel
├── src/                        ← Código de la aplicación
└── data/cache/                 ← Caché automático (no tocar)
```

> **Importante:** Copiá `.env.example` a `.env` y completá tus credenciales. El archivo Excel debe estar en la raíz del proyecto.

## 📋 Solución de problemas

### Problemas comunes

1) Errores de importación

```bash
# Reinstalá el paquete
pip install -e .
```

2) Problemas de conexión con Excel

- Asegurate de que Excel esté instalado y accesible
- Verificá los permisos del archivo Excel
- Comprobá que xlwings esté correctamente instalado

3) Errores de autenticación con la API

Síntomas:

```
❌ AUTHENTICATION FAILED
🔐 PyRofex rejected your credentials
Error details: Authentication fails. Incorrect User or Password
```

Soluciones sugeridas:

- Verificá tus credenciales en la plataforma de tu proveedor de pyRofex. Las credenciales pueden expirar o cambiar.
- Actualizá el archivo `.env` con tus credenciales:

```bash
# Editá el archivo .env en la raíz del proyecto
PYROFEX_USER=tu_usuario
PYROFEX_PASSWORD=tu_contraseña
PYROFEX_ACCOUNT=tu_cuenta
```

- Validá la configuración ejecutando:

```bash
python tools/validate_system.py
```

4) La aplicación no encuentra el archivo `.env`

Si ves un error como "No se encontró el archivo .env":

1. Verificá que el archivo `.env` esté en la raíz del proyecto:

```bash
dir .env
```

2. Si no existe, copialo desde la plantilla:

```bash
copy .env.example .env
```

3. Editá el archivo `.env` con tus credenciales reales.

### Obtener ayuda

1. Ejecutá el validador del sistema:

```bash
python tools/validate_system.py
```

2. Verificá tu configuración:

- Revisá que el archivo `.env` exista en la raíz del proyecto y tenga las credenciales correctas
- Confirmá que el entorno virtual esté activado
- Asegurate de que Excel esté cerrado antes de ejecutar la aplicación

## 🔒 Consideraciones de seguridad

- Nunca subas tu archivo `.env`: contiene credenciales sensibles
- Establecé permisos apropiados en los archivos de configuración
- Rotá tus credenciales regularmente para mayor seguridad
- El archivo `.env` está excluido del control de versiones por defecto

## 💡 Dependencias principales

Esta aplicación utiliza:

| Paquete | Propósito |
|---------|-----------|
| pyRofex | Integración con la API de Matba Rofex |
| xlwings | Integración con Microsoft Excel |
| pandas  | Manipulación y análisis de datos |
| python-dotenv | Gestión de variables de entorno |

## 👨‍💻 ¿Querés contribuir?

Si sos desarrollador y querés contribuir al proyecto, consultá la guía para desarrolladores en [CONTRIBUTING.md](CONTRIBUTING.md).

## 🆘 Soporte

Para problemas y consultas:

- Ejecutá `python tools/validate_system.py` para validar tu configuración
- Revisá los módulos en `src/epgb_options/config/`
- Asegurate de que el archivo `.env` exista en la raíz del proyecto con las credenciales correctas
- Confirmá que el entorno virtual esté activado
