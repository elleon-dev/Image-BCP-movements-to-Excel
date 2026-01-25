#!/usr/bin/env python3
"""
Script de debug para ver cómo se agrupan las líneas horizontales
"""

import sys
from image_processor_local import LocalImageProcessor

def main():
    if len(sys.argv) < 2:
        print("Uso: python debug_lines.py <ruta_imagen>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    processor = LocalImageProcessor()
    
    # Cargar imagen
    import cv2
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ No se pudo cargar la imagen: {image_path}")
        sys.exit(1)
    
    height, width = image.shape[:2]
    
    # Hacer OCR
    print(f"🔍 Procesando: {image_path}")
    ocr_results = processor.reader.readtext(image)
    
    # Filtrar por región
    header_threshold = height * 0.05
    footer_threshold = height * 0.98
    
    relevant_detections = []
    for detection in ocr_results:
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
    
    print(f"\n📊 Total elementos relevantes: {len(relevant_detections)}")
    
    # Identificar líneas horizontales
    lines = []
    current_line = []
    last_y = None
    y_tolerance = 18
    
    print(f"\n🔍 Agrupando en líneas horizontales (tolerancia Y: {y_tolerance}px):\n")
    
    for i, item in enumerate(relevant_detections):
        y = item['y_center']
        
        if last_y is None or abs(y - last_y) <= y_tolerance:
            current_line.append(item)
            last_y = y if last_y is None else (last_y + y) / 2
            print(f"  [{i+1}] Y={y:.1f} (diff={(y - (last_y if last_y else y)):.1f}) -> MISMA LÍNEA: {item['text']}")
        else:
            if current_line:
                lines.append(sorted(current_line, key=lambda x: x['x_left']))
                print(f"  ⬇️ NUEVA LÍNEA (distancia: {y - last_y:.1f}px)")
            current_line = [item]
            last_y = y
            print(f"  [{i+1}] Y={y:.1f} -> NUEVA LÍNEA: {item['text']}")
    
    if current_line:
        lines.append(sorted(current_line, key=lambda x: x['x_left']))
    
    print(f"\n📋 Total de líneas detectadas: {len(lines)}")
    for i, line in enumerate(lines):
        texts = ' | '.join([item['text'] for item in line])
        print(f"  Línea {i+1}: {texts}")

if __name__ == "__main__":
    main()
