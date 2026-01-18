#!/usr/bin/env python3
"""
Simple Audio Segmenter Web Interface
Splits audio files into segments under 90 seconds
"""

from flask import Flask, request, render_template_string, send_file, jsonify
import subprocess
import os
import shutil
from pathlib import Path
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Audio Segmenter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            background: #fafafa;
        }
        input[type="file"] {
            display: none;
        }
        .btn {
            background: #007bff;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
        }
        .btn:hover {
            background: #0056b3;
        }
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .file-label {
            background: #007bff;
            color: white;
            padding: 12px 30px;
            border-radius: 5px;
            cursor: pointer;
            display: inline-block;
        }
        .file-label:hover {
            background: #0056b3;
        }
        #status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            display: none;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .processing {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .segment-details {
            margin-top: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            font-family: monospace;
            font-size: 14px;
            text-align: left;
        }
        .notes {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            border-radius: 5px;
        }
        .notes h3 {
            margin-top: 0;
            color: #007bff;
        }
        .notes ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .notes li {
            margin: 8px 0;
        }
        #fileName {
            margin-top: 15px;
            font-weight: bold;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Audio Segmenter</h1>
        <p class="subtitle">Split audio files into segments under 90 seconds</p>

        <form id="uploadForm" enctype="multipart/form-data">
            <div class="upload-area">
                <label for="audioFile" class="file-label">
                    Choose Audio File
                </label>
                <input type="file" id="audioFile" name="audio" accept="audio/*" required>
                <div id="fileName"></div>
            </div>

            <button type="submit" class="btn" id="processBtn">Process Audio</button>
        </form>

        <div id="status"></div>

        <div class="notes">
            <h3>How to use:</h3>
            <ul>
                <li>Click "Choose Audio File" and select your audio file (MP3, WAV, M4A, etc.)</li>
                <li>Click "Process Audio" to split it into segments</li>
                <li>Wait for processing to complete</li>
                <li>Download the ZIP file containing all segments</li>
            </ul>

            <h3>Features:</h3>
            <ul>
                <li>Each segment will be exactly 89 seconds (to stay safely under 90)</li>
                <li>The last segment may be shorter</li>
                <li>All segments are named segment_000.mp3, segment_001.mp3, etc.</li>
                <li>Supports most audio formats: MP3, WAV, M4A, AAC, FLAC, OGG</li>
            </ul>
        </div>
    </div>

    <script>
        const audioFile = document.getElementById('audioFile');
        const fileName = document.getElementById('fileName');
        const uploadForm = document.getElementById('uploadForm');
        const status = document.getElementById('status');
        const processBtn = document.getElementById('processBtn');

        audioFile.addEventListener('change', function() {
            if (this.files.length > 0) {
                fileName.textContent = '📁 ' + this.files[0].name;
            }
        });

        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            if (!audioFile.files.length) {
                showStatus('Please select an audio file', 'error');
                return;
            }

            const formData = new FormData();
            formData.append('audio', audioFile.files[0]);

            processBtn.disabled = true;
            showStatus('Processing audio... This may take a moment.', 'processing');

            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    let html = '<strong>✅ Processing Complete!</strong><br><br>';
                    html += result.message;
                    if (result.segments) {
                        html += '<div class="segment-details">';
                        html += result.segments.join('<br>');
                        html += '</div>';
                    }
                    html += '<br><br>';
                    html += `<a href="/download/${result.zip_file}" class="btn" download>Download ZIP File</a>`;
                    showStatus(html, 'success');
                } else {
                    showStatus('❌ Error: ' + result.error, 'error');
                }
            } catch (error) {
                showStatus('❌ Error: ' + error.message, 'error');
            } finally {
                processBtn.disabled = false;
            }
        });

        function showStatus(message, type) {
            status.innerHTML = message;
            status.className = type;
            status.style.display = 'block';
        }
    </script>
</body>
</html>
'''

def get_audio_duration(file_path):
    """Get duration of audio file in seconds"""
    try:
        result = subprocess.run(
            ['ffprobe', '-i', file_path, '-show_entries', 'format=duration',
             '-v', 'quiet', '-of', 'csv=p=0'],
            capture_output=True,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except Exception:
        return None

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file uploaded'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        # Save uploaded file
        filename = secure_filename(audio_file.filename)
        base_name = Path(filename).stem
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(upload_path)

        # Get duration
        duration = get_audio_duration(upload_path)
        if duration is None:
            return jsonify({'error': 'Could not read audio file duration'}), 400

        # Create output folder
        output_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_segments")
        os.makedirs(output_folder, exist_ok=True)

        # Split into 89-second segments
        output_pattern = os.path.join(output_folder, "segment_%03d.mp3")
        result = subprocess.run(
            [
                'ffmpeg', '-i', upload_path,
                '-f', 'segment',
                '-segment_time', '89',
                '-c', 'copy',
                output_pattern
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({'error': f'Error processing audio: {result.stderr}'}), 500

        # Verify segments
        segments = sorted([f for f in os.listdir(output_folder) if f.endswith('.mp3')])
        if len(segments) == 0:
            return jsonify({'error': 'No segments were created'}), 500

        segment_info = []
        all_valid = True

        for segment in segments:
            segment_path = os.path.join(output_folder, segment)
            seg_duration = get_audio_duration(segment_path)

            if seg_duration and seg_duration >= 90:
                all_valid = False
                segment_info.append(f"⚠️ {segment}: {seg_duration:.2f}s (TOO LONG!)")
            else:
                segment_info.append(f"✅ {segment}: {seg_duration:.2f}s")

        # Create zip file
        zip_filename = f"{base_name}_segments"
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
        shutil.make_archive(zip_path, 'zip', output_folder)

        # Create summary
        message = f"<strong>Original file:</strong> {filename}<br>"
        message += f"<strong>Duration:</strong> {duration:.2f} seconds ({duration/60:.1f} minutes)<br>"
        message += f"<strong>Segments created:</strong> {len(segments)}<br>"

        if not all_valid:
            message += "<br>⚠️ <strong>Warning:</strong> Some segments are 90 seconds or longer!"
        else:
            message += "<br>✅ All segments are under 90 seconds!"

        return jsonify({
            'message': message,
            'segments': segment_info,
            'zip_file': f"{zip_filename}.zip"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    return "File not found", 404

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))

    print("\n" + "="*60)
    print("🎵 Audio Segmenter Started!")
    print("="*60)
    print(f"\nRunning on port: {port}")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=port, debug=False)
