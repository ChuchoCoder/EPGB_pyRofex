# EPGB Options - Datos de Mercado en Tiempo Real

Aplicación Python para obtener da- **Gestión de símbolos** de opciones desde tu planilla de Excel> **Nota Importante**: Esta lógica está basada en análisis de 7,590 instrumentos reales del cache de pyRofex (93% con prefijo MERV, 7% sin prefijo).

## 🔍 Validación del Sistema

Verificá que tu instalación esté correcta ejecutando:

```bash
# Validación completa del sistema (estructura, importaciones, entry points)
python tools/validate_system.py

# Validación del quickstart (dependencias, transformaciones, integración)
python tools/validate_quickstart.py
```

**validate_system.py** valida:
- ✅ Importaciones y estructura del paquete `src.epgb_options`
- ✅ Disponibilidad del comando `epgb-options`
- ✅ Presencia de módulos de configuración y archivos necesarios

**validate_quickstart.py** valida:
- ✅ Instalación de dependencias (pyRofex, xlwings, pandas)
- ✅ Acceso al archivo Excel `EPGB OC-DI - Python.xlsb`
- ✅ Configuración del entorno y credenciales
- ✅ Lógica de transformación de símbolos (18 test cases)
- ✅ Validación de datos de mercado
- ✅ Integración de módulos Excel y Market Data
ligente** de instrumentos para mejor rendimiento

## 📁 Estructura de Archivos

Los archivos que necesitás están todos en la raíz del proyecto:

```text
EPGB_pyRofex/
├── .env.example                ← Plantilla de configuración
├── .env                        ← Tu configuración (creala vos)
├── EPGB OC-DI - Python.xlsb   ← Planilla de Excel
├── src/                        ← Código de la aplicación
└── data/cache/                 ← Cache automático (no tocar)
```

> **Importante:** Tanto `.env` como el archivo Excel deben estar en la raíz del proyecto, NO en subcarpetas.

## 🔧 Validación del Sistemade mercado de opciones en tiempo real con integración a Excel usando la API de pyRofex.

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.9 o superior
- Microsoft Excel (para la integración con xlwings)
- Windows (recomendado para la integración con Excel)

### Instalación

#### Opción 1: Instalación Moderna (Recomendada)

```bash
# Clonar el repositorio
git clone https://github.com/ChuchoCoder/EPGB_pyRofex.git
cd EPGB_pyRofex

# Crear y activar un entorno virtual (Windows)
python -m venv .venv
.venv\Scripts\activate

# Instalar el paquete
pip install -e .
```

#### Opción 2: Instalación Manual

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual (Windows)
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración

1. **Copiá el archivo de configuración de ejemplo:**

   ```bash
   copy .env.example .env
   ```

   > **Nota:** Tanto `.env.example` (plantilla) como tu `.env` (configuración) están en la raíz del proyecto.

2. **Editá el archivo `.env` con tus credenciales:**

   ```env
   PYROFEX_USER=tu_usuario
   PYROFEX_PASSWORD=tu_contraseña
   PYROFEX_ACCOUNT=tu_cuenta
   ```

   > **Importante:** Nunca compartas ni subas tu archivo `.env` con tus credenciales reales.

3. **(Opcional) Generá módulos de configuración faltantes:**

   ```bash
   python tools/create_configs.py
   ```

### Ejecutar la Aplicación

```bash
# Ejecutar mediante el comando instalado
epgb-options

# O en forma de módulo (equivalente)
python -m epgb_options.main
```

## 📊 ¿Qué Hace Esta Aplicación?

EPGB Options te permite:

- **Obtener datos de mercado en tiempo real** de opciones usando la API de Matba Rofex
- **Integración directa con Excel** para visualizar y analizar los datos
- **Actualización automática** de precios, volúmenes y otros datos de mercado
- **Gestión de símbolos** de opciones desde tu planilla de Excel
- **Cache inteligente** de instrumentos para mejor rendimiento

### 🔄 Transformación Automática de Símbolos

La aplicación transforma automáticamente los símbolos basándose en análisis de 7,590 instrumentos reales de la API pyRofex:

**Reglas de Transformación:**

**1. Prefijo "MERV - XMEV -"** (93% de los símbolos lo tienen):
- ✅ **SE AGREGA** a: acciones, bonos, cedears, cauciones, letras, ONs del mercado MERV
- ✅ **EXCEPCIÓN ESPECIAL**: `I.MERVAL` SÍ lleva el prefijo
- ❌ **NO SE AGREGA** a:
  - Opciones ROS (295 símbolos): `SOJ.ROS/MAY26 292 C`
  - Futuros ROS (52 símbolos): `MAI.ROS/MAR26`
  - Futuros/Opciones Dólar (84 símbolos): `DLR/FEB26`, `DLR/OCT25 1520 C`
  - Índices (4 símbolos): `I.BTC`, `I.SOJCONT`, `I.TRICONT`, `I.RFX20`
  - Otros mercados internacionales (~60 símbolos): `ORO/ENE26`, `WTI/NOV25`, `.CME/`, `.BRA/`
  - Mercado disponible: `GIR.ROS.P/DISPO`

**2. Sufijo de Liquidación**:
- ✅ Reemplaza ` - spot` por ` - CI` (Contado Inmediato)
- ✅ **Agrega ` - 24hs` por defecto** solo a símbolos MERV sin sufijo
- ✅ Preserva sufijos existentes: ` - 24hs`, ` - 48hs`, ` - 72hs`, ` - CI`, etc.
- ❌ **NO agrega sufijo por defecto** a: cauciones (PESOS - XD), índices, opciones, futuros

**Ejemplos de Transformación:**

| Tipo | Símbolo en Excel | Transformación | Resultado pyRofex |
|------|------------------|----------------|-------------------|
| **MERV** | `YPFD` | Prefijo + sufijo por defecto | `MERV - XMEV - YPFD - 24hs` |
| **MERV** | `YPFD - 24hs` | Prefijo + sufijo preservado | `MERV - XMEV - YPFD - 24hs` |
| **MERV** | `GGAL - spot` | Prefijo + spot→CI | `MERV - XMEV - GGAL - CI` |
| **MERV** | `ALUA - 48hs` | Prefijo + sufijo preservado | `MERV - XMEV - ALUA - 48hs` |
| **MERV** | `PESOS - 3D` | Prefijo (caución, sin sufijo) | `MERV - XMEV - PESOS - 3D` |
| **MERV** | `I.MERVAL` | Prefijo (excepción especial) | `MERV - XMEV - I.MERVAL` |
| **ROS** | `SOJ.ROS/MAY26 292 C` | Sin cambios (opción ROS) | `SOJ.ROS/MAY26 292 C` |
| **ROS** | `MAI.ROS/MAR26` | Sin cambios (futuro ROS) | `MAI.ROS/MAR26` |
| **DLR** | `DLR/FEB26` | Sin cambios (futuro dólar) | `DLR/FEB26` |
| **DLR** | `DLR/OCT25 1520 C` | Sin cambios (opción dólar) | `DLR/OCT25 1520 C` |
| **Índices** | `I.BTC` | Sin cambios (índice) | `I.BTC` |
| **Índices** | `I.SOJCONT` | Sin cambios (índice) | `I.SOJCONT` |
| **Otros** | `ORO/ENE26` | Sin cambios (futuro oro) | `ORO/ENE26` |
| **Otros** | `WTI/NOV25` | Sin cambios (futuro petróleo) | `WTI/NOV25` |
| **Otros** | `GIR.ROS.P/DISPO` | Sin cambios (mercado DISPO) | `GIR.ROS.P/DISPO` |

> **Nota Importante**: Esta lógica está basada en análisis de 7,590 instrumentos reales del cache de pyRofex (93% con prefijo MERV, 7% sin prefijo).

## � Validación del Sistema

Verificá que tu instalación esté correcta ejecutando:

```bash
python tools/validate_system.py
```

Este comando valida:

- ✅ Importaciones y estructura del paquete
- ✅ Disponibilidad del comando `epgb-options`
- ✅ Presencia de módulos de configuración y archivos necesarios

## 📋 Solución de Problemas

### Problemas Comunes

#### 1. Errores de Importación

```bash
# Reinstalá el paquete
pip install -e .
```

#### 2. Problemas de Conexión con Excel

- Asegurate de que Excel esté instalado y accesible
- Verificá los permisos del archivo Excel
- Comprobá que xlwings esté correctamente instalado

#### 3. Errores de Autenticación con la API

**Síntomas:**
```
❌ AUTHENTICATION FAILED
🔐 PyRofex rejected your credentials
Error details: Authentication fails. Incorrect User or Password
```

**Soluciones:**

1. **Verificá tus credenciales:**
   - Ingresá a https://www.cocos.xoms.com.ar/ y verificá que tu usuario/contraseña sean correctos
   - Las credenciales pueden expirar o cambiar

2. **Actualizá el archivo `.env`:**
   ```bash
   # Editá el archivo .env en la raíz del proyecto
   PYROFEX_USER=tu_usuario
   PYROFEX_PASSWORD=tu_contraseña
   PYROFEX_ACCOUNT=tu_cuenta
   ```

3. **Validá la configuración:**
   ```bash
   python tools/validate_system.py
   ```

**Nota de Seguridad:** 
- ⚠️ Nunca subas el archivo `.env` a git
- El archivo `.env` está incluido en `.gitignore` por defecto
- Usa el archivo `.env.example` como plantilla (sin credenciales reales)

#### 4. La aplicación no encuentra el archivo `.env`

Si ves un error como "No se encontró el archivo .env":

1. Verificá que el archivo `.env` esté en la raíz del proyecto:

   ```bash
   dir .env
   ```

2. Si no existe, copialo desde la plantilla:

   ```bash
   copy .env.example .env
   ```

3. Editá el archivo `.env` con tus credenciales reales

### Obtener Ayuda

1. **Ejecutá el validador del sistema:**

   ```bash
   python tools/validate_system.py
   ```

2. **Verificá tu configuración:**

   - Revisá que el archivo `.env` exista en la raíz del proyecto y tenga las credenciales correctas
   - Confirmá que el entorno virtual esté activado
   - Asegurate de que Excel esté cerrado antes de ejecutar la aplicación

## 🔒 Consideraciones de Seguridad

- **Nunca subas tu archivo `.env`** - Contiene credenciales sensibles
- **Establecé permisos apropiados** en los archivos de configuración
- **Rotá tus credenciales regularmente** para mayor seguridad
- El archivo `.env` está excluido del control de versiones por seguridad

## 💡 Dependencias Principales

Esta aplicación utiliza:

| Paquete | Propósito |
|---------|-----------|
| pyRofex | Integración con la API de Matba Rofex |
| xlwings | Integración con Microsoft Excel |
| pandas | Manipulación y análisis de datos |
| python-dotenv | Gestión de variables de entorno |

## 👨‍💻 ¿Querés Contribuir?

Si sos desarrollador y querés contribuir al proyecto, consultá la guía para desarrolladores en [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT.

## 🆘 Soporte

Para problemas y consultas:

- Ejecutá `python tools/validate_system.py` para validar tu configuración
- Revisá los módulos en `src/epgb_options/config/`
- Asegurate de que el archivo `.env` exista en la raíz del proyecto con las credenciales correctas
- Confirmá que el entorno virtual esté activado
