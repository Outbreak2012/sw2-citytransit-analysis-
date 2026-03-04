from .demand_service import demand_service
from .kpi_service import kpi_service
from .report_service import report_service

# Optional services (may require additional dependencies)
try:
    from .ai_service import ai_service
except ImportError:
    ai_service = None

try:
    from .nl2sql_service import nl2sql_service
except ImportError:
    nl2sql_service = None

__all__ = [
    'demand_service', 
    'kpi_service', 
    'report_service',
    'ai_service',
    'nl2sql_service'
]
