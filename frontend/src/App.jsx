import React, { useState } from 'react';
import EncodeForm from './components/EncodeForm';
import DecodeForm from './components/DecodeForm';

function App() {
  const [activeTab, setActiveTab] = useState('encode');

  return (
    <div className="container mt-5">
      <div className="card shadow-sm">
        <div className="card-header bg-white d-flex align-items-center justify-content-between">
          <h4 className="mb-0 text-primary">Camouflage</h4>
          <ul className="nav nav-pills card-header-pills">
            <li className="nav-item">
              <button 
                className={`nav-link ${activeTab === 'encode' ? 'active' : ''}`}
                onClick={() => setActiveTab('encode')}
              >
                Encode
              </button>
            </li>
            <li className="nav-item ms-2">
              <button 
                className={`nav-link ${activeTab === 'decode' ? 'active' : ''}`}
                onClick={() => setActiveTab('decode')}
              >
                Decode
              </button>
            </li>
          </ul>
        </div>
        <div className="card-body p-4">
          {activeTab === 'encode' ? <EncodeForm /> : <DecodeForm />}
        </div>
      </div>
    </div>
  );
}

export default App;
