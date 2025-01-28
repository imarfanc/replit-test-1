import json
import os
import logging
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, abort
from werkzeug.exceptions import HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv
from src.routes import apps, settings, categories
from src.models.exceptions import AppError, handle_app_error, handle_http_error
from src.services.database import DatabaseService
from src.services.data_processing import DataProcessor
from config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__,
                static_folder='src/static',
                template_folder='src/templates')
    
    # Load configuration
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY
    
    # Register blueprints
    app.register_blueprint(apps.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(categories.bp)
    
    # Register error handlers
    app.register_error_handler(AppError, handle_app_error)
    app.register_error_handler(HTTPException, handle_http_error)
    
    # Root route
    @app.route('/')
    def index():
        """Render the main application page."""
        try:
            # Get apps with optional filtering
            category = request.args.get('category')
            sort_by = request.args.get('sort')
            order = request.args.get('order', 'asc')
            
            # Initialize services
            db = DatabaseService(Config.get_supabase_client())
            processor = DataProcessor()
            
            # Get data
            apps_data = db.get_apps()
            settings_data = db.client.table(Config.SETTINGS_TABLE).select("*").execute().data[0]
            categories = db.get_categories()
            
            # Format apps data
            formatted_apps = [processor.format_app_response(app) for app in apps_data]
            
            # Sort apps if requested
            if sort_by:
                reverse = order.lower() == 'desc'
                formatted_apps.sort(
                    key=lambda x: x.get(sort_by, ''),
                    reverse=reverse
                )
            
            # Filter by category if specified
            if category:
                formatted_apps = [
                    app for app in formatted_apps 
                    if app['category'].lower() == category.lower()
                ]
            
            # Prepare template data
            template_data = {
                "apps": formatted_apps,
                "settings": settings_data["settings"],
                "metadata": settings_data["metadata"],
                "categories": categories
            }
            
            return render_template('index.html', data=template_data)
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise AppError("Failed to load application data", 500)
    
    return app

# Create the application instance
app = create_app()
