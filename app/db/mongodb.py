from pymongo import MongoClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """MongoDB database connection"""
    
    def __init__(self):
        self.client = None
        self.db = None
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            connection_string = f"mongodb://{settings.MONGODB_USER}:{settings.MONGODB_PASSWORD}@{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/"
            self.client = MongoClient(connection_string)
            self.db = self.client[settings.MONGODB_DATABASE]
            
            # Test connection
            self.client.server_info()
            logger.info("✅ Connected to MongoDB")
            return self.db
        except Exception as e:
            logger.error(f"❌ Error connecting to MongoDB: {e}")
            raise
    
    def get_collection(self, collection_name: str):
        """Get MongoDB collection"""
        if not self.db:
            self.connect()
        return self.db[collection_name]
    
    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")


# Global connection instance
mongodb_conn = MongoDBConnection()


def get_mongodb():
    """Get MongoDB database"""
    if not mongodb_conn.db:
        mongodb_conn.connect()
    return mongodb_conn.db
