from flask import Flask, request, send_file
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

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

@app.route('/process-srt', methods=['POST'])
def process_srt():
    if 'file' not in request.files:
        return {'error': 'No file provided'}, 400
    
    file = request.files['file']
    char_limit = int(request.form.get('charLimit', 42))
    export_format = request.form.get('exportFormat', 'original')
    
    if file.filename == '':
        return {'error': 'No file selected'}, 400
    
    if not (file.filename.endswith('.srt') or file.filename.endswith('.txt')):
        return {'error': 'File must be an SRT or TXT file'}, 400

    # Determine output extension based on export format
    if export_format == 'srt':
        output_extension = '.srt'
    elif export_format == 'txt':
        output_extension = '.txt'
    else:  # 'original'
        output_extension = os.path.splitext(file.filename)[1]

    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=output_extension) as temp_out:
        # Read and process the file content
        file_content = file.read().decode('utf-8')
        
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
        
        # Create output filename with appropriate extension
        base_filename = os.path.splitext(file.filename)[0]
        output_filename = secure_filename(base_filename + '_cleaned' + output_extension)
        
        response = send_file(
            temp_out.name,
            as_attachment=True,
            download_name=output_filename,
            mimetype='text/plain'
        )
        
        # Explicitly set the Content-Disposition header
        response.headers["Content-Disposition"] = f"attachment; filename={output_filename}"
        
        return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))