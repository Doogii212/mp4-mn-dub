# MP4 Mongolian Subtitle Translator

This project provides a minimal FastAPI web app that accepts an MP4, transcribes the audio with Whisper, translates the segments to Mongolian, and produces both SRT and MP4 outputs (hard/soft subtitles).

## Requirements

- Python 3.10+
- ffmpeg available on PATH

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860
```

Then open <http://localhost:7860> in your browser.

## Output Files

After processing, the app returns download links for:

1. Translated SRT
2. MP4 with hardcoded subtitles
3. MP4 with soft subtitles

## Notes

- Translation uses `deep-translator` (Google Translate) and targets Mongolian (`mn`) by default.
- Whisper model downloads the first time you run the app.
