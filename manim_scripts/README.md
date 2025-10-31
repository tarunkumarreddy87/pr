# Manim Scripts

This directory contains Manim animation scripts that can be executed to generate educational videos.

## Files

- [computer_parts.py](file:///c:/Users/Tarun/OneDrive/%E6%96%87%E6%A1%A3/cop/manim_scripts/computer_parts.py) - A visualization of computer components with voiceover explanations
- [../process_n8n_output.py](file:///c:/Users/Tarun/OneDrive/%E6%96%87%E6%A1%A3/cop/process_n8n_output.py) - Script to process n8n JSON output and execute Manim code
- [../test_computer_parts.py](file:///c:/Users/Tarun/OneDrive/%E6%96%87%E6%A1%A3/cop/test_computer_parts.py) - Direct test script for the computer parts animation

## Usage

### Direct execution
```bash
python test_computer_parts.py
```

### Processing n8n output
```bash
python process_n8n_output.py n8n_computer_parts_output.json
```

## Requirements

- Manim
- manim-voiceover
- gTTS (Google Text-to-Speech)

Install requirements with:
```bash
pip install manim manim-voiceover gtts
```