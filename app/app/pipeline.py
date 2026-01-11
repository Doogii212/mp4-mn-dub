 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/app/pipeline.py b/app/pipeline.py
new file mode 100644
index 0000000000000000000000000000000000000000..b45a0d23a8c31fcf65de139bd90392e98eec88e6
--- /dev/null
+++ b/app/pipeline.py
@@ -0,0 +1,132 @@
+import logging
+import math
+import uuid
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Iterable, List, Optional
+
+from app.utils_ffmpeg import burn_subtitles, extract_audio, mux_soft_subtitles
+
+logger = logging.getLogger(__name__)
+
+
+@dataclass
+class Segment:
+    start: float
+    end: float
+    text: str
+
+
+class Translator:
+    def translate(self, text: str, source_lang: Optional[str], target_lang: str) -> str:
+        raise NotImplementedError
+
+
+class EchoTranslator(Translator):
+    def translate(self, text: str, source_lang: Optional[str], target_lang: str) -> str:
+        return text
+
+
+def format_srt_timestamp(seconds: float) -> str:
+    if seconds < 0:
+        seconds = 0
+    millis = int(math.floor((seconds - math.floor(seconds)) * 1000))
+    total_seconds = int(math.floor(seconds))
+    hours = total_seconds // 3600
+    minutes = (total_seconds % 3600) // 60
+    secs = total_seconds % 60
+    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
+
+
+def generate_srt(segments: Iterable[Segment]) -> str:
+    lines: List[str] = []
+    for index, segment in enumerate(segments, start=1):
+        start_ts = format_srt_timestamp(segment.start)
+        end_ts = format_srt_timestamp(segment.end)
+        lines.append(str(index))
+        lines.append(f"{start_ts} --> {end_ts}")
+        lines.append(segment.text.strip())
+        lines.append("")
+    return "\n".join(lines).strip() + "\n"
+
+
+def transcribe_audio(
+    audio_path: Path,
+    source_lang: Optional[str],
+    model_size: str = "small",
+) -> List[Segment]:
+    try:
+        from faster_whisper import WhisperModel
+    except ImportError as exc:
+        raise RuntimeError(
+            "faster-whisper is required for transcription. Install it in requirements.txt"
+        ) from exc
+
+    logger.info("Loading Whisper model: %s", model_size)
+    model = WhisperModel(model_size, device="cpu", compute_type="int8")
+    language = None if source_lang == "auto" else source_lang
+    logger.info("Transcribing audio with language=%s", language or "auto")
+    segments, info = model.transcribe(str(audio_path), language=language)
+    results: List[Segment] = []
+    for segment in segments:
+        results.append(Segment(start=segment.start, end=segment.end, text=segment.text))
+    logger.info("Transcription complete: %s segments", len(results))
+    return results
+
+
+def translate_segments(
+    segments: Iterable[Segment],
+    translator: Translator,
+    source_lang: Optional[str],
+    target_lang: str,
+) -> List[Segment]:
+    translated: List[Segment] = []
+    for segment in segments:
+        translated_text = translator.translate(segment.text, source_lang, target_lang)
+        translated.append(
+            Segment(start=segment.start, end=segment.end, text=translated_text)
+        )
+    return translated
+
+
+def run_pipeline(
+    input_video: Path,
+    output_dir: Path,
+    source_lang: str,
+    target_lang: str = "mn",
+    translator: Optional[Translator] = None,
+    model_size: str = "small",
+) -> dict:
+    translator = translator or EchoTranslator()
+    output_dir.mkdir(parents=True, exist_ok=True)
+    job_id = uuid.uuid4().hex
+
+    audio_path = output_dir / f"{job_id}_audio.wav"
+    srt_path = output_dir / f"{job_id}_translated.srt"
+    burned_path = output_dir / f"{job_id}_burned.mp4"
+    soft_path = output_dir / f"{job_id}_soft.mp4"
+
+    logger.info("Extracting audio from %s", input_video)
+    extract_audio(input_video, audio_path)
+
+    segments = transcribe_audio(audio_path, source_lang=source_lang, model_size=model_size)
+    translated_segments = translate_segments(
+        segments, translator=translator, source_lang=source_lang, target_lang=target_lang
+    )
+
+    srt_content = generate_srt(translated_segments)
+    srt_path.write_text(srt_content, encoding="utf-8")
+    logger.info("Wrote SRT to %s", srt_path)
+
+    logger.info("Burning subtitles into video")
+    burn_subtitles(input_video, srt_path, burned_path)
+
+    logger.info("Muxing soft subtitles")
+    mux_soft_subtitles(input_video, srt_path, soft_path)
+
+    return {
+        "job_id": job_id,
+        "srt_path": srt_path,
+        "burned_path": burned_path,
+        "soft_path": soft_path,
+    }
 
EOF
)
