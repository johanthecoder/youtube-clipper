# youtube-clipper

Grab a section of a video — from YouTube, Vimeo, and the hundreds of other
sites [yt-dlp](https://github.com/yt-dlp/yt-dlp) supports — and save it as
MP4, MP3, or GIF. Paste a link, drag the start/end handles to the part you
want, pick a format, and download it. The frontend runs in the browser; a
small backend does the actual fetching and cutting with yt-dlp and
[ffmpeg](https://ffmpeg.org/).

## Features

- Works with any [yt-dlp-supported site](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md), not just YouTube
- Trim any part of a video instead of downloading the whole thing
- Export to **MP4** (up to 1080p60), **MP3**, or **GIF**
- Pick the output resolution from whatever the source actually offers
- Live progress that reports downloading vs. converting, so long jobs don't
  look frozen
- Skips re-encoding when you grab the whole video, so full downloads stay fast
- Runs entirely on your own machine

## How it works

```
 browser (Next.js)  ──►  FastAPI  ──►  yt-dlp  ──►  ffmpeg
   trim + format          jobs        download       cut / transcode
```

1. You paste a URL; the backend returns the title, thumbnail, duration, and
   available resolutions.
2. You choose a range and format and hit **Create clip**.
3. The backend starts a background job. If you asked for a section, it downloads
   just that range and re-encodes at the cut points for a frame-accurate trim.
   If you asked for the whole video, it skips the re-encode and downloads
   directly.
4. The frontend polls the job for progress and, when it's done, hands you a
   download link.

Finished files live in a temp folder and are cleaned up after an hour.

## Project layout

```
youtube-clipper/
├─ server/                FastAPI backend
│  ├─ main.py             HTTP routes
│  ├─ clipper.py          yt-dlp + ffmpeg wrapper
│  ├─ jobs.py             in-memory job tracking + temp cleanup
│  ├─ requirements.txt
│  ├─ requirements-dev.txt
│  └─ tests/
└─ web/                   Next.js + TypeScript frontend
   ├─ app/page.tsx        the whole UI flow
   ├─ components/TrimBar.tsx
   └─ lib/api.ts          typed backend client
```

## Requirements

- Node 18+ and pnpm
- Python 3.10+
- ffmpeg on your PATH (on Windows the backend also picks up a
  `winget install Gyan.FFmpeg` install automatically)

## Setup

**Backend**

```bash
cd server
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend**

```bash
cd web
pnpm install
pnpm dev
```

Open http://localhost:3000.

## Configuration

The frontend talks to `http://localhost:8000` by default. Point it elsewhere
with an env var (see `web/.env.example`):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API

| Method | Path                    | Body / params                                   | Returns |
|--------|-------------------------|-------------------------------------------------|---------|
| POST   | `/api/info`             | `{ url }`                                        | title, uploader, duration, thumbnail, resolutions |
| POST   | `/api/clip`             | `{ url, start, end, format, quality, title, duration }` | `{ job_id }` |
| GET    | `/api/progress/{id}`    | —                                                | `{ status, progress, downloaded, total, filename, error }` |
| GET    | `/api/download/{id}`    | —                                                | the finished file |

`status` moves through `queued → downloading → processing → done` (or `error`).

## Tests

```bash
cd server
pip install -r requirements-dev.txt
pytest
```

The suite covers the filename sanitizer, the trim-vs-whole-video logic, the job
store, and the API routes (the heavy download step is stubbed, so tests don't
touch the network).

## Notes

- A long **trim** re-encodes for an accurate cut and can take a little while —
  that's expected, and the UI shows a "Converting…" state for it.
- GIFs of long selections get big fast; they're meant for short clips.
- The in-memory job store is fine for local single-process use. For anything
  shared you'd want a real queue and storage.

## Disclaimer

This is for downloading content you own or have permission to use. Downloading
videos may be against YouTube's Terms of Service, and the content may be
copyrighted. You're responsible for how you use it.

## License

MIT — see [LICENSE](LICENSE).
