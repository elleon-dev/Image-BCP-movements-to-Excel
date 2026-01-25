# Bank Transaction Image to Excel Extractor

Aplicación Python que extrae automáticamente movimientos bancarios de capturas de pantalla usando GPT-4o Vision API.

## Características

- 🔍 Extrae transacciones de imágenes de aplicaciones bancarias móviles
- 🚫 Omite automáticamente transacciones marcadas con overlay rojizo
- 📊 Exporta a Excel con formato profesional
- 🗓️ Organiza por meses en hojas separadas
- 🔄 Soporta múltiples imágenes de diferentes meses
- 📈 Ordena transacciones de más reciente a más antigua

## Requisitos

- Python 3.8+
- OpenAI API Key (GPT-4o access)

## Instalación

1. Crear entorno virtual e instalar dependencias:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configurar API key:

```bash
cp .env.example .env
# Editar .env y agregar tu OPENAI_API_KEY
```

3. (Opcional) Usar script de activación rápida:

```bash
source activate.sh
```

## Uso

### Procesar una imagen

```bash
python main.py path/to/screenshot.jpg
```

### Procesar múltiples imágenes

```bash
python main.py image1.jpg image2.jpg image3.jpg
```

### Procesar todas las imágenes en una carpeta

```bash
python main.py input_images/*.jpg
```

## Estructura de Datos

Las transacciones se extraen con los siguientes campos:

- `date`: Fecha de la transacción (DD/MM/YYYY)
- `name`: Descripción/nombre del movimiento
- `amount`: Monto (negativo para cargos, positivo para abonos)
- `type`: "cargo" o "abono"
- `month`: Mes y año (ej: "Agosto 2025")

## Salida

El archivo Excel generado incluye:

- Una hoja por mes
- Título con información de cuenta
- Transacciones ordenadas por fecha descendente
- Formato de moneda para montos

Archivo de salida: `output/movimientos_bancarios.xlsx`

## Costo Estimado

- GPT-4o Vision: ~$0.001-0.003 USD por imagen
- Aproximadamente $1-3 USD por cada 1000 imágenes procesadas
