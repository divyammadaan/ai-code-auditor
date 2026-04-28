# 🎨 AI Code Auditor Frontend

Simple web interface for the AI Code Auditor v4.

## 🚀 Quick Start

### 1. Start the Backend API
```bash
# From project root
python start_api.py --load-model --model-path models/lora_adapter_v4
```

### 2. Open Frontend
- Open `frontend/index.html` in your browser
- Or serve with a local server:
```bash
# Option 1: Python
cd frontend
python -m http.server 3000

# Option 2: Node.js (if you have it)
cd frontend  
npx serve .
```

### 3. Test the Interface
1. Paste vulnerable C/C++ code in the input area
2. Toggle RAG search if desired
3. Click "Analyze Code"
4. View results with CWE classification and secure rewrite

## 🔧 Configuration

Edit the `API_BASE` variable in `index.html` if your FastAPI server runs on a different port:

```javascript
const API_BASE = 'http://localhost:8000';  // Change this if needed
```

## 📱 Features

- **Real-time Analysis**: Instant vulnerability detection
- **CWE Classification**: Automatic security weakness identification  
- **Secure Code Generation**: AI-powered secure rewrites
- **RAG Integration**: Toggle vector search for enhanced context
- **Responsive Design**: Works on desktop and mobile
- **Status Monitoring**: Live API health checks

## 🎯 Example Code to Test

```c
// Buffer Overflow Example
void copy_data(char* dest, char* src) {
    char buffer[256];
    strcpy(buffer, src);  // Vulnerable!
    strcpy(dest, buffer);
}

// SQL Injection Example  
void query_user(char* username) {
    char query[512];
    sprintf(query, "SELECT * FROM users WHERE name='%s'", username);
    execute_query(query);  // Vulnerable!
}

// Integer Overflow Example
int allocate_memory(int count, int size) {
    int total = count * size;  // Vulnerable!
    return malloc(total);
}
```

## 🔍 Troubleshooting

**"API Offline" Status:**
- Make sure FastAPI server is running: `python start_api.py`
- Check the console for CORS errors
- Verify API_BASE URL is correct

**"Model Not Loaded" Warning:**
- Start API with: `python start_api.py --load-model`
- Ensure v4 LoRA adapter exists in `models/lora_adapter_v4/`

**No Results Displayed:**
- Check browser console for JavaScript errors
- Verify API response format matches expected schema
- Test API directly: `curl http://localhost:8000/health`

## 🎨 Customization

The interface is built with vanilla HTML/CSS/JS for easy customization:

- **Styling**: Edit the `<style>` section in `index.html`
- **API Integration**: Modify the JavaScript functions
- **Layout**: Adjust the CSS Grid in `.main-content`
- **Branding**: Update colors, fonts, and logos

## 🚀 Production Deployment

For production use:

1. **Backend**: Deploy FastAPI with proper WSGI server (gunicorn)
2. **Frontend**: Serve static files with nginx/Apache
3. **Security**: Enable HTTPS, update CORS origins
4. **Monitoring**: Add logging and health checks

---

**Ready to analyze code? Start the API and open the frontend! 🛡️**