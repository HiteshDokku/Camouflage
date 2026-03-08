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

def test_api_image(client):
    # Dummy PNG image minimum size ensuring enough payload space
    img = np.random.randint(0, 256, (30, 30, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.png', img)
    
    secret = 'my_secret_image_message'
    key = 'testkey_img'
    
    # Encode
    res_enc = client.post('/api/encode', data={
        'media_type': 'image',
        'secret_text': secret,
        'secret_key': key,
        'output_name': 'out_image',
        'encrypt': 'false',
        'cover': (io.BytesIO(img_encoded.tobytes()), 'cover.png')
    }, content_type='multipart/form-data')
    
    assert res_enc.status_code == 200, f"Encode failing, Error: {res_enc.data}"
    stego_bytes = res_enc.data
    
    # Decode
    res_dec = client.post('/api/decode', data={
        'media_type': 'image',
        'secret_key': key,
        'stego': (io.BytesIO(stego_bytes), 'stego.png')
    }, content_type='multipart/form-data')
    
    assert res_dec.status_code == 200
    assert res_dec.is_json
    assert res_dec.get_json()['extracted_text'] == secret

def test_api_audio(client):
    data = np.random.randint(-32000, 32000, (44100, 2), dtype=np.int16)
    f = io.BytesIO()
    wav.write(f, 44100, data)
    f.seek(0)
    
    secret = 'my_secret_audio_message'
    key = 'testkey_audio'
    
    res_enc = client.post('/api/encode', data={
        'media_type': 'audio',
        'secret_text': secret,
        'secret_key': key,
        'output_name': 'out_audio',
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
    assert res_dec.is_json
    assert res_dec.get_json()['extracted_text'] == secret

def test_api_video(client):
    with tempfile.NamedTemporaryFile(suffix='.avi', delete=False) as tf:
        cover_path = tf.name
        
    writer = cv2.VideoWriter(cover_path, cv2.VideoWriter_fourcc(*'RGBA'), 10, (64, 64), True)
    for _ in range(5):
        frame = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        writer.write(frame)
    writer.release()
    
    with open(cover_path, 'rb') as f:
        video_bytes = f.read()
    os.remove(cover_path)
        
    secret = 'my_secret_video_message'
    key = 'testkey_video'
    
    res_enc = client.post('/api/encode', data={
        'media_type': 'video',
        'secret_text': secret,
        'secret_key': key,
        'output_name': 'out_video',
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
    assert res_dec.is_json
    assert res_dec.get_json()['extracted_text'] == secret

def test_api_encryption(client):
    img = np.random.randint(0, 256, (30, 30, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.png', img)
    
    secret = 'my_secret_ENCRYPTED_message'
    key = 'super_secure_password'
    
    # Encode with encrypt=true
    res_enc = client.post('/api/encode', data={
        'media_type': 'image',
        'secret_text': secret,
        'secret_key': key,
        'output_name': 'out_image',
        'encrypt': 'true',
        'cover': (io.BytesIO(img_encoded.tobytes()), 'cover.png')
    }, content_type='multipart/form-data')
    
    assert res_enc.status_code == 200
    stego_bytes = res_enc.data
    
    # Decode
    res_dec = client.post('/api/decode', data={
        'media_type': 'image',
        'secret_key': key,
        'stego': (io.BytesIO(stego_bytes), 'stego.png')
    }, content_type='multipart/form-data')
    
    assert res_dec.status_code == 200
    assert res_dec.is_json
    assert res_dec.get_json()['extracted_text'] == secret
