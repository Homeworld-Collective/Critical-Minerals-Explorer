import { kv } from '@vercel/kv';

// Configuration from environment variables
const MAX_COMMENTS_PER_HOUR = parseInt(process.env.MAX_COMMENTS_PER_HOUR) || 3;
const COMMENT_MAX_LENGTH = parseInt(process.env.COMMENT_MAX_LENGTH) || 500;

// Helper function to validate comment data
function validateComment(comment) {
  const required = ['selectedText', 'comment', 'metalName', 'context'];
  return required.every(field => comment[field] && comment[field].toString().trim().length > 0);
}

// Helper function to sanitize comment data
function sanitizeComment(comment) {
  return {
    id: Date.now() + Math.random(),
    selectedText: comment.selectedText.trim().substring(0, COMMENT_MAX_LENGTH),
    comment: comment.comment.trim().substring(0, COMMENT_MAX_LENGTH),
    metalName: comment.metalName.toLowerCase().trim(),
    context: {
      sectionTitle: comment.context?.sectionTitle?.trim().substring(0, 200) || 'Unknown Section',
      selectedText: comment.selectedText.trim().substring(0, COMMENT_MAX_LENGTH)
    },
    timestamp: new Date().toISOString(),
    approved: false, // Comments start as unapproved for moderation
    ip: null // Will be set from request
  };
}

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    if (req.method === 'GET') {
      // Get comments for a specific metal
      const { metal } = req.query;
      
      if (!metal) {
        return res.status(400).json({ error: 'Metal parameter is required' });
      }

      const key = `comments:${metal.toLowerCase()}`;
      const comments = await kv.get(key) || [];
      
      // Only return approved comments for public viewing
      const approvedComments = comments.filter(comment => comment.approved);
      
      res.status(200).json(approvedComments);
    } 
    else if (req.method === 'POST') {
      // Add a new comment
      const comment = req.body;
      
      if (!validateComment(comment)) {
        return res.status(400).json({ error: 'Invalid comment data' });
      }

      // Sanitize and enhance comment data
      const sanitizedComment = sanitizeComment(comment);
      
      // Add IP address for moderation purposes (if available)
      const forwarded = req.headers['x-forwarded-for'];
      const ip = forwarded ? forwarded.split(/, /)[0] : req.connection?.remoteAddress;
      sanitizedComment.ip = ip;

      // Get existing comments for this metal
      const key = `comments:${sanitizedComment.metalName}`;
      const existingComments = await kv.get(key) || [];
      
      // Basic spam prevention: limit comments per IP per metal per hour
      if (ip) {
        const recentComments = existingComments.filter(c => 
          c.ip === ip && 
          new Date(c.timestamp) > new Date(Date.now() - 60 * 60 * 1000)
        );
        
        if (recentComments.length >= MAX_COMMENTS_PER_HOUR) {
          return res.status(429).json({ error: `Too many comments. Please wait before commenting again. (Limit: ${MAX_COMMENTS_PER_HOUR} per hour)` });
        }
      }

      // Add new comment
      existingComments.push(sanitizedComment);
      
      // Store back to KV
      await kv.set(key, existingComments);
      
      res.status(201).json({ 
        success: true, 
        message: 'Comment submitted successfully! It will appear after moderation.',
        id: sanitizedComment.id
      });
    } 
    else {
      res.status(405).json({ error: 'Method not allowed' });
    }
  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}