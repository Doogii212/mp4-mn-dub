 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index 114d99f98ba0a9232ad180562ee21cd7e359692c..30bb07054a8da704073434f846b70ce94d1171ab 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,35 @@
-# mp4-mn-dub
-MP4 video to Mongolian dubbing pipeline (ASR → Translate → TTS)
+# MP4 Mongolian Subtitle Translator
+
+This project provides a minimal FastAPI web app that accepts an MP4, transcribes the audio with Whisper, translates the segments to Mongolian, and produces both SRT and MP4 outputs (hard/soft subtitles).
+
+## Requirements
+
+- Python 3.10+
+- ffmpeg available on PATH
+
+## Install
+
+```bash
+pip install -r requirements.txt
+```
+
+## Run
+
+```bash
+uvicorn app.main:app --host 0.0.0.0 --port 7860
+```
+
+Then open <http://localhost:7860> in your browser.
+
+## Output Files
+
+After processing, the app returns download links for:
+
+1. Translated SRT
+2. MP4 with hardcoded subtitles
+3. MP4 with soft subtitles
+
+## Notes
+
+- The default translator is a placeholder that echoes the source text. Swap `EchoTranslator` in `app/pipeline.py` for a real translator later.
+- Whisper model downloads the first time you run the app.
 
EOF
)
