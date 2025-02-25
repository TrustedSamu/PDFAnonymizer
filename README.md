# LebenslaufLicht - CV Anonymizer

A web application that automatically anonymizes CVs/resumes using AI. Built with FastAPI and React.

## Features

- Upload PDF CVs/resumes
- AI-powered anonymization of personal information
- Maintains formatting and structure
- Download anonymized PDFs
- Modern, responsive UI
- Real-time server status monitoring

## Tech Stack

### Backend
- Python 3.8+
- FastAPI
- OpenAI/OpenRouter API
- PyPDF2 for PDF processing
- ReportLab for PDF generation

### Frontend
- React
- TypeScript
- Modern CSS with animations
- Responsive design

## Setup

### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd PDFAnonymizer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Create a `.env` file in the backend directory:
```env
OPENAI_API_KEY=your-openrouter-api-key
OPENAI_API_BASE=https://openrouter.ai/api/v1
ORGANIZATION=null
FRONTEND_URL=http://localhost:3000
```

5. Start the backend server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create a `.env` file in the frontend directory:
```env
REACT_APP_API_URL=http://localhost:8001
```

3. Start the development server:
```bash
npm start
```

## Usage

1. Open your browser and navigate to `http://localhost:3000`
2. Upload a PDF CV/resume
3. Wait for the AI to process and anonymize the document
4. Review the anonymized text
5. Download the anonymized PDF

## API Endpoints

- `POST /api/analyze-cv`: Upload and analyze a CV
- `POST /api/create-pdf`: Create a PDF from anonymized text
- `GET /api/health`: Health check endpoint

## Environment Variables

### Backend
- `OPENAI_API_KEY`: Your OpenRouter API key
- `OPENAI_API_BASE`: OpenRouter API base URL
- `FRONTEND_URL`: URL of the frontend application

### Frontend
- `REACT_APP_API_URL`: URL of the backend API

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License. 