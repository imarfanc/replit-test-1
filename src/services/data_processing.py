from datetime import datetime
from typing import Dict, Any, Optional
from ..models.exceptions import AppError
from config import Config

class DataProcessor:
    """Service class for data processing and validation."""

    @staticmethod
    def to_camel_case(snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    @classmethod
    def snake_to_camel_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert all dictionary keys from snake_case to camelCase."""
        return {
            cls.to_camel_case(key): value
            for key, value in data.items()
        }

    @staticmethod
    def camel_to_snake(camel_str: str) -> str:
        """Convert camelCase to snake_case."""
        snake_str = camel_str[0].lower()
        for char in camel_str[1:]:
            if char.isupper():
                snake_str += '_' + char.lower()
            else:
                snake_str += char
        return snake_str

    @classmethod
    def camel_to_snake_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert all dictionary keys from camelCase to snake_case."""
        return {
            cls.camel_to_snake(key): value
            for key, value in data.items()
        }

    @staticmethod
    def format_app_response(app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format app data for API response."""
        return {
            "id": app_data["id"],
            "name": app_data["name"],
            "category": app_data["category"],
            "iconUrl": app_data["icon_url"],
            "appStoreLink": app_data["app_store_link"],
            "launchCount": app_data["launch_count"],
            "lastModified": app_data["last_modified"],
            "lastLaunched": app_data["last_launched"]
        }

    @staticmethod
    def validate_app_data(data: Dict[str, Any], for_update: bool = False) -> Dict[str, Any]:
        """Validate and format app data for database operations."""
        if not for_update and not data.get("name"):
            raise AppError("App name is required")

        validated = {}
        
        if "name" in data:
            validated["name"] = data["name"]
        
        if "category" in data:
            validated["category"] = data["category"].lower() if data["category"] else Config.DEFAULT_CATEGORY
        
        if "iconUrl" in data:
            icon_url = data["iconUrl"].strip()
            if icon_url.startswith("@"):
                icon_url = icon_url[1:]
            if icon_url and not (icon_url.startswith("http://") or icon_url.startswith("https://")):
                raise AppError("Icon URL must be a valid HTTP/HTTPS URL")
            validated["icon_url"] = icon_url
        
        if "appStoreLink" in data:
            app_store_link = data["appStoreLink"].strip()
            if app_store_link and not app_store_link.startswith(Config.APP_STORE_URL_PREFIX):
                raise AppError("Invalid App Store link format")
            validated["app_store_link"] = app_store_link

        if not for_update:
            validated.update({
                "launch_count": 0,
                "last_modified": datetime.utcnow().isoformat(),
                "last_launched": None
            })
        else:
            validated["last_modified"] = datetime.utcnow().isoformat()

        return validated

    @staticmethod
    def validate_category_name(name: str) -> str:
        """Validate and format category name."""
        if not name or not name.strip():
            raise AppError("Category name is required")
        
        formatted_name = name.strip().lower()
        if len(formatted_name) > 50:  # arbitrary limit
            raise AppError("Category name is too long")
        
        return formatted_name 