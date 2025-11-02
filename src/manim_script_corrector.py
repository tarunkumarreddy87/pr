import re
import sys
import os

def fix_color_constants(script_content):
    """Replace color palette variants with base colors unless they're imported."""
    # Check if color variants are imported
    has_color_import = re.search(r'from\s+manim\.utils\.color\s+import', script_content)
    
    if not has_color_import:
        # Replace color variants with base colors
        color_bases = ['BLUE', 'RED', 'GREEN', 'YELLOW', 'PURPLE', 'ORANGE', 'PINK', 'CYAN', 'TEAL', 'WHITE', 'BLACK', 'GRAY', 'GREY']
        for base_color in color_bases:
            # Replace variants like BLUE_A, BLUE_B, etc. with just BLUE
            script_content = re.sub(rf'{base_color}_[A-E]', base_color, script_content)
    
    return script_content

def fix_fonts(script_content):
    """Replace custom fonts with Sans font."""
    # Replace font="Montserrat" or other custom fonts with font="Sans"
    script_content = re.sub(r'font\s*=\s*["\'](?!Sans)[^"\']+["\']', 'font="Sans"', script_content)
    return script_content

def fix_voiceover_service(script_content):
    """Add offline TTS fallback for Google TTS and improve reliability."""
    # Check if script uses Google TTS
    if 'GTTSService' in script_content:
        # Add import for pyttsx3 service if not already present
        if 'from manim_voiceover.services.pyttsx3 import PyTTSX3Service' not in script_content:
            # Add import after other manim_voiceover imports
            script_content = re.sub(
                r'(from manim_voiceover\.services\.gtts import GTTSService)',
                r'\1\nfrom manim_voiceover.services.pyttsx3 import PyTTSX3Service',
                script_content
            )
        
        # Improve the fallback mechanism with better error handling
        if 'self.set_speech_service(GTTSService())' in script_content and 'try:' not in script_content:
            script_content = re.sub(
                r'(self\.set_speech_service\(GTTSService\(\)\))',
                r'try:\n            # Try to use Google TTS (requires internet)\n            \1\n        except Exception as e:\n            # Fallback to offline TTS\n            print(f"Warning: GTTSService failed: {e}. Using offline PyTTSX3Service.")\n            self.set_speech_service(PyTTSX3Service())',
                script_content
            )
    
    return script_content

def fix_syntax_errors(script_content):
    """Fix common syntax errors in Manim scripts."""
    # Fix missing parentheses in function calls - more specific and safer pattern
    lines = script_content.split('\n')
    fixed_lines = []
    for line in lines:
        # Fix self.play calls that are missing closing parenthesis
        # Look for lines with .play( that have more open than close parentheses
        if '.play(' in line and line.count('(') > line.count(')'):
            # Add the missing closing parenthesis
            line = line.rstrip() + ')'
        # Fix self.wait calls that are missing closing parenthesis
        elif '.wait(' in line and line.count('(') > line.count(')'):
            line = line.rstrip() + ')'
        # Fix self.add calls that are missing closing parenthesis
        elif '.add(' in line and line.count('(') > line.count(')'):
            line = line.rstrip() + ')'
        # Fix self.set_speech_service calls that are missing closing parenthesis
        elif 'self.set_speech_service(' in line and line.count('(') > line.count(')'):
            line = line.rstrip() + ')'
        # Fix GTTSService calls that are missing closing parenthesis
        elif 'GTTSService(' in line and line.count('(') > line.count(')'):
            line = line.rstrip() + ')'
        fixed_lines.append(line)
    script_content = '\n'.join(fixed_lines)
    
    return script_content

def fix_external_assets(script_content):
    """Remove or replace references to external assets."""
    # Replace SVGMobject with Text or Circle
    script_content = re.sub(
        r'SVGMobject\([^)]+\)',
        r'Text("SVG Placeholder", font="Sans")',
        script_content
    )
    
    # Replace ImageMobject with Rectangle
    script_content = re.sub(
        r'ImageMobject\([^)]+\)',
        r'Rectangle(height=2, width=3, color=WHITE, fill_opacity=0.5)',
        script_content
    )
    
    return script_content

def correct_manim_script(script_content):
    """Apply all corrections to the Manim script."""
    script_content = fix_color_constants(script_content)
    script_content = fix_fonts(script_content)
    script_content = fix_voiceover_service(script_content)
    script_content = fix_syntax_errors(script_content)
    script_content = fix_external_assets(script_content)
    
    return script_content

def main():
    if len(sys.argv) < 2:
        print("Usage: python manim_script_corrector.py <input_script_path> [output_script_path]")
        return
    
    input_path = sys.argv[1]
    
    # If output path is not provided, use input path with "_corrected" suffix
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_corrected{ext}"
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        corrected_script = correct_manim_script(script_content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(corrected_script)
        
        print(f"Script corrected and saved to {output_path}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()