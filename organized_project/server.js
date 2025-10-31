// Simple HTTP server for the organized project that proxies API requests to the backend

const http = require('http');
const fs = require('fs');
const path = require('path');
const { createProxy } = require('http-proxy');

// Port to run the server on
const PORT = 8082;
const BACKEND_PORT = 5000;

// MIME types for different file extensions
const MIME_TYPES = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

// Create a proxy to forward API requests to the backend
const proxy = createProxy({});

// Create the HTTP server
const server = http.createServer((req, res) => {
  console.log(`Request received: ${req.method} ${req.url}`);
  
  // Check if this is an API request
  if (req.url.startsWith('/api/') || req.url.startsWith('/video/')) {
    // Proxy API requests to the backend
    proxy.web(req, res, { target: `http://localhost:${BACKEND_PORT}` }, (err) => {
      console.error('Proxy error:', err);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Backend service unavailable' }));
    });
    return;
  }
  
  // Parse the requested URL
  let filePath = '.' + req.url;
  
  // If the URL is just '/', serve index.html
  if (filePath === './') {
    filePath = './index.html';
  }
  
  // Resolve the full file path
  filePath = path.resolve(filePath);
  
  // Security check to prevent directory traversal
  const rootDir = path.resolve('.');
  if (!filePath.startsWith(rootDir)) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    res.end('403 Forbidden');
    return;
  }
  
  // Get the file extension
  const extname = path.extname(filePath).toLowerCase();
  
  // Set the content type based on the file extension
  const contentType = MIME_TYPES[extname] || 'application/octet-stream';
  
  // Read the file
  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // File not found
        console.log(`File not found: ${filePath}`);
        res.writeHead(404, { 'Content-Type': 'text/html' });
        res.end('<h1>404 Not Found</h1><p>The requested file was not found on this server.</p>');
      } else {
        // Server error
        console.error(`Server error: ${err.code}`);
        res.writeHead(500, { 'Content-Type': 'text/html' });
        res.end('<h1>500 Internal Server Error</h1><p>Sorry, there was an error on the server.</p>');
      }
    } else {
      // Success
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
    }
  });
});

// Start the server
server.listen(PORT, () => {
  console.log(`Organized project server running at http://localhost:${PORT}/`);
  console.log(`API requests will be proxied to backend at http://localhost:${BACKEND_PORT}/`);
  console.log(`Press Ctrl+C to stop the server`);
});