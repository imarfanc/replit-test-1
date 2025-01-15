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
    DEFAULT_ICON_SIZE = 60
    BACKUP_COUNT = 5

class AppError(Exception):
    pass

class AppDataManager:
    @staticmethod
    def load_apps():
        try:
            if not os.path.exists(Config.JSON_FILE):
                os.makedirs(os.path.dirname(Config.JSON_FILE), exist_ok=True)
                return {"apps": [], "settings": {"iconSize": Config.DEFAULT_ICON_SIZE, "theme": "dark"}, 
                        "metadata": {"lastUpdated": datetime.utcnow().isoformat(), "version": "1.0"}}
            
            with open(Config.JSON_FILE, 'r') as f:
                return json.load(f)
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
    required = ["name", "category", "iconUrl", "appStoreLink"]
    if not all(key in data for key in required):
        raise AppError("Missing required fields")
    
    if not data["appStoreLink"].startswith("https://apps.apple.com/"):
        raise AppError("Invalid App Store link")

@app.route("/")
def home():
    data = AppDataManager.load_apps()
    return render_template("index.html", data=data)

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
