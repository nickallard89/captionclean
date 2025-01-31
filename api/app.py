from flask import Flask, request, send_file
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

def split_subtitle_text(text, char_limit):
    words = text.split()
    total_length = len(text)
    
    if total_length <= char_limit:
        return text
    
    best_split = None
    best_diff = float("inf")
    
    for i in range(1, len(words)):
        first_part = " ".join(words[:i])
        second_part = " ".join(words[i:])
        
        if len(first_part) < len(second_part):
            diff = abs(len(first_part) - len(second_part))
            if diff < best_diff:
                best_split = (first_part, second_part)
                best_diff = diff
    
    if best_split:
        return f"{best_split[0]}\n{best_split[1]}"
    else:
        return text

@app.route('/test', methods=['GET'])
def test():
    return {"message": "Backend is working!"}

@app.route('/process-srt', methods=['POST'])
def process_srt():
    if 'file' not in request.files:
        return {'error': 'No file provided'}, 400
    
    file = request.files['file']
    char_limit = int(request.form.get('charLimit', 42))
    
    if file.filename == '':
        return {'error': 'No file selected'}, 400
    
    if not (file.filename.endswith('.srt') or file.filename.endswith('.txt')):
        return {'error': 'File must be an SRT or TXT file'}, 400

    # Create temporary files for input and output
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.srt') as temp_in, \
         tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.srt') as temp_out:
        
        # Save uploaded file
        file_content = file.read().decode('utf-8')
        temp_in.write(file_content)
        temp_in.seek(0)
        
        # Process the file
        buffer = []
        for line in file_content.split('\n'):
            if line.strip():
                buffer.append(line.strip())
            else:
                if buffer:
                    number = buffer[0]
                    timestamp = buffer[1]
                    text = " ".join(buffer[2:])
                    
                    balanced_text = split_subtitle_text(text, char_limit)
                    
                    temp_out.write(f"{number}\n{timestamp}\n{balanced_text}\n\n")
                buffer = []
        
        # Handle last block if file doesn't end with newline
        if buffer:
            number = buffer[0]
            timestamp = buffer[1]
            text = " ".join(buffer[2:])
            balanced_text = split_subtitle_text(text, char_limit)
            temp_out.write(f"{number}\n{timestamp}\n{balanced_text}\n")
        
        temp_out.seek(0)
        
        # Create response filename
        output_filename = secure_filename(file.filename.replace('.srt', '_cleaned.srt'))
        
        return send_file(
            temp_out.name,
            as_attachment=True,
            download_name=output_filename,
            mimetype='text/plain'
        )

if __name__ == '__main__':
    app.run(port=5000, debug=True)