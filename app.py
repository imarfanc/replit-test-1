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
            # Convert snake_case to camelCase for frontend
            apps = []
            for app in response.data or []:
                apps.append({
                    "id": app["id"],
                    "name": app["name"],
                    "category": app["category"],
                    "iconUrl": app["icon_url"],
                    "appStoreLink": app["app_store_link"],
                    "launchCount": app["launch_count"],
                    "lastModified": app["last_modified"],
                    "lastLaunched": app["last_launched"]
                })
            return {"apps": apps}
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
    
    # Convert camelCase to snake_case for database
    db_data = {
        "name": data.get("name"),
        "category": data.get("category", "").lower() or "uncategorized",
        "icon_url": data.get("iconUrl", "").strip(),
        "app_store_link": data.get("appStoreLink", ""),
        "launch_count": data.get("launchCount", 0),
        "last_modified": datetime.utcnow().isoformat(),
        "last_launched": data.get("lastLaunched")
    }
    
    # Validate App Store link format if provided
    if db_data["app_store_link"] and not db_data["app_store_link"].startswith("https://apps.apple.com/"):
        raise AppError("Invalid App Store link format")
    
    # Validate icon URL
    if db_data["icon_url"]:
        if db_data["icon_url"].startswith("@"):
            db_data["icon_url"] = db_data["icon_url"][1:]  # Remove @ prefix if present
        if not (db_data["icon_url"].startswith("http://") or db_data["icon_url"].startswith("https://")):
            raise AppError("Icon URL must be a valid HTTP/HTTPS URL")
    
    return db_data

@app.route('/')
def index():
    try:
        apps_data = AppDataManager.load_apps()
        settings_data = load_settings()
        
        # Load categories from Supabase
        try:
            categories_response = supabase.table(Config.CATEGORIES_TABLE).select("*").execute()
            categories = [cat["name"] for cat in categories_response.data] if categories_response.data else ["uncategorized"]
            logger.info(f"Loaded categories: {categories}")
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            categories = ["uncategorized"]
        
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
        response = supabase.table(Config.APPS_TABLE).select("*").execute()
        # Convert snake_case to camelCase for frontend
        apps = []
        for app in response.data or []:
            apps.append({
                "id": app["id"],
                "name": app["name"],
                "category": app["category"],
                "iconUrl": app["icon_url"],
                "appStoreLink": app["app_store_link"],
                "launchCount": app["launch_count"],
                "lastModified": app["last_modified"],
                "lastLaunched": app["last_launched"]
            })
        return jsonify({"apps": apps})
    
    if request.method == "POST":
        app_data = request.json
        db_data = validate_app_data(app_data)
        db_data["id"] = str(uuid.uuid4())
        
        response = supabase.table(Config.APPS_TABLE).insert(db_data).execute()
        
        # Convert response back to camelCase
        result = response.data[0]
        return jsonify({
            "status": "success",
            "app": {
                "id": result["id"],
                "name": result["name"],
                "category": result["category"],
                "iconUrl": result["icon_url"],
                "appStoreLink": result["app_store_link"],
                "launchCount": result["launch_count"],
                "lastModified": result["last_modified"],
                "lastLaunched": result["last_launched"]
            }
        })
    
    if request.method == "PUT":
        app_data = request.json
        db_data = validate_app_data(app_data)
        
        response = supabase.table(Config.APPS_TABLE)\
            .update(db_data)\
            .eq("id", app_data["id"])\
            .execute()
            
        if not response.data:
            abort(404)
        
        # Convert response back to camelCase
        result = response.data[0]
        return jsonify({
            "status": "success",
            "app": {
                "id": result["id"],
                "name": result["name"],
                "category": result["category"],
                "iconUrl": result["icon_url"],
                "appStoreLink": result["app_store_link"],
                "launchCount": result["launch_count"],
                "lastModified": result["last_modified"],
                "lastLaunched": result["last_launched"]
            }
        })

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
    try:
        response = supabase.table(Config.APPS_TABLE)\
            .delete()\
            .eq("id", app_id)\
            .execute()
        
        if not response.data:
            logger.error(f"App not found or not deleted: {app_id}")
            abort(404)
        
        logger.info(f"Successfully deleted app: {app_id}")
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error deleting app {app_id}: {str(e)}")
        raise AppError(f"Failed to delete app: {str(e)}")

@app.route("/api/apps/<app_id>/launch", methods=["POST"])
def increment_launch_count(app_id):
    # First get the current app to ensure it exists
    app_response = supabase.table(Config.APPS_TABLE)\
        .select("launch_count")\
        .eq("id", app_id)\
        .execute()
    
    if not app_response.data:
        abort(404)
    
    current_count = app_response.data[0].get("launch_count", 0)
    
    # Update the launch count and last launched time
    response = supabase.table(Config.APPS_TABLE)\
        .update({
            "launch_count": current_count + 1,
            "last_launched": datetime.utcnow().isoformat()
        })\
        .eq("id", app_id)\
        .execute()
    
    result = response.data[0]
    return jsonify({
        "status": "success",
        "launchCount": result["launch_count"]
    })

@app.route("/api/categories", methods=["GET", "POST"])
def manage_categories():
    if request.method == "GET":
        try:
            response = supabase.table(Config.CATEGORIES_TABLE).select("*").execute()
            categories = [cat["name"] for cat in response.data] if response.data else ["uncategorized"]
            return jsonify({"categories": categories})
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            raise AppError(f"Failed to load categories: {str(e)}")
    
    if request.method == "POST":
        try:
            category = request.json.get("name")
            if not category:
                raise AppError("Category name is required")
            
            # Convert to lowercase for consistency
            category = category.lower().strip()
            
            # Check if category already exists
            existing = supabase.table(Config.CATEGORIES_TABLE)\
                .select("*")\
                .eq("name", category)\
                .execute()
            
            if existing.data:
                return jsonify({"status": "exists", "category": category})
            
            # Add new category
            response = supabase.table(Config.CATEGORIES_TABLE)\
                .insert({"name": category})\
                .execute()
            
            return jsonify({
                "status": "success",
                "category": response.data[0]["name"]
            })
        except Exception as e:
            logger.error(f"Error adding category: {e}")
            raise AppError(f"Failed to add category: {str(e)}")

@app.route("/api/apps/import", methods=["POST"])
def import_data():
    try:
        data = request.json
        logger.info(f"Importing data: {json.dumps(data)}")  # Log the import data
        
        # Handle both formats: {"apps": [...]} and direct array [...]
        apps_to_import = data.get("apps", []) if isinstance(data, dict) else data
        
        if not isinstance(apps_to_import, list):
            raise AppError("Invalid data format - expected array of apps")
        
        # Convert and validate each app
        db_apps = []
        for app in apps_to_import:
            try:
                # If the app already exists (has an ID), update it instead of creating new
                if "id" in app:
                    existing = supabase.table(Config.APPS_TABLE)\
                        .select("*")\
                        .eq("id", app["id"])\
                        .execute()
                    
                    if existing.data:
                        db_data = validate_app_data(app)
                        db_data["id"] = app["id"]
                        
                        supabase.table(Config.APPS_TABLE)\
                            .update(db_data)\
                            .eq("id", app["id"])\
                            .execute()
                        
                        logger.info(f"Updated existing app: {app.get('name')}")
                        continue
                
                db_data = validate_app_data(app)
                db_data["id"] = app.get("id") or str(uuid.uuid4())
                db_apps.append(db_data)
                logger.info(f"Prepared app for import: {app.get('name')}")
            except Exception as e:
                logger.warning(f"Skipping invalid app {app.get('name', 'unknown')}: {str(e)}")
                continue
        
        if not db_apps and not any("id" in app for app in apps_to_import):
            raise AppError("No valid apps found to import")
        
        # Insert new apps in a single batch
        if db_apps:
            response = supabase.table(Config.APPS_TABLE)\
                .insert(db_apps)\
                .execute()
            logger.info(f"Inserted {len(db_apps)} new apps")
        
        return jsonify({
            "status": "success",
            "imported": len(db_apps),
            "updated": len([app for app in apps_to_import if "id" in app]),
            "total": len(apps_to_import)
        })
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
