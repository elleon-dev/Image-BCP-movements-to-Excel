"""
Aplicación principal para extraer movimientos bancarios de imágenes y exportar a Excel.
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

try:
    from image_processor_local import LocalImageProcessor as ImageProcessor
    USE_LOCAL = True
except ImportError:
    from image_processor import ImageProcessor
    USE_LOCAL = False

from excel_exporter import ExcelExporter


# Ruta del archivo de datos persistentes
DATA_FILE = "transactions_data.json"


def load_existing_data() -> List[Dict[str, Any]]:
    """
    Carga transacciones existentes del archivo JSON.
    
    Returns:
        Lista de transacciones previamente guardadas
    """
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error al cargar datos existentes: {e}")
            return []
    return []


def save_data(transactions: List[Dict[str, Any]]):
    """
    Guarda transacciones en archivo JSON.
    
    Args:
        transactions: Lista de transacciones a guardar
    """
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, ensure_ascii=False, indent=2)
        print(f"💾 Datos guardados en {DATA_FILE}")
    except Exception as e:
        print(f"❌ Error al guardar datos: {e}")


def deduplicate_transactions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Elimina transacciones duplicadas basándose en (fecha, nombre, monto, moneda).
    Cada transacción mantiene su ID único, pero no se permiten duplicados de datos.
    
    Args:
        transactions: Lista de transacciones
        
    Returns:
        Lista de transacciones sin duplicados
    """
    seen = set()
    unique = []
    
    for transaction in transactions:
        # Crear clave única basada en los datos de la transacción (no el ID)
        key = (
            transaction.get('date', ''),
            transaction.get('name', ''),
            transaction.get('amount', 0),
            transaction.get('currency', 'S/')
        )
        
        if key not in seen:
            seen.add(key)
            unique.append(transaction)
    
    duplicates_removed = len(transactions) - len(unique)
    if duplicates_removed > 0:
        print(f"🔄 Duplicados eliminados: {duplicates_removed}")
    
    return unique


def print_banner():
    """Imprime banner de la aplicación."""
    print("\n" + "="*70)
    print("  📊 EXTRACTOR DE MOVIMIENTOS BANCARIOS - Imagen a Excel")
    print("="*70 + "\n")


def print_usage():
    """Imprime instrucciones de uso."""
    print("Uso:")
    print("  python main.py <imagen1> [imagen2] [imagen3] ...")
    print("\nEjemplos:")
    print("  python main.py screenshot.jpg")
    print("  python main.py img1.jpg img2.jpg img3.jpg")
    print("  python main.py input_images/*.jpg")
    print("\nNota: Asegúrate de configurar OPENAI_API_KEY en el archivo .env")


def main():
    """Función principal de la aplicación."""
    print_banner()
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Determinar si usar procesador local o API
    if USE_LOCAL:
        print("🆓 Usando OCR Local (EasyOCR) - Sin costos de API\n")
        processor = ImageProcessor()
    else:
        # Verificar API key para procesador con API
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your-api-key-here':
            print("❌ Error: OPENAI_API_KEY no configurado")
            print("\nPasos para configurar:")
            print("1. Copia .env.example a .env")
            print("2. Edita .env y agrega tu OpenAI API key")
            print("3. Ejecuta nuevamente el programa")
            print("\n💡 Tip: Para usar OCR local sin API, instala:")
            print("    pip install easyocr opencv-python")
            return 1
        
        print("☁️  Usando GPT-4o Vision API\n")
        processor = ImageProcessor(api_key)
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("❌ Error: No se especificaron imágenes para procesar\n")
        print_usage()
        return 1
    
    # Obtener rutas de imágenes
    image_paths = sys.argv[1:]
    
    # Verificar que las imágenes existen
    valid_paths = []
    for path in image_paths:
        if os.path.exists(path):
            valid_paths.append(path)
        else:
            print(f"⚠️  Imagen no encontrada: {path}")
    
    if not valid_paths:
        print("\n❌ Error: No se encontraron imágenes válidas")
        return 1
    
    print(f"📁 Imágenes a procesar: {len(valid_paths)}\n")
    
    # Procesar imágenes
    print("🔄 Iniciando extracción de transacciones...\n")
    new_transactions = processor.process_multiple_images(valid_paths)
    
    if not new_transactions:
        print("\n⚠️  No se extrajeron transacciones de las imágenes")
        return 0
    
    # Cargar transacciones existentes
    existing_transactions = load_existing_data()
    print(f"\n📂 Transacciones existentes: {len(existing_transactions)}")
    
    # Combinar y eliminar duplicados
    all_transactions = existing_transactions + new_transactions
    all_transactions = deduplicate_transactions(all_transactions)
    
    print(f"📊 Total de transacciones únicas: {len(all_transactions)}")
    
    # Guardar datos actualizados
    save_data(all_transactions)
    
    # Obtener información de cuenta
    account_type = os.getenv('ACCOUNT_TYPE', 'Cuenta')
    account_number = os.getenv('ACCOUNT_NUMBER', '')
    bank_name = os.getenv('BANK_NAME', 'Banco')
    
    # Exportar a Excel
    print("\n📈 Generando archivo Excel...\n")
    exporter = ExcelExporter(
        account_type=account_type,
        account_number=account_number,
        bank_name=bank_name
    )
    
    output_path = "output/movimientos_bancarios.xlsx"
    exporter.create_excel(all_transactions, output_path)
    
    # Resumen final
    print("\n" + "="*70)
    print("  ✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*70)
    print(f"\n📄 Archivo Excel: {output_path}")
    print(f"💾 Datos guardados: {DATA_FILE}")
    print(f"📊 Total transacciones: {len(all_transactions)}")
    print(f"🆕 Nuevas transacciones: {len(new_transactions)}")
    print("\n💡 Tip: Puedes agregar más imágenes ejecutando el programa nuevamente")
    print("         Las nuevas transacciones se agregarán al archivo existente.\n")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
