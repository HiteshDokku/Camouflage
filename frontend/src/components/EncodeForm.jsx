import React, { useState } from 'react';
import axios from 'axios';

const apiBase = import.meta.env.PROD ? '/api' : 'http://localhost:5000/api';

function EncodeForm() {
  const [mediaType, setMediaType] = useState('image');
  const [coverFile, setCoverFile] = useState(null);
  const [secretText, setSecretText] = useState('');
  const [secretFile, setSecretFile] = useState(null);
  const [useSecretFile, setUseSecretFile] = useState(false);
  const [secretKey, setSecretKey] = useState('');
  const [encrypt, setEncrypt] = useState(false);
  const [outputName, setOutputName] = useState('output');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError(null);

    const formData = new FormData();
    formData.append('media_type', mediaType);
    if (coverFile) formData.append('cover', coverFile);
    
    if (useSecretFile && secretFile) {
      formData.append('secret_file', secretFile);
    } else {
      formData.append('secret_text', secretText);
    }
    
    formData.append('secret_key', secretKey);
    formData.append('encrypt', document.getElementById('encryptSecret').checked);
    formData.append('output_name', outputName);

    try {
      // Expecting a file download directly
      const res = await axios.post(`${apiBase}/encode`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        responseType: 'blob' // Important to handle file downlaod
      });
      
      // Create a URL for the blob
      const url = window.URL.createObjectURL(new Blob([res.data]));
      
      // Extract filename from content-disposition header if present
      let filename = outputName + (mediaType === 'image' ? '.png' : mediaType === 'audio' ? '.wav' : '.avi');
      const disposition = res.headers['content-disposition'];
      if (disposition && disposition.indexOf('attachment') !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) { 
          filename = matches[1].replace(/['"]/g, '');
        }
      }
      
      setResult({ url, filename });
      
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data && err.response.data instanceof Blob) {
        // Read blob as text to get error message
        const text = await err.response.data.text();
        try {
          const json = JSON.parse(text);
          setError(json.error || 'An error occurred during encoding');
        } catch(e) {
          setError('An internal server error occurred');
        }
      } else {
        setError(err.message || 'An error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h5 className="mb-3">Encode Message</h5>
      
      {error && <div className="alert alert-danger">{error}</div>}
      
      <div className="mb-3">
        <label className="form-label">Media Type</label>
        <select className="form-select" value={mediaType} onChange={(e) => setMediaType(e.target.value)}>
          <option value="image">Image</option>
          <option value="audio">Audio</option>
          <option value="video">Video</option>
        </select>
      </div>

      <div className="mb-3">
        <label className="form-label">Cover File ({mediaType})</label>
        <input 
          type="file" 
          className="form-control" 
          accept={mediaType === 'image' ? 'image/png, image/jpeg, image/jpg, image/bmp' : mediaType === 'audio' ? 'audio/wav' : 'video/avi'}
          onChange={(e) => setCoverFile(e.target.files[0])} 
          required 
        />
      </div>

      <div className="mb-3">
        <label className="form-label">Secret Key / Password</label>
        <input 
          type="text" 
          className="form-control" 
          value={secretKey} 
          onChange={(e) => setSecretKey(e.target.value)} 
          required 
          placeholder="Enter a secret password"
        />
      </div>

      <div className="mb-3 form-check">
        <input 
          type="checkbox" 
          className="form-check-input" 
          id="useSecretFile" 
          checked={useSecretFile}
          onChange={(e) => setUseSecretFile(e.target.checked)}
        />
        <label className="form-check-label" htmlFor="useSecretFile">
          Upload secret file instead of text
        </label>
      </div>

      {useSecretFile ? (
        <div className="mb-3">
          <label className="form-label">Secret File</label>
          <input 
            type="file" 
            className="form-control" 
            onChange={(e) => setSecretFile(e.target.files[0])} 
            required={useSecretFile} 
          />
        </div>
      ) : (
        <div className="mb-3">
          <label className="form-label">Secret Message</label>
          <textarea 
            className="form-control" 
            rows="3" 
            value={secretText}
            onChange={(e) => setSecretText(e.target.value)}
            required={!useSecretFile}
            placeholder="Enter the message you want to hide..."
          ></textarea>
        </div>
      )}

      <div className="mb-3 form-check">
        <input 
          type="checkbox" 
          className="form-check-input" 
          id="encryptSecret" 
          checked={encrypt}
          onChange={(e) => setEncrypt(e.target.checked)}
        />
        <label className="form-check-label" htmlFor="encryptSecret">
          <strong>Encrypt Secret with AES</strong>
        </label>
        <div className="form-text">If checked, your secret will be securely encrypted with AES-GCM before embedding. Ensure you use the same password when decoding.</div>
      </div>

      <div className="mb-3">
        <label className="form-label">Output Filename (without extension)</label>
        <input 
          type="text" 
          className="form-control" 
          value={outputName} 
          onChange={(e) => setOutputName(e.target.value)} 
          required 
        />
      </div>

      <button type="submit" className="btn btn-primary" disabled={loading}>
        {loading ? (
          <>
            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Encoding in progress... {mediaType === 'video' ? 'Large videos may take some time.' : ''}
          </>
        ) : (
          'Encode'
        )}
      </button>

      {result && (
        <div className="alert alert-success mt-4">
          <h6 className="alert-heading">Encoding Successful!</h6>
          <p>Your media has been encoded.</p>
          <hr />
          <div className="d-flex gap-2 mb-3">
            <a href={result.url} className="btn btn-success" download={result.filename}>
              Download {result.filename}
            </a>
          </div>
        </div>
      )}
    </form>
  );
}

export default EncodeForm;
