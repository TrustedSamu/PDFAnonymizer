import React, { useState } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [serverStatus, setServerStatus] = useState<string>('checking...');
  const [anonymizedText, setAnonymizedText] = useState<string | null>(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  // Add health check function
  const checkServerHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`);
      if (response.ok) {
        setServerStatus('connected');
        console.log('Backend server is running');
      } else {
        setServerStatus('error');
        console.error('Backend server returned error');
      }
    } catch (error) {
      setServerStatus('disconnected');
      console.error('Cannot connect to backend server');
    }
  };

  // Check server health on component mount
  React.useEffect(() => {
    checkServerHealth();
    const interval = setInterval(checkServerHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    console.log('File selected:', selectedFile?.name);
    
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
      setStatus(`Datei ausgewählt: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(2)} KB)`);
    } else {
      setFile(null);
      setError('Bitte wählen Sie eine gültige PDF-Datei aus');
      setStatus('');
    }
  };

  const handleCreatePdf = async () => {
    if (!anonymizedText) return;
    
    try {
      setDownloadingPdf(true);
      setStatus('Erstelle PDF...');
      
      const response = await fetch(`${API_URL}/api/create-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          text: anonymizedText,
          filename: file?.name || 'lebenslauf'
        }),
      });

      if (!response.ok) {
        throw new Error('Fehler beim Erstellen der PDF');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = response.headers.get('content-disposition')?.split('filename=')[1] || 'anonymisierter-lebenslauf.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setStatus('PDF erfolgreich erstellt und heruntergeladen!');
    } catch (err) {
      setError('Fehler beim Erstellen der PDF: ' + (err instanceof Error ? err.message : 'Unbekannter Fehler'));
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError('Bitte wählen Sie eine PDF-Datei aus');
      return;
    }

    if (serverStatus !== 'connected') {
      setError('Backend-Server ist nicht verbunden. Bitte versuchen Sie es erneut.');
      return;
    }

    setLoading(true);
    setError(null);
    setStatus('Bereite Upload vor...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      console.log('Starting file upload to server...');
      setStatus('Lade Lebenslauf hoch und analysiere...');
      
      const response = await fetch(`${API_URL}/api/analyze-cv`, {
        method: 'POST',
        body: formData,
      });

      console.log('Server response status:', response.status);
      
      if (!response.ok) {
        let errorMessage = 'Fehler bei der Analyse des Lebenslaufs';
        try {
          const errorData = await response.json();
          console.error('Server error:', errorData);
          errorMessage = errorData.error || errorMessage;
        } catch (e) {
          console.error('Error parsing error response:', e);
        }
        throw new Error(errorMessage);
      }

      const jsonResponse = await response.json();
      console.log('Received analyzed CV data');
      setAnonymizedText(jsonResponse.analyzed_data);
      setStatus('Lebenslauf erfolgreich analysiert!');
      setFile(null);
      
    } catch (err) {
      console.error('Error during processing:', err);
      setError(err instanceof Error ? err.message : 'Ein Fehler ist aufgetreten');
      setStatus('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="brand-container">
          <h1 className="brand-name">LebenslaufLicht</h1>
          <p className="brand-slogan">Ihre Qualifikationen im Rampenlicht, Ihre Privatsphäre im Schatten</p>
        </div>
        <div className="server-status" style={{
          color: serverStatus === 'connected' ? '#4CAF50' : 
                 serverStatus === 'checking...' ? '#FFA500' : '#FF0000'
        }}>
          {serverStatus === 'connected' ? '✓ System Bereit' : 
           serverStatus === 'checking...' ? '⟳ Verbinde...' : '✕ Nicht Verbunden'}
        </div>
        <div className="upload-container">
          <form onSubmit={handleSubmit}>
            <div className="file-input-container">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                id="file-input"
                className="file-input"
              />
              <label htmlFor="file-input" className="file-input-label">
                {file ? file.name : '📄 Lebenslauf (PDF) auswählen'}
              </label>
            </div>
            {file && (
              <button type="submit" className="submit-button" disabled={loading}>
                {loading ? '⚡ Verarbeite...' : '✨ Lebenslauf Analysieren'}
              </button>
            )}
          </form>
          {status && <div className="status-message">{status}</div>}
          {error && <div className="error-message">{error}</div>}
          {loading && <div className="loading">Transformiere Ihren Lebenslauf</div>}
          {anonymizedText && (
            <div className="anonymized-text">
              <div className="anonymized-header">
                <h3>✨ Ihre Anonymisierten Daten</h3>
                <button 
                  onClick={handleCreatePdf} 
                  className="download-pdf-button"
                  disabled={downloadingPdf}
                >
                  {downloadingPdf ? '📄 Erstelle PDF...' : '📄 Als PDF Herunterladen'}
                </button>
              </div>
              <pre>
                {anonymizedText}
              </pre>
            </div>
          )}
        </div>
      </header>
    </div>
  );
}

export default App;
