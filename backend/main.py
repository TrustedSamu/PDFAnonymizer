from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import PyPDF2
import io
import openai
import os
from dotenv import load_dotenv
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
import logging
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import ParagraphStyle
from io import BytesIO
import asyncio

# Configure logging with more details
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

app = FastAPI()

# Initialize OpenRouter client
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.error("OpenAI API key not found in environment variables!")
openai.api_base = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
logger.info(f"OpenAI API Base URL: {openai.api_base}")

# Define OpenRouter headers
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/OpenRouterTeam/openrouter-python",
    "X-Title": "PDF Anonymizer",
    "Content-Type": "application/json"
}

# Configure CORS to be more permissive for development
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
ALLOWED_ORIGINS = [FRONTEND_URL]

# Add additional origins if specified
additional_origins = os.getenv("ADDITIONAL_ORIGINS")
if additional_origins:
    ALLOWED_ORIGINS.extend(additional_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"CORS configured with allowed origins: {ALLOWED_ORIGINS}")

# Add response headers middleware to handle CORS preflight
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        logger.info("Starting PDF text extraction")
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for i, page in enumerate(pdf_reader.pages):
            logger.info(f"Processing page {i+1} of {len(pdf_reader.pages)}")
            text += page.extract_text()
        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error extracting text from PDF: {str(e)}")

def analyze_cv(text: str) -> dict:
    try:
        logger.info("Starting CV analysis with OpenAI")
        prompt = """Analysiere diesen Lebenslauf und extrahiere die folgenden Informationen. Befolge dabei STRIKT diese Anonymisierungsregeln:

1. Persönliche Informationen:
   - Der Name MUSS IMMER durch [NAME] ersetzt werden
   - Adresse: 
     * Straße und Hausnummer durch [STRASSE] ersetzen
     * PLZ und Stadt bleiben sichtbar (Beispiel: "[STRASSE], 12345 München")
   - E-Mail-Adresse durch [EMAIL] ersetzen
   - Telefonnummer durch [TELEFON] ersetzen
   - Geburtsdatum durch [GEBURTSDATUM] ersetzen
   - WICHTIG: Der Name darf NIRGENDS im Text erscheinen, auch nicht in Berufserfahrung oder Ausbildung

2. Ausbildung:
   - Bildungseinrichtungen (Name der Schule/Universität beibehalten)
   - Abschlüsse
   - Zeiträume
   - Noten (falls vorhanden)

3. Berufserfahrung:
   - Unternehmen
   - Position/Rolle
   - Zeitraum
   - Hauptaufgaben und Verantwortlichkeiten

4. Fähigkeiten:
   - Technische Kompetenzen
   - Soft Skills
   - Software-Kenntnisse

5. Sprachen:
   - Sprache und Niveau

6. Zertifizierungen:
   - Name der Zertifizierung
   - Ausstellungsdatum

WICHTIGE ANWEISUNGEN:
- Der Name der Person MUSS ÜBERALL durch [NAME] ersetzt werden
- Stelle sicher, dass der Name auch in Formulierungen wie "Herr/Frau [Nachname]" oder in Projektbeschreibungen durch [NAME] ersetzt wird
- Bei der Adresse nur Straße und Hausnummer durch [STRASSE] ersetzen, PLZ und Stadt bleiben sichtbar
- Formatiere die Ausgabe übersichtlich mit Überschriften und Aufzählungszeichen

Lebenslauf Text:
{text}"""

        logger.info("Sending request to OpenAI")
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Experte für die Analyse und Anonymisierung von Lebensläufen. Deine wichtigste Aufgabe ist es, ALLE personenbezogenen Daten korrekt zu anonymisieren, insbesondere den Namen der Person. Der Name darf NIRGENDS im Text erscheinen. Antworte auf Deutsch."
                },
                {
                    "role": "user",
                    "content": prompt.format(text=text)
                }
            ],
            temperature=0.7,
            headers={
                "HTTP-Referer": "https://github.com/OpenRouterTeam/openrouter-python",
                "X-Title": "PDF Anonymizer"
            }
        )
        
        if not completion.choices or not completion.choices[0].message:
            raise ValueError("Invalid response from OpenAI")
            
        analyzed_data = completion.choices[0].message.content
        logger.info("Successfully analyzed CV data")
        return {"analyzed_data": analyzed_data}
    except Exception as e:
        logger.error(f"Error in AI analysis: {str(e)}", exc_info=True)
        raise

def create_pdf_from_text(text: str, original_filename: str = None) -> bytes:
    """Create a PDF file from the given text."""
    try:
        logger.info("Starting PDF creation")
        # Create a new PDF with ReportLab
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create the story (content) for the PDF
        story = []
        
        # Add a title
        title_style = ParagraphStyle(
            'CustomTitle',
            fontSize=16,
            spaceAfter=30,
            alignment=1,  # Center alignment
            fontName='Helvetica-Bold'
        )
        
        # Create title from original filename or use default
        if original_filename:
            # Remove .pdf extension if present
            base_name = original_filename.lower().replace('.pdf', '')
            title = f"{base_name} - Anonymisiert"
        else:
            title = "Lebenslauf - Anonymisiert"
        
        story.append(Paragraph(title, title_style))
        
        # Add the text content with proper styling
        text_style = ParagraphStyle(
            'CustomText',
            fontSize=11,
            leading=14,  # Line spacing
            spaceAfter=12
        )
        
        # Split text into paragraphs and add them
        paragraphs = text.split('\n')
        for para in paragraphs:
            if para.strip():  # Only add non-empty paragraphs
                story.append(Paragraph(para, text_style))
                
        # Build the PDF
        logger.info("Building PDF document")
        doc.build(story)
        
        # Get the value from the buffer
        pdf_content = buffer.getvalue()
        buffer.close()
        
        logger.info("PDF creation successful")
        return pdf_content
        
    except Exception as e:
        logger.error(f"Error in create_pdf_from_text: {str(e)}", exc_info=True)
        raise Exception(f"Failed to create PDF: {str(e)}")

@app.options("/api/anonymize")
async def options_anonymize():
    return {"message": "OK"}

@app.post("/api/analyze-cv")
async def analyze_cv_endpoint(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file: {file.filename}")
        
        if not file.filename.lower().endswith('.pdf'):
            logger.warning("Invalid file type received")
            return JSONResponse(
                status_code=400,
                content={"error": "Only PDF files are accepted"}
            )
        
        # Read the file content
        file_content = await file.read()
        if len(file_content) == 0:
            logger.error("Received empty file")
            return JSONResponse(
                status_code=400,
                content={"error": "The uploaded file is empty"}
            )
        
        # Extract text from PDF
        text = extract_text_from_pdf(file_content)
        if not text.strip():
            logger.warning("No text could be extracted from PDF")
            return JSONResponse(
                status_code=400,
                content={"error": "Could not extract text from PDF"}
            )
        
        # Analyze and anonymize CV data
        result = analyze_cv(text)
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error processing CV: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred: {str(e)}"}
        )

@app.post("/api/create-pdf")
async def create_pdf(request: Request):
    temp_output_file = None
    try:
        # Get the request body as JSON
        body = await request.json()
        text = body.get('text')
        original_filename = body.get('filename', 'lebenslauf')
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
            
        # Create new PDF with provided text
        logger.info("Creating new PDF from text")
        pdf_content = create_pdf_from_text(text, original_filename)
        
        # Save the PDF temporarily
        logger.info("Saving PDF")
        temp_output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_output_file.write(pdf_content)
        temp_output_file.close()
        
        logger.info(f"Returning PDF (size: {len(pdf_content)} bytes)")
        
        # Create a background task to remove the file after it's sent
        async def remove_file():
            try:
                await asyncio.sleep(1)  # Give time for the file to be sent
                if os.path.exists(temp_output_file.name):
                    os.unlink(temp_output_file.name)
                    logger.info("Temporary file cleaned up successfully")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file: {str(cleanup_error)}")
        
        # Create download filename from original filename
        download_filename = f"{original_filename.lower().replace('.pdf', '')}_anonymisiert.pdf"
        
        response = FileResponse(
            temp_output_file.name,
            media_type='application/pdf',
            filename=download_filename
        )
        response.background = remove_file()
        return response
        
    except Exception as e:
        # Clean up the file if there was an error
        if temp_output_file and os.path.exists(temp_output_file.name):
            try:
                os.unlink(temp_output_file.name)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file: {str(cleanup_error)}")
                
        logger.error(f"Error creating PDF: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Error creating PDF: {str(e)}"}
        )

@app.get("/api/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 