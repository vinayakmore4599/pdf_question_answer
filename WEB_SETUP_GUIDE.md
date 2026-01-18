# 🌐 PDF Q&A Web Application Setup Guide

## ✅ Complete! Web application created successfully!

Your PDF Q&A system now has a beautiful React frontend and FastAPI backend.

---

## 📁 Project Structure

```
mcp_pdf/
├── backend/
│   ├── api.py              # FastAPI server
│   └── requirements.txt    # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   ├── App.css        # Styling
│   │   ├── main.jsx       # React entry point
│   │   └── index.css      # Global styles
│   ├── index.html         # HTML template
│   ├── package.json       # Node dependencies
│   └── vite.config.js     # Vite configuration
├── start_backend.sh       # Backend startup script
└── start_frontend.sh      # Frontend startup script
```

---

## 🚀 Quick Start

### Step 1: Install Node.js (if not installed)

```bash
# On macOS with Homebrew:
brew install node

# Or download from: https://nodejs.org/
```

### Step 2: Start the Backend

Open a terminal and run:

```bash
chmod +x start_backend.sh
./start_backend.sh
```

The backend will run on: **http://localhost:8000**  
API docs available at: **http://localhost:8000/docs**

### Step 3: Start the Frontend

Open a **new terminal** and run:

```bash
chmod +x start_frontend.sh
./start_frontend.sh
```

The frontend will run on: **http://localhost:3000**

---

## 🎯 How to Use

### 1. **Upload a PDF**
   - Open http://localhost:3000 in your browser
   - Click "Choose PDF file" and select your PDF
   - Click "Upload & Process"
   - Wait for processing confirmation

### 2. **Ask Questions**

**Single Question Mode:**
- Type your question in the input box
- Press Enter or click "Ask Now"
- See the answer immediately below

**Batch Mode:**
- Type a question and click "Add to Batch"
- Repeat for multiple questions
- Click "Process All Questions" to get all answers at once

### 3. **View Answers**
- Answers appear with:
  - The original question
  - AI-generated answer (from PDF only)
  - Model used
  - Token usage stats

---

## 🌟 Features

✅ **Beautiful UI** - Modern gradient design, responsive  
✅ **Drag & Drop** - Easy PDF upload  
✅ **Real-time Answers** - Instant question processing  
✅ **Batch Processing** - Ask multiple questions at once  
✅ **RAG Powered** - Efficient context retrieval  
✅ **PDF-Only Answers** - No web search, pure document analysis  
✅ **Error Handling** - Clear error messages  
✅ **Token Tracking** - See API usage per question  

---

## 🔧 API Endpoints

### Backend API (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/upload` | POST | Upload and process PDF |
| `/ask/{pdf_id}` | POST | Ask single question |
| `/ask-multiple/{pdf_id}` | POST | Ask multiple questions |
| `/pdfs` | GET | List all processed PDFs |
| `/pdf/{pdf_id}` | DELETE | Delete PDF from cache |

### Example API Usage

```bash
# Upload PDF
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"

# Ask question
curl -X POST http://localhost:8000/ask/{pdf_id} \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

---

## 📊 Architecture

```
┌─────────────┐      HTTP       ┌──────────────┐      Python      ┌─────────────┐
│   Browser   │  ──────────────> │  FastAPI     │  ──────────────> │ RAG System  │
│  (React)    │ <────────────── │  Backend     │ <────────────── │ + Perplexity│
└─────────────┘   JSON/REST     └──────────────┘      API         └─────────────┘
   Port 3000                        Port 8000                       Embeddings
                                                                    + Vector DB
```

### Data Flow:
1. User uploads PDF → Backend processes with RAG
2. User asks question → RAG retrieves relevant chunks
3. Backend sends chunks to Perplexity AI
4. AI returns answer → Display in React UI

---

## 🛠️ Development

### Backend Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
uvicorn backend.api:app --reload --port 8000

# View API docs
open http://localhost:8000/docs
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Activate virtual environment first
source venv/bin/activate
python backend/api.py
```

### Frontend won't start
```bash
# Install Node.js
brew install node

# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### CORS errors
- Make sure backend is running on port 8000
- Make sure frontend is running on port 3000
- Check browser console for errors

---

## 📝 Environment Variables

Make sure your `.env` file contains:

```env
PERPLEXITY_API_KEY=your_api_key_here
```

---

## 🚀 Production Deployment

### Backend
```bash
# Use production ASGI server
pip install gunicorn
gunicorn backend.api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Frontend
```bash
cd frontend
npm run build
# Serve the 'dist' folder with nginx or similar
```

---

## 📚 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Perplexity AI** - LLM for answering
- **FAISS** - Vector database for RAG
- **Sentence Transformers** - Text embeddings

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Axios** - HTTP client
- **CSS3** - Modern styling with gradients

---

## 🎨 UI Preview

The application features:
- **Purple gradient background** for modern look
- **Card-based layout** for clear sections
- **Responsive design** works on mobile/desktop
- **Smooth animations** for better UX
- **Real-time feedback** for all actions
- **Error handling** with clear messages

---

## 📄 License

Same as main project

---

## 🤝 Support

For issues or questions:
1. Check the logs: `output/logs/backend.log`
2. View browser console for frontend errors
3. Check API docs: http://localhost:8000/docs

---

**Enjoy your PDF Q&A web application! 🎉**
