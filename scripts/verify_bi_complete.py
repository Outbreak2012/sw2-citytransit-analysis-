"""
Business Intelligence Verification Script
Verifica que todos los componentes de BI estén funcionando correctamente
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_services():
    """Verify all services are importable"""
    print_section("1. Verificando Servicios")
    
    services = []
    
    try:
        from app.services.kpi_service import kpi_service
        services.append(("KPI Service", "✅"))
        logger.info("✅ KPI Service importado correctamente")
    except Exception as e:
        services.append(("KPI Service", f"❌ {e}"))
        logger.error(f"❌ Error importando KPI Service: {e}")
    
    try:
        from app.services.report_service import report_service
        services.append(("Report Service", "✅"))
        logger.info("✅ Report Service importado correctamente")
    except Exception as e:
        services.append(("Report Service", f"❌ {e}"))
        logger.error(f"❌ Error importando Report Service: {e}")
    
    try:
        from app.services.demand_service import demand_service
        services.append(("Demand Service", "✅"))
        logger.info("✅ Demand Service importado correctamente")
    except Exception as e:
        services.append(("Demand Service", f"❌ {e}"))
        logger.error(f"❌ Error importando Demand Service: {e}")
    
    return services


def check_kpis():
    """Test KPI calculations"""
    print_section("2. Verificando KPIs")
    
    results = []
    
    try:
        from app.services.kpi_service import kpi_service
        
        # Test passenger KPIs
        passenger_kpis = kpi_service.get_passenger_kpis(days=7)
        results.append(("Passenger KPIs", "✅", passenger_kpis))
        logger.info(f"✅ Passenger KPIs: {passenger_kpis.get('total_passengers')} passengers")
        
        # Test route KPIs
        route_kpis = kpi_service.get_route_kpis()
        results.append(("Route KPIs", "✅", route_kpis))
        logger.info(f"✅ Route KPIs: {route_kpis.get('active_routes')} active routes")
        
        # Test occupancy KPIs
        occupancy_kpis = kpi_service.get_occupancy_kpis()
        results.append(("Occupancy KPIs", "✅", occupancy_kpis))
        logger.info(f"✅ Occupancy KPIs: {occupancy_kpis.get('avg_occupancy')*100:.1f}% avg occupancy")
        
        # Test sentiment KPIs
        sentiment_kpis = kpi_service.get_sentiment_kpis()
        results.append(("Sentiment KPIs", "✅", sentiment_kpis))
        logger.info(f"✅ Sentiment KPIs: {sentiment_kpis.get('avg_sentiment'):.2f} avg sentiment")
        
        # Test revenue analytics
        revenue = kpi_service.get_revenue_analytics(days=7)
        results.append(("Revenue Analytics", "✅", revenue['summary']))
        logger.info(f"✅ Revenue Analytics: ${revenue['summary']['total_revenue']:,.0f} total")
        
        # Test all KPIs together
        all_kpis = kpi_service.get_all_kpis()
        results.append(("All KPIs Combined", "✅", {"sources": all_kpis.get('data_sources')}))
        logger.info(f"✅ All KPIs: Data sources = {all_kpis.get('data_sources')}")
        
    except Exception as e:
        results.append(("KPI Tests", f"❌ {e}", {}))
        logger.error(f"❌ Error testing KPIs: {e}")
    
    return results


def check_reports():
    """Test report generation"""
    print_section("3. Verificando Generación de Reportes")
    
    results = []
    
    try:
        from app.services.report_service import report_service
        
        # Test executive summary
        exec_summary = report_service.generate_executive_summary(days=7)
        results.append(("Executive Summary", "✅", {
            "recommendations": len(exec_summary.get('recommendations', [])),
            "highlights": list(exec_summary.get('highlights', {}).keys())
        }))
        logger.info(f"✅ Executive Summary: {len(exec_summary.get('recommendations', []))} recommendations")
        
        # Test route performance
        route_report = report_service.generate_route_performance_report(days=7)
        results.append(("Route Performance", "✅", {
            "routes_analyzed": route_report['summary']['total_routes_analyzed'],
            "total_revenue": route_report['summary']['total_revenue']
        }))
        logger.info(f"✅ Route Performance: {route_report['summary']['total_routes_analyzed']} routes")
        
        # Test sentiment report
        sentiment_report = report_service.generate_sentiment_report(days=7)
        results.append(("Sentiment Report", "✅", {
            "total_feedback": sentiment_report.get('total_feedback_analyzed', 0),
            "data_source": sentiment_report.get('data_source')
        }))
        logger.info(f"✅ Sentiment Report: {sentiment_report.get('total_feedback_analyzed', 0)} feedbacks")
        
        # Test demand forecast
        forecast = report_service.generate_demand_forecast_report(days_ahead=3)
        results.append(("Demand Forecast", "✅", {
            "predictions": len(forecast.get('hourly_predictions', [])),
            "avg_confidence": forecast['model_info']['avg_confidence']
        }))
        logger.info(f"✅ Demand Forecast: {len(forecast.get('hourly_predictions', []))} predictions")
        
    except Exception as e:
        results.append(("Report Tests", f"❌ {e}", {}))
        logger.error(f"❌ Error testing reports: {e}")
    
    return results


def check_ml_models():
    """Verify ML models are loaded"""
    print_section("4. Verificando Modelos ML")
    
    results = []
    
    # Check LSTM model
    try:
        from app.ml.lstm_model import lstm_predictor
        if hasattr(lstm_predictor, 'model') and lstm_predictor.model is not None:
            results.append(("LSTM Model", "✅ Loaded"))
            logger.info("✅ LSTM Model cargado")
        else:
            results.append(("LSTM Model", "⚠️ Not loaded (using fallback)"))
            logger.warning("⚠️ LSTM Model no cargado, usando fallback")
    except Exception as e:
        results.append(("LSTM Model", f"❌ {e}"))
        logger.error(f"❌ Error con LSTM: {e}")
    
    # Check BERT model
    try:
        from app.ml.bert_model import bert_analyzer
        test_result = bert_analyzer.analyze("Excelente servicio")
        results.append(("BERT Model", f"✅ {test_result['sentiment']}"))
        logger.info(f"✅ BERT Model funcionando: {test_result['sentiment']}")
    except Exception as e:
        results.append(("BERT Model", f"❌ {e}"))
        logger.error(f"❌ Error con BERT: {e}")
    
    # Check DBSCAN
    try:
        from app.ml.dbscan_model import dbscan_model
        results.append(("DBSCAN Model", "✅ Available"))
        logger.info("✅ DBSCAN Model disponible")
    except Exception as e:
        results.append(("DBSCAN Model", f"❌ {e}"))
        logger.error(f"❌ Error con DBSCAN: {e}")
    
    return results


def check_datasets():
    """Verify datasets exist"""
    print_section("5. Verificando Datasets")
    
    results = []
    datasets = [
        ('models/lstm_demand_prediction.h5', 'LSTM Trained Model'),
        ('models/training_metrics.json', 'Training Metrics'),
        ('models/historical_demand_dataset.json', 'Historical Demand Dataset')
    ]
    
    for path, name in datasets:
        if os.path.exists(path):
            size = os.path.getsize(path)
            results.append((name, f"✅ {size:,} bytes"))
            logger.info(f"✅ {name}: {size:,} bytes")
        else:
            results.append((name, "❌ Not found"))
            logger.warning(f"⚠️ {name}: No encontrado")
    
    return results


def generate_summary(all_results):
    """Generate summary report"""
    print_section("📊 RESUMEN DE VERIFICACIÓN BI")
    
    total_checks = 0
    passed = 0
    warnings = 0
    failed = 0
    
    for section, results in all_results.items():
        print(f"\n{section}:")
        for item in results:
            name = item[0]
            status = item[1] if len(item) > 1 else "Unknown"
            
            total_checks += 1
            if "✅" in str(status):
                passed += 1
                print(f"  ✅ {name}")
            elif "⚠️" in str(status):
                warnings += 1
                print(f"  ⚠️ {name}")
            else:
                failed += 1
                print(f"  ❌ {name}: {status}")
    
    print("\n" + "=" * 60)
    print(f"  TOTAL: {total_checks} verificaciones")
    print(f"  ✅ Exitosas: {passed}")
    print(f"  ⚠️ Advertencias: {warnings}")
    print(f"  ❌ Fallidas: {failed}")
    print("=" * 60)
    
    completion = (passed / total_checks * 100) if total_checks > 0 else 0
    print(f"\n  📈 Completitud BI: {completion:.1f}%")
    
    if completion >= 90:
        print("  🎉 ¡Business Intelligence completamente funcional!")
    elif completion >= 70:
        print("  ✅ Business Intelligence mayormente funcional")
    else:
        print("  ⚠️ Se requieren más correcciones")
    
    return {
        'total': total_checks,
        'passed': passed,
        'warnings': warnings,
        'failed': failed,
        'completion': completion
    }


def main():
    """Main verification function"""
    print("\n" + "🔍" * 30)
    print("  VERIFICACIÓN DE BUSINESS INTELLIGENCE")
    print("  CityTransit Analytics Service")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🔍" * 30)
    
    all_results = {}
    
    # Run all checks
    all_results['Servicios'] = check_services()
    all_results['KPIs'] = check_kpis()
    all_results['Reportes'] = check_reports()
    all_results['Modelos ML'] = check_ml_models()
    all_results['Datasets'] = check_datasets()
    
    # Generate summary
    summary = generate_summary(all_results)
    
    # Save results
    results_file = 'models/bi_verification_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'details': {k: [(r[0], str(r[1])) for r in v] for k, v in all_results.items()}
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n📄 Resultados guardados en: {results_file}")
    
    return summary


if __name__ == "__main__":
    main()
