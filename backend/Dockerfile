FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Create active storage directories
RUN mkdir -p uploads outputs

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
