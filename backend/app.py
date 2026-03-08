import os
import uuid
import logging
from flask import Flask, request, jsonify, send_file, after_this_request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

import stego_adapter

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
CORS(app)

# Configure directories
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Basic logging
logging.basicConfig(level=logging.INFO)

def get_ext(filename):
    if '.' in filename:
        return '.' + filename.rsplit('.', 1)[1].lower()
    return ''

@app.route('/api/encode', methods=['POST'])
def encode_api():
    try:
        media_type = request.form.get('media_type')
        secret_key = request.form.get('secret_key')
        output_name = request.form.get('output_name', 'encoded_media')
        secret_text = request.form.get('secret_text')
        encrypt_flag = request.form.get('encrypt', 'false').lower() == 'true'
        
        cover_file = request.files.get('cover')
        secret_file = request.files.get('secret_file')

        # Validation
        if not cover_file:
            return jsonify({"error": "cover file is required."}), 400
        if not secret_key:
            return jsonify({"error": "secret_key is required."}), 400
        if not media_type in ['image', 'audio', 'video']:
            return jsonify({"error": "Invalid media_type. Must be image, audio, or video."}), 400
        if not secret_text and not secret_file:
            return jsonify({"error": "Must provide either secret_text or secret_file."}), 400

        job_id = str(uuid.uuid4())
        
        cover_path = os.path.join(UPLOAD_FOLDER, f"cover_{job_id}{get_ext(cover_file.filename)}")
        cover_file.save(cover_path)

        secret_path = None
        if secret_file:
            secret_path = os.path.join(UPLOAD_FOLDER, f"secret_{job_id}_{secure_filename(secret_file.filename)}")
            secret_file.save(secret_path)

        # Build output path based on media type mapping if possible
        ext = '.png'
        if media_type == 'audio':
            ext = '.wav'
        elif media_type == 'video':
            ext = '.avi'
        
        output_path = os.path.join(OUTPUT_FOLDER, f"{secure_filename(output_name)}{ext}")

        # Try mapping to the adapter
        stego_adapter.encode(
            cover_path=cover_path,
            secret_text=secret_text,
            secret_file=secret_path,
            key=secret_key,
            media_type=media_type,
            output_path=output_path,
            encrypt=encrypt_flag
        )

        @after_this_request
        def cleanup(response):
            try:
                os.remove(cover_path)
                if secret_path and os.path.exists(secret_path):
                    os.remove(secret_path)
                # Note: output_path will be locked by send_file if not careful, 
                # but flask's send_file can be finicky with deletion immediately.
            except Exception as e:
                app.logger.error(f"Error cleaning up temp files: {e}")
            return response

        # Note: attachment_filename is deprecated in recent Flask for download_name
        return send_file(output_path, as_attachment=True, download_name=f"{secure_filename(output_name)}{ext}")

    except ValueError as ve:
        app.logger.warning(f"Validation Error: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        app.logger.error(f"Server Error during encode: {str(e)}", exc_info=app.debug)
        return jsonify({"error": "Internal Server Error during encoding."}), 500


@app.route('/api/decode', methods=['POST'])
def decode_api():
    try:
        media_type = request.form.get('media_type')
        secret_key = request.form.get('secret_key')
        stego_file = request.files.get('stego')

        # Validation
        if not stego_file:
            return jsonify({"error": "stego file is required."}), 400
        if not secret_key:
            return jsonify({"error": "secret_key is required."}), 400
        if not media_type in ['image', 'audio', 'video']:
            return jsonify({"error": "Invalid media_type. Must be image, audio, or video."}), 400

        job_id = str(uuid.uuid4())
        stego_path = os.path.join(UPLOAD_FOLDER, f"stego_{job_id}{get_ext(stego_file.filename)}")
        stego_file.save(stego_path)

        result = stego_adapter.decode(
            stego_path=stego_path,
            key=secret_key,
            media_type=media_type
        )

        @after_this_request
        def cleanup(response):
            try:
                os.remove(stego_path)
            except Exception as e:
                app.logger.error(f"Error cleaning up temp files: {e}")
            return response

        if 'text' in result:
            return jsonify({"extracted_text": result['text']}), 200
        elif 'file_path' in result:
            file_path = result['file_path']
            filename = result.get('name', 'extracted_secret')
            
            return send_file(file_path, as_attachment=True, download_name=secure_filename(filename))
        else:
            return jsonify({"error": "Unknown decode result format."}), 500

    except ValueError as ve:
        app.logger.warning(f"Validation Error: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        app.logger.error(f"Server Error during decode: {str(e)}", exc_info=app.debug)
        return jsonify({"error": "Internal Server Error during decoding. Did you use the correct password?"}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
