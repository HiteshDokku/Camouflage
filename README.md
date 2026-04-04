# 🕵️‍♂️ Camouflage - Full-Stack Steganography App

[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)](https://vitejs.dev/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

Camouflage is a full-stack web application that allows you to securely hide secret text messages or files inside everyday media formats like **Images (PNG), Audio (WAV), and Video (AVI)**. 

Built with a React frontend and a Python/Flask backend, it leverages Least Significant Bit (LSB) steganography with pseudo-random bit shuffling and optional AES-GCM payload encryption to ensure your hidden data remains completely undetectable and secure.

---

## ✨ Features

- **🖼️ Multi-Media Support:** Hide data inside Images, Audio files, and Video streams.
- **🔒 Secure Password Seeding:** Uses your password to seed a pseudo-random bit-shuffling algorithm. The data is scattered across the file, making it impossible to extract without the exact password.
- **🛡️ AES-GCM Encryption:** Optional military-grade encryption encrypts the payload before it is even embedded into the media.
- **📁 File & Text Payloads:** Hide plain text messages or upload entire files (PDFs, ZIPs, etc.) inside the cover media.
- **⚙️ 100% Transparent Abstraction:** No need to manage clumsy 'key files'. The payload size and shuffle mappings are handled dynamically and seamlessly via a custom 8-byte header sequence.
- **🐳 Docker Ready:** Instantly deploy the entire stack using `docker-compose`.

---

## 🏗️ System Architecture

The project is divided into a decoupled Frontend and Backend, communicating via RESTful APIs.

1. **Frontend (React + Vite):** Provides an intuitive, responsive UI with separate tabs for Encoding and Decoding. It handles file staging and binary blob downloads.
2. **Backend API (Flask):** Exposes `/api/encode` and `/api/decode`. Manages temporary file saving and routes data to the Stego Adapter.
3. **Stego Adapter (`stego_adapter.py`):** The mastermind wrapper. It prepends binary length headers, performs AES encryption using `cryptography`, and generates deterministic shuffle dictionaries based on the user's password.
4. **Core Steganography Engine:** Operates directly on bytes. Modifies the Least Significant Bits (LSB) of RGB channels (via `OpenCV`) or Audio frames (via `SciPy`).

---

## 🛠️ Tech Stack

### Frontend
* **React 18** (UI Library)
* **Vite** (Build Tool)
* **Bootstrap 5** (Styling)
* **Axios** (API Client)

### Backend
* **Python 3.11+**
* **Flask** & **Gunicorn** (Web Server)
* **OpenCV** (`cv2`) & **NumPy** (Image & Video processing)
* **SciPy** (WAV Audio processing)
* **Cryptography** (AES-GCM & PBKDF2HMAC)

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- **Node.js**: (Version 18+)
- **Python**: (Version 3.11+)
- **FFmpeg**: Required for backend audio/video stream copying. *(Install via `sudo apt install ffmpeg` on Linux or via Homebrew on Mac)*

### 1. Start the Python Backend
Open a terminal and navigate to the `backend` directory:
```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the Flask development server
python app.py
