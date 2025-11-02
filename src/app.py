from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
import os
import logging
import datetime
import shutil
import json
import uuid
import requests
import ast
import re
# Updated import path to reflect new directory structure
from manim_executor import execute_manim_script, VIDEO_DIR, cleanup_old_animations
from typing import Dict, Optional
from gtts import gTTS

# Set up logging with more detailed configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)


# OpenRouter API Configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
# Updated static folder path to reflect new directory structure
app = Flask(__name__, template_folder='../templates', static_folder='../public')
app.config['DEBUG'] = False  # Disable debug mode to prevent frequent restarts
app.config['USE_RELOADER'] = False  # Disable reloader to prevent frequent restarts

# Global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error
    logger.error(f"Unhandled error occurred: {str(e)}", exc_info=True)
    
    # Return a generic error response
    return jsonify({
        "error": "An unexpected error occurred",
        "message": "Please try again later"
    }), 500

CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:5173"], supports_credentials=True)  # Enable CORS for all routes

# Store latest video file path (in-memory for simplicity)
LATEST_VIDEO: Dict[str, Optional[str]] = {"path": None, "error": None}

# Create directory for generated animations in the generated folder
os.makedirs('generated/anim_generated', exist_ok=True)

# Custom route to serve assets from the new public directory
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    try:
        logger.info(f"Attempting to serve asset: {filename}")
        public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public')
        logger.info(f"Public directory path: {public_dir}")
        logger.info(f"Full file path: {os.path.join(public_dir, filename)}")
        if not os.path.exists(os.path.join(public_dir, filename)):
            logger.error(f"File not found: {filename}")
            return jsonify({"error": "File not found"}), 404
        return send_from_directory(public_dir, filename)
    except Exception as e:
        logger.error(f"Error serving asset {filename}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error serving asset: {str(e)}"}), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return empty response with 204 No Content status

@app.route('/@vite/client')
def vite_client():
    return '', 204  # Return empty response to prevent 404 errors

@app.route('/api/voiceover', methods=['POST'])
def generate_voiceover():
    try:
        data = request.json
        if data is None:
            return jsonify({"error": "No data provided"}), 400
        text = data.get('text')
        service = data.get('service', 'gtts')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
            
        # Create directory for audio files if it doesn't exist
        audio_dir = os.path.join('../public', 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"voiceover_{uuid.uuid4()}.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # Use gTTS for text-to-speech
        tts = gTTS(text=text, lang='en')
        tts.save(filepath)
        
        # Return the URL to the generated audio file
        audio_url = f"/assets/audio/{filename}"
        return jsonify({"audio_url": audio_url, "success": True})
        
    except Exception as e:
        logger.error(f"Error generating voiceover: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to generate voiceover: {str(e)}"}), 500

@app.route('/api/cleanup_audio', methods=['POST'])
def cleanup_audio():
    try:
        # Delete audio files older than 1 hour
        audio_dir = os.path.join('../public', 'audio')
        if os.path.exists(audio_dir):
            current_time = datetime.datetime.now()
            for filename in os.listdir(audio_dir):
                if filename.startswith('voiceover_'):
                    file_path = os.path.join(audio_dir, filename)
                    file_creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                    if (current_time - file_creation_time).total_seconds() > 3600:  # 1 hour
                        os.remove(file_path)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error cleaning up audio files: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to clean up audio files: {str(e)}"}), 500

@app.route("/")
def index():
    # Redirect to the professional website as the default page
    return render_template('professional_website.html')

@app.route("/simplified")
def simplified():
    # Serve the simplified professional website
    return render_template('professional_website.html')

@app.route("/enhanced")
def enhanced():
    # Serve the professional website
    return render_template('professional_website.html')

@app.route("/chatgpt")
def chatgpt():
    # Serve the ChatGPT-style interface
    return render_template('chatgpt_interface.html')

@app.route("/avatar")
def avatar():
    # Serve the avatar frontend HTML
    avatar_path = os.path.join('avatar', 'frontend', 'public', 'fullscreen-avatar-demo.html')
    if os.path.exists(avatar_path):
        return send_file(avatar_path)
    else:
        # Fallback to a simple avatar page
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Interview AI Tutor</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #1a2a6c, #2c3e50);
                    color: white;
                    min-height: 100vh;
                    overflow: hidden;
                }
                
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                
                header {
                    text-align: center;
                    padding: 20px 0;
                    margin-bottom: 30px;
                }
                
                h1 {
                    font-size: 2.5rem;
                    margin-bottom: 10px;
                    background: linear-gradient(to right, #3498db, #2c3e50);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                
                .subtitle {
                    font-size: 1.2rem;
                    opacity: 0.8;
                    max-width: 600px;
                    margin: 0 auto;
                }
                
                .content {
                    display: flex;
                    flex: 1;
                    gap: 30px;
                }
                
                .features {
                    flex: 1;
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }
                
                .feature-card {
                    margin-bottom: 25px;
                    padding: 20px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 15px;
                    transition: transform 0.3s ease;
                }
                
                .feature-card:hover {
                    transform: translateY(-5px);
                    background: rgba(255, 255, 255, 0.1);
                }
                
                .feature-card h3 {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 10px;
                    color: #3498db;
                }
                
                .feature-card p {
                    opacity: 0.9;
                    line-height: 1.6;
                }
                
                .demo-area {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                }
                
                .avatar-preview {
                    flex: 1;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    overflow: hidden;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }
                
                .avatar-placeholder {
                    width: 80%;
                    height: 80%;
                    background: linear-gradient(45deg, #3498db, #8e44ad);
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    overflow: hidden;
                }
                
                .avatar-placeholder::before {
                    content: "";
                    position: absolute;
                    width: 150%;
                    height: 150%;
                    background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
                    transform: rotate(45deg);
                    animation: shine 3s infinite;
                }
                
                @keyframes shine {
                    0% { transform: rotate(45deg) translateX(-100%); }
                    100% { transform: rotate(45deg) translateX(100%); }
                }
                
                .avatar-placeholder-inner {
                    width: 70%;
                    height: 70%;
                    background: rgba(0, 0, 0, 0.2);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 3rem;
                }
                
                .controls {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 20px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }
                
                .control-buttons {
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    flex-wrap: wrap;
                }
                
                .btn {
                    padding: 12px 25px;
                    border: none;
                    border-radius: 50px;
                    background: linear-gradient(to right, #6a11cb, #2575fc);
                    color: white;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                }
                
                .btn:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
                }
                
                .btn.secondary {
                    background: rgba(255, 255, 255, 0.2);
                }
                
                .btn.secondary:hover {
                    background: rgba(255, 255, 255, 0.3);
                }
                
                .btn.fullscreen {
                    background: linear-gradient(to right, #27ae60, #2ecc71);
                }
                
                footer {
                    text-align: center;
                    padding: 20px;
                    margin-top: 30px;
                    opacity: 0.7;
                    font-size: 0.9rem;
                }
                
                @media (max-width: 768px) {
                    .content {
                        flex-direction: column;
                    }
                    
                    h1 {
                        font-size: 2rem;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Interview AI Tutor</h1>
                    <p class="subtitle">Immersive 3D avatar experience with voice and expression controls</p>
                </header>
                
                <div class="content">
                    <div class="features">
                        <div class="feature-card">
                            <h3>
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                    <circle cx="12" cy="7" r="4"></circle>
                                </svg>
                                Realistic 3D Avatar
                            </h3>
                            <p>High-quality ReadyPlayerMe avatar with realistic facial expressions and lip synchronization for natural conversation.</p>
                        </div>
                        
                        <div class="feature-card">
                            <h3>
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                                    <line x1="12" y1="19" x2="12" y2="23"></line>
                                    <line x1="8" y1="23" x2="16" y2="23"></line>
                                </svg>
                                Voice Integration
                            </h3>
                            <p>Text-to-speech with ElevenLabs and real-time lip synchronization for immersive conversation experience.</p>
                        </div>
                        
                        <div class="feature-card">
                            <h3>
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <line x1="12" y1="16" x2="12" y2="12"></line>
                                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                                </svg>
                                Expression Controls
                            </h3>
                            <p>Dynamic facial expressions including smile, serious, thinking, confident, and confused for contextual responses.</p>
                        </div>
                        
                        <div class="feature-card">
                            <h3>
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
                                </svg>
                                Full-Screen Mode
                            </h3>
                            <p>Immersive full-screen experience with intuitive controls and responsive design for all devices.</p>
                        </div>
                    </div>
                    
                    <div class="demo-area">
                        <div class="avatar-preview">
                            <div class="avatar-placeholder">
                                <div class="avatar-placeholder-inner">
                                    🤖
                                </div>
                            </div>
                        </div>
                        
                        <div class="controls">
                            <div class="control-buttons">
                                <button class="btn secondary" onclick="showInstructions()">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="12" cy="12" r="10"></circle>
                                        <line x1="12" y1="16" x2="12" y2="12"></line>
                                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                                    </svg>
                                    Instructions
                                </button>
                                <button class="btn fullscreen" onclick="startAvatarExperience()">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                                    </svg>
                                    Start Experience
                                </button>
                                <button class="btn" onclick="window.close()">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <footer>
                    <p>Interview AI Tutor • Built with React Three Fiber and ReadyPlayerMe</p>
                </footer>
            </div>

            <script>
                function showInstructions() {
                    alert("To use the full avatar experience:\\n\\n1. Make sure the avatar backend is running on port 8004\\n2. Start the avatar frontend separately using 'npm run dev' in the avatar/frontend directory\\n3. Click 'Start Experience' to open the full avatar interface\\n\\nFor the best experience, use a modern browser with WebGL support.");
                }
                
                function startAvatarExperience() {
                    // Try to open the avatar frontend in a new window
                    const avatarWindow = window.open('http://localhost:5173', '_blank');
                    
                    // If popup blocker prevents opening, show instructions
                    if (!avatarWindow) {
                        alert("Please allow popups for this site to open the avatar interface.\\n\\nAlternatively, you can manually navigate to:\\nhttp://localhost:5173\\n\\nMake sure the avatar frontend is running first.");
                    }
                }
            </script>
        </body>
        </html>
        '''

@app.route("/api/generate", methods=["POST"])
def generate():
    """
    Receives Manim script (from n8n), executes it, and returns video URL or error.
    """
    try:
        logger.info("Received request to /api/generate")
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        
        script = data.get("script") if data else None
        if not script:
            logger.warning("No script provided in request")
            return jsonify({"error": "No script provided"}), 400
        
        logger.info(f"Received script (first 200 chars): {script[:200]}...")
        
        # Additional validation to catch common errors before execution
        if "self." in script and "class " not in script:
            error_msg = "Invalid script: 'self' used outside of class context. Please ensure your code is properly structured within a class that inherits from Scene."
            logger.error(error_msg)
            return jsonify({
                "error": error_msg,
                "details": "The script contains 'self' references but is not properly structured within a Scene class."
            }), 400
        
        # Log the script for debugging
        logger.debug(f"Full script: {script}")
        
        video_path, error = execute_manim_script(script)
        if error:
            LATEST_VIDEO["path"] = None
            LATEST_VIDEO["error"] = error
            logger.error(f"Execution error: {error}")
            # Return more detailed error information
            return jsonify({
                "error": error,
                "details": "Check the server logs for more information about the error."
            }), 400
        
        # Save latest video path
        LATEST_VIDEO["path"] = video_path
        LATEST_VIDEO["error"] = None
        # Return endpoint for video
        video_url = "/video/latest"
        logger.info(f"Successfully generated video at: {video_path}")
        
        # Check if the video includes voiceover
        has_voiceover = False
        if video_path and isinstance(video_path, str):
            # Check if the video filename indicates voiceover is included
            has_voiceover = "_with_voiceover" in video_path or "VoiceoverScene" in (script or "")
        
        return jsonify({
            "video_url": video_url,
            "message": "Animation generated successfully!",
            "has_voiceover": has_voiceover
        })
    
    except Exception as e:
        logger.exception("Error in generate endpoint")
        return jsonify({
            "error": f"Server error: {str(e)}",
            "details": "An unexpected error occurred while generating the animation."
        }), 500

@app.route("/video/latest")
def get_latest_video():
    """
    Streams the latest generated video.
    """
    try:
        logger.info("Received request to /video/latest")
        video_path = LATEST_VIDEO.get("path")
        logger.debug(f"Video path from LATEST_VIDEO: {video_path}")
        
        if not video_path or not os.path.exists(video_path):
            logger.warning(f"Video not found at path: {video_path}")
            # Return a default placeholder video or image
            placeholder_path = os.path.join(os.path.dirname(__file__), "..", "public", "videos",
"placeholder.txt")
            if os.path.exists(placeholder_path):
                return send_file(placeholder_path, mimetype="text/plain")
            else:
                return "No video available.", 404
            
        logger.info(f"Serving video from: {video_path}")
        return send_file(video_path, mimetype="video/mp4", conditional=True)
    except Exception as e:
        logger.exception("Error serving video")
        # Return a default placeholder video or image
        placeholder_path = os.path.join(os.path.dirname(__file__), "..", "public", "videos",
"placeholder.txt")
        if os.path.exists(placeholder_path):
            return send_file(placeholder_path, mimetype="text/plain")
        else:
            return f"Error serving video: {str(e)}", 500

@app.route("/api/cleanup", methods=["POST"])
def cleanup():
    """
    Cleanup old animation files to free up space.
    """
    try:
        # Optimize cleanup to run faster by reducing max_age_hours
        deleted_count = cleanup_old_animations(max_age_hours=1)  # Clean up files older than 1 hour
        return jsonify({
            "message": f"Cleanup completed. Deleted {deleted_count} old directories.",
            "deleted_count": deleted_count
        })
    except Exception as e:
        logger.exception("Error during cleanup")
        return jsonify({
            "error": f"Cleanup failed: {str(e)}"
        }), 500

@app.route("/healthz")
def health_check():
    """
    Health check endpoint for Render and other monitoring services.
    """
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.now().isoformat()})

@app.route("/api/test-fix", methods=["POST"])
def test_fix():
    """
    Test endpoint to verify that the positional argument fix is working.
    """
    try:
        data = request.get_json()
        script = data.get("script") if data else None
        
        if not script:
            return jsonify({"error": "No script provided"}), 400
        
        # Import the sanitize function from manim_executor
        from manim_executor import sanitize_manim_code
        
        # Sanitize the script
        sanitized_script = sanitize_manim_code(script)
        
        return jsonify({
            "original_script": script,
            "sanitized_script": sanitized_script,
            "fix_applied": script != sanitized_script
        })
    
    except Exception as e:
        logger.exception("Error in test-fix endpoint")
        return jsonify({"error": str(e)}), 500

@app.route("/api/n8n/webhook", methods=["POST"])
def n8n_webhook():
    """
    Receives webhook from n8n with natural language input,
    converts it to Manim code, executes it, and returns the video URL.
    """
    try:
        logger.info("Received webhook from n8n")
        data = request.get_json()
        logger.debug(f"Webhook data: {data}")
        
        # Extract the natural language input from n8n payload
        # This assumes n8n sends data in a specific format
        # You may need to adjust this based on your n8n workflow
        if isinstance(data, dict):
            # Try different possible keys for the input
            natural_language_input = (
                data.get("input") or 
                data.get("text") or 
                data.get("query") or 
                data.get("prompt") or
                str(data)
            )
        else:
            natural_language_input = str(data)
        
        if not natural_language_input:
            logger.warning("No input provided in n8n webhook")
            return jsonify({"error": "No input provided"}), 400
        
        logger.info(f"Received natural language input: {natural_language_input}")
        
        # Convert natural language to Manim code
        # In a real implementation, you would use an LLM or predefined templates
        # For now, we'll use a simple template-based approach
        manim_code = generate_manim_code_from_prompt(natural_language_input)
        
        logger.info(f"Generated Manim code: {manim_code}")
        
        # Execute the generated Manim code
        video_path, error = execute_manim_script(manim_code)
        if error:
            LATEST_VIDEO["path"] = None
            LATEST_VIDEO["error"] = error
            logger.error(f"Execution error: {error}")
            return jsonify({
                "error": error,
                "details": "Check the server logs for more information about the error.",
                "generated_code": manim_code
            }), 400
        
        # Save latest video path
        LATEST_VIDEO["path"] = video_path
        LATEST_VIDEO["error"] = None
        
        # Return the generated code in the format expected by the frontend
        # The frontend expects either:
        # 1. {manimCode: "...", timeline: "..."}
        # 2. [{manim_code: "..."}]
        # 3. {script: "..."}
        return jsonify({
            "manimCode": manim_code,
            "timeline": "Generated from natural language input: " + natural_language_input
        })
    
    except Exception as e:
        logger.exception("Error in n8n webhook endpoint")
        return jsonify({
            "error": f"Server error: {str(e)}",
            "details": "An unexpected error occurred while processing the n8n webhook."
        }), 500

@app.route("/api/openrouter/generate-code", methods=["POST"])
def openrouter_generate_code():
    """
    Generate Manim code using OpenRouter API based on user input.
    """
    try:
        logger.info("=== STARTING OPENROUTER CODE GENERATION ===")
        logger.info("Received request to OpenRouter code generation")
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        logger.debug(f"Request data type: {type(data)}")
        
        user_input = data.get("input") if data else None
        custom_api_key = data.get("api_key") if data else None  # Allow custom API key
        logger.info(f"Custom API key provided: {'Yes' if custom_api_key else 'No'}")
        
        if not user_input:
            logger.warning("No input provided in request")
            return jsonify({"error": "No input provided"}), 400
        
        logger.info(f"Received user input: {user_input}")
        
        # Use custom API key if provided, otherwise use default
        api_key = custom_api_key if custom_api_key else OPENROUTER_API_KEY
        
        # Add extensive debugging for API key
        logger.info(f"Selected API key: {api_key}")
        logger.info(f"Selected API key type: {type(api_key)}")
        logger.info(f"Selected API key length: {len(api_key) if api_key else 0}")
        logger.info(f"Default API key length: {len(OPENROUTER_API_KEY)}")
        logger.info(f"Keys match: {api_key == OPENROUTER_API_KEY if api_key else 'N/A'}")
        
        # Log the API key being used (first 10 and last 5 characters for debugging)
        if api_key:
            logger.info(f"Using API key: {api_key[:10]}...{api_key[-5:]}")
            logger.info(f"API key length: {len(api_key)}")
        else:
            logger.error("API key is None or empty!")
            return jsonify({"error": "API key is missing"}), 401
        
        # Validate that we have a valid API key
        if not api_key or not api_key.startswith("sk-or-v"):
            logger.error(f"Invalid API key format: {api_key}")
            return jsonify({"error": "Invalid API key format"}), 401
            
        # Additional validation
        if len(api_key) < 50:  # API keys should be longer than 50 characters
            logger.error(f"API key too short: {len(api_key)} characters")
            return jsonify({"error": "API key too short"}), 401
            
        # Prepare the prompt for OpenRouter
        system_prompt = """ 
 You are a professional Manim animation director and Python developer. 
 You create visually stunning, high-quality, and educational Manim animations based on input text or concepts. 
 
 🎯 GOAL: 
 Produce smooth, cinematic, and educational animations that are visually clear, centered, well-timed, and free of any overlapping. 
 
 ⚙ RULES: 
 
 1. *Visual Composition* 
    - Maintain balanced layouts: ABSOLUTELY NO overlaps between text, shapes, or graphs. 
    - Use spacing via .shift(UP/DOWN), .next_to(obj, direction, buff=0.5), .arrange(DOWN, buff=0.5) for clean arrangement. 
    - Center main content using .to_edge()/.move_to(ORIGIN). 
    - Keep all elements within screen coordinates (-7 to 7 for x, -4 to 4 for y). 
    - Use .scale(0.5) for all visual elements to ensure proper sizing and best animations.
 
 2. *Animation Quality* 
    - Employ cinematic effects: FadeIn, FadeOut, Write, Transform, Create, GrowFromCenter, LaggedStart. 
    - Use advanced animation methods: move_to_target, shift, move_along_path, transform, fade_in, fade_out, write, grow_arrow, rotating.
    - Animations must be smooth with run_time between 1.5-3 seconds for optimal quality.
    - Use high-quality rendering settings for professional appearance.
    - Ensure all animations are visually appealing with proper timing and flow.
 
 3. *Timing & Flow* 
    - Show one key concept at a time with self.wait(1–2) between major steps. 
    - Sequence: Title → Visuals → Formula → Summary. 
    - Synchronize all visual animations with voiceover narration using tracker.duration.
 
 4. *Text & Fonts* 
    - Use Text for headings and MathTex for equations. 
    - Elegantly scale and position text (.scale(0.8), .to_edge(UP)), never overlapping labels. 
    - For long text, use .scale(0.7) or add line breaks. 
 
 5. *Scene Design* 
    - Use `class ConceptScene(VoiceoverScene):` and place all animations inside construct(self). 
    - Always inherit from VoiceoverScene, not Scene. 
    - Always include self.set_speech_service(GTTSService()) in construct method with proper error handling.
    - Include fallback to offline PyTTSX3Service if GTTSService fails.
 
 6. *Camera Motion* 
    - Use gentle zooms/pans (e.g., self.camera.frame.animate.scale(0.8).move_to(target)). 
    - Avoid abrupt camera changes. 
 
 7. *Performance & Compatibility* 
    - Output must be clean, error-free, and run-ready for Manim CE (latest). 
    - Use only 2D scenes unless 3D is specifically requested. 
    - Keep animations efficient but maintain high visual quality. 
    - Avoid overly complex animations that take more than 30 seconds to render. 
 
 8. *Voice-over Integration (MANDATORY)* 
    - ALWAYS use manim-voiceover and GTTS for narration. 
    - Structure ALL animations within voiceover context managers. 
    - Use proper syntax: with self.voiceover(text="Your explanation here") as tracker: 
    - Time animations to match speech pacing using tracker.duration. 
    - Include self.wait() after complex points for comprehension. 
    - Write clear, educational voiceover scripts. 
    - Ensure voiceover audio files are properly generated and synchronized.
    - Use tracker.duration * 0.5 for proper timing synchronization.
 
 9. *Final Output* 
    - Output ONLY valid Python code that starts with "from manim import *" 
    - Do NOT include any natural language text, questions, or explanations in your response. 
    - Do NOT ask questions like "Would you like me to proceed with this task?". 
    - Do NOT include phrases like "I'm sorry, but I can only provide Python code" 
    - Do NOT include any text that is not Python code or comments. 
    - The response must contain only executable Python code and comments. 
    - Must render cleanly at 1920x1080 with NO overlaps or cut-off. 
    - All coordinates and scaling tested for on-screen fit. 
 
 10. *Bonus Aesthetic Enhancements* 
     - Use light color gradients (color=BLUE_B, fill_opacity=0.5) for shapes. 
     - Group objects with VGroup().arrange(DOWN, center=True, buff=0.5). 
     - Use arrows and labels to show relationships. 
     - Apply .scale(0.5) to all visual elements for consistent sizing.
 
 11. *File Handling* 
     - Do NOT reference external files (avoid ImageMobject, SVGMobject, or any external file-based mobjects). 
 
 Your generated Manim code must: 
 ✅ Look professional 
 ✅ Run without modification 
 ✅ Have ABSOLUTELY NO overlapping elements 
 ✅ Be visually balanced 
 ✅ Fit ALL elements within screen boundaries 
 ✅ Include GTTS-based voice-over integration (MANDATORY) 
 ✅ Contain ONLY Python code and comments, NO natural language text or questions
 ✅ Always inherit from VoiceoverScene
 ✅ Always include self.set_speech_service(GTTSService())
 ✅ Start with "from manim import *"
 ✅ Be simple enough to render in under 30 seconds
 ✅ Apply .scale(0.5) to all visual elements for proper sizing
 ✅ Ensure voiceover audio is properly generated and synchronized
 ✅ Use voiceover context managers for ALL animations
 ✅ Synchronize animations with tracker.duration for smooth timing
 ✅ Use high-quality rendering settings for professional results
 ✅ Use advanced animation methods: move_to_target, shift, move_along_path, transform, fade_in, fade_out, write, grow_arrow, rotating
 ✅ Apply .scale(0.15) for small elements and .scale(0.5) for standard elements as appropriate
 
 Example response format: 
 
 from manim import * 
 from manim_voiceover import VoiceoverScene 
 from manim_voiceover.services.gtts import GTTSService 
 
 class MyScene(VoiceoverScene): 
     def construct(self): 
         self.set_speech_service(GTTSService()) 
         # Create a circle with voiceover explanation
         circle = Circle() 
         circle.scale(0.5).move_to(ORIGIN).set_fill(BLUE, opacity=0.5) 
         with self.voiceover(text="This is a circle.") as tracker: 
             self.play(Create(circle), run_time=2)
             self.wait(tracker.duration * 0.5) 
         with self.voiceover(text="Now it turns red.") as tracker: 
             self.play(circle.animate.set_fill(RED, opacity=1), run_time=2)
             self.wait(tracker.duration * 0.5) 
 """
        
        # Prepare the messages for OpenRouter
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # Make the API request to OpenRouter
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:5000",  # Optional, for dashboard stats
            "X-Title": "EduVis Pro Educational Platform",  # Optional, for dashboard stats
            "Content-Type": "application/json"
        }
        
        # Log headers for debugging (without the full API key)
        safe_headers = headers.copy()
        safe_headers["Authorization"] = f"Bearer {api_key[:10]}...{api_key[-5:]}"
        logger.info(f"Request headers: {safe_headers}")
        
        payload = {
            "model": "openai/gpt-3.5-turbo",  # You can change this to other models
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        logger.info("Sending request to OpenRouter API")
        logger.info(f"Request payload: {payload}")
        
        # Add more detailed logging
        logger.info(f"Full API key length: {len(api_key)}")
        logger.info(f"API key starts with: {api_key[:20]}")
        logger.info(f"API key ends with: {api_key[-10:]}")
        
        # Log the exact headers being sent
        logger.info(f"Exact headers being sent: {headers}")
        
        response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
        
        logger.info(f"OpenRouter API response status: {response.status_code}")
        logger.info(f"OpenRouter API response text: {response.text[:500]}")  # Log first 500 chars
        
        if response.status_code != 200:
            error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), response.status_code
        
        # Parse the response
        response_data = response.json()
        logger.debug(f"OpenRouter response: {response_data}")
        
        # Extract the generated code
        generated_code = response_data["choices"][0]["message"]["content"]
        
        # Clean up the code by removing markdown code blocks and any additional text
        # Handle different markdown formats
        if "```python" in generated_code:
            # Extract code between ```python and ```
            start_idx = generated_code.find("```python")
            end_idx = generated_code.find("```", start_idx + 9)  # 9 is length of "```python"
            if start_idx != -1 and end_idx != -1:
                generated_code = generated_code[start_idx + 9:end_idx]
        elif "```" in generated_code:
            # Extract code between ``` and ```
            start_idx = generated_code.find("```")
            end_idx = generated_code.find("```", start_idx + 3)  # 3 is length of "```"
            if start_idx != -1 and end_idx != -1:
                generated_code = generated_code[start_idx + 3:end_idx]
        
        # Strip any leading/trailing whitespace
        generated_code = generated_code.strip()
        
        # Additional validation to ensure we only have valid Python code
        # Check if the response contains natural language text instead of code
        natural_language_indicators = [
            "would you like me to",
            "do you want",
            "i'm sorry",
            "i can only provide",
            "i can help you",
            "here is the code",
            "this is the code"
        ]
        
        # Convert to lowercase for comparison
        code_lower = generated_code.lower()
        contains_natural_language = any(indicator in code_lower for indicator in natural_language_indicators)
        
        if contains_natural_language:
            logger.error("Generated code contains natural language text instead of Python code")
            logger.error(f"Problematic code:\n{generated_code}")
            return jsonify({
                "error": "Invalid response format",
                "details": "The AI generated a natural language response instead of Python code. Please try again with a more specific request.",
                "code": generated_code
            }), 500
        
        # Check if the code starts with the required import
        if not generated_code.startswith("from manim import *"):
            logger.error("Generated code does not start with required import")
            logger.error(f"Problematic code:\n{generated_code}")
            return jsonify({
                "error": "Invalid code format",
                "details": "The generated code does not start with 'from manim import *'. Please try again.",
                "code": generated_code
            }), 500
        
        # If the code is empty after cleaning, return an error
        if not generated_code:
            logger.error("Generated code is empty after cleaning")
            return jsonify({
                "error": "Generated code is empty",
                "details": "The AI response did not contain valid Python code."
            }), 500
        
        # Ensure the code starts with proper imports
        if not generated_code.startswith("from manim import *"):
            # Try to find the first import line and slice from there
            import_idx = generated_code.find("from manim import *")
            if import_idx != -1:
                generated_code = generated_code[import_idx:]
            else:
                # If no manim import found, add it at the beginning
                generated_code = "from manim import *\n\n" + generated_code
        
        # Apply corrections from the script corrector
        try:
            from manim_script_corrector import correct_manim_script
            generated_code = correct_manim_script(generated_code)
            logger.info("Applied script corrections")
        except Exception as e:
            logger.warning(f"Failed to apply script corrections: {e}")
        
        # Validate the generated code for syntax errors
        try:
            ast.parse(generated_code)
            logger.info("Generated code passed syntax validation")
        except SyntaxError as e:
            logger.error(f"Generated code has syntax error: {e}")
            logger.error(f"Problematic code:\n{generated_code}")
            # Try to fix common issues
            generated_code = fix_generated_code(generated_code)
            logger.info(f"Code after fix attempt:\n{generated_code}")
            # Validate again
            try:
                ast.parse(generated_code)
                logger.info("Generated code passed syntax validation after fixes")
            except SyntaxError as e2:
                logger.error(f"Generated code still has syntax error after fixes: {e2}")
                logger.error(f"Problematic code after fix:\n{generated_code}")
                return jsonify({
                    "error": f"Generated code has syntax error: {e2.msg}",
                    "details": "The AI generated code with syntax errors. Please try again or rephrase your request.",
                    "code": generated_code  # Include the code in the response for debugging
                }), 500
        
        logger.info("Successfully generated code with OpenRouter")
        
        # Return the generated code
        response_data = {
            "manimCode": generated_code,
            "timeline": f"Generated from user input: {user_input}"
        }
        logger.info("=== ENDING OPENROUTER CODE GENERATION SUCCESSFULLY ===")
        return jsonify(response_data)
        
    except Exception as e:
        logger.exception("Error in OpenRouter code generation endpoint")
        error_response = {
            "error": f"Server error: {str(e)}",
            "details": "An unexpected error occurred while generating code with OpenRouter."
        }
        logger.info("=== ENDING OPENROUTER CODE GENERATION WITH ERROR ===")
        return jsonify(error_response), 500

def fix_generated_code(code: str) -> str:
    """
    Fix common syntax errors in generated code.
    """
    if not code.strip():
        return code
    
    # Normalize problematic Unicode and invisible characters that can break parsing
    # 1) Replace smart quotes and full-width punctuation with ASCII equivalents
    import re
    unicode_translations = {
        '“': '"', '”': '"', '„': '"', '‟': '"', '＂': '"',
        '‘': "'", '’': "'", '‚': "'", '‛': "'", '＇': "'",
        '（': '(', '）': ')', '［': '[', '］': ']', '｛': '{', '｝': '}',
        '，': ',', '：': ':', '；': ';',
        '—': '-', '–': '-', '−': '-', '‐': '-', '‒': '-',
        '…': '...', '。': '.',
    }
    code = ''.join(unicode_translations.get(ch, ch) for ch in code)
    # 2) Strip BOM and zero-width/invisible spaces
    code = code.replace('\ufeff', '')
    code = re.sub(r'[\u200B-\u200D\uFEFF\u2060]', '', code)
    
    # First, check for and fix color variants (BLUE_B, CYAN_B, etc.)
    color_pattern = r'\b([A-Z]+)_[A-Z]\b'
    code = re.sub(color_pattern, r'\1', code)
    
    lines = code.split('\n')
    fixed_lines = []
    in_multiline_string = False
    string_delimiter = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append(line)
            continue
            
        # Skip comments
        if stripped.startswith('#') and not in_multiline_string:
            fixed_lines.append(line)
            continue
        
        # Handle multiline strings
        if not in_multiline_string and (stripped.count('"""') % 2 == 1 or stripped.count("'''") % 2 == 1):
            in_multiline_string = True
            string_delimiter = '"""' if stripped.count('"""') % 2 == 1 else "'''"
        elif in_multiline_string and string_delimiter is not None and stripped.count(string_delimiter) % 2 == 1:
            in_multiline_string = False
            string_delimiter = None
        
        # Ensure class/def headers end with a colon
        if not in_multiline_string and (stripped.startswith('class ') or stripped.startswith('def ')) and not stripped.endswith(':'):
            line = line + ':'
        
        # Fix positional arguments after keyword arguments
        if not in_multiline_string and '=' in line and ',' in line:
            parts = line.split(',')
            has_keyword = False
            for i, part in enumerate(parts):
                if '=' in part and not any(q in part.split('=')[0] for q in ['"', "'"]):
                    has_keyword = True
                elif has_keyword and '=' not in part and part.strip() and not part.strip().startswith(('#', ')', ']', '}')):
                    # Found positional arg after keyword - convert to keyword
                    arg_name = part.strip()
                    parts[i] = f"{arg_name}={arg_name}"
            line = ','.join(parts)
        
        # Fix incomplete parentheses in function calls and VGroup constructions
        if '(' in line and line.count('(') > line.count(')'):
            open_count = line.count('(')
            close_count = line.count(')')
            line = line + ')' * (open_count - close_count)
        
        # Fix incomplete brackets
        if '[' in line and line.count('[') > line.count(']'):
            open_count = line.count('[')
            close_count = line.count(']')
            line = line + ']' * (open_count - close_count)
        
        # Fix incomplete braces
        if '{' in line and line.count('{') > line.count('}'):
            open_count = line.count('{')
            close_count = line.count('}')
            line = line + '}' * (open_count - close_count)
        
        # Fix incomplete string literals
        if not in_multiline_string:
            if line.count('"') % 2 == 1:
                line = line + '"'
            if line.count("'") % 2 == 1:
                line = line + "'"
        
        fixed_lines.append(line)
    
    # If a multiline string was opened and never closed, close it at end
    if in_multiline_string and string_delimiter:
        fixed_lines.append(string_delimiter)
        in_multiline_string = False
        string_delimiter = None
    
    fixed_code = '\n'.join(fixed_lines)
    
    # Ensure the code has proper structure
    if 'class' not in fixed_code and 'def construct(' not in fixed_code:
        # If no class is found, wrap the code in a basic scene class
        fixed_code = f"""from manim import *

class GeneratedScene(Scene):
    def construct(self):
{chr(10).join('        ' + line for line in fixed_code.split(chr(10)) if line.strip())}
"""
    
    # Additional validation to remove any natural language text
    lines = fixed_code.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip lines that contain natural language questions
        if "would you like me to" in line.lower() or "do you want" in line.lower():
            continue
        cleaned_lines.append(line)
    
    fixed_code = '\n'.join(cleaned_lines)
    
    return fixed_code

def generate_manim_code_from_prompt(prompt):
    """
    Converts natural language prompt to Manim code.
    This is a simplified implementation - in a real scenario, you would use an LLM.
    """
    # Simple template-based approach for demonstration
    # In a real implementation, you would use a more sophisticated method
    
    # Convert prompt to lowercase for matching
    prompt_lower = prompt.lower()
    
    if "binary search" in prompt_lower:
        return '''from manim import *

class BinarySearchVisualization(Scene):
    def construct(self):
        # Title
        title = Text("Binary Search Algorithm", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create array
        arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
        squares = VGroup(*[Square(side_length=0.8) for _ in arr])
        squares.arrange(RIGHT, buff=0.1)
        squares.shift(DOWN)
        
        # Add numbers
        numbers = VGroup()
        for i, value in enumerate(arr):
            num = Text(str(value), font_size=24)
            num.move_to(squares[i])
            numbers.add(num)
        
        # Show array
        self.play(Create(squares), Write(numbers))
        self.wait(1)
        
        # Target value
        target_text = Text("Target: 7", font_size=30)
        target_text.next_to(title, DOWN, buff=0.5)
        self.play(Write(target_text))
        self.wait(1)
        
        # Pointers
        left_ptr = Arrow(start=UP, end=DOWN, color=BLUE)
        right_ptr = Arrow(start=UP, end=DOWN, color=BLUE)
        mid_ptr = Arrow(start=UP, end=DOWN, color=YELLOW)
        
        left = 0
        right = len(arr) - 1
        
        left_ptr.next_to(squares[left], UP, buff=0.1)
        right_ptr.next_to(squares[right], UP, buff=0.1)
        
        self.play(GrowArrow(left_ptr), GrowArrow(right_ptr))
        self.wait(1)
        
        # Binary search process
        while left <= right:
            mid = (left + right) // 2
            mid_ptr.next_to(squares[mid], UP, buff=0.1)
            
            self.play(GrowArrow(mid_ptr))
            self.wait(0.5)
            
            if arr[mid] == 7:  # Found target
                found_text = Text("Found!", font_size=30, color=GREEN)
                found_text.next_to(target_text, DOWN)
                self.play(Write(found_text))
                squares[mid].set_fill(GREEN, opacity=0.5)
                self.play(FadeIn(squares[mid]))
                break
            elif arr[mid] < 7:  # Search right half
                left = mid + 1
                left_ptr.next_to(squares[left], UP, buff=0.1)
                self.play(MoveToTarget(left_ptr))
                # Fade out left portion
                for i in range(mid + 1):
                    squares[i].set_fill(RED, opacity=0.3)
                self.play(*[FadeIn(squares[i]) for i in range(mid + 1)])
            else:  # Search left half
                right = mid - 1
                right_ptr.next_to(squares[right], UP, buff=0.1)
                self.play(MoveToTarget(right_ptr))
                # Fade out right portion
                for i in range(mid, len(arr)):
                    squares[i].set_fill(RED, opacity=0.3)
                self.play(*[FadeIn(squares[i]) for i in range(mid, len(arr))])
            
            self.play(FadeOut(mid_ptr))
            self.wait(0.5)
        
        self.wait(2)

if __name__ == "__main__":
    from manim import *
    scene = BinarySearchVisualization()
    scene.render()

'''
    
    elif "sorting" in prompt_lower or "sort" in prompt_lower:
        return '''from manim import *

class BubbleSortVisualization(Scene):
    def construct(self):
        # Title
        title = Text("Bubble Sort Algorithm", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create array
        arr = [64, 34, 25, 12, 22, 11, 90]
        squares = VGroup(*[Square(side_length=0.8) for _ in arr])
        squares.arrange(RIGHT, buff=0.1)
        
        # Add numbers
        numbers = VGroup()
        for i, value in enumerate(arr):
            num = Text(str(value), font_size=24)
            num.move_to(squares[i])
            numbers.add(num)
        
        # Show array
        self.play(Create(squares), Write(numbers))
        self.wait(1)
        
        # Bubble sort algorithm
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                # Highlight comparing elements
                squares[j].set_fill(YELLOW, opacity=0.5)
                squares[j+1].set_fill(YELLOW, opacity=0.5)
                self.play(FadeIn(squares[j]), FadeIn(squares[j+1]))
                self.wait(0.5)
                
                if arr[j] > arr[j+1]:
                    # Swap elements
                    arr[j], arr[j+1] = arr[j+1], arr[j]
                    
                    # Animate swap
                    self.play(
                        numbers[j].animate.move_to(squares[j+1]),
                        numbers[j+1].animate.move_to(squares[j])
                    )
                    
                    # Swap numbers in the group
                    numbers[j], numbers[j+1] = numbers[j+1], numbers[j]
                
                # Reset colors
                squares[j].set_fill(opacity=0)
                squares[j+1].set_fill(opacity=0)
                self.play(FadeIn(squares[j]), FadeIn(squares[j+1]))
        
        # Highlight sorted array
        for square in squares:
            square.set_fill(GREEN, opacity=0.3)
        self.play(*[FadeIn(square) for square in squares])
        self.wait(2)

if __name__ == "__main__":
    from manim import *
    scene = BubbleSortVisualization()
    scene.render()

'''
    
    else:
        # Default animation for any other prompt
        return '''from manim import *

class DefaultVisualization(Scene):
    def construct(self):
        # Title based on input
        title = Text("Visualization", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create a circle and square
        circle = Circle(radius=1, color=BLUE)
        square = Square(side_length=2, color=GREEN)
        
        # Position shapes
        circle.shift(LEFT * 2)
        square.shift(RIGHT * 2)
        
        # Show shapes
        self.play(Create(circle), Create(square))
        self.wait(1)
        
        # Transform circle to square
        self.play(Transform(circle, square.copy()))
        self.wait(1)
        
        # Create text
        text = Text("EduVis AI", font_size=36)
        text.next_to(title, DOWN, buff=1)
        self.play(Write(text))
        self.wait(2)

'''

# User profile data (in-memory for simplicity)
USER_PROFILE = {
    "id": "user_123",
    "name": "Alex Morgan",
    "email": "alex.m@example.com",
    "avatar": "AM",
    "preferences": {
        "theme": "dark",
        "notifications": True,
        "language": "en"
    },
    "stats": {
        "completed_modules": 12,
        "total_hours": 15,
        "current_streak": 5
    }
}

# Chat messages storage (in-memory for simplicity)
CHAT_MESSAGES = [
    {
        "id": "msg_1",
        "sender": "ai",
        "content": "Hello! I'm your AI tutor. Ask me anything about the visualization or concepts you're learning.",
        "timestamp": "2025-10-05T10:00:00Z"
    },
    {
        "id": "msg_2",
        "sender": "user",
        "content": "How does binary search compare to linear search?",
        "timestamp": "2025-10-05T10:01:00Z"
    },
    {
        "id": "msg_3",
        "sender": "ai",
        "content": "Great question! Binary search is much more efficient than linear search for sorted data. While linear search has O(n) time complexity, binary search has O(log n) complexity. This means for 1000 items, linear search might take up to 1000 steps, but binary search takes only about 10 steps.",
        "timestamp": "2025-10-05T10:01:30Z"
    },
    {
        "id": "msg_4",
        "sender": "user",
        "content": "Can binary search work on unsorted data?",
        "timestamp": "2025-10-05T10:02:00Z"
    },
    {
        "id": "msg_5",
        "sender": "ai",
        "content": "No, binary search requires sorted data to work correctly. If the data is unsorted, you would need to sort it first (which takes O(n log n) time) or use linear search instead.",
        "timestamp": "2025-10-05T10:02:30Z"
    }
]

@app.route("/api/profile", methods=["GET"])
def get_profile():
    """
    Get user profile information.
    """
    try:
        logger.info("Received request to /api/profile")
        return jsonify(USER_PROFILE)
    except Exception as e:
        logger.exception("Error in get_profile endpoint")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/profile", methods=["PUT"])
def update_profile():
    """
    Update user profile information.
    """
    try:
        logger.info("Received request to update profile")
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Update profile data
        if "name" in data:
            USER_PROFILE["name"] = data["name"]
        if "email" in data:
            USER_PROFILE["email"] = data["email"]
        if "preferences" in data:
            USER_PROFILE["preferences"].update(data["preferences"])
            
        logger.info("Profile updated successfully")
        return jsonify(USER_PROFILE)
    except Exception as e:
        logger.exception("Error in update_profile endpoint")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/chat/messages", methods=["GET"])
def get_chat_messages():
    """
    Get chat messages for the AI tutor.
    """
    try:
        logger.info("Received request to /api/chat/messages")
        return jsonify(CHAT_MESSAGES)
    except Exception as e:
        logger.exception("Error in get_chat_messages endpoint")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/chat/messages", methods=["POST"])
def send_chat_message():
    """
    Send a new message to the chat.
    """
    try:
        logger.info("Received request to send chat message")
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        message_content = data.get("content")
        if not message_content:
            return jsonify({"error": "Message content is required"}), 400
            
        # Create new message
        new_message = {
            "id": f"msg_{len(CHAT_MESSAGES) + 1}",
            "sender": "user",
            "content": message_content,
            "timestamp": datetime.datetime.now().isoformat() + "Z"
        }
        
        CHAT_MESSAGES.append(new_message)
        
        # Simulate AI response
        ai_response = {
            "id": f"msg_{len(CHAT_MESSAGES) + 1}",
            "sender": "ai",
            "content": f"I understand your question about '{message_content}'. This is a great point to consider in the context of educational visualizations. Let me explain...",
            "timestamp": datetime.datetime.now().isoformat() + "Z"
        }
        
        CHAT_MESSAGES.append(ai_response)
        
        logger.info("Message sent and AI response generated successfully")
        return jsonify({"user_message": new_message, "ai_response": ai_response})
    except Exception as e:
        logger.exception("Error in send_chat_message endpoint")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/sidebar/toggle", methods=["POST"])
def toggle_sidebar():
    """
    Toggle sidebar state.
    """
    try:
        logger.info("Received request to toggle sidebar")
        data = request.get_json()
        collapsed = data.get("collapsed", False) if data else False
        
        # In a real app, this would be stored in user preferences
        USER_PROFILE["preferences"]["sidebar_collapsed"] = collapsed
        
        logger.info(f"Sidebar toggled to {'collapsed' if collapsed else 'expanded'}")
        return jsonify({"success": True, "collapsed": collapsed})
    except Exception as e:
        logger.exception("Error in toggle_sidebar endpoint")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/navigation/items", methods=["GET"])
def get_navigation_items():
    """
    Get navigation items for the sidebar.
    """
    try:
        logger.info("Received request to /api/navigation/items")
        # In a real application, this would come from a database
        nav_items = [
            {
                "id": "dashboard",
                "icon": "fas fa-home",
                "text": "Dashboard",
                "active": True
            },
            {
                "id": "generator",
                "icon": "fas fa-code",
                "text": "Generator"
            },
            {
                "id": "ai-tutor",
                "icon": "fas fa-robot",
                "text": "AI Tutor"
            },
            {
                "id": "library",
                "icon": "fas fa-book",
                "text": "Library"
            }
        ]
        return jsonify(nav_items)
    except Exception as e:
        logger.exception("Error in get_navigation_items endpoint")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/navigation/select", methods=["POST"])
def select_navigation_item():
    """
    Select a navigation item and return associated content.
    """
    try:
        logger.info("Received request to /api/navigation/select")
        data = request.get_json()
        item_id = data.get("item_id") if data else None
        
        if not item_id:
            return jsonify({"error": "No item_id provided"}), 400
            
        # In a real application, this would fetch content based on the selected item
        content_map = {
            "dashboard": {
                "title": "Educational Dashboard",
                "content": "Welcome to the main dashboard. Here you can create and view educational visualizations."
            },
            "generator": {
                "title": "Code Generator",
                "content": "Use this section to generate Manim code from descriptions or edit code directly."
            },
            "ai-tutor": {
                "title": "AI Tutor",
                "content": "Interact with the AI tutor to learn about algorithms and data structures."
            },
            "library": {
                "title": "Content Library",
                "content": "Browse educational content and saved visualizations."
            }
        }
        
        content = content_map.get(item_id, {
            "title": "Unknown Section",
            "content": "This section is not yet implemented."
        })
        
        logger.info(f"Selected navigation item: {item_id}")
        return jsonify(content)
    except Exception as e:
        logger.exception("Error in select_navigation_item endpoint")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Educational content structure
LEARNING_PATHS = {
    "mathematics": {
        "title": "Mathematics Fundamentals",
        "description": "Master core mathematical concepts through interactive visualizations",
        "icon": "fas fa-calculator",
        "topics": [
            {
                "id": "algebra-basics",
                "title": "Algebra Basics",
                "description": "Learn fundamental algebraic concepts and equations",
                "difficulty": "Beginner",
                "estimated_time": "30 minutes",
                "concepts": ["Variables", "Equations", "Linear Functions"]
            },
            {
                "id": "geometry-fundamentals",
                "title": "Geometry Fundamentals",
                "description": "Explore shapes, angles, and geometric relationships",
                "difficulty": "Beginner",
                "estimated_time": "45 minutes",
                "concepts": ["Triangles", "Circles", "Angles", "Area"]
            },
            {
                "id": "calculus-intro",
                "title": "Introduction to Calculus",
                "description": "Understand limits, derivatives, and integrals",
                "difficulty": "Intermediate",
                "estimated_time": "60 minutes",
                "concepts": ["Limits", "Derivatives", "Integration"]
            }
        ]
    },
    "science": {
        "title": "Science Explorations",
        "description": "Discover scientific principles through animated explanations",
        "icon": "fas fa-flask",
        "topics": [
            {
                "id": "physics-motion",
                "title": "Laws of Motion",
                "description": "Understand Newton's laws and motion principles",
                "difficulty": "Beginner",
                "estimated_time": "40 minutes",
                "concepts": ["Inertia", "Force", "Acceleration"]
            },
            {
                "id": "chemistry-basics",
                "title": "Chemistry Basics",
                "description": "Explore atoms, molecules, and chemical reactions",
                "difficulty": "Beginner",
                "estimated_time": "50 minutes",
                "concepts": ["Atoms", "Molecules", "Reactions", "Periodic Table"]
            },
            {
                "id": "biology-cells",
                "title": "Cell Biology",
                "description": "Learn about cell structure and functions",
                "difficulty": "Intermediate",
                "estimated_time": "55 minutes",
                "concepts": ["Cell Structure", "Organelles", "Cell Division"]
            }
        ]
    },
    "history": {
        "title": "Historical Journeys",
        "description": "Experience history through animated timelines and events",
        "icon": "fas fa-history",
        "topics": [
            {
                "id": "ancient-civilizations",
                "title": "Ancient Civilizations",
                "description": "Explore the rise and fall of ancient societies",
                "difficulty": "Beginner",
                "estimated_time": "35 minutes",
                "concepts": ["Egypt", "Greece", "Rome", "Mesopotamia"]
            },
            {
                "id": "world-wars",
                "title": "World Wars",
                "description": "Understand the causes and impacts of global conflicts",
                "difficulty": "Intermediate",
                "estimated_time": "65 minutes",
                "concepts": ["WWI", "WWII", "Causes", "Consequences"]
            }
        ]
    }
}

if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=False)
