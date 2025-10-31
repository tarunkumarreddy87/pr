# EduVis Pro - Organized Project

This is the organized version of the EduVis Pro educational platform with separated pages and proper backend integration.

## Project Structure

```
organized_project/
├── api/              # API client for backend communication
├── css/              # Stylesheets
├── js/               # JavaScript files (one per page)
├── pages/            # HTML files for each page
├── index.html        # Main HTML file
├── server.js         # Frontend server with API proxy
└── package.json      # Node.js dependencies
```

## Quick Start

### Option 1: Run everything with one command (Recommended)
```bash
# On Windows
run_app.bat

# Or using PowerShell
.\run_app.ps1
```

### Option 2: Manual setup
1. **Install Python dependencies** (if not already installed):
   ```bash
   pip install -r ../requirements.txt
   ```

2. **Start the backend server** (if not already running):
   ```bash
   cd ..
   python app.py
   ```

3. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

4. **Start the frontend server**:
   ```bash
   node server.js
   ```

5. **Access the application**:
   Open your browser and go to http://localhost:8082

## Features

- Clean separation of pages into individual HTML and JS files
- Backend integration with Manim executor for video generation
- Responsive design with collapsible sidebar
- API proxy for seamless backend communication
- Modern UI with educational platform aesthetics

## API Endpoints

The frontend communicates with the backend through the following endpoints:

- `/api/generate` - Generate Manim animations
- `/video/latest` - Retrieve the latest generated video
- `/api/profile` - User profile management
- `/api/chat/messages` - Chat functionality
- And more...

All API requests are automatically proxied from the frontend server to the backend.

## Development

To modify the project:

1. Edit HTML files in the `pages/` directory
2. Update JavaScript functionality in the `js/` directory
3. Modify styles in the `css/` directory
4. Update API calls in the `api/` directory

The main entry point is `index.html` which loads all other pages dynamically.