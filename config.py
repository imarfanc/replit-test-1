import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # App configuration
    SECRET_KEY = os.urandom(24)
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Database configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Table configuration
    TABLE_PREFIX = "launcher_"
    APPS_TABLE = TABLE_PREFIX + "apps"
    SETTINGS_TABLE = TABLE_PREFIX + "settings"
    CATEGORIES_TABLE = TABLE_PREFIX + "categories"
    
    # App defaults
    DEFAULT_ICON_SIZE = 60
    DEFAULT_CATEGORY = "uncategorized"
    
    # API configuration
    APP_STORE_URL_PREFIX = "https://apps.apple.com/"
    
    @classmethod
    def get_supabase_client(cls):
        from supabase import create_client
        return create_client(cls.SUPABASE_URL, cls.SUPABASE_KEY) 