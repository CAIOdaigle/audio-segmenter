# Audio Segmenter

A web application that splits audio files into segments under 90 seconds.

## Features

- Upload audio files in various formats (MP3, WAV, M4A, AAC, FLAC, OGG)
- Automatically splits into 89-second segments
- Download all segments as a ZIP file
- Validates that all segments are under 90 seconds

## Tech Stack

- Python 3.9+
- Flask
- FFmpeg (for audio processing)
- Gunicorn (production server)

## How It Works

1. Upload an audio file through the web interface
2. The app uses FFmpeg to split the file into 89-second segments
3. All segments are packaged into a ZIP file
4. Download the ZIP with all your segments

## Deployment

This app is configured for deployment on Railway.app or Render.com.

### Requirements

- FFmpeg must be available in the deployment environment
- Both Railway and Render provide FFmpeg by default

### Environment Variables

- `PORT` - Automatically set by the hosting platform

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Visit `http://localhost:8080` in your browser.

## Note

FFmpeg is required for audio processing. Make sure it's installed on your system or deployment platform.
