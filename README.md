# Python Animation Generator with 3D Avatar Tutor

This application combines a Python animation generator with a 3D avatar tutor for interactive learning experiences.

## Project Structure

```
cop/
├── app.py                 # Main Flask application
├── manim_executor.py      # Manim animation execution engine
├── cleanup_animations.py  # Animation file cleanup utility
├── start_avatar.bat       # Windows script to start avatar services
├── run_eduviz.py          # Cross-platform startup script
├── run_eduviz.bat         # Windows startup script
├── run_eduviz.sh          # Unix/Linux/Mac startup script
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   └── index.html         # Main interface
├── avatar/                # 3D Avatar components
│   ├── backend/           # Avatar backend (Node.js)
│   └── frontend/          # Avatar frontend (React Three Fiber)
└── anim_generated/        # Generated animation files (created automatically)
```

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Avatar Services Dependencies

```bash
# Install avatar backend dependencies
cd avatar/backend
npm install

# Install avatar frontend dependencies
cd ../frontend
npm install
```

## Running the Application

### Method 1: Simple Start (Recommended)

On Windows, double-click `run_eduviz.bat` to start the entire application.

On Unix/Linux/Mac systems, run `./run_eduviz.sh` from the terminal.

This will automatically:
- Install dependencies if needed
- Start the Flask application on port 5000
- Open your browser to http://localhost:5000

### Method 2: Using the Start Script (Windows)

Double-click `start_avatar.bat` to start the avatar services, then:

```bash
# Start the main Flask application
python app.py
```

### Method 3: Manual Start

1. Start the avatar backend:
   ```bash
   cd avatar/backend
   npm start
   ```
   (Runs on port 8004)

2. Start the avatar frontend:
   ```bash
   cd avatar/frontend
   npm run dev
   ```
   (Runs on port 5173)

3. Start the main application:
   ```bash
   python app.py
   ```
   (Runs on port 5000)

## Accessing the Application

1. Main Interface: http://localhost:5000
2. Avatar Interface: http://localhost:5173

## Features

### Main Interface (Port 5000)
- Natural language to Manim code conversion
- Animation generation and playback
- Code editor with syntax highlighting
- Example animations
- Avatar Tutor button to access 3D avatar
- Professional sidebar navigation with profile section

### Avatar Tutor (Port 5173)
- Full-screen 3D avatar interface
- Voice integration with ElevenLabs
- Facial expression controls
- Interview simulation mode
- Real-time lip synchronization

## Usage

1. **Generate Animations**:
   - Enter a description in the input field
   - Click "Ask" to generate Manim code
   - Click "Generate Animation" to create the video
   - View the generated animation

2. **Use Avatar Tutor**:
   - Click the "Avatar Tutor" button in the main interface
   - Interact with the 3D avatar
   - Use voice controls and expression buttons
   - Practice interview scenarios

## Cleanup

To remove old animation files and free up space:
- Use the "Cleanup Files" button in the main interface
- Or run: `python cleanup_animations.py`

## Requirements

- Python 3.8+
- Node.js 16+
- npm 8+
- Manim Community Edition
- OpenAI API key (for avatar backend)
- ElevenLabs API key (for voice features, optional)

## Troubleshooting

1. **Avatar not loading**:
   - Ensure both avatar backend and frontend are running
   - Check that ports 8004 and 5173 are not blocked
   - Verify API keys are set in avatar/backend/.env

2. **Animation generation fails**:
   - Check the error message for syntax issues
   - Ensure Manim is properly installed
   - Verify the generated code structure

3. **Video not playing**:
   - Check browser console for errors
   - Ensure ffmpeg is available for video processing
   - Try refreshing the page