import { kv } from '@vercel/kv';

// Admin authentication from environment variables
const ADMIN_SECRET = process.env.ADMIN_SECRET;

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Check authentication
  const authHeader = req.headers.authorization;
  if (!ADMIN_SECRET || !authHeader || authHeader !== `Bearer ${ADMIN_SECRET}`) {
    return res.status(401).json({ error: 'Unauthorized - Admin secret not configured or invalid' });
  }

  try {
    if (req.method === 'GET') {
      // Get all pending comments for moderation
      const allKeys = [];
      let cursor = '0';
      
      // Scan for all comment keys
      do {
        const result = await kv.scan(cursor, { match: 'comments:*' });
        cursor = result[0];
        allKeys.push(...result[1]);
      } while (cursor !== '0');

      const pendingComments = [];
      
      for (const key of allKeys) {
        const comments = await kv.get(key) || [];
        const metalName = key.replace('comments:', '');
        
        comments.forEach(comment => {
          if (!comment.approved) {
            pendingComments.push({
              ...comment,
              metalName,
              key
            });
          }
        });
      }

      // Sort by timestamp, newest first
      pendingComments.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

      res.status(200).json(pendingComments);
    }
    else if (req.method === 'POST') {
      // Approve or reject a comment
      const { commentId, action, metalName } = req.body;
      
      if (!commentId || !action || !metalName) {
        return res.status(400).json({ error: 'Missing required fields' });
      }

      const key = `comments:${metalName}`;
      const comments = await kv.get(key) || [];
      
      if (action === 'approve') {
        // Approve the comment
        const updated = comments.map(comment => 
          comment.id === commentId 
            ? { ...comment, approved: true, approvedAt: new Date().toISOString() }
            : comment
        );
        await kv.set(key, updated);
        
        res.status(200).json({ success: true, message: 'Comment approved' });
      }
      else if (action === 'reject') {
        // Remove the comment
        const filtered = comments.filter(comment => comment.id !== commentId);
        await kv.set(key, filtered);
        
        res.status(200).json({ success: true, message: 'Comment rejected and removed' });
      }
      else {
        res.status(400).json({ error: 'Invalid action' });
      }
    }
    else {
      res.status(405).json({ error: 'Method not allowed' });
    }
  } catch (error) {
    console.error('Moderation API Error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}