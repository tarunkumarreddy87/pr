# OpenRouter API Integration

## Overview
This document describes the integration of the OpenRouter API into the EduVis Pro Educational Platform. This integration allows users to generate Manim code using advanced language models through the OpenRouter API.

## Changes Made

### 1. Backend (Flask App - app.py)

1. **Added OpenRouter API Configuration**:
   - Added default API key: `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`
   - Added base URL: `https://openrouter.ai/api/v1/chat/completions`

2. **Created New API Endpoint**:
   - Endpoint: `/api/openrouter/generate-code`
   - Method: POST
   - Function: `openrouter_generate_code()`
   - Features:
     - Accepts user input for Manim code generation
     - Uses system prompt optimized for Manim code generation
     - Supports custom API keys via request body
     - Returns generated Manim code in the same format as existing endpoints

### 2. Frontend (JavaScript - assets/js/main.js)

1. **Updated Code Generation Functions**:
   - Modified `fetchCode()` to use OpenRouter API instead of n8n webhook
   - Modified `generateCodeFromDescription()` to use OpenRouter API instead of n8n webhook
   - Added support for custom API keys from localStorage

2. **Added API Key Management**:
   - Added `saveOpenRouterApiKey()` function
   - Updated page load handler to initialize API key from localStorage
   - Added proper error handling for API requests

### 3. UI (HTML - templates/professional_website.html)

1. **Updated Settings Page**:
   - Added input field for OpenRouter API Key
   - Added save button for API Key configuration

## How It Works

1. **User Input**: User provides a description of what they want to visualize
2. **API Request**: The frontend sends the description to the Flask backend
3. **OpenRouter Integration**: The backend forwards the request to OpenRouter API
4. **Code Generation**: OpenRouter generates Manim code using advanced language models
5. **Response**: The generated code is returned to the frontend
6. **Code Execution**: The frontend automatically runs the generated code to create animations

## API Endpoint Details

### `/api/openrouter/generate-code`

**Method**: POST

**Request Body**:
```json
{
  "input": "string",           // User description of desired animation
  "api_key": "string"          // Optional: Custom OpenRouter API key
}
```

**Response**:
```json
{
  "manimCode": "string",       // Generated Manim code
  "timeline": "string"         // Description of what the code does
}
```

**Error Response**:
```json
{
  "error": "string",           // Error message
  "details": "string"          // Additional details
}
```

## Usage Instructions

1. **Default Setup**: The application comes with a default OpenRouter API key configured
2. **Custom API Key**: Users can add their own OpenRouter API key in the Settings page
3. **Generating Visualizations**:
   - Go to the Auto Generator page
   - Enter a description of what you want to visualize
   - Click "Generate Visualization"
   - The system will generate Manim code and automatically run it
4. **Editing Code**:
   - Go to the Code Editor page
   - Enter a description of what you want to create
   - Click "Generate from Description"
   - Edit the generated code as needed
   - Click "Run Code" to execute

## Benefits

1. **Advanced Code Generation**: Uses state-of-the-art language models for better code generation
2. **Educational Focus**: System prompt optimized for educational content
3. **Flexibility**: Supports custom API keys for users with their own OpenRouter accounts
4. **Seamless Integration**: Works within the existing application workflow
5. **Error Handling**: Comprehensive error handling and user feedback

## Future Improvements

1. **Model Selection**: Allow users to choose different language models
2. **Prompt Engineering**: Further optimize prompts for specific educational domains
3. **Caching**: Implement caching for common requests to reduce API usage
4. **Rate Limiting**: Add rate limiting to prevent API abuse
5. **Analytics**: Track usage patterns to improve the service