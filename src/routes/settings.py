from flask import Blueprint, request, jsonify
from datetime import datetime
from ..services.database import DatabaseService
from ..models.exceptions import AppError
from config import Config

# Initialize blueprint
bp = Blueprint('settings', __name__, url_prefix='/api/settings')

# Initialize services
db = DatabaseService(Config.get_supabase_client())

def validate_settings(settings):
    """Validate settings data."""
    if "iconSize" in settings:
        try:
            icon_size = int(settings["iconSize"])
            if not (24 <= icon_size <= 96):
                raise AppError("Icon size must be between 24 and 96 pixels")
        except ValueError:
            raise AppError("Invalid icon size value")
    
    # Add more validation as needed
    return settings

@bp.route('', methods=['GET'])
def get_settings():
    """Get current settings."""
    try:
        response = db.client.table(Config.SETTINGS_TABLE).select("*").execute()
        if not response.data:
            # Create default settings
            default_settings = {
                "metadata": {
                    "lastUpdated": datetime.utcnow().isoformat(),
                    "version": "1.0"
                },
                "settings": {
                    "gridGap": "5",
                    "gridPadding": "0",
                    "iconSize": Config.DEFAULT_ICON_SIZE,
                    "theme": "dark",
                    "appNameColor": "#ffffff",
                    "paddingX": "2",
                    "paddingY": "6",
                    "safeAreaTop": "0"
                }
            }
            response = db.client.table(Config.SETTINGS_TABLE).insert(default_settings).execute()
            return jsonify(default_settings)
        
        return jsonify(response.data[0])
    except Exception as e:
        raise AppError(f"Failed to get settings: {str(e)}")

@bp.route('', methods=['PUT'])
def update_settings():
    """Update settings."""
    try:
        # Get current settings first
        current = db.client.table(Config.SETTINGS_TABLE).select("*").execute()
        if not current.data:
            raise AppError("Settings not found")
        
        settings_data = current.data[0]
        new_settings = request.json
        
        # Validate new settings
        validated_settings = validate_settings(new_settings)
        
        # Update settings
        settings_data["settings"].update(validated_settings)
        settings_data["metadata"]["lastUpdated"] = datetime.utcnow().isoformat()
        
        # Save to database
        response = db.client.table(Config.SETTINGS_TABLE)\
            .update(settings_data)\
            .eq("id", settings_data["id"])\
            .execute()
        
        return jsonify({
            "status": "success",
            "settings": response.data[0]["settings"]
        })
    except Exception as e:
        raise AppError(f"Failed to update settings: {str(e)}")

@bp.route('/reset', methods=['POST'])
def reset_settings():
    """Reset settings to defaults."""
    try:
        default_settings = {
            "metadata": {
                "lastUpdated": datetime.utcnow().isoformat(),
                "version": "1.0"
            },
            "settings": {
                "gridGap": "5",
                "gridPadding": "0",
                "iconSize": Config.DEFAULT_ICON_SIZE,
                "theme": "dark",
                "appNameColor": "#ffffff",
                "paddingX": "2",
                "paddingY": "6",
                "safeAreaTop": "0"
            }
        }
        
        # Get current settings to get the ID
        current = db.client.table(Config.SETTINGS_TABLE).select("*").execute()
        if current.data:
            # Update existing settings
            response = db.client.table(Config.SETTINGS_TABLE)\
                .update(default_settings)\
                .eq("id", current.data[0]["id"])\
                .execute()
        else:
            # Create new settings
            response = db.client.table(Config.SETTINGS_TABLE).insert(default_settings).execute()
        
        return jsonify({
            "status": "success",
            "settings": response.data[0]["settings"]
        })
    except Exception as e:
        raise AppError(f"Failed to reset settings: {str(e)}") 