import os
import tempfile
import subprocess
import sys
import uuid
from typing import Tuple, Optional, Union, Dict, Any
import logging
import re
import shutil
import platform
import glob
from datetime import datetime, timedelta
import ast
import json

# Set up logging - reduced level for better performance
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Directory to store generated videos
VIDEO_DIR = os.path.join(os.path.dirname(__file__), "anim_generated")
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

def sanitize_manim_code(code: Union[str, Dict]) -> str:
    """
    Sanitize Manim code to fix common issues that cause errors.
    """
    # If code is a dict (new format), extract the manimCode
    if isinstance(code, dict):
        if "manimCode" in code and isinstance(code["manimCode"], str):
            code_str = code["manimCode"]
        elif "script" in code and isinstance(code["script"], str):
            code_str = code["script"]
        else:
            # If it's a dict but doesn't have expected keys, convert to string
            code_str = str(code)
    else:
        code_str = code
    
    # Fix undefined color constants - more comprehensive replacement
    # Handle color constants that might appear in different contexts
    color_replacements = {
        'ORANGE_C': 'ORANGE',
        'RED_C': 'RED',
        'BLUE_C': 'BLUE',
        'GREEN_C': 'GREEN',
        'YELLOW_C': 'YELLOW',
        'PURPLE_C': 'PURPLE',
        'WHITE_C': 'WHITE',
        'BLACK_C': 'BLACK',
        'GREY_C': 'GREY',
        'GRAY_C': 'GRAY',
        'TEAL_C': 'TEAL',
        'MAROON_C': 'MAROON',
        'LIME_C': 'LIME',
        'OLIVE_C': 'OLIVE',
        'NAVY_C': 'NAVY',
        'CYAN_C': 'CYAN',
        'MAGENTA_C': 'MAGENTA',
        'PINK_C': 'PINK',
        'LIGHT_PINK_C': 'LIGHT_PINK',
        'DARK_PINK_C': 'DARK_PINK'
    }
    
    # Apply all color replacements to the entire code
    for old_color, new_color in color_replacements.items():
        code_str = code_str.replace(old_color, new_color)
    
    # Fix Code object parameters
    if 'Code(' in code_str:
        # Replace 'code' parameter with 'code_string'
        code_str = code_str.replace('code=', 'code_string=')
        
        # Remove invalid parameters
        code_str = code_str.replace('font_size=', 'font=')
        code_str = code_str.replace(', font=', ', ')
        code_str = code_str.replace('insert_line_no=', '')
        code_str = code_str.replace('background_stroke_width=', '')
        code_str = code_str.replace('background_stroke_color=', '')
        
        # Clean up any double commas or trailing commas
        code_str = code_str.replace(',,', ',')
        code_str = code_str.replace('(,', '(')
        code_str = code_str.replace(',)', ')')
    
    # Fix FunctionGraph parameter issues
    # Replace x_min and x_max with x_range tuple
    import re
    
    # Simple pattern matching and replacement
    # Handle common patterns where x_min and x_max are used incorrectly
    code_str = re.sub(r'FunctionGraph\(([^,]+),\s*x_min\s*=\s*([^,]+),\s*x_max\s*=\s*([^,]+)\)', 
                      r'FunctionGraph(\1, x_range=(\2, \3))', code_str)
    code_str = re.sub(r'FunctionGraph\(([^,]+),\s*x_max\s*=\s*([^,]+),\s*x_min\s*=\s*([^,]+)\)', 
                      r'FunctionGraph(\1, x_range=(\3, \2))', code_str)
    
    # Fix other common FunctionGraph issues
    code_str = re.sub(r'FunctionGraph\(([^,]+),\s*x_min\s*=\s*([^\s,]+)\s*\)', 
                      r'FunctionGraph(\1, x_range=(\2, 10))', code_str)  # Default x_max
    code_str = re.sub(r'FunctionGraph\(([^,]+),\s*x_max\s*=\s*([^\s,]+)\s*\)', 
                      r'FunctionGraph(\1, x_range=(-10, \2))', code_str)  # Default x_min
    
    # Fix text element positioning to ensure they stay within screen boundaries
    # Ensure Text elements have appropriate positioning
    code_str = re.sub(r'Text\(([^)]+)\)\.to_edge\(DOWN\)', r'Text(\1).to_edge(DOWN, buff=0.5)', code_str)
    code_str = re.sub(r'Text\(([^)]+)\)\.to_edge\(UP\)', r'Text(\1).to_edge(UP, buff=0.5)', code_str)
    code_str = re.sub(r'Text\(([^)]+)\)\.to_edge\(LEFT\)', r'Text(\1).to_edge(LEFT, buff=0.5)', code_str)
    code_str = re.sub(r'Text\(([^)]+)\)\.to_edge\(RIGHT\)', r'Text(\1).to_edge(RIGHT, buff=0.5)', code_str)
    code_str = re.sub(r'Text\(([^)]+)\)\.to_corner\((UL|UR|DL|DR)\)', r'Text(\1).to_corner(\2, buff=0.5)', code_str)
    
    # Ensure minimum font size for readability
    code_str = re.sub(r'font_size\s*=\s*(\d+)', 
                      lambda m: f'font_size={max(int(m.group(1)), 24)}', code_str)
    
    # Fix element spacing to prevent overlap
    # Add buffer space to positioning methods
    code_str = re.sub(r'\.next_to\(([^,]+),\s*([A-Z_]+)\)', r'.next_to(\1, \2, buff=0.5)', code_str)
    code_str = re.sub(r'\.arrange\(([^)]*)\)', r'.arrange(\1, buff=0.5)', code_str)
    
    # Fix duplicate parameters in arrange calls
    def fix_duplicate_buff(match):
        # Extract the parameters
        params = match.group(1)
        # Remove duplicate buff parameters, keeping only the first one
        if params.count('buff=') > 1:
            # Split by comma and process
            param_list = [p.strip() for p in params.split(',')]
            seen_buff = False
            new_params = []
            for param in param_list:
                if param.startswith('buff='):
                    if not seen_buff:
                        new_params.append(param)
                        seen_buff = True
                    # Skip duplicate buff parameters
                else:
                    new_params.append(param)
            return '.arrange(' + ', '.join(new_params) + ')'
        return match.group(0)
    
    code_str = re.sub(r'\.arrange\(([^)]+)\)', fix_duplicate_buff, code_str)
    
    # Simpler fix for duplicate parameters - remove consecutive duplicate parameters
    # This pattern matches cases where the same parameter appears twice in a row
    code_str = re.sub(r'(\w+=\s*[^,)]+,\s*)(\1)', r'\1', code_str)
    
    # More comprehensive fix for duplicate parameters in method calls
    def fix_duplicate_params_in_methods(code):
        # Pattern to match method calls with parameters
        pattern = r'(\w+\s*\([^)]*\))'
        matches = re.finditer(pattern, code)
        
        # Process matches in reverse order to maintain string indices
        fixed_code = code
        for match in reversed(list(matches)):
            full_match = match.group(1)
            # Check if this looks like a method call with parameters
            if '(' in full_match and ')' in full_match and '=' in full_match:
                # Extract method name and parameters
                method_end = full_match.find('(')
                method_name = full_match[:method_end]
                params_section = full_match[method_end+1:-1]  # Extract parameters without parentheses
                
                if params_section and '=' in params_section:
                    # Split parameters by comma
                    param_list = [p.strip() for p in params_section.split(',')]
                    seen_params = {}
                    new_param_list = []
                    
                    for param in param_list:
                        if '=' in param and not param.startswith("'") and not param.startswith('"'):
                            # This is likely a keyword parameter
                            param_name = param.split('=')[0].strip()
                            if param_name not in seen_params:
                                new_param_list.append(param)
                                seen_params[param_name] = True
                            # Skip duplicate parameters
                        else:
                            # This is a positional parameter or string
                            new_param_list.append(param)
                    
                    # Reconstruct the method call
                    if new_param_list:
                        new_params = ', '.join(new_param_list)
                        new_call = f'{method_name}({new_params})'
                        fixed_code = fixed_code[:match.start()] + new_call + fixed_code[match.end():]
        
        return fixed_code
    
    code_str = fix_duplicate_params_in_methods(code_str)
    
    # Specific fix for the arrange method duplicate buff parameter issue
    code_str = re.sub(r'(\.arrange\s*\([^)]*)buff\s*=\s*([^\s,]+)\s*,\s*buff\s*=\s*([^\s,)]+)([^)]*\))', 
                      r'\1buff=\2\4', code_str)
    
    # Fix ImageMobject usage to avoid missing image files
    # Replace ImageMobject with a placeholder shape when the image file doesn't exist
    code_str = re.sub(r'ImageMobject\("([^"]+)"\)', r' RoundedRectangle(width=4, height=3, color=BLUE)', code_str)
    code_str = re.sub(r'ImageMobject\(\'([^\']+)\'\)', r' RoundedRectangle(width=4, height=3, color=BLUE)', code_str)
    
    # Fix Tex mobject usage to avoid LaTeX compilation issues
    # Replace Tex with Text to avoid requiring LaTeX installation
    code_str = re.sub(r'Tex\("([^"]+)"\)', r'Text("\1")', code_str)
    code_str = re.sub(r'Tex\(\'([^\']+)\'\)', r'Text(\'\1\')', code_str)
    
    # Fix MathTex mobject usage to avoid LaTeX compilation issues
    code_str = re.sub(r'MathTex\("([^"]+)"\)', r'Text("\1")', code_str)
    code_str = re.sub(r'MathTex\(\'([^\']+)\'\)', r'Text(\'\1\')', code_str)
    
    # Add import for random module if it's used in the code
    if 'random.' in code_str and 'import random' not in code_str:
        # Find the first import statement and add the random import before it
        lines = code_str.split('\n')
        new_lines = []
        random_import_added = False
        
        for line in lines:
            # Add random import before the first from import statement
            if line.strip().startswith('from') and not random_import_added:
                new_lines.append('import random')
                random_import_added = True
            new_lines.append(line)
        
        # If no from import was found, add it at the beginning
        if not random_import_added:
            new_lines.insert(0, 'import random')
            
        code_str = '\n'.join(new_lines)
    
    # Fix Arrow and CurvedArrow constructors - remove invalid 'buff' parameter
    # Process line by line for these specific fixes
    lines = code_str.split('\n')
    sanitized_lines = []
    
    for line in lines:
        if 'Arrow(' in line and 'buff=' in line:
            # Remove buff parameter
            line = re.sub(r'\s*,?\s*buff\s*=\s*[^,)]+', '', line)
            # Clean up any double commas
            line = re.sub(r',\s*,', ',', line)
            # Clean up any trailing commas before closing parenthesis
            line = re.sub(r',\s*\)', ')', line)
        
        if 'CurvedArrow(' in line and 'buff=' in line:
            # Remove buff parameter
            line = re.sub(r'\s*,?\s*buff\s*=\s*[^,)]+', '', line)
            # Clean up any double commas
            line = re.sub(r',\s*,', ',', line)
            # Clean up any trailing commas before closing parenthesis
            line = re.sub(r',\s*\)', ')', line)
            
        # Fix invalid Arrow parameters that cause TypeError
        if 'Arrow(' in line and 'max_tip_length_to_total_length_ratio=' in line:
            # Remove max_tip_length_to_total_length_ratio parameter
            line = re.sub(r'\s*,?\s*max_tip_length_to_total_length_ratio\s*=\s*[^,)]+', '', line)
            # Clean up any double commas
            line = re.sub(r',\s*,', ',', line)
            # Clean up any trailing commas before closing parenthesis
            line = re.sub(r',\s*\)', ')', line)
            
        # Fix other invalid Arrow parameters
        if 'Arrow(' in line and 'max_stroke_width_to_length_ratio=' in line:
            # Remove max_stroke_width_to_length_ratio parameter
            line = re.sub(r'\s*,?\s*max_stroke_width_to_length_ratio\s*=\s*[^,)]+', '', line)
            # Clean up any double commas
            line = re.sub(r',\s*,', ',', line)
            # Clean up any trailing commas before closing parenthesis
            line = re.sub(r',\s*\)', ')', line)
        
        # Fix any other invalid parameters that might cause TypeError
        # Remove any parameter that might cause issues with Mobject.__init__()
        invalid_params = [
            'max_tip_length_to_total_length_ratio',
            'max_stroke_width_to_length_ratio',
            'tip_length_to_length_ratio',
            'max_tip_length_to_width_ratio',
            'max_stroke_width_to_height_ratio'
        ]
        
        for param in invalid_params:
            if 'Arrow(' in line and f'{param}=' in line:
                # Remove the parameter
                line = re.sub(r'\s*,?\s*' + re.escape(param) + r'\s*=\s*[^,)]+', '', line)
                # Clean up any double commas
                line = re.sub(r',\s*,', ',', line)
                # Clean up any trailing commas before closing parenthesis
                line = re.sub(r',\s*\)', ')', line)
        
        sanitized_lines.append(line)
    
    # Join the lines back together
    code_str = '\n'.join(sanitized_lines)
    
    # Fix incomplete lines that might cause syntax errors
    lines = code_str.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has more opening parentheses than closing ones
        if line.count('(') > line.count(')') and i < len(lines) - 1:
            # Try to find the next line that completes it
            j = i + 1
            while j < len(lines) and line.count('(') > line.count(')'):
                line += ' ' + lines[j].strip()
                j += 1
            i = j  # Skip the lines we've merged
        else:
            i += 1
            
        fixed_lines.append(line)
    
    # Join the lines back together
    code_str = '\n'.join(fixed_lines)
    
    # Fix indentation issues and self usage errors
    lines = code_str.split('\n')
    fixed_lines = []
    
    # Parse the code to fix missing indented blocks
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        # Check for control structures that require indented blocks
        if stripped.startswith(('for ', 'if ', 'while ', 'try:', 'with ', 'elif ', 'else:', 'except:', 'finally:')) and stripped.endswith(':'):
            # Look ahead to find the next non-empty line
            j = i + 1
            next_non_empty_line = None
            next_non_empty_indent = 0
            
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.lstrip()
                
                # Skip empty lines
                if not next_stripped:
                    j += 1
                    continue
                    
                next_non_empty_line = next_line
                next_non_empty_indent = len(next_line) - len(next_stripped)
                break
            
            # If we found a next non-empty line and it's not properly indented, add a pass statement
            if next_non_empty_line and next_non_empty_indent <= current_indent:
                # Add the current line
                fixed_lines.append(line)
                # Add a pass statement with proper indentation
                pass_line = ' ' * (current_indent + 4) + 'pass'
                fixed_lines.append(pass_line)
                i += 1
                continue
        
        fixed_lines.append(line)
        i += 1
    
    # Second pass: fix class and method structure
    lines = fixed_lines
    fixed_lines = []
    in_class = False
    in_method = False
    
    for line in lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append(line)
            continue
            
        # Check if we're entering or leaving a class
        if stripped.startswith('class ') and '(Scene):' in stripped:
            in_class = True
            in_method = False
        elif stripped.startswith('class ') and '(Scene):' not in stripped:
            in_class = False
            in_method = False
            
        # Check if we're entering a method
        if in_class and stripped.startswith('def ') and '(self' in stripped and stripped.endswith(':'):
            in_method = True
        elif stripped in ['return', 'pass', 'break', 'continue'] or stripped.startswith('return '):
            # These statements might end a method block
            pass
            
        # Apply correct indentation
        if in_class:
            if stripped.startswith('class '):
                # Class definition at base level
                fixed_line = stripped
            elif stripped.startswith('def ') and '(self' in stripped:
                # Method definition at class level
                fixed_line = '    ' + stripped
            elif in_method:
                # Inside method, ensure proper indentation
                if current_indent >= 4:
                    fixed_line = line  # Keep current indentation if it's correct or deeper
                else:
                    fixed_line = '    ' + line.lstrip()  # Apply 4-space indentation
            else:
                # Other class content at class level
                if current_indent >= 4:
                    fixed_line = line  # Keep current indentation if it's correct or deeper
                else:
                    fixed_line = '    ' + stripped  # 4 spaces for class content
        else:
            # Outside class, no additional indentation needed
            fixed_line = line
            
        fixed_lines.append(fixed_line)
        
        # Check for method end
        if in_method and stripped in ['return', 'pass', 'break', 'continue']:
            # These might end a method
            pass
    
    # NEW: Fix positional argument follows keyword argument error
    # This is a common error in generated code where arguments are not properly ordered
    code_str = '\n'.join(fixed_lines)
    code_str = fix_argument_order(code_str)
    
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
    # If script is a dict (new format), extract the manimCode
    if isinstance(script, dict):
        if "manimCode" in script and isinstance(script.get("manimCode"), str):
            script_str = script.get("manimCode", "")
        elif "script" in script and isinstance(script.get("script"), str):
            script_str = script.get("script", "")
        else:
            # If it's a dict but doesn't have expected keys, convert to string
            script_str = str(script)
    else:
        script_str = script
    
    # Clean up old animations before running new one
    cleanup_old_animations()
    
    # Validate Python syntax first
    is_valid, validation_msg = validate_python_syntax(script_str)
    if not is_valid:
        return None, f"Invalid Python syntax: {validation_msg}"
    
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
    TIMEOUT_SECONDS = 120  # 2 minutes for faster execution
    
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
        
        # Extract scene class name from the script
        scene_class = "Scene"  # Default fallback
        for line in sanitized_script.split("\n"):
            if line.strip().startswith("class ") and "(Scene)" in line:
                scene_class = line.split()[1].replace("(Scene):", "").replace("(Scene)", "").strip()
                logger.info(f"Found scene class: {scene_class}")
                break
        
        # Optimize Manim command for educational content with faster rendering
        # Use even lower quality for educational purposes to speed up rendering
        # Compatible with Manim v0.17.2
        cmd = [
            sys.executable, "-m", "manim",
            "render",  # Add render subcommand for v0.17.2
            script_path,
            scene_class,
            "-ql",  # Low quality for faster rendering (l = low)
            "--media_dir", temp_dir,
            "--disable_caching",  # Disable caching for faster rendering
            "--progress_bar", "none",  # Disable progress bar for faster output
            "--flush_cache",  # Flush cache to avoid memory issues
            "--format", "mp4",  # Explicitly specify format
            "--renderer", "cairo",  # Use Cairo renderer for better compatibility
            "--frame_rate", "10",  # Further reduce frame rate for faster rendering
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
                "-ql",
                "--media_dir", temp_dir,
                "--disable_caching",
                "--progress_bar", "none",
                "--flush_cache",
                "--format", "mp4",  # Try MP4 format instead
                "--frame_rate", "10",  # Further reduce frame rate for faster rendering
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
                    "-ql",
                    "--media_dir", temp_dir,
                    "--disable_caching",
                    "--progress_bar", "none",
                    "--flush_cache",
                    "--format", "png",  # Try PNG sequence
                    "--frame_rate", "10",  # Further reduce frame rate for faster rendering
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
                    "-ql",
                    "--media_dir", temp_dir,
                    "--disable_caching",
                    "--progress_bar", "none",
                    "--flush_cache",
                    "--format", "mp4",  # Explicitly specify format
                    "--renderer", "cairo",  # Use Cairo renderer for better compatibility
                    "--frame_rate", "10",  # Further reduce frame rate for faster rendering
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
def create_manim_scene_with_voiceover(script: str, voiceover_text: Optional[str] = None, 
                                    voiceover_file: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Create a Manim scene with optional voiceover integration for longer educational content.
    
    Args:
        script: The Manim script to execute
        voiceover_text: Text to convert to voiceover using gTTS
        voiceover_file: Path to existing audio file to use as voiceover
        
    Returns:
        Tuple of (video_path, error_message)
    """
    # First, generate the basic Manim video
    video_path, error = execute_manim_script(script)
    if error:
        return None, error
        
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
