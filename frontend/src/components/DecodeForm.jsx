import React, { useState } from 'react';
import axios from 'axios';

const apiBase = import.meta.env.PROD ? '/api' : 'http://localhost:5000/api';

function DecodeForm() {
  const [mediaType, setMediaType] = useState('image');
  const [stegoFile, setStegoFile] = useState(null);
  const [secretKey, setSecretKey] = useState('');
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
    if (stegoFile) formData.append('stego', stegoFile);
    formData.append('secret_key', secretKey);

    try {
      // Decode can return either JSON or binary blob depending on what was hidden
      const res = await axios.post(`${apiBase}/decode`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        responseType: 'arraybuffer' // to handle both text and files
      });

      // let's try reading it as JSON first
      const decoder = new TextDecoder('utf-8');
      const text = decoder.decode(res.data);
      
      try {
        const json = JSON.parse(text);
        if (json.extracted_text) {
          setResult({ type: 'text', data: json.extracted_text });
        } else {
          setError("Unknown JSON format returned.")
        }
      } catch (e) {
        // Not a JSON -> was a binary file
        const blob = new Blob([res.data]);
        const url = window.URL.createObjectURL(blob);
        
        let filename = 'extracted_secret.bin';
        const disposition = res.headers['content-disposition'];
        if (disposition && disposition.indexOf('attachment') !== -1) {
          const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
          const matches = filenameRegex.exec(disposition);
          if (matches != null && matches[1]) { 
            filename = matches[1].replace(/['"]/g, '');
          }
        }
        
        setResult({ type: 'file', url, filename });
      }

    } catch (err) {
      console.error(err);
      
      if (err.response && err.response.data) {
        const decoder = new TextDecoder('utf-8');
        const text = decoder.decode(err.response.data);
        try {
          const json = JSON.parse(text);
          setError(json.error || 'An error occurred during decoding');
        } catch(e) {
          setError('An internal server error occurred');
        }
      } else {
        setError(err.message || 'An error occurred during decoding. Make sure the secret password is correct.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h5 className="mb-3">Decode Media</h5>

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
        <label className="form-label">Stego File ({mediaType})</label>
        <input 
          type="file" 
          className="form-control" 
          accept={mediaType === 'image' ? 'image/*' : mediaType === 'audio' ? 'audio/*' : 'video/*'}
          onChange={(e) => setStegoFile(e.target.files[0])} 
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
          placeholder="Enter the secret password used during encoding"
        />
      </div>

      <button type="submit" className="btn btn-primary" disabled={loading}>
        {loading ? (
          <>
            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Decoding in progress... {mediaType === 'video' ? 'Large videos may take some time.' : ''}
          </>
        ) : (
          'Decode'
        )}
      </button>

      {result && (
        <div className="alert alert-success mt-4">
          <h6 className="alert-heading">Decoding Successful!</h6>
          
          {result.type === 'text' && (
            <div>
              <p>Your extracted message is:</p>
              <textarea className="form-control" readOnly value={result.data} rows="3"></textarea>
            </div>
          )}

          {result.type === 'file' && (
            <div className="mt-3">
              <a href={result.url} className="btn btn-success" download={result.filename}>
                Download {result.filename}
              </a>
            </div>
          )}
        </div>
      )}
    </form>
  );
}

export default DecodeForm;
