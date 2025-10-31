// Initialize CodeMirror for the editor page
var editor;

// Utility function to clean invalid Unicode characters that can cause syntax errors
function cleanInvalidUnicode(text) {
    if (typeof text !== 'string') return text;
    
    return text.replace(/\u2013|\u2014|\u2018|\u2019|\u201c|\u201d|\u2026/g, function(match) {
        switch(match) {
            case '\u2013': // en dash
            case '\u2014': // em dash
                return '-';
            case '\u2018': // left single quotation mark
            case '\u2019': // right single quotation mark
                return "'";
            case '\u201c': // left double quotation mark
            case '\u201d': // right double quotation mark
                return '"';
            case '\u2026': // horizontal ellipsis
                return '...';
            default:
                return match;
        }
    });
}

// Test server connection on page load
window.addEventListener('DOMContentLoaded', async function() {
    try {
        // Initialize webhook URL from localStorage if available
        const savedWebhookUrl = localStorage.getItem('n8nWebhookUrl');
        if (savedWebhookUrl) {
            document.getElementById('n8n-webhook').value = savedWebhookUrl;
        }
        
        // Initialize OpenRouter API Key from localStorage if available
        const savedOpenRouterApiKey = localStorage.getItem('openrouterApiKey');
        if (savedOpenRouterApiKey) {
            document.getElementById('openrouter-api-key').value = savedOpenRouterApiKey;
        }
        
        const response = await fetch('/healthz');
        if (!response.ok) {
            console.error('Server health check failed');
            // Update status on all pages to show server connection issue
            document.querySelectorAll('.status-text').forEach(status => {
                if (status.id.includes('status')) {
                    status.textContent = "Server not connected. Please start the Flask server.";
                    status.className = "status-text status-error";
                }
            });
        } else {
            console.log('Server is running and healthy');
            // Update server status in settings
            const serverStatus = document.getElementById('server-status');
            if (serverStatus) {
                serverStatus.textContent = "Online";
                serverStatus.style.color = "var(--success)";
            }
        }
    } catch (error) {
        console.error('Server connection error:', error);
        // Update status on all pages to show server connection issue
        document.querySelectorAll('.status-text').forEach(status => {
            if (status.id.includes('status')) {
                status.textContent = "Server not connected. Please start the Flask server.";
                status.className = "status-text status-error";
            }
        });
    }
});

// Toggle sidebar function
function toggleSidebar() {
    const sidebar = document.getElementById('mainSidebar');
    const toggleIcon = document.getElementById('toggleIcon');
    const mainContent = document.querySelector('.main-content');
    sidebar.classList.toggle('collapsed');
    
    if (sidebar.classList.contains('collapsed')) {
        toggleIcon.className = 'fas fa-chevron-right';
        mainContent.classList.add('sidebar-collapsed');
    } else {
        toggleIcon.className = 'fas fa-chevron-left';
        mainContent.classList.remove('sidebar-collapsed');
    }
}

// Function to trigger video generation when clicking play icon
function triggerGeneration() {
    const activePage = document.querySelector('.page-content.active').id;
    
    if (activePage === 'generator-page') {
        const input = document.getElementById('userInput').value;
        if (input.trim() !== '') {
            fetchCode();
        } else {
            showSampleDesign();
        }
    } else if (activePage === 'editor-page') {
        const code = editor.getValue();
        if (code.trim() !== '') {
            runCode();
        } else {
            generateCodeFromDescription();
        }
    }
}

// Function to simulate YouTube-like loading
function startYouTubeLoading() {
    const loaders = document.querySelectorAll('.youtube-loader');
    loaders.forEach(loader => {
        loader.style.display = 'block';
    });
}

function stopYouTubeLoading() {
    const loaders = document.querySelectorAll('.youtube-loader');
    loaders.forEach(loader => {
        loader.style.display = 'none';
        loader.querySelector('.youtube-loader-bar').style.width = '0%';
    });
}

// Navigation function
function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.remove('active');
    });
    
    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show the selected page
    document.getElementById(`${pageId}-page`).classList.add('active');
    
    // Add active class to the clicked nav item
    event.target.closest('.nav-item').classList.add('active');
    
    // Initialize CodeMirror when first visiting the editor page
    if (pageId === 'editor' && !editor) {
        editor = CodeMirror.fromTextArea(document.getElementById("code-editor"), {
            mode: "python",
            theme: "monokai",
            lineNumbers: true,
            autoCloseBrackets: true,
            indentUnit: 4,
            value: "# Write your Manim code here\n\nfrom manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        # Your animation code here\n        circle = Circle(radius=1, color=BLUE)\n        self.play(Create(circle))\n        self.wait(2)"
        });
    }
}

// Notification function
function showNotification() {
    alert("You have no new notifications.\n\nThis is a professional educational platform notification system.");
}

// Generator page functions
function loadExample(type) {
    const examples = {
        science: "Explain the process of photosynthesis with an animation",
        math: "Illustrate the Pythagorean theorem with a visual proof",
        history: "Animate the water cycle showing evaporation and precipitation"
    };
    
    document.getElementById('userInput').value = examples[type];
}

// Function to parse and display n8n output with separate manim code and timeline
function parseAndDisplayN8nOutput(data) {
    console.log('Parsing n8n output:', data);
    
    // Check if data is in the new format with manimCode and timeline
    if (data.manimCode && data.timeline) {
        // Clean the manim code of invalid Unicode characters
        let cleanCode = cleanInvalidUnicode(data.manimCode);
        
        // Display manim code in the editor
        if (typeof editor !== 'undefined') {
            editor.setValue(cleanCode);
        } else {
            // If CodeMirror editor is not available, use the textarea
            const codeEditor = document.getElementById('code-editor');
            if (codeEditor) {
                codeEditor.value = cleanCode;
            }
        }
        
        // Display timeline in the transcript section
        const transcriptContainer = document.getElementById('timeline-container');
        const transcriptContent = document.getElementById('transcript-content');
        if (transcriptContainer && transcriptContent) {
            transcriptContent.textContent = data.timeline;
            transcriptContainer.style.display = 'block';
        }
        
        // Automatically run the generated code
        runGeneratedCode(cleanCode);
        
        return cleanCode;
    } 
    // Handle old format
    else if (Array.isArray(data) && data[0]) {
        const sectionObj = data[0];
        if (sectionObj.manim_code) {
            // Clean the code of invalid Unicode characters
            let cleanCode = cleanInvalidUnicode(sectionObj.manim_code);
            
            // Automatically run the generated code
            runGeneratedCode(cleanCode);
            return cleanCode;
        } else {
            // Original format - concatenate all sections
            let code = Object.keys(sectionObj)
                .map(key => sectionObj[key])
                .join("\n\n")
                .replace(/```python|```/g, '')
                .trim();
            
            // Clean the code of invalid Unicode characters
            code = cleanInvalidUnicode(code);
            
            // Automatically run the generated code
            runGeneratedCode(code);
            return code;
        }
    }
    // Handle direct script format
    else if (data.script) {
        // Clean the script of invalid Unicode characters
        let cleanScript = cleanInvalidUnicode(data.script);
        
        // Automatically run the generated code
        runGeneratedCode(cleanScript);
        return cleanScript;
    }
    // If we can't parse, return as is
    return data;
}

// Function to fetch code from OpenRouter API
async function fetchCode() {
    let input = document.getElementById('userInput').value;
    const statusIndicator = document.getElementById('generator-status-indicator');
    const statusText = document.getElementById('generator-status');
    const error = document.getElementById('generator-error');
    const loading = document.getElementById('generator-loading');
    const videoPlaceholder = document.getElementById('generator-video-container').querySelector('.video-placeholder');
    const video = document.getElementById('generator-output-video');
    const generateBtn = document.getElementById('generate-btn');
    const buttonLoader = document.getElementById('button-loader');

    if (!input) {
        error.textContent = "Please enter a learning topic!";
        error.style.display = "block";
        return;
    }

    // Clean the input of invalid Unicode characters before sending
    input = cleanInvalidUnicode(input);

    // Show loading state
    loading.style.display = "flex";
    buttonLoader.style.display = "inline-block";
    generateBtn.style.display = "none";
    error.style.display = "none";
    videoPlaceholder.style.display = "none";
    video.style.display = "none";
    statusText.textContent = "Generating educational visualization...";
    statusText.className = "status-text status-loading";
    
    try {
        // First check if the server is reachable
        await fetch('/healthz');
        
        // Get custom API key if available
        const customApiKey = localStorage.getItem('openrouterApiKey');
        const requestBody = { input: input };
        if (customApiKey) {
            requestBody.api_key = customApiKey;
        }
        
        // Call the OpenRouter API endpoint
        const response = await fetch('/api/openrouter/generate-code', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
                },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Unknown error');
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Parse and display the OpenRouter output
        const script = parseAndDisplayN8nOutput(data);

        if (!script) {
            throw new Error("No script returned from OpenRouter");
        }

        // Update UI with success
        loading.style.display = "none";
        buttonLoader.style.display = "none";
        generateBtn.style.display = "inline-flex";
        statusText.textContent = "Educational visualization generated successfully";
        statusText.className = "status-text status-success";
        
    } catch (err) {
        console.error("Error fetching code:", err);
        error.textContent = "Error generating visualization: " + err.message;
        error.style.display = "block";
        loading.style.display = "none";
        buttonLoader.style.display = "none";
        generateBtn.style.display = "inline-flex";
        videoPlaceholder.style.display = "block";
        statusText.textContent = "Error occurred";
        statusText.className = "status-text status-error";
    }
}

// Validate Manim script for common issues and clean invalid characters
function isValidManimScript(script) {
    // Check if script has proper class structure
    if (!script.includes('class ') || !script.includes('(Scene):')) {
        return false;
    }
    
    // Clean common invalid Unicode characters that can cause syntax errors
    script = cleanInvalidUnicode(script);
    
    // Check if self is used properly within class methods
    const lines = script.split('\n');
    let inClass = false;
    let inMethod = false;
    
    for (let line of lines) {
        const trimmed = line.trim();
        
        if (trimmed.startsWith('class ') && trimmed.includes('(Scene):')) {
            inClass = true;
            inMethod = false;
        } else if (inClass && trimmed.startsWith('def ') && trimmed.includes('(self')) {
            inMethod = true;
        } else if (trimmed === '' || trimmed.startsWith('#')) {
            // Empty line or comment, continue
            continue;
        } else if (trimmed.startsWith('class ') && !trimmed.includes('(Scene):')) {
            // New class that's not a Scene, reset
            inClass = false;
            inMethod = false;
        } else if (inClass && trimmed.startsWith('self.') && !inMethod) {
            // self used outside of method
            return false;
        } else if (inMethod && (trimmed === 'return' || trimmed.startsWith('return '))) {
            inMethod = false;
        }
    }
    
    return true;
}

// NEW: Enhanced validation to check for positional argument follows keyword argument error
function hasArgumentOrderError(script) {
    // Check for common patterns where positional arguments follow keyword arguments
    const lines = script.split('\n');
    
    for (let line of lines) {
        const trimmed = line.trim();
        
        // Check for play() calls with potential argument order issues
        if (trimmed.includes('self.play(') && trimmed.includes('=')) {
            if (hasPositionalAfterKeyword(trimmed)) {
                return true;
            }
        }
        
        // Check for other common Manim function calls
        const manimFunctions = ['Create', 'Transform', 'Write', 'FadeIn', 'FadeOut', 'MoveToTarget'];
        for (let func of manimFunctions) {
            if (trimmed.includes(func + '(') && trimmed.includes('=')) {
                if (hasPositionalAfterKeyword(trimmed)) {
                    return true;
                }
            }
        }
    }
    
    return false;
}

// Helper function to detect positional arguments after keyword arguments
function hasPositionalAfterKeyword(line) {
    // Simple approach to detect the pattern
    // This looks for a function call with both = and , and checks if there's
    // a pattern like: func(arg1, kwarg=value, arg2)
    
    // Extract arguments from function calls
    const funcCallMatch = line.match(/\w+$$([^)]*)$$/);
    if (funcCallMatch) {
        const argsStr = funcCallMatch[1];
        const args = argsStr.split(',').map(arg => arg.trim());
        let foundKeyword = false;
        
        for (let arg of args) {
            if (arg.includes('=')) {
                foundKeyword = true;
            } else if (foundKeyword && !arg.includes('=') && arg.length > 0) {
                // Found a positional argument after a keyword argument
                return true;
            }
        }
    }
    
    return false;
}

// Run the generated code and display the video
async function runGeneratedCode(script) {
    const loading = document.getElementById('generator-loading');
    const error = document.getElementById('generator-error');
    const videoContainer = document.getElementById('generator-video-container');
    const video = document.getElementById('generator-output-video');
    const status = document.getElementById('generator-status');

    // Clean the script of invalid Unicode characters before sending
    script = cleanInvalidUnicode(script);

    // NEW: Check for argument order errors before sending to backend
    if (hasArgumentOrderError(script)) {
        showError("The generated code has a syntax error: positional argument follows keyword argument. Please regenerate or fix the code manually.", error, status);
        status.textContent = "Code validation failed";
        status.className = "status-text status-error";
        return;
    }

    // Show loading state
    loading.style.display = 'block';
    error.style.display = 'none';
    videoContainer.querySelector('.video-placeholder').style.display = 'none';
    video.style.display = 'none';
    status.textContent = "Creating educational animation...";
    status.className = "status-text status-loading";

    try {
        // First check if the server is reachable
        const healthCheck = await fetch('/healthz');
        if (!healthCheck.ok) {
            throw new Error('Server is not responding. Please make sure the Flask server is running.');
        }

        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ script: script })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error('HTTP error! status: ' + response.status + ', body: ' + errorText);
        }

        const data = await response.json();
        loading.style.display = 'none';
        
        if (data.error) {
            error.textContent = 'Server Error: ' + data.error;
            error.style.display = 'block';
            status.textContent = "Animation creation failed";
            status.className = "status-text status-error";
            console.error('Server error:', data.error);
        } else {
            // Successfully generated video
            videoContainer.querySelector('.video-placeholder').style.display = 'none';
            video.style.display = 'block';
            video.src = data.video_url + '?t=' + new Date().getTime(); // Prevent caching

            video.onerror = function(e) {
                console.error('Video loading error:', e);
                error.textContent = 'Error loading video. Please try again.';
                error.style.display = 'block';
                videoContainer.querySelector('.video-placeholder').style.display = 'block';
                video.style.display = 'none';
                status.textContent = "Animation creation failed";
                status.className = "status-text status-error";
            };

            video.onloadeddata = function() {
                stopYouTubeLoading();
            };
            
            // Add onload event to properly update UI when video is loaded
            video.onload = function() {
                status.textContent = "Educational animation created successfully";
                status.className = "status-text status-success";
                stopYouTubeLoading();
            };
            
            // Add onerror event to handle video loading errors
            video.onerror = function(e) {
                console.error('Video loading error:', e);
                error.textContent = 'Error loading video. Please try again.';
                error.style.display = 'block';
                videoContainer.querySelector('.video-placeholder').style.display = 'block';
                video.style.display = 'none';
                status.textContent = "Code execution failed";
                status.className = "status-text status-error";
                stopYouTubeLoading();
            };
            video.load();
        }
    } catch (err) {
        console.error('Fetch error:', err);
        loading.style.display = 'none';
        error.textContent = 'Network Error: ' + err.message;
        error.style.display = 'block';
        status.textContent = "Animation creation failed: API request failed";
        status.className = "status-text status-error";
    }
}

// Clear the generator
function clearGenerator() {
    document.getElementById('userInput').value = "";
    document.getElementById('generator-status').textContent = "Ready to create educational visualizations";
    document.getElementById('generator-status').className = "status-text";
    document.getElementById('generator-error').style.display = "none";
    document.getElementById('generator-video-container').querySelector('.video-placeholder').style.display = "block";
    document.getElementById('generator-output-video').style.display = "none";
}

// Show error message
function showError(message, errorElement, statusElement) {
    errorElement.textContent = message;
    errorElement.style.display = "block";
    statusElement.textContent = "Error occurred";
    statusElement.className = "status-text status-error";
}

// Cleanup old animation files
function cleanupFiles() {
    const status = document.getElementById('generator-status');
    status.textContent = "Cleaning up files...";
    status.className = "status-text status-loading";
    
    fetch('/api/cleanup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("HTTP error! status: " + response.status);
        }
        return response.json();
    })
    .then(data => {
        status.textContent = "Cleanup complete";
        status.className = "status-text status-success";
        setTimeout(() => {
            status.textContent = "Ready to create educational visualizations";
            status.className = "status-text";
        }, 3000);
        console.log('Cleanup result:', data);
    })
    .catch(err => {
        console.error('Cleanup error:', err);
        status.textContent = "Cleanup failed";
        status.className = "status-text status-error";
        showError("Cleanup failed: " + err.message, document.getElementById('generator-error'), status);
    });
}

// Editor page functions
// Sample code templates with voiceover integration
const sampleCodes = {
    basic: {
        code: `from manim import *

class MyScene(Scene):
    def construct(self):
        # Create a circle
        circle = Circle(radius=1, color=BLUE)
        self.play(Create(circle))
        self.wait(1)
        
        # Transform to a square
        square = Square(side_length=2, color=YELLOW)
        self.play(Transform(circle, square))
        self.wait(1)
        
        # Fade out
        self.play(FadeOut(circle))
        self.wait(1)`,
        description: "Basic geometric transformations with circle to square animation",
        voiceover: "In this animation, we'll explore basic geometric transformations. First, we create a blue circle. Then, we transform it into a yellow square. Finally, we fade out the shape. This demonstrates how Manim can smoothly transition between different geometric forms."
    },
    
    text: {
        code: `from manim import *

class MyScene(Scene):
    def construct(self):
        # Create title
        title = Text("Hello, EduVis Pro!", color=GREEN)
        self.play(Write(title))
        self.wait(2)
        
        # Move title to top
        self.play(title.animate.to_edge(UP))
        
        # Create explanation text
        explanation = Text("Learning made visual", color=YELLOW)
        self.play(Write(explanation))
        self.wait(2)
        
        # Fade everything out
        self.play(FadeOut(title), FadeOut(explanation))
        self.wait(1)`,
        description: "Text animation with writing effects and positioning",
        voiceover: "This example shows how to animate text in Manim. We start by creating a title with the text 'Hello, EduVis Pro!' in green. We use the Write animation to make it appear as if it's being written. Then we move the title to the top of the screen. Next, we add an explanation text and animate it similarly. Finally, we fade out both text elements."
    },
    
    graph: {
        code: `from manim import *

class MyScene(Scene):
    def construct(self):
        # Create axes
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            axis_config={"color": BLUE},
        )
        
        # Create a graph
        graph = axes.plot(lambda x: x**2, color=YELLOW)
        graph_label = axes.get_graph_label(graph, label="y = x^2")
        
        # Animate
        self.play(Create(axes), Create(graph))
        self.play(Write(graph_label))
        self.wait(2)`,
        description: "Graph plotting with axes and mathematical functions",
        voiceover: "In this example, we create a mathematical graph visualization. First, we define the coordinate axes with a range from negative three to positive three. Then we plot the function y equals x squared, which creates a parabola. We add a label to identify the function. The animation shows the axes being created, followed by the graph itself, and finally the label being written. This demonstrates how Manim can visualize mathematical concepts."
    }
};

// Load sample code
function loadSampleCode(type) {
    const sample = sampleCodes[type];
    // Clean the sample code of invalid Unicode characters
    const cleanCode = cleanInvalidUnicode(sample.code);
    editor.setValue(cleanCode);
    document.getElementById('code-description').value = sample.description;
    clearEditorOutput();
}

// Generate code from description using OpenRouter API
async function generateCodeFromDescription() {
    let description = document.getElementById('code-description').value;
    const status = document.getElementById('editor-status');
    const error = document.getElementById('editor-error');
    const loading = document.getElementById('editor-loading');

    if (!description) {
        showError("Please enter a description!", error, status);
        return;
    }

    // Clean the description of invalid Unicode characters before sending
    description = cleanInvalidUnicode(description);

    status.textContent = "Generating code from description...";
    status.className = "status-text status-loading";
    error.style.display = "none";
    loading.style.display = "block";

    try {
        // Get custom API key if available
        const customApiKey = localStorage.getItem('openrouterApiKey');
        const requestBody = { input: description };
        if (customApiKey) {
            requestBody.api_key = customApiKey;
        }
        
        // Try OpenRouter API first
        const response = await fetch('/api/openrouter/generate-code', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        console.log('OpenRouter response status:', response.status);
        console.log('OpenRouter response headers:', [...response.headers.entries()]);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error("OpenRouter API returned HTTP " + response.status + ": " + errorText);
        }

        const data = await response.json();
        console.log('OpenRouter response data:', data);

        if (data.error) {
            throw new Error(data.error);
        }

        // Handle different response formats
        let script = '';
        if (data.manimCode) {
            // New format from OpenRouter
            script = data.manimCode;
        } else if (data.script) {
            // Old format
            script = data.script;
        } else if (Array.isArray(data) && data[0]) {
            // Old format - array of sections
            const sectionObj = data[0];
            if (sectionObj.manim_code) {
                // Simulated webhook format
                script = sectionObj.manim_code;
            } else {
                // Original format - concatenate all sections
                script = Object.keys(sectionObj)
                    .map(key => sectionObj[key])
                    .join("\n\n")
                    .replace(/```python|```/g, '')
                    .trim();
            }
        }

        if (!script) {
            throw new Error("No script returned from OpenRouter API");
        }

        // Clean the script of invalid Unicode characters before setting in editor
        script = cleanInvalidUnicode(script);

        editor.setValue(script);
        status.textContent = "Code generated successfully with OpenRouter";
        status.className = "status-text status-success";
        loading.style.display = "none";

    } catch (error) {
        console.error("Error generating code:", error);
        showError("Error generating code: " + error.message, error, status);
        status.textContent = "Error occurred";
        status.className = "status-text status-error";
        loading.style.display = "none";
    }
}

// Run the code in the editor
async function runCode() {
    const code = editor.getValue();
    const loading = document.getElementById('editor-loading');
    const error = document.getElementById('editor-error');
    const videoContainer = document.getElementById('editor-video-container');
    const video = document.getElementById('editor-output-video');
    const status = document.getElementById('editor-status');

    if (!code.trim()) {
        showError("Please enter some code to run!", error, status);
        return;
    }

    // Clean the code of invalid Unicode characters before sending
    let cleanCode = cleanInvalidUnicode(code);

    // Show loading state
    loading.style.display = 'block';
    error.style.display = 'none';
    videoContainer.querySelector('.video-placeholder').style.display = 'none';
    video.style.display = 'none';
    status.textContent = "Running your code...";
    status.className = "status-text status-loading";
    startYouTubeLoading();

    try {
        // First check if the server is reachable
        const healthCheck = await fetch('/healthz');
        if (!healthCheck.ok) {
            throw new Error('Server is not responding. Please make sure the Flask server is running.');
        }

        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ script: cleanCode })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error('HTTP error! status: ' + response.status + ', body: ' + errorText);
        }

        const data = await response.json();
        loading.style.display = 'none';
        
        if (data.error) {
            error.textContent = 'Server Error: ' + data.error;
            error.style.display = 'block';
            status.textContent = "Code execution failed";
            status.className = "status-text status-error";
            console.error('Server error:', data.error);
        } else {
            // Successfully generated video
            videoContainer.querySelector('.video-placeholder').style.display = 'none';
            video.style.display = 'block';
            video.src = data.video_url + '?t=' + new Date().getTime(); // Prevent caching

            video.onerror = function(e) {
                console.error('Video loading error:', e);
                error.textContent = 'Error loading video. Please try again.';
                error.style.display = 'block';
                videoContainer.querySelector('.video-placeholder').style.display = 'block';
                video.style.display = 'none';
                status.textContent = "Code execution failed";
                status.className = "status-text status-error";
            };

            video.onloadeddata = function() {
                stopYouTubeLoading();
            };
        }
    } catch (error) {
        console.error("Error running code:", error);
        showError("Error running code: " + error.message, error, status);
        status.textContent = "Error occurred";
        status.className = "status-text status-error";
        loading.style.display = "none";
        stopYouTubeLoading();
    }
}

// The fetchCode function is already defined above

// Clear the editor
function clearEditor() {
    editor.setValue("# Write your Manim code here\n\nfrom manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        # Your animation code here\n        pass");
    document.getElementById('code-description').value = "";
    clearEditorOutput();
}

// Clear editor output
function clearEditorOutput() {
    document.getElementById('editor-status').textContent = "Ready to edit and run Manim code";
    document.getElementById('editor-status').className = "status-text";
    document.getElementById('editor-error').style.display = "none";
    document.getElementById('editor-video-container').querySelector('.video-placeholder').style.display = "block";
    document.getElementById('editor-output-video').style.display = "none";
}

// Avatar page functions
// Handle Enter key press in the user input field
function handleUserInputKeyPress(event) {
    if (event.key === 'Enter') {
        fetchCode();
    }
}

// Handle Enter key press in chat input
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Handle Enter key press in doubt input
function handleDoubtKeyPress(event) {
    if (event.key === 'Enter') {
        askDoubt();
    }
}

// Ask a doubt about the visualization
function askDoubt() {
    const input = document.getElementById('doubt-input');
    const question = input.value.trim();
    
    if (!question) return;
    
    // Add user question to doubt panel
    addDoubtMessage('user', question);
    input.value = '';
    
    // Pause the video while answering
    const video = document.getElementById('generator-output-video');
    const wasPlaying = !video.paused;
    if (wasPlaying) {
        video.pause();
    }
    
    // Show loading state
    const status = document.getElementById('generator-status');
    status.textContent = "AI tutor is answering your doubt...";
    status.className = "status-text status-loading";
    
    // Simulate AI response (in a real implementation, this would call an AI service)
    setTimeout(() => {
        const responses = [
            "That's a great question! Let me explain this concept in more detail...",
            "I understand your confusion. Here's a clearer explanation...",
            "This is an important concept. Let me break it down for you...",
            "You're on the right track! Here's some additional information...",
            "That's an interesting point. Let me provide some context..."
        ];
        
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        addDoubtMessage('avatar', randomResponse);
        
        status.textContent = "Educational visualization created successfully";
        status.className = "status-text status-success";
        
        // Resume video if it was playing
        if (wasPlaying) {
            video.play();
        }
    }, 1500);
}

// Add message to doubt display
function addDoubtMessage(sender, message) {
    const chatContainer = document.getElementById('doubt-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = `<strong>You:</strong> ${message}`;
    } else {
        messageDiv.innerHTML = `<strong>AI Tutor:</strong> ${message}`;
    }
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Send message to AI tutor
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    const status = document.getElementById('avatar-status');
    const error = document.getElementById('avatar-error');
    const loading = document.getElementById('avatar-loading');
    
    if (!message) {
        showError("Please enter a question!", error, status);
        return;
    }
    
    // Add user message to chat
    addMessageToChat('user', message);
    input.value = '';
    
    // Show loading state
    status.textContent = "AI tutor is answering your question...";
    status.className = "status-text status-loading";
    error.style.display = "none";
    loading.style.display = "block";
    startYouTubeLoading();

    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            throw new Error('Server Error: ' + response.statusText);
        }

        const data = await response.json();

        if (data.error) {
            error.textContent = 'Server Error: ' + data.error;
            error.style.display = 'block';
            status.textContent = "Code execution failed";
            status.className = "status-text status-error";
            console.error('Server error:', data.error);
        } else {
            // Successfully generated video
            videoContainer.querySelector('.video-placeholder').style.display = 'none';
            video.style.display = 'block';
            video.src = data.video_url + '?t=' + new Date().getTime(); // Prevent caching

            video.onerror = function(e) {
                console.error('Video loading error:', e);
                error.textContent = 'Error loading video. Please try again.';
                error.style.display = 'block';
                videoContainer.querySelector('.video-placeholder').style.display = 'block';
                video.style.display = 'none';
                status.textContent = "Code execution failed";
                status.className = "status-text status-error";
            };

            video.onloadeddata = function() {
                if (video.readyState >= 2) {
                    // Ensure video plays with sound
                    video.muted = false;
                    video.play().then(() => {
                        console.log('Video playback started successfully');
                    }).catch(e => {
                        console.log('Video autoplay failed:', e);
                        // Try again with muted audio
                        video.muted = true;
                        video.play();
                    });
                    status.textContent = "Code executed successfully";
                    status.className = "status-text status-success";
                }
            };
            video.load();
        }
    } catch (err) {
        console.error('Fetch error:', err);
        loading.style.display = 'none';
        error.textContent = 'Network Error: ' + err.message;
        error.style.display = 'block';
        status.textContent = "Code execution failed: API request failed";
        status.className = "status-text status-error";
        stopYouTubeLoading();
    }
}

// Add message to chat display
function addMessageToChat(sender, message) {
    const chatContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = `<strong>You:</strong> ${message}`;
    } else {
        messageDiv.innerHTML = `<strong>AI Tutor:</strong> ${message}`;
    }
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Ask a predefined question
function askQuestion(question) {
    document.getElementById('chat-input').value = question;
    sendMessage();
}

// Load a prompt for the avatar
function loadAvatarPrompt(type) {
    const prompts = {
        math: "I need help understanding a math concept I just visualized",
        science: "Can you explain the science behind what I just saw?"
    };
    
    document.getElementById('chat-input').value = prompts[type];
}

// Clear the chat
function clearChat() {
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.innerHTML = '<div class="message avatar-message"><strong>AI Tutor:</strong> Hello! I\'m your AI learning assistant. Ask me anything about the visualizations or concepts you\'re learning!</div>';
    document.getElementById('chat-input').value = '';
    document.getElementById('avatar-status').textContent = "AI tutor is ready to help";
    document.getElementById('avatar-status').className = "status-text";
    document.getElementById('avatar-error').style.display = "none";
}

// Voiceover page functions
async function generateVoiceover() {
    const text = document.getElementById('voiceover-text').value;
    const service = document.getElementById('voiceover-service').value;
    const status = document.getElementById('voiceover-status');
    const error = document.getElementById('voiceover-error');
    const loading = document.getElementById('voiceover-loading');
    const audio = document.getElementById('voiceover-audio');
    const placeholder = document.getElementById('voiceover-placeholder');

    if (!text.trim()) {
        showError("Please enter text for voiceover!", error, status);
        return;
    }

    status.textContent = "Generating voiceover...";
    status.className = "status-text status-loading";
    error.style.display = "none";
    loading.style.display = "block";
    placeholder.style.display = "none";
    audio.style.display = "none";

    try {
        // Call the backend API to generate voiceover
        const response = await fetch('/api/voiceover', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text, service: service })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate voiceover');
        }

        const data = await response.json();
        
        status.textContent = "Voiceover generated successfully";
        status.className = "status-text status-success";
        loading.style.display = "none";
        
        // Set the audio source to the generated file
        audio.src = data.audio_url;
        audio.style.display = "block";
        placeholder.style.display = "none";
        
    } catch (err) {
        console.error('Error:', err);
        loading.style.display = 'none';
        error.textContent = 'Error: ' + err.message;
        error.style.display = "block";
        status.textContent = "Error occurred";
        status.className = "status-text status-error";
        placeholder.style.display = "block";
        audio.style.display = "none";
    }
}

// Clear voiceover
function clearVoiceover() {
    document.getElementById('voiceover-text').value = "";
    document.getElementById('voiceover-status').textContent = "Ready to generate voiceover";
    document.getElementById('voiceover-status').className = "status-text";
    document.getElementById('voiceover-error').style.display = "none";
    document.getElementById('voiceover-placeholder').style.display = "block";
    document.getElementById('voiceover-audio').style.display = "none";
}

// Settings page functions
function showSettings() {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.remove('active');
    });
    
    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show the settings page
    document.getElementById('settings-page').classList.add('active');
    
    // Add active class to the settings nav item
    // Find the settings nav item and activate it
    const navItems = document.querySelectorAll('.nav-item');
    for (let item of navItems) {
        if (item.innerHTML.includes('Settings')) {
            item.classList.add('active');
            break;
        }
    }
    
    // Initialize webhook URL in settings page
    const savedWebhookUrl = localStorage.getItem('n8nWebhookUrl');
    if (savedWebhookUrl) {
        document.getElementById('n8n-webhook').value = savedWebhookUrl;
    }
    
    // Check server status
    checkServerStatus();
}

function switchTheme(theme) {
    const status = document.getElementById('settings-status');
    status.textContent = `Switching to ${theme} theme...`;
    status.className = "status-text status-loading";
    
    try {
        // In a real implementation, this would change the CSS variables
        // For now, we'll just update the status
        document.getElementById('current-theme').textContent = theme.charAt(0).toUpperCase() + theme.slice(1);
        status.textContent = `Theme switched to ${theme}`;
        status.className = "status-text status-success";
    } catch (error) {
        status.textContent = "Error switching theme";
        status.className = "status-text status-error";
    }
}

function updateWebhookUrl() {
    const status = document.getElementById('settings-status');
    const webhookUrl = document.getElementById('n8n-webhook').value;
    
    if (!webhookUrl) {
        status.textContent = "Please enter a valid webhook URL";
        status.className = "status-text status-error";
        return;
    }
    
    // Save the webhook URL to localStorage so it persists between sessions
    localStorage.setItem('n8nWebhookUrl', webhookUrl);
    
    status.textContent = "Webhook URL updated successfully";
    status.className = "status-text status-success";
}

function saveSettings() {
    const status = document.getElementById('settings-status');
    status.textContent = "Saving settings...";
    status.className = "status-text status-loading";
    
    // Simulate saving settings
    setTimeout(() => {
        status.textContent = "Settings saved successfully";
        status.className = "status-text status-success";
    }, 1000);
}

function resetSettings() {
    const status = document.getElementById('settings-status');
    status.textContent = "Resetting settings...";
    status.className = "status-text status-loading";
    
    // Reset webhook URL to default
    const defaultWebhookUrl = 'https://tharunreddyp12.app.n8n.cloud/webhook-test/manim-webhook';
    document.getElementById('n8n-webhook').value = defaultWebhookUrl;
    localStorage.setItem('n8nWebhookUrl', defaultWebhookUrl);
    
    // Reset theme to default
    document.getElementById('current-theme').textContent = 'Blue';
    
    status.textContent = "Settings reset to defaults";
    status.className = "status-text status-success";
}

function checkServerStatus() {
    const statusElement = document.getElementById('server-status');
    statusElement.textContent = "Checking...";
    
    fetch('/healthz')
        .then(response => {
            if (response.ok) {
                statusElement.textContent = "Online";
                statusElement.style.color = "var(--success)";
            } else {
                statusElement.textContent = "Offline";
                statusElement.style.color = "var(--danger)";
            }
        })
        .catch(error => {
            statusElement.textContent = "Offline";
            statusElement.style.color = "var(--danger)";
        });
}

// Save OpenRouter API Key
function saveOpenRouterApiKey() {
    const apiKey = document.getElementById('openrouter-api-key').value;
    if (apiKey) {
        localStorage.setItem('openrouterApiKey', apiKey);
        alert('OpenRouter API Key saved successfully!');
    } else {
        alert('Please enter a valid API key.');
    }
}
