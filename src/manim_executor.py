import os
import tempfile
import subprocess
import sys
import uuid
from typing import Tuple, Optional, Union, Dict, Any, List
import logging
import re
import shutil
import platform
import glob
from datetime import datetime, timedelta
import ast
import json
import random  # For random color selection if needed
from pathlib import Path  # Added for better cross-platform path handling

# Import the script corrector
from manim_script_corrector import correct_manim_script

# Set up logging - reduced level for better performance
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Define TTS service constants for voiceover
TTS_SERVICE_GTTS = "GTTSService"
TTS_SERVICE_PYTTSX3 = "TTSService"  # pyttsx3 backend in manim-voiceover

# Directory to store generated videos - using pathlib for better cross-platform compatibility
VIDEO_DIR = str(Path(__file__).parent.parent / "generated" / "anim_generated")
os.makedirs(VIDEO_DIR, exist_ok=True)

# Platform-specific settings
IS_WINDOWS = platform.system() == "Windows"

def cleanup_old_animations(max_age_hours=1):
    """
    Delete animation directories older than max_age_hours to free up space.
    Optimized for faster execution and better error handling.
    """
    try:
        current_time = datetime.now()
        deleted_count = 0
        
        # Only check the most recent items to improve performance
        items = os.listdir(VIDEO_DIR)
        # Sort by modification time and only check the most recent 50 items
        items_with_time = [(item, os.path.getmtime(os.path.join(VIDEO_DIR, item))) for item in items if os.path.isdir(os.path.join(VIDEO_DIR, item))]
        items_with_time.sort(key=lambda x: x[1], reverse=True)
        items_to_check = items_with_time[:20]  # Only check the most recent 20 items for faster execution
        
        for item, mod_time in items_to_check:
            item_path = os.path.join(VIDEO_DIR, item)
            
            # Delete if older than max_age_hours
            if current_time - datetime.fromtimestamp(mod_time) > timedelta(hours=max_age_hours):
                try:
                    shutil.rmtree(item_path, ignore_errors=True)
                    logger.info(f"Deleted old animation directory: {item_path}")
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete directory {item_path}: {e}")
                    # Try to remove read-only files first
                    try:
                        for root, dirs, files in os.walk(item_path):
                            for dir_name in dirs:
                                dir_path = os.path.join(root, dir_name)
                                os.chmod(dir_path, 0o777)
                            for file_name in files:
                                file_path = os.path.join(root, file_name)
                                os.chmod(file_path, 0o777)
                        # Try again
                        shutil.rmtree(item_path, ignore_errors=True)
                        logger.info(f"Deleted old animation directory after chmod: {item_path}")
                        deleted_count += 1
                    except Exception as e2:
                        logger.warning(f"Failed to delete directory {item_path} even after chmod: {e2}")
        
        logger.info(f"Cleanup completed. Deleted {deleted_count} old directories.")
        return deleted_count
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return 0

def validate_python_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate Python syntax and check for common Manim errors.
    """
    try:
        # Try to parse the code with AST
        ast.parse(code)
        return True, "Valid syntax"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def sanitize_manim_code(code: Union[str, ast.AST]) -> str:
    """
    Sanitize generated Manim code to fix common syntax errors and issues.
    
    Args:
        code: The code to sanitize (either as string or AST)
        
    Returns:
        str: The sanitized code
    """
    if isinstance(code, ast.AST):
        code_str = ast.unparse(code)
    elif isinstance(code, dict):
        code_str = str(code.get("manimCode", code.get("script", "")))
    else:
        code_str = code
        
    # Normalize problematic Unicode and invisible characters that can break parsing
    # 1) Replace smart quotes and full-width punctuation with ASCII equivalents
    unicode_translations = {
        '“': '"', '”': '"', '„': '"', '‟': '"', '＂': '"',
        '‘': "'", '’': "'", '‚': "'", '‛': "'", '＇': "'",
        '（': '(', '）': ')', '［': '[', '］': ']', '｛': '{', '｝': '}',
        '，': ',', '：': ':', '；': ';',
        '—': '-', '–': '-', '−': '-', '‐': '-', '‒': '-',
        '…': '...', '。': '.',
    }
    # Build the translated string character by character to avoid linter issues
    translated_chars = []
    for ch in code_str:
        if ch in unicode_translations:
            translated_chars.append(unicode_translations[ch])
        else:
            translated_chars.append(ch)
    code_str = ''.join(translated_chars)
    # 2) Strip BOM and zero-width/invisible spaces
    code_str = code_str.replace('\ufeff', '')
    code_str = re.sub(r'[\u200B-\u200D\uFEFF\u2060]', '', code_str)
    
    # Fix unterminated string literals - comprehensive approach
    lines = code_str.split('\n')
    fixed_lines = []
    
    # Track string state across lines
    in_triple_single_quotes = False
    in_triple_double_quotes = False
    in_single_quotes = False
    in_double_quotes = False
    
    for line in lines:
        i = 0
        while i < len(line):
            # Check for triple quotes first
            if i + 2 < len(line):
                if line[i:i+3] == "'''":
                    if not in_triple_double_quotes and not in_single_quotes and not in_double_quotes:
                        in_triple_single_quotes = not in_triple_single_quotes
                    i += 3
                    continue
                elif line[i:i+3] == '"""':
                    if not in_triple_single_quotes and not in_single_quotes and not in_double_quotes:
                        in_triple_double_quotes = not in_triple_double_quotes
                    i += 3
                    continue
            
            # Check for single quotes
            if line[i] == "'" and not in_triple_double_quotes and not in_triple_single_quotes and not in_double_quotes:
                # Check if it's escaped
                if i == 0 or line[i-1] != '\\':
                    in_single_quotes = not in_single_quotes
                i += 1
                continue
                
            # Check for double quotes
            if line[i] == '"' and not in_triple_single_quotes and not in_triple_double_quotes and not in_single_quotes:
                # Check if it's escaped
                if i == 0 or line[i-1] != '\\':
                    in_double_quotes = not in_double_quotes
                i += 1
                continue
                
            i += 1
        
        # Fix unterminated quotes at end of line if not in multi-line string
        if not in_triple_single_quotes and not in_triple_double_quotes:
            if in_single_quotes:
                line += "'"
                in_single_quotes = False
            if in_double_quotes:
                line += '"'
                in_double_quotes = False
        
        fixed_lines.append(line)
    
    # Close any open multi-line strings at the end of the file
    if in_triple_single_quotes:
        fixed_lines.append("'''")
    if in_triple_double_quotes:
        fixed_lines.append('"""')
    
    code_str = '\n'.join(fixed_lines)
    
    # Ensure the code has proper structure
    if 'class' not in code_str and 'def construct(' not in code_str:
        # If no class is found, wrap the code in a basic scene class
        indented_code = '\n'.join('        ' + line for line in code_str.split('\n') if line.strip())
        code_str = f"""from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class GeneratedScene(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService())
{indented_code}

"""
    # If class exists but doesn't inherit from VoiceoverScene, fix it
    elif 'class' in code_str and 'VoiceoverScene' not in code_str and '(Scene):' in code_str:
        code_str = code_str.replace('(Scene):', '(VoiceoverScene):')
        # Add necessary imports if missing
        if 'from manim_voiceover import VoiceoverScene' not in code_str:
            lines = code_str.split('\n')
            # Insert imports after manim import
            for i, line in enumerate(lines):
                if line.startswith('from manim import *'):
                    lines.insert(i+1, 'from manim_voiceover import VoiceoverScene')
                    lines.insert(i+2, 'from manim_voiceover.services.gtts import GTTSService')
                    break
            code_str = '\n'.join(lines)
        # Add set_speech_service call if missing
        if 'self.set_speech_service' not in code_str:
            lines = code_str.split('\n')
            # Find the construct method and add the speech service
            for i, line in enumerate(lines):
                if 'def construct(self):' in line:
                    lines.insert(i+1, '        self.set_speech_service(GTTSService())')
                    break
            code_str = '\n'.join(lines)
    
    # Remove any natural language text that might have been included in the response
    lines = code_str.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip lines that contain natural language text
        natural_language_indicators = [
            "would you like me to",
            "do you want",
            "i'm sorry",
            "i can only provide",
            "i can help you",
            "here is the code",
            "this is the code"
        ]
        
        line_lower = line.lower()
        contains_natural_language = any(indicator in line_lower for indicator in natural_language_indicators)
        
        if contains_natural_language:
            continue
        cleaned_lines.append(line)
    
    code_str = '\n'.join(cleaned_lines)
    
    # Additional validation to ensure we only have valid Python code
    # Remove any lines that don't look like Python code
    lines = code_str.split('\n')
    python_lines = []
    for line in lines:
        stripped_line = line.strip()
        # Keep empty lines, comments, and lines that look like Python code
        if (not stripped_line or 
            stripped_line.startswith('#') or 
            stripped_line.startswith('from ') or 
            stripped_line.startswith('import ') or 
            stripped_line.startswith('class ') or 
            stripped_line.startswith('def ') or 
            stripped_line.startswith('self.') or 
            stripped_line.startswith('with ') or 
            stripped_line.startswith('if ') or 
            stripped_line.startswith('for ') or 
            stripped_line.startswith('while ') or 
            stripped_line.startswith('return') or 
            stripped_line.startswith('pass') or 
            stripped_line.startswith('else:') or 
            stripped_line.startswith('elif ') or
            ' = ' in stripped_line or
            '.animate' in stripped_line or
            '.play(' in stripped_line or
            '.wait(' in stripped_line or
            stripped_line.endswith(':')):
            python_lines.append(line)
        # Skip lines that look like natural language responses
        elif stripped_line and not any(stripped_line.startswith(keyword) for keyword in [
            'from', 'import', 'class', 'def', 'self', 'with', 'if', 'for', 'while', 
            'return', 'pass', 'else:', 'elif', '#']):
            # This might be natural language, skip it
            continue
        else:
            python_lines.append(line)
    
    code_str = '\n'.join(python_lines)
    
    return code_str

def fix_argument_order(code_str: str) -> str:
    """
    Fix common cases where positional arguments follow keyword arguments.
    This is a frequent issue in generated Manim code.
    """
    lines = code_str.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Fix common patterns where positional arguments follow keyword arguments
        # Pattern: function(pos_arg, kw_arg=value, pos_arg2) -> function(pos_arg, pos_arg2, kw_arg=value)
        # Look for common Manim functions that might have this issue
        if ('play(' in line or 'Create(' in line or 'Transform(' in line or 
            'Write(' in line or 'FadeIn(' in line or 'FadeOut(' in line):
            
            # Fix the specific pattern of positional arguments following keyword arguments
            line = fix_function_call_arguments(line)
            
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_function_call_arguments(line: str) -> str:
    """
    Fix function call arguments where positional arguments follow keyword arguments.
    """
    # Handle play() calls specifically
    if 'self.play(' in line and '=' in line:
        # Extract the function call
        match = re.search(r'(self\.play\()(.+)(\))', line)
        if match:
            prefix = match.group(1)
            args_str = match.group(2)
            suffix = match.group(3)
            
            # Split arguments by comma
            args = split_preserving_parentheses(args_str)
            
            # Separate positional and keyword arguments
            positional_args = []
            keyword_args = []
            
            for arg in args:
                arg = arg.strip()
                if '=' in arg and not (arg.startswith("'") and arg.endswith("'")):
                    # This looks like a keyword argument
                    keyword_args.append(arg)
                else:
                    # This is a positional argument
                    positional_args.append(arg)
            
            # Reconstruct with positional args first
            new_args = positional_args + keyword_args
            if new_args:
                new_args_str = ', '.join(new_args)
                line = line.replace(match.group(0), f"{prefix}{new_args_str}{suffix}")
    
    # Handle other common Manim function calls
    manim_functions = ['Create', 'Transform', 'Write', 'FadeIn', 'FadeOut', 'MoveToTarget']
    for func in manim_functions:
        if f'{func}(' in line and '=' in line:
            # Similar pattern for other functions
            pattern = rf'({func}\()(.+)(\))'
            match = re.search(pattern, line)
            if match:
                prefix = match.group(1)
                args_str = match.group(2)
                suffix = match.group(3)
                
                # Split arguments by comma
                args = split_preserving_parentheses(args_str)
                
                # Separate positional and keyword arguments
                positional_args = []
                keyword_args = []
                
                for arg in args:
                    arg = arg.strip()
                    if '=' in arg and not (arg.startswith("'") and arg.endswith("'")):
                        # This looks like a keyword argument
                        keyword_args.append(arg)
                    else:
                        # This is a positional argument
                        positional_args.append(arg)
                
                # Reconstruct with positional args first
                new_args = positional_args + keyword_args
                if new_args:
                    new_args_str = ', '.join(new_args)
                    line = line.replace(match.group(0), f"{prefix}{new_args_str}{suffix}")
    
    return line

def split_preserving_parentheses(s: str) -> list:
    """
    Split a string by commas, but preserve commas inside parentheses/brackets.
    """
    parts = []
    current = ""
    paren_count = 0
    bracket_count = 0
    in_string = False
    string_char = ""
    
    for char in s:
        if not in_string:
            if char in "\"'":
                in_string = True
                string_char = char
            elif char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
            elif char == ',' and paren_count == 0 and bracket_count == 0:
                parts.append(current)
                current = ""
                continue
        else:
            if char == string_char:
                in_string = False
                string_char = ""
        
        current += char
    
    if current:
        parts.append(current)
    
    return parts

def execute_manim_script(script: Union[str, Dict]) -> Tuple[Optional[str], Optional[str]]:
    """
    Execute a Manim script and return the path to the generated video.
    
    Args:
        script: The Manim script to execute (either as string or dict with 'manimCode' or 'script' key)
        
    Returns:
        Tuple[Optional[str], Optional[str]]: (video_path, error_message)
    """
    # If script is a dict (new format), extract the manimCode and voiceover
    voiceover_text = None
    if isinstance(script, dict):
        if "manimCode" in script and isinstance(script.get("manimCode"), str):
            script_str = script.get("manimCode", "")
            voiceover_text = script.get("voiceover", None)
        elif "script" in script and isinstance(script.get("script"), str):
            script_str = script.get("script", "")
            voiceover_text = script.get("voiceover", None)
        else:
            # If it's a dict but doesn't have expected keys, convert to string
            script_str = str(script)
    else:
        script_str = script
    
    # Clean up old animations before running new one
    cleanup_old_animations()
    
    # Log the original script for debugging
    logger.debug(f"Original script:\n{script_str}")
    
    # Apply script corrections to fix common issues
    script_str = correct_manim_script(script_str)
    
    # Log the corrected script for debugging
    logger.debug(f"Corrected script:\n{script_str}")
    
    # Validate Python syntax first
    is_valid, validation_msg = validate_python_syntax(script_str)
    if not is_valid:
        logger.error(f"Invalid Python syntax after correction: {validation_msg}")
        logger.error(f"Problematic script:\n{script_str}")
        return None, f"Sanitized script has invalid Python syntax: {validation_msg}"
    
    # Create a temporary directory for this execution
    run_id = str(uuid.uuid4())
    temp_dir = os.path.join(VIDEO_DIR, run_id)
    
    # Ensure path compatibility on Windows
    if IS_WINDOWS:
        # Use shorter paths and avoid special characters
        temp_dir = os.path.join(VIDEO_DIR, run_id[:8])  # Shorter ID for Windows
        # Ensure ASCII-only path for Windows compatibility
        temp_dir = temp_dir.encode('ascii', 'ignore').decode('ascii')
    else:
        temp_dir = os.path.join(VIDEO_DIR, run_id)
    
    os.makedirs(temp_dir, exist_ok=True)
    
    # Define timeout constant - increased for complex animations
    TIMEOUT_SECONDS = 120  # 2 minutes for better handling of complex animations
    
    try:
        logger.info(f"Executing script in directory: {temp_dir}")
        
        # Sanitize the script to fix common issues
        sanitized_script = sanitize_manim_code(script_str)
        
        # Validate sanitized script as well
        is_valid, validation_msg = validate_python_syntax(sanitized_script)
        if not is_valid:
            return None, f"Sanitized script has invalid Python syntax: {validation_msg}"
        
        # Write the script to a temporary file
        script_path = os.path.join(temp_dir, "scene.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(sanitized_script)
        
        logger.info(f"Script written to: {script_path}")
        
        # Extract scene class name from the script and check for VoiceoverScene
        scene_class = "Scene"  # Default fallback
        is_voiceover_scene = False
        
        for line in sanitized_script.split("\n"):
            line = line.strip()
            # Look for class definitions that inherit from Scene or VoiceoverScene
            if line.startswith("class ") and ("(Scene)" in line or "(VoiceoverScene)" in line):
                # Extract class name more robustly
                class_part = line.split(":")[0]  # Remove anything after colon
                class_name = class_part.replace("class ", "").strip()
                if "(" in class_name:
                    scene_class = class_name.split("(")[0].strip()
                else:
                    scene_class = class_name
                
                # Check if this is a VoiceoverScene
                if "(VoiceoverScene)" in line:
                    is_voiceover_scene = True
                
                logger.info(f"Found scene class: {scene_class}, VoiceoverScene: {is_voiceover_scene}")
                break
        
        # Add TTS fallback for VoiceoverScene if not already present
        if is_voiceover_scene:
            # Check if the script already has TTS service configuration
            has_gtts = "GTTSService" in sanitized_script
            has_tts_fallback = "PyTTSX3Service" in sanitized_script
            
            if has_gtts and not has_tts_fallback:
                # Add pyttsx3 fallback for gTTS with better error handling
                tts_fallback_code = """
        # Fallback to offline TTS if gTTS fails due to internet connectivity
        try:
            self.set_speech_service(GTTSService(lang="en"))
        except Exception as e:
            print(f"Warning: Failed to initialize GTTSService: {e}")
            try:
                self.set_speech_service(PyTTSX3Service())
                print("Using offline PyTTSX3Service as fallback")
            except Exception as e2:
                print(f"Error: Failed to initialize PyTTSX3Service fallback: {e2}")
                # If both services fail, continue without voiceover
                print("Warning: Both GTTSService and PyTTSX3Service failed. Continuing without voiceover.")
"""
                # Insert the fallback code after the class definition
                lines = sanitized_script.split('\n')
                for i, line in enumerate(lines):
                    if 'def construct(self):' in line:
                        # Insert the fallback code with proper indentation
                        fallback_lines = tts_fallback_code.strip().split('\n')
                        indented_fallback = [f"        {l}" if l.strip() else l for l in fallback_lines]
                        lines[i+1:i+1] = indented_fallback
                        break
                sanitized_script = '\n'.join(lines)
            
            # Add necessary imports if not present
            if "from manim_voiceover" not in sanitized_script:
                import_line = "from manim_voiceover import VoiceoverScene\nfrom manim_voiceover.services.gtts import GTTSService\nfrom manim_voiceover.services.base import TTSService\n"
                sanitized_script = import_line + sanitized_script
                logger.info("Added voiceover imports")
        
        # Additional validation to ensure we have a valid scene class
        if not scene_class or scene_class == "":
            scene_class = "Scene"
            logger.warning("Could not extract scene class, using default 'Scene'")
        
        # Optimize Manim command for educational content with better quality animations
        # Use optimized settings for quality while maintaining reasonable performance
        # Compatible with Manim v0.17.2
        cmd = [
            sys.executable, "-m", "manim",
            "render",  # Add render subcommand for v0.17.2
            script_path,
            scene_class,
            "-qm",  # Medium quality for better visual quality (m = medium)
            "--media_dir", temp_dir,
            "--disable_caching",  # Disable caching for better consistency
            "--progress_bar", "none",  # Disable progress bar for cleaner output
            "--flush_cache",  # Flush cache to avoid memory issues
            "--format", "mp4",  # Explicitly specify format
            "--renderer", "cairo",  # Use Cairo renderer for better compatibility
            "--frame_rate", "30",  # Higher frame rate for smoother animations
            "--resolution", "1280,720",  # HD resolution for better quality
            "-v", "ERROR"  # Reduce log level to speed up (using -v instead of --log_level)
        ]
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Execute the command with environment variables to fix Unicode issues
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Platform-specific environment variables
        if IS_WINDOWS:
            # Add environment variables to handle Windows encoding issues
            env['PYTHONLEGACYWINDOWSFSENCODING'] = '1'
            env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
            # Use ASCII-friendly paths on Windows
            env['TEMP'] = temp_dir
            env['TMP'] = temp_dir
        
        # Add environment variable to prefer simple video encoding
        env['MANIM_USE_FFMPEG_CACHE'] = '0'
        
        # Try to run the command and handle encoding issues
        try:
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                env=env,
                encoding='utf-8',
                errors='replace'  # Replace encoding errors with placeholder characters
            )
        except UnicodeDecodeError as e:
            # If we still get Unicode errors, try with different encoding
            logger.warning(f"UnicodeDecodeError occurred: {e}. Retrying with errors='ignore'")
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                env=env,
                encoding='utf-8',
                errors='ignore'  # Ignore encoding errors
            )
        except subprocess.TimeoutExpired as e:
            error_msg = f"Manim execution timed out after {TIMEOUT_SECONDS} seconds. Your animation may be too complex or resource-intensive."
            logger.exception(error_msg)
            return None, error_msg
        except FileNotFoundError as e:
            error_msg = f"Manim executable not found. Please ensure Manim is properly installed: {str(e)}"
            logger.exception(error_msg)
            return None, error_msg
        except PermissionError as e:
            error_msg = f"Permission error when executing Manim. Check file permissions: {str(e)}"
            logger.exception(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Subprocess execution failed: {str(e)}"
            logger.exception(error_msg)
            return None, error_msg
        
        logger.info(f"Command completed with return code: {result.returncode}")
        logger.debug(f"Stdout: {result.stdout}")
        logger.debug(f"Stderr: {result.stderr}")
        
        # If we get a non-zero return code, try alternative approaches
        if result.returncode != 0:
            error_output = f"{result.stderr}\n{result.stdout}"
            logger.warning(f"Manim execution failed. Error output: {error_output}")
            
            # Try with different settings (GIF format as fallback)
            logger.info("Trying alternative approach with MP4 format...")
            # Adjust command based on platform
            alt_cmd = [
                sys.executable, "-m", "manim",
                "render",  # Add render subcommand for v0.17.2
                script_path,
                scene_class,
                "-qm",  # Medium quality for better visual quality
                "--media_dir", temp_dir,
                "--disable_caching",
                "--progress_bar", "none",
                "--flush_cache",
                "--format", "mp4",  # Try MP4 format instead
                "--frame_rate", "30",  # Higher frame rate for smoother animations
                "--resolution", "1280,720",  # HD resolution for better quality
                "-v", "ERROR"  # Reduce log level to speed up (using -v instead of --log_level)
            ]
            
            logger.info(f"Trying alternative command: {' '.join(alt_cmd)}")
            try:
                alt_result = subprocess.run(
                    alt_cmd,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT_SECONDS,
                    env=env,
                    encoding='utf-8',
                    errors='replace'
                )
                
                if alt_result.returncode == 0:
                    logger.info("Alternative approach succeeded!")
                    result = alt_result
                else:
                    alt_error_output = f"{alt_result.stderr}\n{alt_result.stdout}"
                    logger.error(f"Alternative approach also failed: {alt_error_output}")
            except Exception as alt_e:
                logger.error(f"Alternative approach failed with exception: {alt_e}")
            
            # If GIF also fails on Windows, try PNG sequence
            if result.returncode != 0 and IS_WINDOWS:
                logger.info("Trying PNG sequence format for Windows...")
                png_cmd = [
                    sys.executable, "-m", "manim",
                    "render",  # Add render subcommand for v0.17.2
                    script_path,
                    scene_class,
                    "-qm",  # Medium quality for better visual quality
                    "--media_dir", temp_dir,
                    "--disable_caching",
                    "--progress_bar", "none",
                    "--flush_cache",
                    "--format", "png",  # Try PNG sequence
                    "--frame_rate", "24",  # Good frame rate for PNG sequences
                    "-v", "ERROR"  # Reduce log level to speed up (using -v instead of --log_level)
                ]
                
                logger.info(f"Trying PNG command: {' '.join(png_cmd)}")
                try:
                    png_result = subprocess.run(
                        png_cmd,
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=TIMEOUT_SECONDS,
                        env=env,
                        encoding='utf-8',
                        errors='replace'
                    )
                    
                    if png_result.returncode == 0:
                        logger.info("PNG approach succeeded!")
                        result = png_result
                    else:
                        png_error_output = f"{png_result.stderr}\n{png_result.stdout}"
                        logger.error(f"PNG approach also failed: {png_error_output}")
                except Exception as png_e:
                    logger.error(f"PNG approach failed with exception: {png_e}")
            
            # If all else fails, try without specifying format (let Manim decide)
            if result.returncode != 0:
                logger.info("Trying with default format settings...")
                default_cmd = [
                    sys.executable, "-m", "manim",
                    "render",  # Add render subcommand for v0.17.2
                    script_path,
                    scene_class,
                    "-qm",  # Medium quality for better visual quality
                    "--media_dir", temp_dir,
                    "--disable_caching",
                    "--progress_bar", "none",
                    "--flush_cache",
                    "--format", "mp4",  # Explicitly specify format
                    "--renderer", "cairo",  # Use Cairo renderer for better compatibility
                    "--frame_rate", "24",  # Good frame rate for default quality
                    "-v", "ERROR"  # Reduce log level to speed up (using -v instead of --log_level)
                ]
                
                logger.info(f"Trying default command: {' '.join(default_cmd)}")
                try:
                    default_result = subprocess.run(
                        default_cmd,
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=TIMEOUT_SECONDS,
                        env=env,
                        encoding='utf-8',
                        errors='replace'
                    )
                    
                    if default_result.returncode == 0:
                        logger.info("Default approach succeeded!")
                        result = default_result
                    else:
                        default_error_output = f"{default_result.stderr}\n{default_result.stdout}"
                        logger.error(f"Default approach also failed: {default_error_output}")
                except Exception as default_e:
                    logger.error(f"Default approach failed with exception: {default_e}")
        
        if result.returncode != 0:
            error_msg = f"Manim execution failed (exit code {result.returncode}):\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}"
            logger.error(error_msg)
            return None, error_msg
        
        # Find the generated media file (both mp4 and gif)
        video_files = glob.glob(os.path.join(temp_dir, "**", "*.mp4"), recursive=True)
        gif_files = glob.glob(os.path.join(temp_dir, "**", "*.gif"), recursive=True)
        png_files = glob.glob(os.path.join(temp_dir, "**", "*.png"), recursive=True) if IS_WINDOWS else []
        
        all_media_files = video_files + gif_files + png_files
        logger.info(f"Found media files: {all_media_files}")
        
        # If no files found with recursive search, try direct directory search
        if not all_media_files:
            # Look directly in temp_dir and its immediate subdirectories
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith((".mp4", ".gif", ".png")):
                        all_media_files.append(os.path.join(root, file))
                # Limit depth on Windows to avoid issues
                if IS_WINDOWS and root.count(os.sep) - temp_dir.count(os.sep) >= 2:
                    break
        
        if not all_media_files:
            error_msg = f"No media file was generated. Check the script for errors.\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}"
            logger.error(error_msg)
            return None, error_msg
        
        # Return the first media file found
        media_path = all_media_files[0]
        logger.info(f"Successfully generated media at: {media_path}")
        
        # Check if this is a VoiceoverScene by examining the script
        is_voiceover_scene = False
        if script:
            # Check if the script contains VoiceoverScene and voiceover context managers
            is_voiceover_scene = (
                "VoiceoverScene" in script and 
                "self.voiceover(" in script and
                "with self.voiceover(" in script
            )
        
        # If voiceover text is provided or this is already a voiceover scene, 
        # check if the video filename indicates voiceover is already included
        if voiceover_text or is_voiceover_scene:
            # If the video already has "_with_voiceover" in its name, it already includes voiceover
            if "_with_voiceover" in media_path:
                logger.info("Video already includes voiceover")
                return media_path, None
            # If this is a VoiceoverScene, the voiceover is already integrated
            elif is_voiceover_scene:
                logger.info("Voiceover is already integrated in the scene")
                return media_path, None
            else:
                logger.info(f"Adding external voiceover to video: {voiceover_text[:50]}...")
                combined_path, error = create_manim_scene_with_voiceover(None, voiceover_text=voiceover_text, 
                                                                        existing_video_path=media_path)
                if combined_path and not error:
                    return combined_path, None
                else:
                    logger.warning(f"Voiceover addition had issues: {error}")
                    # Return the original video if voiceover fails
        
        return media_path, None
        
    except subprocess.TimeoutExpired:
        error_msg = f"Manim execution timed out after {TIMEOUT_SECONDS} seconds"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Error executing Manim script: {str(e)}"
        logger.exception(error_msg)
        return None, error_msg

# Add a new function to create Manim scenes with voiceover integration
def create_manim_scene_with_voiceover(script: Optional[str] = None, voiceover_text: Optional[str] = None, 
                                    voiceover_file: Optional[str] = None, existing_video_path: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Create a Manim scene with optional voiceover integration for longer educational content.
    
    Args:
        script: The Manim script to execute (optional if existing_video_path is provided)
        voiceover_text: Text to convert to voiceover using gTTS
        voiceover_file: Path to existing audio file to use as voiceover
        existing_video_path: Path to an existing video to add voiceover to
        
    Returns:
        Tuple of (video_path, error_message)
    """
    # Use existing video path or generate a new one
    video_path = existing_video_path
    
    # If no existing video and script is provided, generate the basic Manim video
    if not video_path and script:
        video_path, error = execute_manim_script(script)
        if error:
            return None, error
    
    # If no video path available, return error
    if not video_path:
        return None, "No video path provided or generated"
        
    # If no voiceover is requested, return the basic video
    if not voiceover_text and not voiceover_file:
        return video_path, None
        
    # If voiceover text is provided, generate audio
    if voiceover_text:
        try:
            from gtts import gTTS
            import tempfile
            
            # Generate voiceover audio
            tts = gTTS(voiceover_text, lang='en')
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_audio.close()
            tts.save(temp_audio.name)
            voiceover_file = temp_audio.name
        except Exception as e:
            logger.error(f"Error generating voiceover: {e}")
            return video_path, f"Voiceover generation failed: {e}"
    
    # Combine video and audio using ffmpeg
    try:
        import subprocess
        
        # Create output path for combined video
        if video_path is None:
            return None, "Video path is None"
            
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        combined_video_path = os.path.join(video_dir, f"{video_name}_with_voiceover.mp4")
        
        # Use ffmpeg to combine video and audio
        if voiceover_file is None:
            return video_path, "Voiceover file path is None"
            
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", voiceover_file,
            "-c:v", "copy",
            "-c:a", "aac",
            "-strict", "experimental",
            combined_video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            # Clean up temp audio file if we created it
            if voiceover_text and voiceover_file and os.path.exists(voiceover_file):
                os.unlink(voiceover_file)
            return video_path, "Failed to combine video and audio"
            
        # Clean up temp audio file if we created it
        if voiceover_text and voiceover_file and os.path.exists(voiceover_file):
            os.unlink(voiceover_file)
            
        logger.info(f"Successfully created video with voiceover: {combined_video_path}")
        return combined_video_path, None
        
    except Exception as e:
        # Handle subprocess.TimeoutExpired specifically
        if "subprocess" in locals() or "subprocess" in globals():
            import subprocess
            if isinstance(e, subprocess.TimeoutExpired):
                error_msg = "Voiceover combination timed out"
                logger.error(error_msg)
                # Clean up temp audio file if we created it
                if voiceover_text and voiceover_file and os.path.exists(voiceover_file):
                    os.unlink(voiceover_file)
                return video_path, error_msg
        
        error_msg = f"Error combining video and voiceover: {str(e)}"
        logger.error(error_msg)
        # Clean up temp audio file if we created it
        if voiceover_text and voiceover_file and os.path.exists(voiceover_file):
            os.unlink(voiceover_file)
        return video_path, error_msg

# Add a function to handle sequential animations with synchronized voiceover for longer content
def create_sequential_animation_with_voiceover(content_segments: list) -> Tuple[Optional[str], Optional[str]]:
    """
    Create sequential animations with synchronized voiceover for educational content longer than 2 minutes.
    
    Args:
        content_segments: List of dictionaries with 'script' and 'voiceover' keys
        
    Returns:
        Tuple of (final_video_path, error_message)
    """
    temp_dir = None
    try:
        import subprocess
        import tempfile
        
        # Create temporary directory for intermediate files
        temp_dir = tempfile.mkdtemp()
        video_segments = []
        
        # Generate each segment
        for i, segment in enumerate(content_segments):
            script = segment.get('script', '')
            voiceover_text = segment.get('voiceover', '')
            
            if not script:
                continue
                
            # Generate video for this segment
            video_path, error = execute_manim_script(script)
            if error:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                return None, f"Error generating segment {i+1}: {error}"
                
            if video_path is None:
                continue
                
            # Generate voiceover for this segment if provided
            if voiceover_text:
                try:
                    from gtts import gTTS
                    tts = gTTS(voiceover_text, lang='en')
                    audio_path = os.path.join(temp_dir, f"segment_{i}_audio.mp3")
                    tts.save(audio_path)
                    
                    # Combine video and audio for this segment
                    combined_path = os.path.join(temp_dir, f"segment_{i}_combined.mp4")
                    cmd = [
                        "ffmpeg",
                        "-i", video_path,
                        "-i", audio_path,
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-strict", "experimental",
                        combined_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        video_segments.append(combined_path)
                        # Clean up original video and audio
                        if os.path.exists(video_path):
                            os.unlink(video_path)
                        if os.path.exists(audio_path):
                            os.unlink(audio_path)
                    else:
                        video_segments.append(video_path)  # Use video without audio if combination fails
                except Exception as e:
                    logger.warning(f"Failed to add voiceover to segment {i+1}: {e}")
                    video_segments.append(video_path)  # Use video without audio
            else:
                video_segments.append(video_path)
        
        # Concatenate all segments
        if len(video_segments) == 0:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None, "No video segments were generated"
        elif len(video_segments) == 1:
            # Only one segment, return it
            final_video = video_segments[0]
        else:
            # Create file list for concatenation
            file_list_path = os.path.join(temp_dir, "file_list.txt")
            with open(file_list_path, 'w') as f:
                for segment in video_segments:
                    f.write(f"file '{segment}'\n")
            
            # Concatenate videos
            final_video_path = os.path.join(temp_dir, "final_video.mp4")
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", file_list_path,
                "-c", "copy",
                final_video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                return None, f"Failed to concatenate video segments: {result.stderr}"
                
            final_video = final_video_path
        
        # Move final video to anim_generated directory
        final_dir = os.path.join(VIDEO_DIR, f"sequential_{uuid.uuid4().hex[:8]}")
        os.makedirs(final_dir, exist_ok=True)
        final_video_name = os.path.basename(final_video)
        final_output_path = os.path.join(final_dir, final_video_name)
        shutil.move(final_video, final_output_path)
        
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        logger.info(f"Successfully created sequential animation with voiceover: {final_output_path}")
        return final_output_path, None
        
    except Exception as e:
        logger.exception("Error in sequential animation with voiceover")
        # Clean up temporary directory if it was created
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
        return None, f"Error creating sequential animation: {str(e)}"
