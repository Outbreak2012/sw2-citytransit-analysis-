"""
Script simplificado para iniciar el servicio Analytics
Sin dependencias pesadas de ML para testing rápido
"""
import uvicorn
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Iniciando CityTransit Analytics Service (Modo Simple)")
    print("=" * 60)
    print("📚 Documentación API: http://localhost:8001/docs")
    print("💡 Health check: http://localhost:8001/health")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
