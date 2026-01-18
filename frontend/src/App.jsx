import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import jsPDF from 'jspdf';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [file, setFile] = useState(null);
  const [pdfId, setPdfId] = useState(null);
  const [pdfInfo, setPdfInfo] = useState(null);
  const [question, setQuestion] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const chatEndRef = useRef(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a valid PDF file');
      setFile(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a PDF file first');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setPdfId(response.data.pdf_id);
      setPdfInfo(response.data);
      setChatMessages([]);
      setQuestion('');
      alert(`PDF uploaded successfully! ${response.data.message}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading PDF');
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!pdfId) {
      setError('Please upload a PDF first');
      return;
    }

    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    const userQuestion = question.trim();
    
    // Add user message to chat
    setChatMessages(prev => [...prev, {
      type: 'user',
      content: userQuestion,
      timestamp: new Date().toISOString()
    }]);
    
    setQuestion('');
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_URL}/ask/${pdfId}`, {
        question: userQuestion,
      });

      // Add AI response to chat
      const aiAnswer = response.data.answers[0];
      setChatMessages(prev => [...prev, {
        type: 'assistant',
        content: aiAnswer.answer,
        model: aiAnswer.model,
        usage: aiAnswer.usage,
        timestamp: new Date().toISOString()
      }]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error getting answer');
      console.error('Question error:', err);
      // Add error message to chat
      setChatMessages(prev => [...prev, {
        type: 'error',
        content: err.response?.data?.detail || 'Error getting answer',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAskQuestion();
    }
  };

  const clearChat = () => {
    setChatMessages([]);
  };

  const downloadChatAsPDF = () => {
    if (chatMessages.length === 0) {
      alert('No chat history to download');
      return;
    }

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 15;
    const maxWidth = pageWidth - 2 * margin;
    let yPosition = 20;

    // Add title
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.text('PDF Q&A Chat History', margin, yPosition);
    yPosition += 10;

    // Add PDF info
    if (pdfInfo) {
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(`Document: ${pdfInfo.filename}`, margin, yPosition);
      yPosition += 6;
      doc.text(`Date: ${new Date().toLocaleDateString()}`, margin, yPosition);
      yPosition += 10;
    }

    // Add separator line
    doc.setLineWidth(0.5);
    doc.line(margin, yPosition, pageWidth - margin, yPosition);
    yPosition += 10;

    // Filter out error messages and process Q&A pairs
    const validMessages = chatMessages.filter(msg => msg.type !== 'error');
    
    for (let i = 0; i < validMessages.length; i++) {
      const msg = validMessages[i];
      
      if (msg.type === 'user') {
        // Add question
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(102, 126, 234); // Purple color
        
        const questionNumber = Math.floor(i / 2) + 1;
        const questionHeader = `Q${questionNumber}:`;
        doc.text(questionHeader, margin, yPosition);
        yPosition += 6;
        
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(0, 0, 0);
        
        // Wrap and add question text
        const questionLines = doc.splitTextToSize(msg.content, maxWidth);
        questionLines.forEach(line => {
          if (yPosition > pageHeight - 30) {
            doc.addPage();
            yPosition = 20;
          }
          doc.text(line, margin, yPosition);
          yPosition += 5;
        });
        yPosition += 5;
      } else if (msg.type === 'assistant') {
        // Add answer
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(118, 75, 162); // Purple color
        doc.text('A:', margin, yPosition);
        yPosition += 6;
        
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(0, 0, 0);
        
        // Remove markdown formatting for PDF
        let cleanAnswer = msg.content
          .replace(/#{1,6}\s/g, '') // Remove headers
          .replace(/\*\*(.+?)\*\*/g, '$1') // Remove bold
          .replace(/\*(.+?)\*/g, '$1') // Remove italic
          .replace(/`(.+?)`/g, '$1'); // Remove code blocks
        
        // Wrap and add answer text
        const answerLines = doc.splitTextToSize(cleanAnswer, maxWidth);
        answerLines.forEach(line => {
          if (yPosition > pageHeight - 30) {
            doc.addPage();
            yPosition = 20;
          }
          doc.text(line, margin, yPosition);
          yPosition += 5;
        });
        
        // Add model info
        if (msg.model) {
          yPosition += 3;
          doc.setFontSize(8);
          doc.setTextColor(128, 128, 128);
          doc.text(`Model: ${msg.model}`, margin, yPosition);
          yPosition += 8;
        }
        
        // Add separator between Q&A pairs
        if (i < validMessages.length - 1) {
          doc.setDrawColor(200, 200, 200);
          doc.setLineWidth(0.3);
          doc.line(margin, yPosition, pageWidth - margin, yPosition);
          yPosition += 8;
        }
      }
      
      // Check if we need a new page
      if (yPosition > pageHeight - 40) {
        doc.addPage();
        yPosition = 20;
      }
    }

    // Add footer on last page
    const totalPages = doc.internal.pages.length - 1;
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(128, 128, 128);
      doc.text(
        `Page ${i} of ${totalPages}`,
        pageWidth / 2,
        pageHeight - 10,
        { align: 'center' }
      );
    }

    // Generate filename with timestamp
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const filename = `chat-history-${timestamp}.pdf`;
    
    // Save the PDF
    doc.save(filename);
  };

  return (
    <div className="App">
      <header className="header">
        <h1>📄 PDF Q&A Assistant</h1>
        <p>Upload a PDF and ask questions - AI will extract answers from the document</p>
      </header>

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      <div className="container">
        {/* Main Card - Upload and Chat Combined */}
        <div className="card main-section">
          {/* Upload Area */}
          <div className="upload-area">
            <h2>📄 PDF Q&A Assistant</h2>
            <div className="upload-controls">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                id="file-upload"
                className="file-input"
              />
              <label htmlFor="file-upload" className="file-label">
                {file ? file.name : '📁 Choose PDF file...'}
              </label>
              <button
                onClick={handleUpload}
                disabled={!file || loading}
                className="btn btn-primary"
              >
                {loading ? '⏳ Processing...' : '🚀 Upload & Process'}
              </button>
            </div>

            {pdfInfo && (
              <div className="pdf-info-compact">
                <span className="pdf-badge">✅ {pdfInfo.filename}</span>
                {chatMessages.length > 0 && (
                  <div className="chat-actions-compact">
                    <button onClick={downloadChatAsPDF} className="btn-icon" title="Download Chat">
                      📥
                    </button>
                    <button onClick={clearChat} className="btn-icon" title="Clear Chat">
                      🗑️
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Chat Section */}
          {pdfId && (
            <>
              <div className="chat-container">
                <div className="chat-messages">
                  {chatMessages.length === 0 ? (
                    <div className="empty-chat">
                      <p>👋 Start by asking a question about your PDF document</p>
                      <p className="hint">Try: "What is this document about?" or "Summarize the key points"</p>
                    </div>
                  ) : (
                    <>
                      {chatMessages.map((msg, index) => (
                        <div key={index} className={`chat-message ${msg.type}`}>
                          <div className="message-header">
                            <span className="message-icon">
                              {msg.type === 'user' ? '👤' : msg.type === 'error' ? '⚠️' : '🤖'}
                            </span>
                            <span className="message-role">
                              {msg.type === 'user' ? 'You' : msg.type === 'error' ? 'Error' : 'AI Assistant'}
                            </span>
                          </div>
                          <div className="message-content">
                            {msg.type === 'assistant' ? (
                              <ReactMarkdown>{msg.content}</ReactMarkdown>
                            ) : (
                              <p>{msg.content}</p>
                            )}
                          </div>
                        </div>
                      ))}
                      <div ref={chatEndRef} />
                    </>
                  )}
                </div>
                
                <div className="chat-input-area">
                  {loading && (
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  )}
                  <div className="chat-input-container">
                    <textarea
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Ask a question about your PDF..."
                      className="chat-input"
                      disabled={loading}
                      rows="1"
                    />
                    <button
                      onClick={handleAskQuestion}
                      disabled={!question.trim() || loading}
                      className="btn-send"
                      title="Send message (Enter)"
                    >
                      {loading ? '⏳' : '📤'}
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <footer className="app-footer">
        <p>🔮 Powered by RAG • MCP • Perplexity AI</p>
      </footer>
    </div>
  );
}

export default App;
