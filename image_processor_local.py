"""
Módulo para procesar imágenes de movimientos bancarios usando OCR local.
Detecta correctamente el layout: nombre arriba, fecha y monto abajo.
Omite transacciones con overlay rojizo.
SIN COSTOS DE API - 100% Local y Gratuito
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
import re
from datetime import datetime
import easyocr
import uuid


class LocalImageProcessor:
    """Procesador de imágenes bancarias con OCR local."""
    
    def __init__(self):
        """Inicializa el procesador de imágenes local."""
        print("🔄 Inicializando EasyOCR (puede tardar un momento la primera vez)...")
        self.reader = easyocr.Reader(['es', 'en'], gpu=False)
        print("✅ EasyOCR inicializado correctamente")
    
    def detect_red_overlay(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> bool:
        """
        Detecta si un área de la imagen tiene overlay rojizo.
        
        Args:
            image: Imagen en formato BGR
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            True si tiene overlay rojo, False si no
        """
        x1, y1, x2, y2 = [int(coord) for coord in bbox]
        
        # Extraer región de interés
        roi = image[y1:y2, x1:x2]
        
        if roi.size == 0:
            return False
        
        # Convertir a HSV para mejor detección de color
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Definir rangos de rojo en HSV (el rojo está en dos rangos)
        # Rango 1: rojo oscuro/marron rojizo
        lower_red1 = np.array([0, 40, 40])
        upper_red1 = np.array([10, 255, 255])
        
        # Rango 2: rojo brillante
        lower_red2 = np.array([160, 40, 40])
        upper_red2 = np.array([180, 255, 255])
        
        # Crear máscaras
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask1 + mask2
        
        # Calcular porcentaje de píxeles rojos
        red_percentage = np.sum(red_mask > 0) / red_mask.size
        
        # Si más del 15% del área es roja, considerarla marcada
        return red_percentage > 0.15
    
    def parse_date(self, date_str: str, month_context: str = None) -> str:
        """
        Parsea diferentes formatos de fecha.
        
        Args:
            date_str: String con la fecha
            month_context: Contexto del mes (ej: "Agosto 2025")
            
        Returns:
            Fecha en formato DD/MM/YYYY
        """
        # Limpiar string
        date_str = date_str.strip()
        
        # Corrección de errores comunes de OCR en días
        # "71" -> "11", "72" -> "12", etc.
        date_str = re.sub(r'\b7([0-9])\b', r'1\1', date_str)
        
        # Patrón: "31 Agosto" o solo "31"
        day_match = re.search(r'\b(\d{1,2})\b', date_str)
        
        if day_match:
            day = day_match.group(1).zfill(2)
            
            # Buscar mes en el string
            meses = {
                'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
            }
            
            month = None
            year = None
            
            # Buscar mes en date_str
            for mes_name, mes_num in meses.items():
                if mes_name.lower() in date_str.lower():
                    month = mes_num
                    break
            
            # Buscar año
            year_match = re.search(r'\b(20\d{2})\b', date_str)
            if year_match:
                year = year_match.group(1)
            
            # Si no encontramos mes/año, usar el contexto
            if not month or not year:
                if month_context:
                    # Extraer mes y año del contexto (ej: "Agosto 2025")
                    for mes_name, mes_num in meses.items():
                        if mes_name.lower() in month_context.lower():
                            month = mes_num
                            break
                    
                    year_match = re.search(r'\b(20\d{2})\b', month_context)
                    if year_match:
                        year = year_match.group(1)
            
            # Si aún no tenemos mes/año, usar fecha actual
            if not month:
                month = datetime.now().strftime('%m')
            if not year:
                year = datetime.now().strftime('%Y')
            
            return f"{day}/{month}/{year}"
        
        return ""
    
    def parse_amount(self, amount_str: str) -> Tuple[float, str, str]:
        """
        Extrae monto, determina tipo (cargo/abono) y detecta moneda.
        
        Args:
            amount_str: String con el monto (ej: "S/ -50.00", "$ 145.25", "Sl-35.00")
            
        Returns:
            Tupla (monto, tipo, moneda) donde tipo es "cargo" o "abono" y moneda es "S/" o "$"
        """
        # Detectar moneda antes de limpiar
        moneda = "S/"  # Por defecto soles
        if '$' in amount_str:
            moneda = "$"
        elif 'S/' in amount_str or 's/' in amount_str or 'Sl' in amount_str or 'sl' in amount_str or 'SI' in amount_str or '5/' in amount_str:
            moneda = "S/"
        
        # Limpiar string - manejar variaciones de OCR (S/, Sl, SI, 5/, $)
        amount_str = amount_str.replace('S/', '').replace('s/', '').replace('Sl', '').replace('sl', '').replace('SI', '').replace('5/', '').replace('$', '').strip()
        
        # Buscar número con posible signo negativo y separador de miles
        # Capturar formato: -4,900.00 o -4900.00 o 4,900.00
        amount_match = re.search(r'(-?\s*\d{1,3}(?:[.,]\d{3})*[.,]\d+|-?\s*\d+[.,]\d+|-?\s*\d+)', amount_str)
        
        if amount_match:
            amount_text = amount_match.group(1).replace(' ', '')
            
            # Manejar separador de miles: si hay comas antes del último punto/coma, es separador de miles
            # Formato peruano: 4,900.00 (coma = miles, punto = decimales)
            if ',' in amount_text and '.' in amount_text:
                # Si coma viene antes del punto, coma es separador de miles
                if amount_text.rfind(',') < amount_text.rfind('.'):
                    amount_text = amount_text.replace(',', '')  # Quitar separador de miles
            elif ',' in amount_text:
                # Solo coma: si está en posición de miles (ej: 4,900), es separador
                # Si está al final (ej: 50,45), es decimal
                parts = amount_text.split(',')
                if len(parts[-1]) == 2:  # Es decimal (ej: 50,45)
                    amount_text = amount_text.replace(',', '.')
                elif len(parts[-1]) == 3:  # Es separador de miles (ej: 4,900)
                    amount_text = amount_text.replace(',', '')
            
            try:
                amount = float(amount_text)
                tipo = "cargo" if amount < 0 else "abono"
                return amount, tipo, moneda
            except ValueError:
                pass
        
        return 0.0, "cargo", moneda
    
    def extract_month_year(self, image_path: str, ocr_results: List) -> str:
        """
        Extrae el mes y año del encabezado de la imagen o de las fechas detectadas.
        
        Args:
            image_path: Ruta a la imagen
            ocr_results: Resultados del OCR
            
        Returns:
            String con mes y año (ej: "Agosto 2025")
        """
        # Buscar en la parte superior de la imagen
        for detection in ocr_results[:10]:  # Revisar primeras 10 detecciones
            text = detection[1].strip()
            
            # Buscar patrón de mes y año en español
            meses_pattern = r'(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)\s*(20\d{2})'
            match = re.search(meses_pattern, text, re.IGNORECASE)
            
            if match:
                return f"{match.group(1).capitalize()} {match.group(2)}"
        
        # Si no encontramos en el header, buscar en las fechas del contenido
        meses_es = {
            'enero': 'Enero', 'febrero': 'Febrero', 'marzo': 'Marzo', 'abril': 'Abril',
            'mayo': 'Mayo', 'junio': 'Junio', 'julio': 'Julio', 'agosto': 'Agosto',
            'septiembre': 'Septiembre', 'octubre': 'Octubre', 'noviembre': 'Noviembre', 'diciembre': 'Diciembre'
        }
        
        # Buscar menciones de meses en el contenido
        for detection in ocr_results:
            text = detection[1].strip().lower()
            for mes_lower, mes_proper in meses_es.items():
                if mes_lower in text:
                    # Buscar año cercano
                    year_match = re.search(r'20\d{2}', detection[1])
                    if year_match:
                        return f"{mes_proper} {year_match.group(0)}"
                    # Si no hay año, usar 2025 por defecto (año de las imágenes)
                    return f"{mes_proper} 2025"
        
        # Si no encontramos, intentar extraer de nombre de archivo
        filename = Path(image_path).stem.lower()
        for mes_lower, mes_proper in meses_es.items():
            if mes_lower in filename:
                # Buscar año en filename
                year_match = re.search(r'20\d{2}', filename)
                year = year_match.group(0) if year_match else "2025"
                return f"{mes_proper} {year}"
        
        # Default: usar el mes más común en las fechas detectadas
        # Buscar todas las fechas en formato DD Mes
        for detection in ocr_results:
            text = detection[1].strip()
            match = re.search(r'\d{1,2}\s+(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)', text, re.IGNORECASE)
            if match:
                return f"{match.group(1).capitalize()} 2025"
        
        # Último recurso: mes actual
        return datetime.now().strftime('%B %Y')
    
    def group_transaction_elements(self, detections: List, image_height: int, image_width: int) -> List[Dict[str, Any]]:
        """
        Agrupa elementos de OCR en transacciones.
        Layout: Cada transacción tiene múltiples líneas verticalmente.
        
        Args:
            detections: Resultados del OCR
            image_height: Alto de la imagen
            image_width: Ancho de la imagen
            
        Returns:
            Lista de transacciones agrupadas
        """
        # Filtrar detecciones de la parte superior (header) y inferior
        # Como las imágenes están recortadas, usar umbrales muy pequeños
        header_threshold = image_height * 0.02  # Solo 2% para evitar cortar transacciones arriba
        footer_threshold = image_height * 0.98  # Mantener 98% del bottom
        
        relevant_detections = []
        for detection in detections:
            bbox = detection[0]
            y_center = (bbox[0][1] + bbox[2][1]) / 2
            x_center = (bbox[0][0] + bbox[2][0]) / 2
            
            if header_threshold < y_center < footer_threshold:
                relevant_detections.append({
                    'bbox': bbox,
                    'text': detection[1],
                    'confidence': detection[2],
                    'y_center': y_center,
                    'x_center': x_center,
                    'x_left': bbox[0][0],
                    'x_right': bbox[2][0],
                    'y_top': bbox[0][1],
                    'y_bottom': bbox[2][1],
                    'width': bbox[2][0] - bbox[0][0],
                    'height': bbox[2][1] - bbox[0][1]
                })
        
        # Ordenar por posición vertical
        relevant_detections.sort(key=lambda x: x['y_center'])
        
        # Identificar líneas horizontales (elementos en la misma altura Y)
        lines = []
        current_line = []
        last_y = None
        y_tolerance = 18  # Más estricto para evitar combinar transacciones cercanas
        
        for item in relevant_detections:
            if last_y is None or abs(item['y_center'] - last_y) <= y_tolerance:
                current_line.append(item)
                last_y = item['y_center'] if last_y is None else (last_y + item['y_center']) / 2
            else:
                if current_line:
                    lines.append(sorted(current_line, key=lambda x: x['x_left']))
                current_line = [item]
                last_y = item['y_center']
        
        if current_line:
            lines.append(sorted(current_line, key=lambda x: x['x_left']))
        
        # Agrupar líneas en transacciones
        transactions = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Buscar elementos que indican una transacción
            has_amount = any('S/' in item['text'] or 's/' in item['text'] or re.search(r'-?\s*\d+[.,]\d+', item['text']) for item in line)
            has_description = any(len(item['text']) > 3 and not item['text'].isdigit() and 'S/' not in item['text'] for item in line)
            
            # Si esta línea tiene descripción o monto, es probablemente parte de una transacción
            if has_description or has_amount:
                transaction_lines = [line]
                
                # Buscar líneas adicionales que pertenezcan a esta transacción (dentro de ~80px)
                j = i + 1
                while j < len(lines) and j < i + 5:  # Máximo 5 líneas por transacción
                    next_line = lines[j]
                    y_distance = next_line[0]['y_center'] - transaction_lines[-1][0]['y_center']
                    
                    if y_distance <= 80:  # Más estricto para evitar combinar transacciones
                        transaction_lines.append(next_line)
                        j += 1
                    else:
                        break
                
                # Extraer información de todas las líneas de la transacción
                all_items = [item for tline in transaction_lines for item in tline]
                
                name_parts = []
                date_text = ""
                amount_text = ""
                
                for item in all_items:
                    text = item['text'].strip()
                    
                    # Detectar monto (con variaciones de OCR: S/, Sl, SI, $)
                    is_amount = (('S/' in text or 's/' in text or 'Sl' in text or 'sl' in text or 'SI' in text or '$' in text) and re.search(r'\d', text))
                    # También detectar números con signo negativo directo
                    is_amount = is_amount or re.match(r'^-?\s*\d+[.,]\d+$', text)
                    
                    if is_amount:
                        if not amount_text or len(text) > len(amount_text):
                            amount_text = text
                    # Detectar fecha (número pequeño + posible mes)
                    elif re.match(r'^\d{1,2}(\s+(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre))?$', text, re.IGNORECASE):
                        if not date_text:
                            date_text = text
                    # Detectar fecha con formato extendido "18 Septiembre; 01.41"
                    elif re.match(r'^\d{1,2}\s+\w+;\s*\d', text, re.IGNORECASE):
                        if not date_text:
                            date_text = text
                    # Detectar descripción (texto que no es fecha ni monto)
                    elif len(text) > 2 and not text.isdigit() and 'S/' not in text and 's/' not in text and 'Sl' not in text and '$' not in text:
                        # Evitar agregar el header "Movimientos" o "Fecha" o iconos
                        if text.lower() not in ['movimientos', 'fecha', 'monto', 'in', 'co', 'im', 'de', 'tr', '#', 'pm', 'p.m.', 'a.m.', 'pm.', 'a.m', 'ma', 'po', 'en', 'eb', 'ley', 'ex']:
                            name_parts.append(text)
                
                name = ' '.join(name_parts) if name_parts else ""
                
                # Filtrar nombres que obviamente no son transacciones
                invalid_names = ['septiembre 2025', 'agosto 2025', 'enero 2026', 'movimientos fecha', 'buscador de movimientos']
                if name.lower() in invalid_names or len(name) < 3:
                    i = j
                    continue
                
                # Validar que sea una transacción real
                # Ahora aceptamos si tiene nombre + (monto O fecha), no necesariamente ambos
                if name and len(name) > 3:
                    # Calcular bbox completo
                    min_x = min(item['x_left'] for item in all_items)
                    min_y = min(item['y_top'] for item in all_items)
                    max_x = max(item['x_right'] for item in all_items)
                    max_y = max(item['y_bottom'] for item in all_items)
                    
                    transactions.append({
                        'name': name,
                        'date_text': date_text,
                        'amount_text': amount_text,
                        'bbox': [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]
                    })
                
                # Avanzar al siguiente grupo
                i = j
            else:
                i += 1
        
        return transactions
    
    def extract_transactions(self, image_path: str, debug: bool = False) -> List[Dict[str, Any]]:
        """
        Extrae transacciones de una imagen usando OCR local.
        
        Args:
            image_path: Ruta a la imagen de movimientos bancarios
            debug: Si es True, muestra información detallada de depuración
            
        Returns:
            Lista de transacciones extraídas
        """
        print(f"📸 Procesando imagen: {Path(image_path).name}")
        
        try:
            # Leer imagen
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ No se pudo leer la imagen: {image_path}")
                return []
            
            image_height, image_width = image.shape[:2]
            
            # Realizar OCR
            print("  🔍 Extrayendo texto con OCR...")
            results = self.reader.readtext(image)
            
            if not results:
                print("  ⚠️  No se detectó texto en la imagen")
                return []
            
            if debug:
                print(f"\n  🐛 DEBUG: Total de elementos OCR detectados: {len(results)}")
                for i, detection in enumerate(results):
                    print(f"    {i+1}. {detection[1]}")
            
            # Extraer mes y año
            month_year = self.extract_month_year(image_path, results)
            print(f"  📅 Mes detectado: {month_year}")
            
            # Agrupar elementos en transacciones
            transaction_groups = self.group_transaction_elements(results, image_height, image_width)
            print(f"  📊 Transacciones detectadas: {len(transaction_groups)}")
            
            if debug:
                print(f"\n  🐛 DEBUG: Transacciones agrupadas:")
                for i, group in enumerate(transaction_groups):
                    print(f"    {i+1}. Nombre: {group['name'][:40]}")
                    print(f"       Fecha: {group['date_text']}")
                    print(f"       Monto: {group['amount_text']}")
            
            # Procesar cada transacción
            transactions = []
            
            for group in transaction_groups:
                # Verificar overlay rojo
                bbox = group['bbox']
                x1 = min([p[0] for p in bbox])
                y1 = min([p[1] for p in bbox])
                x2 = max([p[0] for p in bbox])
                y2 = max([p[1] for p in bbox])
                
                # Expandir bbox para capturar toda la transacción
                y2 = min(y2 + 100, image_height)
                
                if self.detect_red_overlay(image, (x1, y1, x2, y2)):
                    print(f"  🚫 Omitiendo transacción con overlay rojo: {group['name'][:30]}")
                    continue
                
                # Parsear fecha
                date = self.parse_date(group['date_text'], month_year)
                if not date:
                    # Intentar extraer fecha del nombre (ej: "DEPOSITO EFECTIVO 29 Septiembre")
                    date_in_name = re.search(r'(\d{1,2})\s+(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)', group['name'], re.IGNORECASE)
                    if date_in_name:
                        date = self.parse_date(date_in_name.group(0), month_year)
                        # No remover la fecha del nombre ya que puede ser parte de la descripción
                    else:
                        # Si solo tiene el mes en el nombre (sin día), usar el último día del mes del contexto
                        month_only = re.search(r'(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)', group['name'], re.IGNORECASE)
                        if month_only and month_year:
                            # Usar el último día del mes del contexto
                            meses = {
                                'enero': ('31', '01'), 'febrero': ('28', '02'), 'marzo': ('31', '03'), 
                                'abril': ('30', '04'), 'mayo': ('31', '05'), 'junio': ('30', '06'),
                                'julio': ('31', '07'), 'agosto': ('31', '08'), 'septiembre': ('30', '09'),
                                'octubre': ('31', '10'), 'noviembre': ('30', '11'), 'diciembre': ('31', '12')
                            }
                            mes_name = month_only.group(1).lower()
                            if mes_name in meses:
                                ultimo_dia, mes_num = meses[mes_name]
                                # Extraer año del contexto
                                year_match = re.search(r'\b(20\d{2})\b', month_year)
                                year = year_match.group(1) if year_match else datetime.now().strftime('%Y')
                                date = f"{ultimo_dia}/{mes_num}/{year}"
                
                if not date:
                    # Si no hay fecha explícita, usar mes/año del contexto
                    date = f"01/{datetime.now().strftime('%m/%Y')}"
                
                # Parsear monto y moneda
                amount, tipo, moneda = self.parse_amount(group['amount_text'])
                
                # Si no hay monto en amount_text, intentar extraerlo del nombre
                if amount == 0 and group['name']:
                    # Buscar patrones de monto en el nombre (S/ o $)
                    amount_in_name = re.search(r'([5S$]/?\s*-?\s*\d+[.,]\d+)', group['name'])
                    if amount_in_name:
                        amount, tipo, moneda = self.parse_amount(amount_in_name.group(1))
                        if amount != 0:
                            # Remover el monto del nombre
                            group['name'] = re.sub(r'[5S]/?\s*-?\s*\d+[.,]\d+', '', group['name']).strip()
                
                # Validar que tengamos datos mínimos
                if group['name'] and amount != 0:
                    transactions.append({
                        'id': str(uuid.uuid4()),
                        'date': date,
                        'name': group['name'].strip(),
                        'amount': amount,
                        'type': tipo,
                        'currency': moneda,
                        'month': month_year
                    })
                elif group['name'] and len(group['name']) > 5:  # Incluir transacciones sin monto si el nombre es razonable
                    if debug:
                        print(f"  ⚠️  Transacción sin monto detectado: {group['name'][:40]}")
                    # Agregar con monto 0 para no perderla
                    transactions.append({
                        'id': str(uuid.uuid4()),
                        'date': date if date else "01/01/2026",
                        'name': group['name'].strip() + " [SIN MONTO DETECTADO]",
                        'amount': 0.0,
                        'type': "cargo",
                        'currency': "S/",
                        'month': month_year
                    })
            
            print(f"  ✅ Extraídas {len(transactions)} transacciones válidas")
            
            if debug:
                print(f"\n  🐛 DEBUG: Transacciones finales:")
                for i, t in enumerate(transactions):
                    print(f"    {i+1}. {t['date']} - {t['name'][:40]} - S/ {t['amount']}")
            
            return transactions
            
        except Exception as e:
            print(f"  ❌ Error al procesar imagen: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def process_multiple_images(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Procesa múltiples imágenes y combina las transacciones.
        
        Args:
            image_paths: Lista de rutas a imágenes
            
        Returns:
            Lista combinada de todas las transacciones
        """
        all_transactions = []
        
        for image_path in image_paths:
            if not Path(image_path).exists():
                print(f"⚠️  Imagen no encontrada: {image_path}")
                continue
            
            transactions = self.extract_transactions(image_path)
            all_transactions.extend(transactions)
        
        print(f"\n📊 Total de transacciones extraídas: {len(all_transactions)}")
        return all_transactions
