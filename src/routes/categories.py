from flask import Blueprint, request, jsonify
from ..services.database import DatabaseService
from ..services.data_processing import DataProcessor
from ..models.exceptions import AppError
from config import Config

# Initialize blueprint
bp = Blueprint('categories', __name__, url_prefix='/api/categories')

# Initialize services
db = DatabaseService(Config.get_supabase_client())
processor = DataProcessor()

@bp.route('', methods=['GET'])
def get_categories():
    """Get all categories."""
    try:
        categories = db.get_categories()
        return jsonify({"categories": categories})
    except Exception as e:
        raise AppError(f"Failed to get categories: {str(e)}")

@bp.route('', methods=['POST'])
def add_category():
    """Add a new category."""
    try:
        category_name = request.json.get("name")
        if not category_name:
            raise AppError("Category name is required")
        
        # Validate and format category name
        formatted_name = processor.validate_category_name(category_name)
        
        # Add category to database
        result = db.add_category(formatted_name)
        return jsonify(result)
    
    except Exception as e:
        raise AppError(f"Failed to add category: {str(e)}")

@bp.route('/<category>/apps', methods=['GET'])
def get_apps_by_category(category):
    """Get all apps in a category."""
    try:
        apps = db.get_apps({"category": category.lower()})
        formatted_apps = [processor.format_app_response(app) for app in apps]
        return jsonify({"apps": formatted_apps})
    except Exception as e:
        raise AppError(f"Failed to get apps for category {category}: {str(e)}") 