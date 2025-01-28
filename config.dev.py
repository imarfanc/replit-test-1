"""Development configuration."""
from config import Config

class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = True
    
    # Logging
    LOG_LEVEL = "DEBUG"
    
    # Development database - can be overridden by environment variables
    SUPABASE_URL = "http://localhost:54321"  # Default Supabase local development URL
    
    # Additional development settings
    CORS_ENABLED = True
    JSON_SORT_KEYS = False  # Better for debugging 