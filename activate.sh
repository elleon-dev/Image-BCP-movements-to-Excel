#!/bin/bash
# Script de activación rápida del entorno virtual

cd "/Users/noel/Desktop/image to json"
source venv/bin/activate

echo "✅ Entorno virtual activado"
echo "📁 Directorio: $(pwd)"
echo ""
echo "Comandos disponibles:"
echo "  python main.py <imagen.jpg>          - Procesar una imagen"
echo "  python main.py *.jpg                 - Procesar todas las imágenes"
echo "  python main.py input_images/*.jpg    - Procesar imágenes de input_images/"
echo ""
echo "Archivos importantes:"
echo "  .env                                 - Configuración (API key)"
echo "  transactions_data.json               - Datos acumulados"
echo "  output/movimientos_bancarios.xlsx    - Excel generado"
echo ""
