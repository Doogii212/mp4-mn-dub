import logging
import shlex
import subprocess
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def _run_command(command: List[str]) -> None:
    logger.info("Running command: %s", " ".join(shlex.quote(part) for part in command))
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        logger.error("Command failed with code %s", process.returncode)
        logger.error("stdout: %s", process.stdout)
        logger.error("stderr: %s", process.stderr)
        raise RuntimeError(
            "FFmpeg command failed: "
            + " ".join(shlex.quote(part) for part in command)
        )


def extract_audio(input_video: Path, output_audio: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_video),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_audio),
    ]
    _run_command(command)


def burn_subtitles(input_video: Path, subtitle_file: Path, output_video: Path) -> None:
    subtitle_path = subtitle_file.as_posix().replace("\\", "\\\\").replace(":", "\\:")
    subtitle_path = subtitle_path.replace("'", "\\'")
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_video),
        "-vf",
        f"subtitles='{subtitle_path}'",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_video),
    ]
    _run_command(command)


def mux_soft_subtitles(
    input_video: Path, subtitle_file: Path, output_video: Path
) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_video),
        "-i",
        str(subtitle_file),
        "-c",
        "copy",
        "-c:s",
        "mov_text",
        "-metadata:s:s:0",
        "language=mon",
        str(output_video),
    ]
    _run_command(command)
