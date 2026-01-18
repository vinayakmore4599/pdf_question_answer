# PDF Q&A Web Application

A modern web application for extracting answers from PDF documents using AI and RAG (Retrieval-Augmented Generation).

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm or yarn

### Backend Setup

1. **Install Python dependencies:**
```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Also make sure main dependencies are installed
pip install -r requirements.txt
```

2. **Configure environment:**
Make sure your `.env` file has the Perplexity API key:
```
PERPLEXITY_API_KEY=your_api_key_here
```

3. **Start the backend server:**
```bash
python backend/api.py
```
The API will run on `http://localhost:8000`

### Frontend Setup

1. **Install Node.js dependencies:**
```bash
cd frontend
npm install
```

2. **Start the development server:**
```bash
npm run dev
```
The React app will run on `http://localhost:3000`

## 📖 Usage

1. **Upload PDF:**
   - Click "Choose PDF file" and select your PDF document
   - Click "Upload & Process" to process the PDF with RAG
   - Wait for the success message

2. **Ask Questions:**
   - **Single Question:** Type a question and click "Ask Now"
   - **Batch Questions:** Type questions, click "Add to Batch", then "Process All Questions"

3. **View Answers:**
   - Answers appear below with the question, answer text, model used, and token usage
   - Clear answers anytime with the "Clear Answers" button

## 🏗️ Architecture

### Backend (FastAPI)
- **`/upload`** - Upload and process PDF files
- **`/ask/{pdf_id}`** - Ask a single question
- **`/ask-multiple/{pdf_id}`** - Ask multiple questions at once
- **`/pdfs`** - List all processed PDFs
- **`/pdf/{pdf_id}`** - Delete a PDF from cache

### Frontend (React + Vite)
- Modern React with hooks
- Axios for API calls
- Responsive design with gradient UI
- Real-time feedback and error handling

### Features
✅ PDF upload and processing  
✅ RAG-based context retrieval  
✅ Single and batch question answering  
✅ Real-time answer display  
✅ Beautiful, responsive UI  
✅ Error handling and validation  
✅ Token usage tracking  

## 🔧 Development

### Backend API Documentation
Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Build for Production

**Frontend:**
```bash
cd frontend
npm run build
```

**Backend:**
```bash
# Use production ASGI server
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📝 Notes

- PDFs are cached in memory (for production, use Redis or a database)
- The backend uses the same RAG system as the CLI version
- CORS is configured for local development
- All answers are extracted ONLY from the PDF content (no web search)

## 🛠️ Technologies

- **Backend:** FastAPI, Uvicorn, Python 3.12
- **Frontend:** React 18, Vite, Axios
- **AI:** Perplexity API, Sentence Transformers, FAISS
- **PDF Processing:** pdfplumber

## 📄 License

Same as main project
