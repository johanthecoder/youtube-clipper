# youtube-clipper

Grab a section of a YouTube video and save it as MP4, MP3, or GIF. Paste a
link, drag the start/end handles to the part you want, pick a format, and
download it. Nothing to install on the client side — it runs in the browser
against a small local backend.

Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) for fetching and
[ffmpeg](https://ffmpeg.org/) for cutting and transcoding.

## Features

- Trim any part of a video instead of downloading the whole thing
- Export to **MP4** (up to 1080p60), **MP3**, or **GIF**
- Pick the output resolution from whatever the source actually has
- Live progress while the clip is being built
- Runs entirely on your own machine

## How it works

```
 browser (Next.js)  ──►  FastAPI  ──►  yt-dlp  ──►  ffmpeg
   trim + format          jobs        download       cut / transcode
```

The frontend asks the backend for video info, you choose a range and format,
and the backend downloads just that section with yt-dlp and hands it to ffmpeg
to cut and convert. Files are written to a temp folder and cleaned up after an
hour.

## Requirements

- Node 18+ and pnpm
- Python 3.10+
- ffmpeg on your PATH

## Setup

Backend:

```bash
cd server
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
cd web
pnpm install
pnpm dev
```

Then open http://localhost:3000. The frontend talks to the backend at
`http://localhost:8000` by default — override it with `NEXT_PUBLIC_API_URL` if
you run the API somewhere else.

## Disclaimer

This is for downloading content you own or have permission to use. Downloading
videos may be against YouTube's Terms of Service, and the content may be
copyrighted. You're responsible for how you use it.

## License

MIT — see [LICENSE](LICENSE).
