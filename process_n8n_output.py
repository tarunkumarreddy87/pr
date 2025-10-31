#!/usr/bin/env python3
"""
Script to process n8n JSON output and execute the Manim code
"""

import sys
import os
import json

# Add the current directory to the path so we can import manim_executor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manim_executor import execute_manim_script

def process_n8n_output(json_file_path):
    """
    Process n8n JSON output and execute the Manim code
    
    Args:
        json_file_path (str): Path to the JSON file containing n8n output
    """
    # Read the JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            n8n_data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return 1
    
    # Extract the Manim code
    if "manimCode" in n8n_data:
        manim_code = n8n_data["manimCode"]
    else:
        print("No 'manimCode' field found in JSON")
        return 1
    
    # Execute the Manim code
    print("Executing Manim code from n8n output...")
    video_path, error = execute_manim_script(manim_code)
    
    if error:
        print(f"Error executing Manim code: {error}")
        return 1
    else:
        print(f"Animation generated successfully: {video_path}")
        return 0

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_n8n_output.py <n8n_output.json>")
        return 1
    
    json_file_path = sys.argv[1]
    
    if not os.path.exists(json_file_path):
        print(f"File not found: {json_file_path}")
        return 1
    
    return process_n8n_output(json_file_path)

if __name__ == "__main__":
    sys.exit(main())