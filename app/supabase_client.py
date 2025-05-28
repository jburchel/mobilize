import os
import logging
from supabase import create_client, Client

# Configure logging
logger = logging.getLogger(__name__)

class SupabaseClient:
    """Wrapper for Supabase client to handle database operations."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of SupabaseClient."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase client."""
        self.supabase_url = os.environ.get('SUPABASE_URL', 'https://fwnitauuyzxnsvgsbrzr.supabase.co')
        self.supabase_key = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3bml0YXV1eXp4bnN2Z3NicnpyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDEwOTQwNzUsImV4cCI6MjA1NjY3MDA3NX0.OVhgxuiEx8kuIlQqwj5AdfcSoLUDPEM4q-6C-mtBf98')
        
        # Initialize client
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info(f"Supabase client initialized for {self.supabase_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            self.client = None
    
    def test_connection(self):
        """Test connection to Supabase."""
        if not self.client:
            logger.error("Supabase client not initialized")
            return False
        
        try:
            # Test connection by fetching a single user
            response = self.client.table('users').select('*').limit(1).execute()
            if response and hasattr(response, 'data'):
                logger.info("Supabase connection test successful")
                return True
            else:
                logger.error("Supabase connection test failed: No data returned")
                return False
        except Exception as e:
            logger.error(f"Supabase connection test failed: {str(e)}")
            return False
    
    def get_tasks(self, user_id=None, status=None, priority=None, search_text=None):
        """Get tasks from Supabase."""
        if not self.client:
            logger.error("Supabase client not initialized")
            return []
        
        try:
            # Start with base query
            query = self.client.table('tasks').select('*')
            
            # Apply filters
            if user_id:
                query = query.or_(f"assigned_to.eq.{user_id},created_by.eq.{user_id},owner_id.eq.{user_id}")
            
            if status:
                query = query.eq('status', status)
                
            if priority:
                query = query.eq('priority', priority)
            
            # Execute query
            response = query.execute()
            
            if response and hasattr(response, 'data'):
                tasks = response.data
                
                # Apply text search filter in Python (since Supabase REST doesn't support complex text search)
                if search_text and tasks:
                    filtered_tasks = []
                    search_text = search_text.lower()
                    for task in tasks:
                        # Check if search text is in title or description
                        if (
                            (task.get('title') and search_text in task.get('title', '').lower()) or
                            (task.get('description') and search_text in task.get('description', '').lower())
                        ):
                            filtered_tasks.append(task)
                    return filtered_tasks
                
                return tasks
            else:
                logger.error("No data returned from Supabase tasks query")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching tasks from Supabase: {str(e)}")
            return []

# Initialize the client
supabase = SupabaseClient.get_instance()
