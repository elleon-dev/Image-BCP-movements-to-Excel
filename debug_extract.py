#!/usr/bin/env python3
"""Script temporal para debug de extracción"""

from image_processor_local import LocalImageProcessor
import sys

if len(sys.argv) < 2:
    print("Uso: python debug_extract.py <imagen>")
    sys.exit(1)

processor = LocalImageProcessor()
transactions = processor.extract_transactions(sys.argv[1], debug=True)

print(f"\n\n{'='*70}")
print(f"RESUMEN FINAL:")
print(f"{'='*70}")
print(f"Total extraído: {len(transactions)}")
for i, t in enumerate(transactions, 1):
    print(f"{i}. {t['date']} - {t['name'][:50]} - S/ {t['amount']} ({t['type']})")
