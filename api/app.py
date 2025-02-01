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
    
    if file.filename == '':
        return {'error': 'No file selected'}, 400
    
    if not (file.filename.endswith('.srt') or file.filename.endswith('.txt')):
        return {'error': 'File must be an SRT or TXT file'}, 400

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.srt') as temp_out:
        # Read and decode the uploaded file
        file_content = file.read().decode('utf-8')
        
        # Split content into lines
        lines = file_content.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        
        # Process based on file type
        if file.filename.endswith('.txt'):
            # For TXT files, create SRT format
            subtitle_number = 1
            output_lines = []
            
            for i, line in enumerate(cleaned_lines):
                # Add subtitle number
                output_lines.append(str(subtitle_number))
                
                # Add dummy timestamp (you might want to calculate real timestamps)
                start_time = f"00:00:{str(i*4).zfill(2)},000"
                end_time = f"00:00:{str(i*4 + 3).zfill(2)},000"
                output_lines.append(f"{start_time} --> {end_time}")
                
                # Process and add the text
                balanced_text = split_subtitle_text(line, char_limit)
                output_lines.append(balanced_text)
                output_lines.append("")  # Empty line between subtitles
                
                subtitle_number += 1
                
            processed_content = "\n".join(output_lines)
        else:
            # For SRT files, maintain existing format
            buffer = []
            output_lines = []
            
            for line in cleaned_lines:
                buffer.append(line)
                
                if len(buffer) >= 3:
                    number = buffer[0]
                    timestamp = buffer[1]
                    text = " ".join(buffer[2:])
                    
                    balanced_text = split_subtitle_text(text, char_limit)
                    
                    output_lines.extend([number, timestamp, balanced_text, ""])
                    buffer = []
            
            # Handle any remaining lines
            if buffer:
                output_lines.extend(buffer)
                
            processed_content = "\n".join(output_lines)
        
        # Write to output file
        temp_out.write(processed_content)
        temp_out.seek(0)
        
        # Create response filename (always .srt)
        output_filename = secure_filename(file.filename.replace('.txt', '.srt').replace('.srt', '_cleaned.srt'))
        
        return send_file(
            temp_out.name,
            as_attachment=True,
            download_name=output_filename,
            mimetype='text/plain'
        )

if __name__ == '__main__':
    app.run(port=5000, debug=True)