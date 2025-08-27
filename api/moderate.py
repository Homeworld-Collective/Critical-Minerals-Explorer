import json
import os

# Try to import Vercel KV, fall back to dict if not available
HAS_KV = False
kv = None

try:
    from vercel import kv
    HAS_KV = True
except ImportError:
    print("Warning: Vercel KV not available, using in-memory storage")

ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'your_secure_admin_secret_here')

# In-memory storage fallback (for development)
_memory_storage = {}

def handler(request):
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }
    
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        if request.method == 'GET':
            return handle_get_moderate(request, headers)
        elif request.method == 'POST':
            return handle_post_moderate(request, headers)
        else:
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
    except Exception as e:
        print(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_get_moderate(request, headers):
    if not check_admin_auth(request):
        return {
            'statusCode': 401,
            'headers': headers,
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
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
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(pending_comments)
    }

def handle_post_moderate(request, headers):
    if not check_admin_auth(request):
        return {
            'statusCode': 401,
            'headers': headers,
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
    try:
        # Get request body
        if hasattr(request, 'get_json'):
            mod_data = request.get_json()
        else:
            mod_data = json.loads(request.body) if hasattr(request, 'body') else {}
        
        comment_id = mod_data.get('commentId')
        metal_name = mod_data.get('metalName')
        action = mod_data.get('action')  # 'approve' or 'reject'
        
        if not all([comment_id, metal_name, action]):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        if action not in ['approve', 'reject']:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid action'})
            }
        
        # Load comments
        comments = load_comments()
        
        if metal_name not in comments:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Metal not found'})
            }
        
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
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Comment not found'})
            }
        
        # Save updated comments
        save_comments(comments)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': f'Comment {action}d successfully'
            })
        }
        
    except Exception as e:
        print(f"Error handling POST moderate: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Internal server error'})
        }

def check_admin_auth(request):
    """Check if the request has valid admin authorization"""
    auth_header = getattr(request, 'headers', {}).get('authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    
    provided_secret = auth_header[7:]  # Remove 'Bearer ' prefix
    return provided_secret == ADMIN_SECRET

def load_comments():
    try:
        if HAS_KV:
            # Use Vercel KV in production
            return kv.get('comments') or {}
        else:
            # Use in-memory storage for development
            return _memory_storage
    except Exception as e:
        print(f"Error loading comments: {e}")
        return {}

def save_comments(comments):
    try:
        if HAS_KV:
            # Use Vercel KV in production
            kv.set('comments', comments)
        else:
            # Use in-memory storage for development
            global _memory_storage
            _memory_storage = comments
    except Exception as e:
        print(f"Error saving comments: {e}")