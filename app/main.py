import logging
import uuid
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

# жишээ:
return FileResponse(result["mp4_hard"], filename="subtitled.mp4")
# эсвэл SRT:
return FileResponse(result["srt"], filename="subs.srt")


from app.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MP4 Mongolian Subtitle Translator")

BASE_OUTPUT_DIR = Path("/tmp/mp4-mn-dub")
BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

JOB_REGISTRY: Dict[str, Dict[str, Path]] = {}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <html>
      <head>
        <title>MP4 Mongolian Subtitle Translator</title>
      </head>
      <body>
        <h1>MP4 Mongolian Subtitle Translator</h1>
        <form action="/translate" method="post" enctype="multipart/form-data">
          <label>Upload MP4:</label>
          <input type="file" name="file" accept="video/mp4" required />
          <br />
          <label>Source language:</label>
          <input type="text" name="source_lang" value="auto" />
          <br />
          <label>Target language:</label>
          <span>Mongolian (mn)</span>
          <br />
          <button type="submit">Translate</button>
        </form>
      </body>
    </html>
    """


@app.post("/translate", response_class=HTMLResponse)
async def translate(
    file: UploadFile = File(...),
    source_lang: str = Form("auto"),
) -> str:
    if not source_lang:
        source_lang = "auto"
    if file.content_type not in {"video/mp4", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Please upload an MP4 file.")

    job_dir = BASE_OUTPUT_DIR / "jobs"
    job_dir.mkdir(parents=True, exist_ok=True)
    upload_id = uuid.uuid4().hex
    input_path = job_dir / f"upload_{upload_id}.mp4"

    try:
        contents = await file.read()
        input_path.write_bytes(contents)
        logger.info("Saved upload to %s", input_path)

        result = run_pipeline(
            input_video=input_path,
            output_dir=job_dir,
            source_lang=source_lang,
            target_lang="mn",
        )
        JOB_REGISTRY[result["job_id"]] = {
            "srt": result["srt_path"],
            "burned": result["burned_path"],
            "soft": result["soft_path"],
        }
    except Exception as exc:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    job_id = result["job_id"]
    return f"""
    <html>
      <body>
        <h2>Translation complete</h2>
        <ul>
          <li><a href="/download/{job_id}/srt">Download translated SRT</a></li>
          <li><a href="/download/{job_id}/burned">Download MP4 with hard subtitles</a></li>
          <li><a href="/download/{job_id}/soft">Download MP4 with soft subtitles</a></li>
        </ul>
        <a href="/">Translate another file</a>
      </body>
    </html>
    """


@app.get("/download/{job_id}/{file_type}")
def download(job_id: str, file_type: str) -> FileResponse:
    job = JOB_REGISTRY.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    path = job.get(file_type)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="File not available")

    media_type = "application/octet-stream"
    filename = path.name
    return FileResponse(path, media_type=media_type, filename=filename)
