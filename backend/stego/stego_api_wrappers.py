import os
import sys
import struct
import random
import cv2

# Ensure stego module is in path
stego_path = os.path.dirname(os.path.abspath(__file__))
if stego_path not in sys.path:
    sys.path.insert(0, stego_path)

from stego.image_module import bytes_manipulation as img_bm
from stego.audio import bytes_manipulation as aud_bm
from stego.audio import wav
from stego.video import video as stego_video
from stego import utils

def _get_index_dict(key: str):
    """Seed random securely via the key to reliably generate the same shuffle dictionary."""
    random.seed(key)
    index_dict = utils.generate_dictionary(10)
    random.seed()  # Reset
    return index_dict

def encode_image(cover_path: str, secret_bytes: bytes, key: str, output_path: str) -> None:
    frame = cv2.imread(cover_path)
    if frame is None:
        raise ValueError(f"Failed to read image at {cover_path}")

    # Prepend 8-byte length header
    payload = struct.pack('>Q', len(secret_bytes)) + secret_bytes
    
    if img_bm.check_size(frame, len(payload)) is False:
        raise ValueError("Secret is too large for this image cover")

    index_dict = _get_index_dict(key)
    modified_frame = img_bm.hide_in_frame(frame, list(payload), index_dict)
    cv2.imwrite(output_path, modified_frame)

def decode_image(stego_path: str, key: str) -> bytes:
    frame = cv2.imread(stego_path)
    if frame is None:
        raise ValueError(f"Failed to read stego image at {stego_path}")

    index_dict = _get_index_dict(key)
    inverted_dict = utils.invert_dictionary(index_dict)

    # Decode length header (8 bytes)
    length_bytes = img_bm.retrieve_in_frame(frame, 8, inverted_dict)
    payload_len = struct.unpack('>Q', bytes(length_bytes))[0]
    total_len = payload_len + 8

    # Ensure total_len isn't absurdly large (basic validation)
    max_cap = (frame.shape[0] * frame.shape[1]) // 3
    if total_len > max_cap:
        raise ValueError("Computed payload length exceeds image size. Incorrect password or corrupted file.")

    # Decode entire payload
    full_bytes = img_bm.retrieve_in_frame(frame, total_len, inverted_dict)
    return bytes(full_bytes)[8:]

def encode_audio(cover_path: str, secret_bytes: bytes, key: str, output_path: str) -> None:
    original_song, rate = wav.read_wav_file(cover_path)
    if original_song is None:
        raise ValueError("Failed to read audio cover file")

    payload = struct.pack('>Q', len(secret_bytes)) + secret_bytes
    channel_count = wav.channel_count(original_song)
    max_data = wav.bytes_to_hide_count(original_song)

    if max_data < len(payload):
        raise ValueError("Secret is too large for this audio cover")

    index_dict = _get_index_dict(key)
    message_bytes_array = list(payload)

    for i in range(channel_count):
        channel_bytes = wav.channel_bytes(original_song, i)
        start = (len(channel_bytes) // 8) * i
        stop = start + (len(channel_bytes) // 8)
        
        sub_array = message_bytes_array[start:stop]
        if not sub_array:
            break

        modified_channel_bytes = aud_bm.hide_bytes(channel_bytes, sub_array, index_dict)
        original_song = wav.replace_data_channel(original_song, modified_channel_bytes, i)

    wav.write_wav_file(output_path, original_song, rate)

def decode_audio(stego_path: str, key: str) -> bytes:
    original_song, rate = wav.read_wav_file(stego_path)
    if original_song is None:
        raise ValueError("Failed to read audio stego file")

    channel_count = wav.channel_count(original_song)
    index_dict = _get_index_dict(key)
    inverted_dict = utils.invert_dictionary(index_dict)

    # Retrieve length header from the first channel
    channel_bytes_0 = wav.channel_bytes(original_song, 0)
    len_bytes = aud_bm.retrieve_bytes(channel_bytes_0, 8, inverted_dict)
    payload_len = struct.unpack('>Q', bytes(len_bytes))[0]
    total_len = payload_len + 8

    extracted_bytes_array = []
    bytes_left = total_len

    for i in range(channel_count):
        if bytes_left <= 0:
            break
        channel_bytes = wav.channel_bytes(original_song, i)
        capacity = len(channel_bytes) // 8
        bytes_to_get = min(bytes_left, capacity)
        
        extracted = aud_bm.retrieve_bytes(channel_bytes, bytes_to_get, inverted_dict)
        extracted_bytes_array.extend(extracted)
        bytes_left -= bytes_to_get

    return bytes(extracted_bytes_array)[8:]


def encode_video(cover_path: str, secret_bytes: bytes, key: str, output_path: str) -> None:
    video_file = cv2.VideoCapture(cover_path)
    if not video_file.isOpened():
        raise ValueError(f"Failed to read cover video at {cover_path}")

    fps = stego_video.frames_per_second(video_file)
    width = stego_video.video_width(video_file)
    height = stego_video.video_height(video_file)
    
    # We must save as a lossless codec if possible, standard fourcc used by original lib is RGBA or mp4v
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'RGBA'), fps, (width, height), True)

    payload = struct.pack('>Q', len(secret_bytes)) + secret_bytes
    message_bytes_array = list(payload)
    message_bytes_length = len(message_bytes_array)

    index_dict = _get_index_dict(key)
    frames_bytes_length = stego_video.bytes_to_hide_frame_count(video_file)
    video_bytes_to_hide = stego_video.bytes_to_hide_count(video_file)

    if message_bytes_length > video_bytes_to_hide:
        raise ValueError("Insufficient space to hide the message in this video")

    frame_count = 0
    while video_file.isOpened():
        ret, frame = video_file.read()
        if not ret:
            break

        start = frames_bytes_length * frame_count
        stop = start + frames_bytes_length

        if start < message_bytes_length:
            sub_list = message_bytes_array[start:stop]
            modified_frame = img_bm.hide_in_frame(frame, sub_list, index_dict)
            writer.write(modified_frame)
        else:
            writer.write(frame)
        frame_count += 1

    video_file.release()
    writer.release()

    # Original repo attempts to copy audio streams using ffmpeg wrapped
    try:
        stego_video.copy_audio(cover_path, output_path)
    except Exception:
        pass # Audio copy may fail if ffmpeg missing, but visual stego is retained

def decode_video(stego_path: str, key: str) -> bytes:
    video_file = cv2.VideoCapture(stego_path)
    if not video_file.isOpened():
        raise ValueError(f"Failed to read stego video at {stego_path}")

    index_dict = _get_index_dict(key)
    inverted_dict = utils.invert_dictionary(index_dict)
    frames_bytes_length = stego_video.bytes_to_hide_frame_count(video_file)

    ret, frame = video_file.read()
    if not ret:
        raise ValueError("Video is empty")

    len_bytes = img_bm.retrieve_in_frame(frame, 8, inverted_dict)
    payload_len = struct.unpack('>Q', bytes(len_bytes))[0]
    total_len = payload_len + 8
    
    # Reset video pointer
    video_file.set(cv2.CAP_PROP_POS_FRAMES, 0)
    bytes_left = total_len
    extracted_bytes_array = []

    while video_file.isOpened() and bytes_left > 0:
        ret, frame = video_file.read()
        if not ret:
            break

        bytes_to_get = min(bytes_left, frames_bytes_length)
        extracted = img_bm.retrieve_in_frame(frame, bytes_to_get, inverted_dict)
        extracted_bytes_array.extend(extracted)
        bytes_left -= bytes_to_get

    video_file.release()
    return bytes(extracted_bytes_array)[8:]
