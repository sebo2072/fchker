# 🎯 Fact-Checker - Agentic Editorial Tool

An AI-powered fact-checking tool designed for editorial workflows, featuring two operational modes: single-fact verification and bulk text analysis with human-in-the-loop confirmation.

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI with WebSocket support
- **AI Engine**: Google Vertex AI (Gemini 2.0 Flash Thinking)
- **Grounding**: Google Search Grounding for real-time verification
- **Agents**: Extraction Agent & Verification Agent
- **Orchestration**: Async workflow management with parallel processing

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand
- **Real-time**: WebSocket client for live updates
- **UI**: Multi-pane dashboard with responsive design

## 📋 Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 18 or higher
- **Google Cloud Platform**: Account with Vertex AI enabled
- **GCP Service Account**: JSON key file with Vertex AI permissions

## 🚀 Setup Instructions

### 1. Clone and Navigate
```bash
cd c:\Users\Sebo\Documents\ai_dev\factcheck
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Configure Environment
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env and set your GCP project ID
# GCP_PROJECT_ID=your-actual-project-id
```

#### Place GCP Service Account Key
```bash
# Create key directory
mkdir key

# Place your service account JSON key file in the key folder
# The file should be: key/service-account-key.json
```

### 3. Frontend Setup

#### Install Node Dependencies
```bash
cd frontend
npm install
```

## 🎮 Running the Application

### Start Backend Server
```bash
cd backend
python main.py
```
The backend will start on `http://localhost:8000`

### Start Frontend Development Server
```bash
cd frontend
npm run dev
```
The frontend will start on `http://localhost:3000`

## 📖 Usage Guide

### Single Fact Verification Mode
1. Select "Single Fact" mode in the header
2. Enter a factual claim in the text area
3. Click "Verify Claim"
4. Watch the thinking process in real-time
5. Review verification results with sources

**Example Claims:**
- "The Earth orbits the Sun"
- "Water boils at 100 degrees Celsius at sea level"
- "The Great Wall of China is visible from space"

### Bulk Analysis Mode
1. Select "Bulk Analysis" mode in the header
2. Paste text or upload a PDF document
3. Click "Extract Claims"
4. Review extracted claims (human-in-the-loop)
5. Select claims to verify
6. Click "Verify Selected Claims"
7. Watch parallel verification with real-time updates
8. Review all results in the results pane

## 🔧 API Endpoints

### REST API
- `POST /api/create-session` - Create new verification session
- `POST /api/verify-single` - Verify single claim
- `POST /api/analyze-text` - Extract claims from text
- `POST /api/confirm-claims` - Verify confirmed claims
- `POST /api/upload-pdf` - Upload and extract PDF text
- `GET /api/session/{session_id}` - Get session status
- `GET /api/sessions` - List all active sessions
- `DELETE /api/session/{session_id}` - Delete session

### WebSocket
- `ws://localhost:8000/ws/{session_id}` - Real-time updates

## 📊 Project Structure

```
factcheck/
├── backend/
│   ├── agents/
│   │   ├── extraction_agent.py    # Claim extraction
│   │   └── verification_agent.py  # Claim verification
│   ├── api/
│   │   └── routes.py              # REST endpoints
│   ├── core/
│   │   ├── orchestration_service.py
│   │   └── session_manager.py
│   ├── utils/
│   │   ├── vertex_client.py       # Vertex AI wrapper
│   │   └── pdf_processor.py       # PDF extraction
│   ├── websocket/
│   │   └── websocket_handler.py   # WebSocket manager
│   ├── config.py                  # Configuration
│   ├── main.py                    # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── InputPane.tsx
│   │   │   ├── ThinkingPane.tsx
│   │   │   ├── ResultsPane.tsx
│   │   │   ├── VerificationCard.tsx
│   │   │   └── ClaimConfirmation.tsx
│   │   ├── services/
│   │   │   ├── ApiService.ts
│   │   │   └── WebSocketClient.ts
│   │   ├── store/
│   │   │   └── appStore.ts        # Zustand store
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.ts
├── .env.example
├── .gitignore
└── README.md
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/
```

### Manual Testing Checklist

#### Single Fact Mode
- [ ] Submit a simple factual claim
- [ ] Verify WebSocket connection establishes
- [ ] Confirm thinking process streams in real-time
- [ ] Check verification result displays with sources
- [ ] Test error handling with invalid inputs

#### Bulk Analysis Mode
- [ ] Submit a paragraph with multiple claims
- [ ] Review extracted claims list
- [ ] Confirm/edit claims
- [ ] Verify parallel processing of multiple claims
- [ ] Check all results display correctly

#### PDF Processing
- [ ] Upload a PDF document
- [ ] Verify text extraction works
- [ ] Test claim extraction from PDF content

## 🔐 Security Notes

- **Never commit** `.env` files or service account keys to version control
- **Keep** your GCP credentials in the `/key` folder (gitignored)
- **Rotate** service account keys regularly
- **Limit** service account permissions to only Vertex AI access

## 🐛 Troubleshooting

### "GCP credentials not configured"
- Ensure `GCP_PROJECT_ID` is set in `.env`
- Verify service account key exists at `key/service-account-key.json`
- Check that the service account has Vertex AI permissions

### WebSocket connection fails
- Ensure backend is running on port 8000
- Check browser console for connection errors
- Verify CORS settings in backend configuration

### PDF extraction fails
- Ensure PDF is text-based (not scanned images)
- Check file size (large PDFs may timeout)
- Try with a different PDF

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | Required |
| `GCP_LOCATION` | GCP region | `us-central1` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | `./key/service-account-key.json` |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.0-flash-thinking-exp-01-21` |
| `API_PORT` | Backend server port | `8000` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,http://localhost:5173` |

## 🎨 Features

- ✅ **Two Operational Modes**: Single-fact and bulk analysis
- ✅ **Real-time Thinking Process**: See AI reasoning as it happens
- ✅ **Google Search Grounding**: Real-time web verification
- ✅ **Human-in-the-Loop**: Review and confirm extracted claims
- ✅ **Parallel Verification**: Process multiple claims simultaneously
- ✅ **PDF Support**: Upload and analyze PDF documents
- ✅ **Source Citations**: Automatic citation extraction
- ✅ **Confidence Scoring**: AI confidence levels for each verification
- ✅ **Multi-pane Dashboard**: Intuitive, responsive UI
- ✅ **WebSocket Streaming**: Live updates without polling

## 📄 License

This project is for educational and editorial use.

## 🤝 Contributing

This is a demonstration project. For production use, consider:
- Adding user authentication
- Implementing rate limiting
- Adding result caching
- Enhancing error handling
- Adding comprehensive test coverage
- Implementing result export functionality
