"""
Script de prueba para servicios de IA
"""
import os
import sys

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

print("=" * 50)
print("PRUEBA DE SERVICIOS DE IA")
print("=" * 50)

# Test 1: Importar AIService
print("\n1. Importando AIService...")
try:
    from app.services.ai_service import AIService
    print("   [OK] AIService importado correctamente")
except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)

# Test 2: Importar NL2SQLService
print("\n2. Importando NL2SQLService...")
try:
    from app.services.nl2sql_service import NL2SQLService
    print("   [OK] NL2SQLService importado correctamente")
except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)

# Test 3: Inicializar AIService
print("\n3. Inicializando AIService...")
try:
    ai_service = AIService()
    print(f"   [OK] AIService inicializado")
    print(f"   OpenAI disponible: {ai_service.is_available}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 4: Inicializar NL2SQLService
print("\n4. Inicializando NL2SQLService...")
try:
    nl2sql_service = NL2SQLService()
    print(f"   [OK] NL2SQLService inicializado")
    print(f"   OpenAI disponible: {nl2sql_service.is_available}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 5: Probar chat basico (modo fallback)
print("\n5. Probando chat (modo fallback)...")
try:
    response = ai_service.chat("Hola, que puedes hacer?")
    print(f"   [OK] Respuesta recibida:")
    resp_text = response[:150] + "..." if len(response) > 150 else response
    print(f"   {resp_text}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 6: Probar NL2SQL conversion
print("\n6. Probando NL2SQL (modo regex fallback)...")
try:
    result = nl2sql_service.convert_to_sql("muestrame las transacciones de hoy")
    print(f"   [OK] SQL generado:")
    print(f"   {result['sql']}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "=" * 50)
print("PRUEBAS COMPLETADAS")
print("=" * 50)
