import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from supabase import Client
from ..models.exceptions import AppError
from config import Config

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service class for handling database operations."""
    
    def __init__(self, client: Client):
        self.client = client
        self.apps_table = Config.APPS_TABLE
        self.settings_table = Config.SETTINGS_TABLE
        self.categories_table = Config.CATEGORIES_TABLE

    def get_apps(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Get all apps with optional filtering."""
        try:
            query = self.client.table(self.apps_table).select("*")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to load apps: {e}")
            raise AppError("Failed to load apps", 500)

    def get_app_by_id(self, app_id: str) -> Optional[Dict]:
        """Get a single app by ID."""
        try:
            response = self.client.table(self.apps_table).select("*").eq("id", app_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to load app {app_id}: {e}")
            raise AppError(f"Failed to load app {app_id}", 500)

    def create_app(self, app_data: Dict) -> Dict:
        """Create a new app."""
        try:
            response = self.client.table(self.apps_table).insert(app_data).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create app: {e}")
            raise AppError("Failed to create app", 500)

    def update_app(self, app_id: str, app_data: Dict) -> Dict:
        """Update an existing app."""
        try:
            response = self.client.table(self.apps_table).update(app_data).eq("id", app_id).execute()
            if not response.data:
                raise AppError(f"App {app_id} not found", 404)
            return response.data[0]
        except AppError:
            raise
        except Exception as e:
            logger.error(f"Failed to update app {app_id}: {e}")
            raise AppError(f"Failed to update app {app_id}", 500)

    def delete_app(self, app_id: str) -> bool:
        """Delete an app."""
        try:
            response = self.client.table(self.apps_table).delete().eq("id", app_id).execute()
            if not response.data:
                raise AppError(f"App {app_id} not found", 404)
            return True
        except AppError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete app {app_id}: {e}")
            raise AppError(f"Failed to delete app {app_id}", 500)

    def increment_launch_count(self, app_id: str) -> Dict:
        """Increment the launch count for an app."""
        try:
            app = self.get_app_by_id(app_id)
            if not app:
                raise AppError(f"App {app_id} not found", 404)
            
            response = self.client.table(self.apps_table).update({
                "launch_count": app["launch_count"] + 1,
                "last_launched": datetime.utcnow().isoformat()
            }).eq("id", app_id).execute()
            
            return response.data[0]
        except AppError:
            raise
        except Exception as e:
            logger.error(f"Failed to increment launch count for app {app_id}: {e}")
            raise AppError(f"Failed to update launch count", 500)

    def get_categories(self) -> List[str]:
        """Get all categories."""
        try:
            response = self.client.table(self.categories_table).select("*").execute()
            categories = [cat["name"] for cat in response.data] if response.data else []
            return categories or [Config.DEFAULT_CATEGORY]
        except Exception as e:
            logger.error(f"Failed to load categories: {e}")
            raise AppError("Failed to load categories", 500)

    def add_category(self, name: str) -> Dict:
        """Add a new category."""
        try:
            # Check if category exists
            existing = self.client.table(self.categories_table).select("*").eq("name", name).execute()
            if existing.data:
                return {"status": "exists", "category": name}
            
            # Add new category
            response = self.client.table(self.categories_table).insert({"name": name}).execute()
            return {"status": "success", "category": response.data[0]["name"]}
        except Exception as e:
            logger.error(f"Failed to add category: {e}")
            raise AppError(f"Failed to add category: {str(e)}", 500) 