import os
import cv2
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stego.stego_api_wrappers import (
    encode_image, decode_image,
    encode_audio, decode_audio,
    encode_video, decode_video
)

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

def test_image_wrappers(tmp_dir):
    cover_path = os.path.join(tmp_dir, "cover.png")
    stego_path = os.path.join(tmp_dir, "stego.png")
    
    # Create a dummy image large enough to hold the payload (need at least ~ 8+12 bytes = 20 bytes -> 60 pixels)
    img = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
    cv2.imwrite(cover_path, img)

    secret = b"hello binary"
    key = "my_secret_key"

    encode_image(cover_path, secret, key, stego_path)
    assert os.path.exists(stego_path)

    recovered = decode_image(stego_path, key)
    assert recovered == secret

def test_audio_wrappers(tmp_dir):
    cover_path = os.path.join(tmp_dir, "cover.wav")
    stego_path = os.path.join(tmp_dir, "stego.wav")
    
    # Create dummy audio
    sample_rate = 44100
    # 1 second of audio, 2 channels (stereo), 16-bit
    data = np.random.randint(-32000, 32000, (44100, 2), dtype=np.int16)
    wav.write(cover_path, sample_rate, data)

    secret = b"audio secret test"
    key = "audio_key"

    encode_audio(cover_path, secret, key, stego_path)
    assert os.path.exists(stego_path)

    recovered = decode_audio(stego_path, key)
    assert recovered == secret

def test_video_wrappers(tmp_dir):
    cover_path = os.path.join(tmp_dir, "cover.avi")
    stego_path = os.path.join(tmp_dir, "stego.avi")
    
    # Create dummy video
    fps = 10
    width = 64
    height = 64
    writer = cv2.VideoWriter(cover_path, cv2.VideoWriter_fourcc(*'RGBA'), fps, (width, height), True)
    for _ in range(5): # 5 frames
        frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        writer.write(frame)
    writer.release()

    secret = b"video test"
    key = "video_key"

    encode_video(cover_path, secret, key, stego_path)
    assert os.path.exists(stego_path)

    recovered = decode_video(stego_path, key)
    assert recovered == secret
