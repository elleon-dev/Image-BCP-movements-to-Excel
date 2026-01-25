# Guía de Uso - Extractor de Movimientos Bancarios

## 🚀 Inicio Rápido

### 1. Configurar API Key (IMPORTANTE)

Edita el archivo `.env` y agrega tu OpenAI API key:

```bash
OPENAI_API_KEY=sk-tu-api-key-aqui
```

Para obtener tu API key:

- Ve a https://platform.openai.com/api-keys
- Crea una nueva API key
- Copia y pega en el archivo .env

### 2. Activar Entorno Virtual

```bash
source venv/bin/activate
```

O usa el script rápido:

```bash
source activate.sh
```

### 3. Preparar Imágenes

Opción A: Coloca tus capturas de pantalla en la carpeta `input_images/`
Opción B: Usa rutas directas a tus imágenes

### 4. Ejecutar el Programa

**Procesar una imagen:**

```bash
python main.py screenshot.jpg
```

**Procesar múltiples imágenes:**

```bash
python main.py img1.jpg img2.jpg img3.jpg
```

**Procesar todas las imágenes de una carpeta:**

```bash
python main.py input_images/*.jpg
```

### 5. Revisar Resultados

El archivo Excel se generará en: `output/movimientos_bancarios.xlsx`

---

## 📋 Ejemplo Completo

```bash
# 1. Activar entorno
source venv/bin/activate

# 2. Procesar imágenes de agosto
python main.py agosto_1.jpg agosto_2.jpg agosto_3.jpg

# 3. Procesar imágenes de septiembre (se agregarán al Excel existente)
python main.py septiembre_1.jpg septiembre_2.jpg

# 4. Ver el Excel generado
open output/movimientos_bancarios.xlsx
```

---

## 🔍 Características Especiales

### Omisión de Transacciones Marcadas

Las transacciones con overlay rojizo se omiten automáticamente. GPT-4o detecta visualmente estas marcas.

### Acumulación de Datos

- Primera ejecución: Crea el archivo Excel con las transacciones
- Ejecuciones siguientes: Agrega nuevas transacciones al Excel existente
- Los duplicados se eliminan automáticamente

### Organización por Meses

El Excel tendrá una hoja por cada mes encontrado en las imágenes:

- Agosto 2025
- Septiembre 2025
- Octubre 2025
- etc.

### Datos Persistentes

Las transacciones se guardan en `transactions_data.json` para:

- Evitar reprocesar imágenes
- Mantener histórico
- Permitir agregar imágenes incrementalmente

---

## ⚙️ Configuración Opcional

### Información de Cuenta

Edita `.env` para personalizar el encabezado del Excel:

```bash
ACCOUNT_TYPE=Cuenta de Ahorros
ACCOUNT_NUMBER=1234567890
BANK_NAME=BCP
```

El Excel mostrará:

```
Agosto 2025 - Cuenta de Ahorros N° 1234567890 - BCP
```

---

## 🐛 Solución de Problemas

### Error: "OPENAI_API_KEY no configurado"

- Asegúrate de editar el archivo `.env` (no `.env.example`)
- Verifica que tu API key sea válida
- Quita las comillas si las agregaste

### Error: "No se extrajeron transacciones"

- Verifica que la imagen sea clara y legible
- Asegúrate de que la imagen contenga transacciones
- Si todas tienen overlay rojo, ninguna se extraerá

### Error: "Imagen no encontrada"

- Usa rutas absolutas o relativas correctas
- Verifica que el archivo exista
- Intenta: `ls -l tu_imagen.jpg`

### Las transacciones aparecen duplicadas

- El programa elimina duplicados automáticamente
- Si persiste, borra `transactions_data.json` y vuelve a ejecutar

---

## 💰 Costos Estimados

| Cantidad de Imágenes | Costo Aproximado (USD) |
| -------------------- | ---------------------- |
| 10 imágenes          | $0.01 - $0.03          |
| 100 imágenes         | $0.10 - $0.30          |
| 1,000 imágenes       | $1.00 - $3.00          |

Modelo usado: GPT-4o (~$0.001-0.003 por imagen)

---

## 📁 Estructura de Archivos

```
image to json/
├── main.py                          # Programa principal
├── image_processor.py               # Extracción con GPT-4o
├── excel_exporter.py                # Generación de Excel
├── .env                             # Configuración (API key)
├── transactions_data.json           # Datos acumulados
├── input_images/                    # Carpeta para imágenes
├── output/
│   └── movimientos_bancarios.xlsx   # Excel generado
└── venv/                            # Entorno virtual
```

---

## 🔄 Workflow Típico

1. **Primera vez:**
   - Configurar .env con API key
   - Procesar imágenes del primer mes
   - Revisar Excel generado

2. **Agregar más meses:**
   - Procesar nuevas imágenes
   - El Excel se actualiza automáticamente
   - Cada mes aparece en una hoja separada

3. **Mantenimiento:**
   - Si necesitas empezar de cero: borra `transactions_data.json`
   - Para limpiar: `rm transactions_data.json output/*.xlsx`
   - Para ver datos: `cat transactions_data.json | python -m json.tool`

---

## 📞 Soporte

Si encuentras problemas:

1. Verifica que el entorno virtual esté activado
2. Asegúrate de tener la API key configurada
3. Revisa que las imágenes sean claras y legibles
4. Verifica tu saldo en OpenAI: https://platform.openai.com/usage
