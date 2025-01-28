import json
import os
import logging
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, abort
from werkzeug.exceptions import HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class Config:
    DEFAULT_ICON_SIZE = 60
    TABLE_PREFIX = "launcher_"  # Prefix for all tables
    APPS_TABLE = TABLE_PREFIX + "apps"
    SETTINGS_TABLE = TABLE_PREFIX + "settings"
    CATEGORIES_TABLE = TABLE_PREFIX + "categories"

class AppError(Exception):
    pass

def load_settings():
    try:
        response = supabase.table(Config.SETTINGS_TABLE).select("*").execute()
        if not response.data:
            # Create default settings if none exist
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
            response = supabase.table(Config.SETTINGS_TABLE).insert(default_settings).execute()
            return default_settings
        return response.data[0]
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        raise AppError("Failed to load settings data")

class AppDataManager:
    @staticmethod
    def load_apps():
        try:
            response = supabase.table(Config.APPS_TABLE).select("*").execute()
            return {"apps": response.data or []}
        except Exception as e:
            logger.error(f"Error loading apps: {e}")
            raise AppError("Failed to load app data")

    @staticmethod
    def save_apps(data):
        try:
            # In Supabase, we don't need to save all apps at once
            # This method is kept for compatibility but should not be used
            pass
        except Exception as e:
            logger.error(f"Error saving apps: {e}")
            raise AppError("Failed to save app data")

def validate_app_data(data):
    if not data.get("name"):
        raise AppError("App name is required")
    
    # Set defaults for optional fields
    data["category"] = data.get("category", "").lower() or "uncategorized"
    data["iconUrl"] = data.get("iconUrl", "")
    data["appStoreLink"] = data.get("appStoreLink", "")
    
    # Validate App Store link format if provided
    if data["appStoreLink"] and not data["appStoreLink"].startswith("https://apps.apple.com/"):
        raise AppError("Invalid App Store link format")
    
    # Initialize launch count for new apps
    if "launchCount" not in data:
        data["launchCount"] = 0

@app.route('/')
def index():
    try:
        apps_data = AppDataManager.load_apps()
        settings_data = load_settings()
        
        # Load categories from Supabase
        try:
            categories_response = supabase.table(Config.CATEGORIES_TABLE).select("*").execute()
            categories = [cat["name"] for cat in categories_response.data] if categories_response.data else []
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            categories = []
        
        combined_data = {
            **apps_data,
            "settings": settings_data["settings"],
            "metadata": settings_data["metadata"],
            "categories": categories
        }
        return render_template('index.html', data=combined_data)
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        abort(500)

@app.route("/api/apps", methods=["GET", "POST", "PUT"])
def manage_apps():
    if request.method == "GET":
        data = AppDataManager.load_apps()
        return jsonify(data)
    
    if request.method == "POST":
        app_data = request.json
        validate_app_data(app_data)
        app_data["id"] = str(uuid.uuid4())
        app_data["lastModified"] = datetime.utcnow().isoformat()
        
        response = supabase.table(Config.APPS_TABLE).insert(app_data).execute()
        return jsonify({"status": "success", "app": response.data[0]})
    
    if request.method == "PUT":
        app_data = request.json
        validate_app_data(app_data)
        app_data["lastModified"] = datetime.utcnow().isoformat()
        
        response = supabase.table(Config.APPS_TABLE)\
            .update(app_data)\
            .eq("id", app_data["id"])\
            .execute()
            
        if not response.data:
            abort(404)
        return jsonify({"status": "success", "app": response.data[0]})

@app.route("/api/settings", methods=["GET", "PUT"])
def manage_settings():
    if request.method == "GET":
        settings_data = load_settings()
        return jsonify(settings_data["settings"])
    
    if request.method == "PUT":
        settings_data = load_settings()
        new_settings = request.json
        if "iconSize" in new_settings:
            if not (24 <= int(new_settings["iconSize"]) <= 96):
                raise AppError("Invalid icon size")
        
        settings_data["settings"].update(new_settings)
        settings_data["metadata"]["lastUpdated"] = datetime.utcnow().isoformat()
        
        response = supabase.table(Config.SETTINGS_TABLE)\
            .update(settings_data)\
            .eq("id", settings_data["id"])\
            .execute()
        
        return jsonify({"status": "success", "settings": response.data[0]["settings"]})

@app.route("/api/apps/<app_id>", methods=["DELETE"])
def delete_app(app_id):
    response = supabase.table(Config.APPS_TABLE)\
        .delete()\
        .eq("id", app_id)\
        .execute()
    
    if not response.data:
        abort(404)
    return jsonify({"status": "success"})

@app.route("/api/apps/<app_id>/launch", methods=["POST"])
def increment_launch_count(app_id):
    # First get the current app to ensure it exists
    app_response = supabase.table(Config.APPS_TABLE)\
        .select("launchCount")\
        .eq("id", app_id)\
        .execute()
    
    if not app_response.data:
        abort(404)
    
    current_count = app_response.data[0].get("launchCount", 0)
    
    # Update the launch count and last launched time
    response = supabase.table(Config.APPS_TABLE)\
        .update({
            "launchCount": current_count + 1,
            "lastLaunched": datetime.utcnow().isoformat()
        })\
        .eq("id", app_id)\
        .execute()
    
    return jsonify({
        "status": "success",
        "launchCount": response.data[0]["launchCount"]
    })

@app.route("/api/apps/import", methods=["POST"])
def import_data():
    try:
        data = request.json
        if not isinstance(data, dict) or "apps" not in data or not isinstance(data["apps"], list):
            raise AppError("Invalid data format")
        
        # Validate and prepare each app
        for app in data["apps"]:
            validate_app_data(app)
            if "id" not in app:
                app["id"] = str(uuid.uuid4())
            app["lastModified"] = datetime.utcnow().isoformat()
            if "launchCount" not in app:
                app["launchCount"] = 0
            if "lastLaunched" not in app:
                app["lastLaunched"] = None
        
        # Insert all apps in a single batch
        response = supabase.table(Config.APPS_TABLE)\
            .insert(data["apps"])\
            .execute()
        
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Import error: {e}")
        raise AppError(f"Import failed: {str(e)}")

@app.errorhandler(AppError)
def handle_app_error(error):
    response = jsonify({"error": str(error)})
    response.status_code = 400
    return response

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = jsonify({"error": str(e.description)})
    response.status_code = e.code
    return response
