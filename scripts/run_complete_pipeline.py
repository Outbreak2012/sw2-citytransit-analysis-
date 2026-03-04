"""
Script maestro para entrenar todos los modelos ML con datos reales/sintéticos
Ejecuta el pipeline completo: datos → entrenamiento → validación
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import argparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Verificar que las dependencias necesarias estén instaladas"""
    logger.info("🔍 Verificando dependencias...")
    
    dependencies = {
        'tensorflow': False,
        'transformers': False,
        'torch': False,
        'sklearn': True,  # Siempre requerido (scikit-learn)
        'clickhouse_driver': True,
        'pymongo': True
    }
    
    for package, required in dependencies.items():
        try:
            __import__(package)
            logger.info(f"   ✅ {package}")
        except ImportError:
            if required:
                logger.error(f"   ❌ {package} (REQUERIDO)")
                return False
            else:
                logger.warning(f"   ⚠️ {package} (OPCIONAL)")
    
    return True


def populate_databases():
    """Poblar bases de datos con datos sintéticos"""
    logger.info("=" * 70)
    logger.info("📊 POBLANDO BASES DE DATOS")
    logger.info("=" * 70)
    
    try:
        # Poblar ClickHouse
        logger.info("\n🔄 Ejecutando populate_clickhouse.py...")
        os.system("python scripts/populate_clickhouse.py")
        
        # Poblar MongoDB
        logger.info("\n🔄 Ejecutando populate_mongodb.py...")
        os.system("python scripts/populate_mongodb.py")
        
        logger.info("\n✅ Bases de datos pobladas exitosamente!")
        return True
    except Exception as e:
        logger.error(f"❌ Error poblando bases de datos: {e}")
        return False


def train_all_models(lstm_epochs=50, bert_epochs=5):
    """Entrenar todos los modelos"""
    logger.info("=" * 70)
    logger.info("🤖 ENTRENANDO MODELOS ML")
    logger.info("=" * 70)
    
    # Entrenar LSTM
    logger.info("\n📈 Entrenando LSTM...")
    lstm_success = os.system(f"python scripts/train_models.py --model lstm --lstm-epochs {lstm_epochs}") == 0
    
    # Entrenar BERT
    logger.info("\n💬 Entrenando BERT...")
    bert_success = os.system(f"python scripts/train_models.py --model bert --bert-epochs {bert_epochs}") == 0
    
    # Entrenar DBSCAN
    logger.info("\n👥 Entrenando DBSCAN...")
    dbscan_success = os.system("python scripts/train_models.py --model dbscan") == 0
    
    return lstm_success and bert_success and dbscan_success


def main():
    """Función principal - Pipeline completo"""
    parser = argparse.ArgumentParser(description='Pipeline completo de entrenamiento ML')
    parser.add_argument('--skip-data', action='store_true',
                       help='Saltar población de datos (usar datos existentes)')
    parser.add_argument('--lstm-epochs', type=int, default=50,
                       help='Epochs para LSTM (default: 50)')
    parser.add_argument('--bert-epochs', type=int, default=5,
                       help='Epochs para BERT (default: 5)')
    
    args = parser.parse_args()
    
    logger.info("🚀 PIPELINE COMPLETO DE ENTRENAMIENTO ML")
    logger.info(f"   Timestamp: {datetime.now()}")
    logger.info("=" * 70)
    
    # 1. Verificar dependencias
    if not check_dependencies():
        logger.error("❌ Faltan dependencias requeridas")
        logger.info("💡 Instala con: pip install -r requirements.txt")
        return
    
    # 2. Poblar datos (si no se salta)
    if not args.skip_data:
        if not populate_databases():
            logger.error("❌ Error poblando bases de datos")
            return
    else:
        logger.info("⏭️ Saltando población de datos (usando datos existentes)")
    
    # 3. Entrenar modelos
    success = train_all_models(
        lstm_epochs=args.lstm_epochs,
        bert_epochs=args.bert_epochs
    )
    
    # 4. Resumen final
    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN FINAL")
    logger.info("=" * 70)
    
    if success:
        logger.info("🎉 ¡Pipeline completado exitosamente!")
        logger.info("\n📁 Modelos guardados en:")
        logger.info("   - models/lstm_demand_v1.h5")
        logger.info("   - models/bert_sentiment_v1/")
        logger.info("   - models/dbscan_users_v1.pkl")
        logger.info("\n🚀 Siguiente paso: Reiniciar el servicio Analytics")
        logger.info("   python start_simple.py")
    else:
        logger.warning("⚠️ Algunos pasos fallaron. Revisa los logs.")


if __name__ == "__main__":
    main()
