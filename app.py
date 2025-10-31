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
from manim_executor import execute_manim_script, VIDEO_DIR, cleanup_old_animations
from typing import Dict, Optional

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

app = Flask(__name__, template_folder='templates', static_folder='static')
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

# Create directory for generated animations
os.makedirs('anim_generated', exist_ok=True)

# Custom route to serve assets
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return empty response with 204 No Content status

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
        return jsonify({
            "video_url": video_url,
            "message": "Animation generated successfully!"
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
            placeholder_path = os.path.join(os.path.dirname(__file__), "static", "videos", "placeholder.txt")
            if os.path.exists(placeholder_path):
                return send_file(placeholder_path, mimetype="text/plain")
            else:
                return "No video available.", 404
            
        logger.info(f"Serving video from: {video_path}")
        return send_file(video_path, mimetype="video/mp4", conditional=True)
    except Exception as e:
        logger.exception("Error serving video")
        # Return a default placeholder video or image
        placeholder_path = os.path.join(os.path.dirname(__file__), "static", "videos", "placeholder.txt")
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

@app.errorhandler(Exception)
def handle_error(e):
    logger.exception("Unhandled error occurred")
    return jsonify({"error": f"Unhandled server error: {str(e)}"}), 500

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
        logger.info("Received request to OpenRouter code generation")
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        
        user_input = data.get("input") if data else None
        custom_api_key = data.get("api_key") if data else None  # Allow custom API key
        if not user_input:
            logger.warning("No input provided in request")
            return jsonify({"error": "No input provided"}), 400
        
        logger.info(f"Received user input: {user_input}")
        
        # Use custom API key if provided, otherwise use default
        api_key = custom_api_key if custom_api_key else OPENROUTER_API_KEY
        
        # Prepare the prompt for OpenRouter
        system_prompt = """
        You are an expert Python developer specializing in Manim, the mathematical animation engine. 
        Your task is to create Manim code based on the user's request. Follow these guidelines:
        
        1. Always create a complete, runnable Manim scene class
        2. Use proper Manim syntax and best practices
        3. Include clear comments explaining what each part does
        4. Make animations smooth and educational
        5. Use appropriate colors and visual elements
        6. Keep animations concise but informative
        7. Always include self.wait() calls for proper timing
        8. Use standard Manim imports: from manim import *
        9. Name the class appropriately based on the topic
        10. Make sure the code is syntactically correct and will run without errors
        11. ONLY return the Python code, nothing else (no explanations, no additional text)
        12. Do not wrap the code in ```python or ``` markers
        13. Optimize animations for full screen display with proper scaling:
           - Use .scale(2) or .scale(3) to make objects appropriately large for the screen
           - Use .to_edge() or .to_corner() to position elements properly
           - Center important elements on screen using .move_to(ORIGIN)
           - Use screen-filling animations where appropriate
           - Make sure all visual elements are clearly visible
        14. Integrate voiceover support using gTTS (Google Text-to-Speech) with the VoiceoverScene class
        15. Include voiceover text that explains what's happening in the animation
        16. Use proper voiceover timing that syncs with the animations
        17. Configure animations to fill the screen appropriately with proper scaling
        18. Use the correct import: from manim_voiceover import VoiceoverScene
        19. Use the correct import: from manim_voiceover.services.gtts import GTTSService
        20. Class should inherit from VoiceoverScene
        21. Set speech service with self.set_speech_service(GTTSService())
        22. Use voiceover context manager with proper text parameter: with self.voiceover(text="...") as tracker:
        23. Make sure animations are clearly visible and fill a good portion of the screen
        24. Use appropriate durations for animations and voiceover synchronization
        25. Always scale objects to be clearly visible (minimum scale(2))
        26. Position objects to be centered on screen using .move_to(ORIGIN)
        27. Add comments explaining screen sizing and positioning
        28. Ensure all variables are properly defined before use
        29. Use proper VGroup construction syntax - always close parentheses properly
        30. Make sure all parentheses and brackets are properly closed
        31. Double-check that all variable names match exactly where they are used
        32. When creating VGroup objects, make sure to properly close all parentheses and brackets
        33. Avoid incomplete variable assignments that might cause UnboundLocalError
        34. Always complete variable assignments before using the variables
        35. When using Transform, make sure both objects are properly defined
        36. Use proper voiceover syntax: with self.voiceover(text="Your text here") as tracker:
        37. When using FunctionGraph, use x_range=(min, max) instead of x_min and x_max parameters
        38. For FunctionGraph, use proper syntax: FunctionGraph(function, x_range=(min_value, max_value))
        39. Ensure proper spacing between animation elements to prevent overlap
        40. Use appropriate buffer space around text elements to ensure readability
        41. Position all elements within screen boundaries to prevent clipping
        42. Use .to_edge(), .to_corner(), or .shift() with appropriate buffer values for proper spacing
        43. Ensure text elements are large enough to be readable (minimum font_size=24)
        44. Use contrasting colors for text to ensure visibility against backgrounds
        45. Avoid placing elements too close to screen edges to prevent clipping
        46. Use proper grouping with VGroup when multiple elements need to be positioned together
        47. Ensure animations are synchronized with voiceover narration using tracker.duration
        48. Add appropriate wait times between animation sequences for clarity
        49. Use smooth animation transitions with appropriate run_time values
        50. Test that all visual elements remain within screen boundaries throughout the animation
        51. Do not use duplicate parameters in method calls (e.g., don't use buff=0.5 twice in the same method call)
        52. When using .arrange() method, use each parameter only once
        53. Ensure all method calls have unique parameter names
        54. Do not reference external image files that may not exist (avoid ImageMobject with file paths)
        55. If you need to show an image, create a placeholder shape like Rectangle or Circle instead
        56. Use only built-in Manim objects that don't require external files
        57. Avoid using Tex/MathTex mobjects as they require LaTeX installation (use Text instead)
        58. For mathematical expressions, use Text mobject with regular strings
        59. Do not use Tex or MathTex mobjects in the generated code
        60. If you need to use random functions, make sure to add "import random" at the top of the file
        61. Use proper syntax for random functions like random.uniform(), random.randint(), etc.
        
        Example response format:
        from manim import *
        from manim_voiceover import VoiceoverScene
        from manim_voiceover.services.gtts import GTTSService

        class MyScene(VoiceoverScene):
            def construct(self):
                # Your animation code here with voiceover
                self.set_speech_service(GTTSService())
                
                with self.voiceover(text="This is an example animation with voiceover.") as tracker:
                    circle = Circle()
                    circle.scale(2)  # Scale to fill screen appropriately
                    circle.move_to(ORIGIN)  # Center on screen
                    circle.set_fill(BLUE, opacity=0.5)
                    self.play(Create(circle))
                    self.wait(tracker.duration * 0.5)  # Wait for half the voiceover duration
                    self.play(circle.animate.set_fill(RED, opacity=1))
                    self.wait(tracker.duration * 0.5)  # Wait for the remaining voiceover duration
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
        
        payload = {
            "model": "openai/gpt-3.5-turbo",  # You can change this to other models
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        logger.info("Sending request to OpenRouter API")
        response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
        
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
            end_idx = generated_code.find("```", start_idx + 3)  # 3 is length of "``"
            if start_idx != -1 and end_idx != -1:
                generated_code = generated_code[start_idx + 3:end_idx]
        
        # Strip any leading/trailing whitespace
        generated_code = generated_code.strip()
        
        # Additional cleaning to ensure we only have valid Python code
        lines = generated_code.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip empty lines at the beginning
            if not cleaned_lines and not line.strip():
                continue
            cleaned_lines.append(line)
        
        generated_code = '\n'.join(cleaned_lines)
        
        # Ensure the code starts with proper imports
        if not generated_code.startswith("from manim import *"):
            # Try to find the first import line and slice from there
            import_idx = generated_code.find("from manim import *")
            if import_idx != -1:
                generated_code = generated_code[import_idx:]
        
        # Validate the generated code for syntax errors
        try:
            ast.parse(generated_code)
            logger.info("Generated code passed syntax validation")
        except SyntaxError as e:
            logger.error(f"Generated code has syntax error: {e}")
            # Try to fix common issues
            generated_code = fix_generated_code(generated_code)
            # Validate again
            try:
                ast.parse(generated_code)
                logger.info("Generated code passed syntax validation after fixes")
            except SyntaxError as e2:
                logger.error(f"Generated code still has syntax error after fixes: {e2}")
                return jsonify({
                    "error": f"Generated code has syntax error: {e2.msg}",
                    "details": "The AI generated code with syntax errors. Please try again or rephrase your request."
                }), 500
        
        logger.info("Successfully generated code with OpenRouter")
        
        # Return the generated code
        return jsonify({
            "manimCode": generated_code,
            "timeline": f"Generated from user input: {user_input}"
        })
        
    except Exception as e:
        logger.exception("Error in OpenRouter code generation endpoint")
        return jsonify({
            "error": f"Server error: {str(e)}",
            "details": "An unexpected error occurred while generating code with OpenRouter."
        }), 500

def fix_generated_code(code: str) -> str:
    """
    Fix common syntax errors in generated code.
    """
    # Fix incomplete VGroup constructions
    # Pattern: VGroup( element1, element2, ... (missing closing parenthesis)
    lines = code.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Fix VGroup constructions that are missing closing parentheses
        if 'VGroup(' in line and line.count('(') > line.count(')'):
            # Count opening and closing parentheses
            open_count = line.count('(')
            close_count = line.count(')')
            
            # Add missing closing parentheses
            line = line + ')' * (open_count - close_count)
        
        # Fix incomplete variable assignments
        # Look for lines that start with a variable assignment but are incomplete
        if '=' in line and not line.strip().endswith(':') and not line.strip().endswith('\\'):
            # Check if this might be an incomplete assignment
            parts = line.split('=')
            if len(parts) >= 2:
                # Check if the right side looks incomplete
                right_side = parts[-1].strip()
                if right_side and not right_side.endswith(')') and not right_side.endswith(']') and not right_side.endswith('"') and not right_side.endswith("'"):
                    # This might be an incomplete assignment, try to fix it
                    # Look for common patterns
                    if 'VGroup(' in right_side and right_side.count('(') > right_side.count(')'):
                        # Add missing closing parenthesis
                        line = line + ')' * (right_side.count('(') - right_side.count(')'))
        
        fixed_lines.append(line)
    
    # Join lines back together
    fixed_code = '\n'.join(fixed_lines)
    
    # Fix any remaining syntax issues
    # Remove any trailing incomplete lines
    lines = fixed_code.split('\n')
    clean_lines = []
    
    for line in lines:
        # Skip lines that are clearly incomplete
        stripped = line.strip()
        if stripped and not stripped.endswith(':') and stripped.count('(') == stripped.count(')'):
            # This line looks complete, add it
            clean_lines.append(line)
        elif not stripped:
            # Empty lines are fine
            clean_lines.append(line)
        elif stripped.endswith(':'):
            # Lines ending with : are fine (control structures)
            clean_lines.append(line)
        # Skip incomplete lines
    
    # But don't remove too many lines, keep the structure
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

# Sample educational content for each topic
EDUCATIONAL_CONTENT = {
    "algebra-basics": {
        "title": "Algebra Basics",
        "description": "Understanding variables and equations",
        "visualization_prompt": "Create an animation that visually explains what variables are in algebra, showing how they can represent unknown numbers in equations. Include examples like 2x + 3 = 7 and demonstrate solving for x.",
        "key_points": [
            "Variables represent unknown values",
            "Equations show relationships between quantities",
            "Solving equations means finding the value of variables"
        ]
    },
    "geometry-fundamentals": {
        "title": "Geometry Fundamentals",
        "description": "Explore shapes, angles, and geometric relationships",
        "visualization_prompt": "Create an animation that demonstrates different geometric shapes (circle, square, triangle) and their properties. Show how to calculate area and perimeter for each shape with visual examples.",
        "key_points": [
            "Shapes have specific properties and formulas",
            "Area measures the space inside a shape",
            "Perimeter measures the distance around a shape"
        ]
    },
    "calculus-intro": {
        "title": "Introduction to Calculus",
        "description": "Understand limits, derivatives, and integrals",
        "visualization_prompt": "Create an animation that visually explains the concept of a derivative as the slope of a tangent line to a curve. Show how the derivative represents the rate of change at any point on a function.",
        "key_points": [
            "Derivatives measure rates of change",
            "Integrals calculate accumulated quantities",
            "Limits help understand behavior at specific points"
        ]
    },
    "physics-motion": {
        "title": "Laws of Motion",
        "description": "Understand Newton's laws and motion principles",
        "visualization_prompt": "Create an animation that demonstrates Newton's three laws of motion with clear visual examples. Show inertia, force and acceleration, and action-reaction pairs.",
        "key_points": [
            "An object at rest stays at rest unless acted upon",
            "Force equals mass times acceleration",
            "For every action, there is an equal and opposite reaction"
        ]
    },
    "chemistry-basics": {
        "title": "Chemistry Basics",
        "description": "Explore atoms, molecules, and chemical reactions",
        "visualization_prompt": "Create an animation that shows the structure of atoms with protons, neutrons, and electrons. Demonstrate how atoms combine to form molecules and how chemical reactions occur.",
        "key_points": [
            "Atoms are the building blocks of matter",
            "Molecules form when atoms bond together",
            "Chemical reactions rearrange atoms to form new substances"
        ]
    },
    "biology-cells": {
        "title": "Cell Biology",
        "description": "Learn about cell structure and functions",
        "visualization_prompt": "Create an animation that explores the structure of a cell, highlighting key organelles like the nucleus, mitochondria, and cell membrane. Show how each organelle contributes to cell function.",
        "key_points": [
            "Cells are the basic units of life",
            "Organelles have specialized functions",
            "Cells can reproduce through division"
        ]
    },
    "ancient-civilizations": {
        "title": "Ancient Civilizations",
        "description": "Explore the rise and fall of ancient societies",
        "visualization_prompt": "Create a timeline animation showing the development of major ancient civilizations including Egypt, Greece, Rome, and Mesopotamia. Highlight key achievements and contributions of each civilization.",
        "key_points": [
            "Civilizations developed in river valleys",
            "Each civilization had unique achievements",
            "Cultural exchange influenced development"
        ]
    },
    "world-wars": {
        "title": "World Wars",
        "description": "Understand the causes and impacts of global conflicts",
        "visualization_prompt": "Create an animation that traces the major events of World War I and World War II, showing how they were connected and their global impacts. Include key battles, leaders, and outcomes.",
        "key_points": [
            "Nationalism and alliances led to global conflict",
            "Technology changed warfare dramatically",
            "Wars reshaped political boundaries and societies"
        ]
    }
}

if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=False)
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=False)