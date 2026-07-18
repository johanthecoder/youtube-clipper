"""Fetch video info and build clips with yt-dlp + ffmpeg."""

import glob
import os
import subprocess
from shutil import which

from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func

MAX_HEIGHT = 1080


def find_ffmpeg():
    """Return the ffmpeg binary, falling back to the winget install path."""
    found = which("ffmpeg")
    if found:
        return found
    pattern = os.path.expanduser(
        r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\**\bin\ffmpeg.exe"
    )
    matches = glob.glob(pattern, recursive=True)
    return matches[0] if matches else "ffmpeg"


FFMPEG = find_ffmpeg()
FFMPEG_DIR = os.path.dirname(FFMPEG) if os.sep in FFMPEG else None

# On Windows the winget build often isn't on PATH, so yt-dlp can't see it.
# Put its folder on PATH for this process and everything downstream finds it.
if FFMPEG_DIR and FFMPEG_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")


def _base_opts():
    opts = {"quiet": True, "no_warnings": True}
    if FFMPEG_DIR:
        opts["ffmpeg_location"] = FFMPEG_DIR
    return opts


def get_info(url):
    with YoutubeDL({**_base_opts(), "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    heights = sorted(
        {f["height"] for f in info.get("formats", []) if f.get("height")},
        reverse=True,
    )
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "duration": info.get("duration"),
        "thumbnail": info.get("thumbnail"),
        "resolutions": [h for h in heights if h <= MAX_HEIGHT],
    }


def is_whole_video(start, end, duration):
    """True when the selection covers essentially the whole video (no trim needed)."""
    if duration is None:
        return False
    return start <= 1 and end >= duration - 1


def make_clip(url, start, end, fmt, quality, out_dir, duration=None, hook=None, pp_hook=None):
    os.makedirs(out_dir, exist_ok=True)
    out_base = os.path.join(out_dir, "clip")
    height = min(int(quality or MAX_HEIGHT), MAX_HEIGHT)

    opts = {
        **_base_opts(),
        "outtmpl": out_base + ".%(ext)s",
    }

    # Only cut when an actual sub-section is asked for. Trimming forces a
    # re-encode at the cut points (slow); grabbing the whole video doesn't
    # need it, and the normal downloader reports real progress.
    if not is_whole_video(start, end, duration):
        opts["download_ranges"] = download_range_func(None, [(start, end)])
        opts["force_keyframes_at_cuts"] = True

    if hook:
        opts["progress_hooks"] = [hook]
    if pp_hook:
        opts["postprocessor_hooks"] = [pp_hook]

    if fmt == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
        return out_base + ".mp3"

    opts["format"] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
    opts["merge_output_format"] = "mp4"
    with YoutubeDL(opts) as ydl:
        ydl.download([url])
    mp4_path = out_base + ".mp4"

    if fmt == "gif":
        gif_path = os.path.join(out_dir, "clip.gif")
        _to_gif(mp4_path, gif_path)
        return gif_path
    return mp4_path


def _to_gif(src, dst, fps=12, width=480):
    # two-pass palette gives a much cleaner gif than the default 256 colors
    vf = (
        f"fps={fps},scale={width}:-1:flags=lanczos,"
        "split[a][b];[a]palettegen[p];[b][p]paletteuse"
    )
    subprocess.run(
        [FFMPEG, "-y", "-i", src, "-vf", vf, dst],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
