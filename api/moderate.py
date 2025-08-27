import json
import os

# Try to import requests for Upstash REST API
HAS_REDIS = False

try:
    import requests
    # Check for Upstash credentials
    REDIS_URL = os.getenv('KV_REST_API_URL')
    REDIS_TOKEN = os.getenv('KV_REST_API_TOKEN')
    
    if REDIS_URL and REDIS_TOKEN:
        HAS_REDIS = True
        print("Using Upstash Redis REST API")
    else:
        print("Redis credentials not found in environment")
except ImportError:
    print("Warning: requests not available, using in-memory storage")

ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'your_secure_admin_secret_here')

# In-memory storage fallback (for development)
_memory_storage = {}

def handler(request, response):
    """Vercel serverless function handler for moderation"""
    # Set CORS headers
    response.headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }
    
    if request.method == 'OPTIONS':
        response.status_code = 200
        return ""
    
    try:
        # Check admin auth
        auth_header = request.headers.get('authorization', '')
        if not auth_header.startswith('Bearer '):
            response.status_code = 401
            return json.dumps({'error': 'Unauthorized'})
        
        provided_secret = auth_header[7:]  # Remove 'Bearer ' prefix
        if provided_secret != ADMIN_SECRET:
            response.status_code = 401
            return json.dumps({'error': 'Unauthorized'})
        
        if request.method == 'GET':
            # Load all comments
            comments = load_comments()
            
            # Get all unapproved comments from all metals
            pending_comments = []
            for metal, metal_comments in comments.items():
                for comment in metal_comments:
                    if not comment.get('approved', False):
                        pending_comments.append(comment)
            
            # Sort by timestamp (newest first)
            pending_comments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            response.status_code = 200
            return json.dumps(pending_comments)
            
        elif request.method == 'POST':
            # Get request body
            try:
                mod_data = json.loads(request.body)
            except json.JSONDecodeError:
                response.status_code = 400
                return json.dumps({'error': 'Invalid JSON'})
            
            comment_id = mod_data.get('commentId')
            metal_name = mod_data.get('metalName')
            action = mod_data.get('action')  # 'approve' or 'reject'
            
            if not all([comment_id, metal_name, action]):
                response.status_code = 400
                return json.dumps({'error': 'Missing required fields'})
            
            if action not in ['approve', 'reject']:
                response.status_code = 400
                return json.dumps({'error': 'Invalid action'})
            
            # Load comments
            comments = load_comments()
            
            if metal_name not in comments:
                response.status_code = 404
                return json.dumps({'error': 'Metal not found'})
            
            # Find and modify the comment
            comment_found = False
            for i, comment in enumerate(comments[metal_name]):
                if str(comment.get('id')) == str(comment_id):
                    if action == 'approve':
                        comments[metal_name][i]['approved'] = True
                    else:  # reject
                        comments[metal_name].pop(i)  # Remove rejected comments
                    comment_found = True
                    break
            
            if not comment_found:
                response.status_code = 404
                return json.dumps({'error': 'Comment not found'})
            
            # Save updated comments
            save_comments(comments)
            
            response.status_code = 200
            return json.dumps({
                'success': True,
                'message': f'Comment {action}d successfully'
            })
            
        else:
            response.status_code = 405
            return json.dumps({'error': 'Method not allowed'})
            
    except Exception as e:
        print(f"Handler error: {e}")
        response.status_code = 500
        return json.dumps({'error': 'Internal server error', 'details': str(e)})

def load_comments():
    """Load comments from Upstash Redis or memory"""
    try:
        if HAS_REDIS:
            import requests
            url = f"{os.getenv('KV_REST_API_URL')}/get/comments"
            headers = {
                'Authorization': f"Bearer {os.getenv('KV_REST_API_TOKEN')}"
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                if result:
                    return json.loads(result)
            return {}
        else:
            # Use in-memory storage for development
            return _memory_storage
    except Exception as e:
        print(f"Error loading comments: {e}")
        return {}

def save_comments(comments):
    """Save comments to Upstash Redis or memory"""
    try:
        if HAS_REDIS:
            import requests
            url = f"{os.getenv('KV_REST_API_URL')}/set/comments"
            headers = {
                'Authorization': f"Bearer {os.getenv('KV_REST_API_TOKEN')}",
                'Content-Type': 'application/json'
            }
            
            # Upstash expects the value as a JSON string
            data = {
                'value': json.dumps(comments)
            }
            
            response = requests.post(url, json=data, headers=headers)
            if response.status_code != 200:
                print(f"Failed to save comments: {response.text}")
        else:
            # Use in-memory storage for development
            global _memory_storage
            _memory_storage = comments
    except Exception as e:
        print(f"Error saving comments: {e}")