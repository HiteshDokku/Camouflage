# Camouflage - Steganography App

Camouflage is a full-stack application that wraps a Python steganography logic library. It supports encoding and decoding secret messages within images, audio, and video files.

## Project Structure
- `backend/` - Flask API that uses the existing python repository
- `backend/stego_adapter.py` - Custom wrapper logic that adapts the original repo's CLI functionality seamlessly via callable endpoints.
- `frontend/` - React frontend built with Vite and Bootstrap

## Prerequisites
- **Node.js**: (Version 16+)
- **Python**: (Version 3.8+)
- **FFmpeg**: Required for audio/video processing. Install via `apt install ffmpeg` or download for Windows.

## Quickstart (Local Development)

### Quick Note on Processing
> **Processing Time for Large Files**: While image and audio modifications are generally fast, processing Video files (especially higher resolutions or larger files) involves unzipping and modifying individual frames heavily via NumPy. **Please note that large videos may take considerable time to complete processing synchronously**. The UI employs a progress spinner outlining these scenarios.

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```
The server will start on `http://127.0.0.1:5000`

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
Open the provided local URL (usually `http://localhost:5173`)

## API Endpoints
- `POST /api/encode` - Accepts `multipart/form-data` with `cover`, `secret_text` or `secret_file`, etc. Returns file attachment directly.
- `POST /api/decode` - Accepts `stego` file and `secret_key` string. Returns extracted text JSON or file download attachment.

### Curl Examples

**Encode:**
```bash
curl -F "media_type=image" -F "cover=@your_image.png" -F "secret_text=hello world" -F "secret_key=mykey" -F "output_name=secret_img" http://localhost:5000/api/encode --output secret_img.png
```

**Decode:**
```bash
curl -F "media_type=image" -F "stego=@secret_img.png" -F "secret_key=mykey" http://localhost:5000/api/decode
```

## Docker Deployment
We provide a `docker-compose` orchestration mapping combining the Python/Gunicorn Backend cluster and Nginx/React load-balanced Frontend proxy: 
```bash
docker-compose up --build
```
Then visit `http://localhost:80` (or `http://localhost`) to view your app.

## Architecture overview
The backend relies on `image_module`, `audio`, and `video` folders directly extracted from `rafaeloliveira00/Steganography`.
Because the algorithm generates a pseudo-random mapping dictionary during basic encoding based on random selections and file sizes, my wrapper automatically seeds the random generator utilizing your user-given password `key`. It implicitly tracks your file payload size metadata dynamically by embedding a binary bit header sequence inside the payload message directly, creating a truly 100% transparent API abstraction allowing you full encoding/decoding access via only a password.
