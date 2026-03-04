from clickhouse_driver import Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ClickHouseConnection:
    """ClickHouse database connection"""
    
    def __init__(self):
        self.client = None
    
    def connect(self):
        """Connect to ClickHouse"""
        try:
            self.client = Client(
                host=settings.CLICKHOUSE_HOST,
                port=settings.CLICKHOUSE_PORT,
                user=settings.CLICKHOUSE_USER,
                password=settings.CLICKHOUSE_PASSWORD,
                database=settings.CLICKHOUSE_DATABASE
            )
            logger.info("✅ Connected to ClickHouse")
            return self.client
        except Exception as e:
            logger.error(f"❌ Error connecting to ClickHouse: {e}")
            raise
    
    def execute(self, query: str, params: dict = None):
        """Execute query"""
        if not self.client:
            self.connect()
        return self.client.execute(query, params or {})
    
    def disconnect(self):
        """Disconnect from ClickHouse"""
        if self.client:
            self.client.disconnect()
            logger.info("Disconnected from ClickHouse")


# Global connection instance
clickhouse_conn = ClickHouseConnection()


def get_clickhouse():
    """Get ClickHouse connection"""
    if not clickhouse_conn.client:
        clickhouse_conn.connect()
    return clickhouse_conn.client
