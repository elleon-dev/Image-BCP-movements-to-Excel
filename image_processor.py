"""
Módulo para procesar imágenes de movimientos bancarios usando GPT-4o Vision API.
Extrae transacciones y omite las que tienen overlay rojizo.
"""

import base64
import os
from typing import List, Dict, Any
from pathlib import Path
import json

from openai import OpenAI
from PIL import Image
import io


class ImageProcessor:
    """Procesador de imágenes bancarias con GPT-4o Vision."""
    
    def __init__(self, api_key: str):
        """
        Inicializa el procesador de imágenes.
        
        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"
    
    def encode_image(self, image_path: str) -> str:
        """
        Codifica una imagen a base64.
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            String base64 de la imagen
        """
        # Abrir y optimizar imagen si es muy grande
        with Image.open(image_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar si es muy grande (máximo 2000px en cualquier dimensión)
            max_size = 2000
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Guardar en buffer
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            # Codificar a base64
            return base64.b64encode(buffer.read()).decode('utf-8')
    
    def extract_transactions(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extrae transacciones de una imagen usando GPT-4o Vision.
        
        Args:
            image_path: Ruta a la imagen de movimientos bancarios
            
        Returns:
            Lista de transacciones extraídas
        """
        print(f"📸 Procesando imagen: {Path(image_path).name}")
        
        # Codificar imagen
        base64_image = self.encode_image(image_path)
        
        # Crear prompt estructurado
        prompt = """Analiza esta captura de pantalla de una aplicación bancaria móvil en español.

INSTRUCCIONES IMPORTANTES:
1. **OMITE/IGNORA** cualquier transacción que tenga un overlay, tinte o color rojizo sobre ella. Estas transacciones están marcadas para ser excluidas.
2. Solo extrae las transacciones que NO tienen marcas rojas.
3. Para cada transacción válida, extrae:
   - date: Fecha en formato DD/MM/YYYY (si solo aparece el día, usa el mes y año del encabezado)
   - name: Descripción o nombre del movimiento (texto completo)
   - amount: Monto numérico (negativo para cargos con "S/ -", positivo para abonos)
   - type: "cargo" si es negativo, "abono" si es positivo
   - month: El mes y año visible en la imagen (ej: "Agosto 2025", "Enero 2026")

FORMATO DE RESPUESTA:
Devuelve SOLO un objeto JSON válido con esta estructura:
{
  "transactions": [
    {
      "date": "31/08/2025",
      "name": "INTERESES DEUDORES",
      "amount": -0.02,
      "type": "cargo",
      "month": "Agosto 2025"
    }
  ]
}

Si la imagen no contiene transacciones válidas (todas tienen overlay rojo), devuelve:
{
  "transactions": []
}

NO incluyas explicaciones, solo el JSON."""

        try:
            # Llamar a GPT-4o Vision
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1  # Baja temperatura para respuestas más consistentes
            )
            
            # Extraer respuesta
            content = response.choices[0].message.content.strip()
            
            # Limpiar markdown code blocks si existen
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Parsear JSON
            result = json.loads(content)
            transactions = result.get("transactions", [])
            
            print(f"✅ Extraídas {len(transactions)} transacciones")
            
            return transactions
            
        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear JSON: {e}")
            print(f"Respuesta recibida: {content[:200]}...")
            return []
        except Exception as e:
            print(f"❌ Error al procesar imagen: {e}")
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
            if not os.path.exists(image_path):
                print(f"⚠️  Imagen no encontrada: {image_path}")
                continue
            
            transactions = self.extract_transactions(image_path)
            all_transactions.extend(transactions)
        
        print(f"\n📊 Total de transacciones extraídas: {len(all_transactions)}")
        return all_transactions
