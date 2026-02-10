"""Global application objects.

This module contains global instances that are shared across the application.
"""

from src.database import Database
from src.notion_api import NotionClient

# Global database instance
db = Database()

# Global Notion API client
notion_client = NotionClient()

# Global notification manager (initialized in main())
notification_manager = None
