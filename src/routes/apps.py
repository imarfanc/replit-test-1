import uuid
from flask import Blueprint, request, jsonify
from ..services.database import DatabaseService
from ..services.data_processing import DataProcessor
from ..models.exceptions import AppError
from config import Config

# Initialize blueprint
bp = Blueprint('apps', __name__, url_prefix='/api/apps')

# Initialize services
db = DatabaseService(Config.get_supabase_client())
processor = DataProcessor()

@bp.route('', methods=['GET'])
def get_apps():
    """Get all apps with optional filtering."""
    try:
        # Get filter parameters
        category = request.args.get('category')
        sort_by = request.args.get('sort')
        order = request.args.get('order', 'asc')
        
        # Build filters
        filters = {}
        if category:
            filters['category'] = category.lower()
        
        # Get apps from database
        apps = db.get_apps(filters)
        
        # Sort apps if requested
        if sort_by:
            reverse = order.lower() == 'desc'
            apps.sort(key=lambda x: x.get(processor.camel_to_snake(sort_by), ''), reverse=reverse)
        
        # Format response
        formatted_apps = [processor.format_app_response(app) for app in apps]
        return jsonify({"apps": formatted_apps})
    
    except Exception as e:
        raise AppError(f"Failed to get apps: {str(e)}")

@bp.route('', methods=['POST'])
def create_app():
    """Create a new app."""
    try:
        app_data = processor.validate_app_data(request.json)
        app_data['id'] = str(uuid.uuid4())
        
        created_app = db.create_app(app_data)
        return jsonify({
            "status": "success",
            "app": processor.format_app_response(created_app)
        }), 201
    
    except Exception as e:
        raise AppError(f"Failed to create app: {str(e)}")

@bp.route('/<app_id>', methods=['GET'])
def get_app(app_id):
    """Get a single app by ID."""
    try:
        app = db.get_app_by_id(app_id)
        if not app:
            raise AppError(f"App {app_id} not found", 404)
        
        return jsonify(processor.format_app_response(app))
    
    except Exception as e:
        raise AppError(f"Failed to get app: {str(e)}")

@bp.route('/<app_id>', methods=['PUT'])
def update_app(app_id):
    """Update an existing app."""
    try:
        app_data = processor.validate_app_data(request.json, for_update=True)
        updated_app = db.update_app(app_id, app_data)
        
        return jsonify({
            "status": "success",
            "app": processor.format_app_response(updated_app)
        })
    
    except Exception as e:
        raise AppError(f"Failed to update app: {str(e)}")

@bp.route('/<app_id>', methods=['DELETE'])
def delete_app(app_id):
    """Delete an app."""
    try:
        db.delete_app(app_id)
        return jsonify({"status": "success"})
    
    except Exception as e:
        raise AppError(f"Failed to delete app: {str(e)}")

@bp.route('/<app_id>/launch', methods=['POST'])
def launch_app(app_id):
    """Increment app launch count."""
    try:
        updated_app = db.increment_launch_count(app_id)
        return jsonify({
            "status": "success",
            "launchCount": updated_app["launch_count"]
        })
    
    except Exception as e:
        raise AppError(f"Failed to update launch count: {str(e)}")

@bp.route('/import', methods=['POST'])
def import_apps():
    """Import apps from JSON data."""
    try:
        data = request.json
        apps_to_import = data.get("apps", []) if isinstance(data, dict) else data
        
        if not isinstance(apps_to_import, list):
            raise AppError("Invalid data format - expected array of apps")
        
        imported_count = 0
        updated_count = 0
        
        for app in apps_to_import:
            try:
                app_data = processor.validate_app_data(app)
                
                if "id" in app:
                    # Update existing app
                    if db.get_app_by_id(app["id"]):
                        db.update_app(app["id"], app_data)
                        updated_count += 1
                        continue
                
                # Create new app
                app_data["id"] = str(uuid.uuid4())
                db.create_app(app_data)
                imported_count += 1
                
            except Exception as e:
                continue  # Skip invalid apps
        
        return jsonify({
            "status": "success",
            "imported": imported_count,
            "updated": updated_count,
            "total": len(apps_to_import)
        })
    
    except Exception as e:
        raise AppError(f"Import failed: {str(e)}") 