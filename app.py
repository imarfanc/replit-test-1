import json
import os
import logging
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, abort
from werkzeug.exceptions import HTTPException

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

class Config:
    JSON_FILE = "data/apps.json"
    CATEGORIES_FILE = "data/categories.json"
    DEFAULT_ICON_SIZE = 60
    BACKUP_COUNT = 5

class AppError(Exception):
    pass

def load_categories():
    try:
        if not os.path.exists(Config.CATEGORIES_FILE):
            os.makedirs(os.path.dirname(Config.CATEGORIES_FILE), exist_ok=True)
            return []
        
        with open(Config.CATEGORIES_FILE, 'r') as f:
            data = json.load(f)
            return data.get('categories', [])
    except Exception as e:
        logger.error(f"Error loading categories: {e}")
        return []

class AppDataManager:
    @staticmethod
    def load_apps():
        try:
            if not os.path.exists(Config.JSON_FILE):
                os.makedirs(os.path.dirname(Config.JSON_FILE), exist_ok=True)
                return {"apps": [], "settings": {"iconSize": Config.DEFAULT_ICON_SIZE, "theme": "dark"}, 
                        "metadata": {"lastUpdated": datetime.utcnow().isoformat(), "version": "1.0"}}
            
            with open(Config.JSON_FILE, 'r') as f:
                data = json.load(f)
                # Ensure launch count exists for all apps
                for app in data.get("apps", []):
                    if "launchCount" not in app:
                        app["launchCount"] = 0
                return data
        except Exception as e:
            logger.error(f"Error loading apps: {e}")
            raise AppError("Failed to load app data")

    @staticmethod
    def save_apps(data):
        try:
            data["metadata"]["lastUpdated"] = datetime.utcnow().isoformat()
            with open(Config.JSON_FILE, 'w') as f:
                json.dump(data, f, indent=2)
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

@app.route("/")
def home():
    data = AppDataManager.load_apps()
    categories = load_categories()
    return render_template("index.html", data=data, categories=categories)

@app.route("/api/apps", methods=["GET", "POST", "PUT"])
def manage_apps():
    data = AppDataManager.load_apps()
    
    if request.method == "GET":
        return jsonify(data)
    
    if request.method == "POST":
        app_data = request.json
        validate_app_data(app_data)
        app_data["id"] = str(uuid.uuid4())
        app_data["lastModified"] = datetime.utcnow().isoformat()
        data["apps"].append(app_data)
        AppDataManager.save_apps(data)
        return jsonify({"status": "success", "app": app_data})
    
    if request.method == "PUT":
        app_data = request.json
        validate_app_data(app_data)
        for i, app in enumerate(data["apps"]):
            if app["id"] == app_data["id"]:
                app_data["lastModified"] = datetime.utcnow().isoformat()
                data["apps"][i] = app_data
                AppDataManager.save_apps(data)
                return jsonify({"status": "success", "app": app_data})
        abort(404)

@app.route("/api/settings", methods=["GET", "PUT"])
def manage_settings():
    data = AppDataManager.load_apps()
    
    if request.method == "GET":
        return jsonify(data["settings"])
    
    if request.method == "PUT":
        settings = request.json
        if "iconSize" in settings:
            if not (24 <= int(settings["iconSize"]) <= 96):
                raise AppError("Invalid icon size")
        data["settings"].update(settings)
        AppDataManager.save_apps(data)
        return jsonify({"status": "success", "settings": data["settings"]})

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

@app.route("/api/apps/<app_id>", methods=["DELETE"])
def delete_app(app_id):
    data = AppDataManager.load_apps()
    
    for i, app in enumerate(data["apps"]):
        if app["id"] == app_id:
            del data["apps"][i]
            AppDataManager.save_apps(data)
            return jsonify({"status": "success"})
    
    abort(404)

@app.route("/api/apps/<app_id>/launch", methods=["POST"])
def increment_launch_count(app_id):
    data = AppDataManager.load_apps()
    
    for app in data["apps"]:
        if app["id"] == app_id:
            app["launchCount"] = app.get("launchCount", 0) + 1
            app["lastLaunched"] = datetime.utcnow().isoformat()
            AppDataManager.save_apps(data)
            return jsonify({"status": "success", "launchCount": app["launchCount"]})
    
    abort(404)

@app.route("/api/apps/import", methods=["POST"])
def import_data():
    try:
        data = request.json
        if not isinstance(data, dict) or "apps" not in data or not isinstance(data["apps"], list):
            raise AppError("Invalid data format")
        
        # Validate each app
        for app in data["apps"]:
            validate_app_data(app)
            if "id" not in app:
                app["id"] = str(uuid.uuid4())
            app["lastModified"] = datetime.utcnow().isoformat()
        
        # Save the imported data
        AppDataManager.save_apps(data)
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Import error: {e}")
        raise AppError(f"Import failed: {str(e)}")
