import os
import io
import json
import pytest
import cv2
import numpy as np
import scipy.io.wavfile as wav
from app import app
import tempfile

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_ac1_image_text(client):
    # 1. Upload an image, hide the text "hello world" with key abc, download stego image, decode it and verify text is "hello world".
    img = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.png', img)
    
    secret = 'hello world'
    key = 'abc'
    
    res_enc = client.post('/api/encode', data={
        'media_type': 'image',
        'secret_text': secret,
        'secret_key': key,
        'output_name': 'ac1_img',
        'encrypt': 'false',
        'cover': (io.BytesIO(img_encoded.tobytes()), 'cover.png')
    }, content_type='multipart/form-data')
    
    assert res_enc.status_code == 200, f"Encode failing: {res_enc.data}"
    stego_bytes = res_enc.data
    
    res_dec = client.post('/api/decode', data={
        'media_type': 'image',
        'secret_key': key,
        'stego': (io.BytesIO(stego_bytes), 'stego.png')
    }, content_type='multipart/form-data')
    
    assert res_dec.status_code == 200
    assert res_dec.is_json
    assert res_dec.get_json()['extracted_text'] == secret

def test_ac2_wav_file(client):
    # 2. Upload a small WAV file, hide a PDF (or text file) in it, download stego audio, decode file and verify bytes match.
    data = np.random.randint(-32000, 32000, (44100, 2), dtype=np.int16)
    f = io.BytesIO()
    wav.write(f, 44100, data)
    f.seek(0)
    
    # fake PDF bytes
    secret_bytes = b'%PDF-1.4 random PDF content...'
    key = 'wav_key'
    
    res_enc = client.post('/api/encode', data={
        'media_type': 'audio',
        'secret_file': (io.BytesIO(secret_bytes), 'secret.pdf'),
        'secret_key': key,
        'output_name': 'ac2_audio',
        'encrypt': 'false',
        'cover': (f, 'cover.wav')
    }, content_type='multipart/form-data')
    
    assert res_enc.status_code == 200
    stego_bytes = res_enc.data
    
    res_dec = client.post('/api/decode', data={
        'media_type': 'audio',
        'secret_key': key,
        'stego': (io.BytesIO(stego_bytes), 'stego.wav')
    }, content_type='multipart/form-data')
    
    assert res_dec.status_code == 200
    assert not res_dec.is_json 
    # should be returned as attachment
    assert res_dec.data == secret_bytes

def test_ac3_avi_png(client):
    # 3. Upload a short AVI video, hide a PNG inside it, download stego video, decode and verify file integrity.
    with tempfile.NamedTemporaryFile(suffix='.avi', delete=False) as tf:
        cover_path = tf.name
        
    writer = cv2.VideoWriter(cover_path, cv2.VideoWriter_fourcc(*'RGBA'), 10, (100, 100), True)
    for _ in range(10):
        frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        writer.write(frame)
    writer.release()
    
    with open(cover_path, 'rb') as f:
        video_bytes = f.read()
    os.remove(cover_path)
    
    # Fake PNG inside
    img = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.png', img)
    secret_png_bytes = img_encoded.tobytes()
    key = 'avi_key'
    
    res_enc = client.post('/api/encode', data={
        'media_type': 'video',
        'secret_file': (io.BytesIO(secret_png_bytes), 'secret.png'),
        'secret_key': key,
        'output_name': 'ac3_video',
        'encrypt': 'false',
        'cover': (io.BytesIO(video_bytes), 'cover.avi')
    }, content_type='multipart/form-data')
    
    assert res_enc.status_code == 200
    stego_bytes = res_enc.data
    
    res_dec = client.post('/api/decode', data={
        'media_type': 'video',
        'secret_key': key,
        'stego': (io.BytesIO(stego_bytes), 'stego.avi')
    }, content_type='multipart/form-data')
    
    assert res_dec.status_code == 200
    assert not res_dec.is_json
    assert res_dec.data == secret_png_bytes

def test_ac4_invalid_media_type(client):
    img = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.png', img)
    
    res_enc = client.post('/api/encode', data={
        'media_type': 'invalid_type',
        'secret_text': 'hello',
        'secret_key': 'key',
        'output_name': 'out',
        'cover': (io.BytesIO(img_encoded.tobytes()), 'cover.png')
    }, content_type='multipart/form-data')
    
    assert res_enc.status_code == 400
    assert b"Invalid media_type" in res_enc.data

def test_ac5_missing_key_or_message(client):
    img = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.png', img)
    
    # Missing message
    res_enc1 = client.post('/api/encode', data={
        'media_type': 'image',
        'secret_key': 'key',
        'output_name': 'out',
        'cover': (io.BytesIO(img_encoded.tobytes()), 'cover.png')
    }, content_type='multipart/form-data')
    
    assert res_enc1.status_code == 400
    assert b"Must provide either secret_text or secret_file" in res_enc1.data

    # Missing key
    res_enc2 = client.post('/api/encode', data={
        'media_type': 'image',
        'secret_text': 'hello',
        'output_name': 'out',
        'cover': (io.BytesIO(img_encoded.tobytes()), 'cover.png')
    }, content_type='multipart/form-data')
    
    assert res_enc2.status_code == 400
    assert b"secret_key is required" in res_enc2.data
    
    # Decode missing key
    res_dec = client.post('/api/decode', data={
        'media_type': 'image',
        'stego': (io.BytesIO(img_encoded.tobytes()), 'stego.png')
    }, content_type='multipart/form-data')
    
    assert res_dec.status_code == 400
    assert b"secret_key is required" in res_dec.data
