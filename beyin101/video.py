"""FFmpeg assembly: narration + B-roll to a long video, then vertical Shorts.

Pixabay clips arrive at assorted resolutions, frame rates and pixel formats,
which the concat demuxer refuses to join. Each clip is therefore normalised to
one common format first; the join itself is then a stream copy and costs
almost nothing.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

# Seconds decoded before the cut point so the exact seek has material to
# work with. Large enough to clear a keyframe interval, small enough to stay
# cheap.
SEEK_PREROLL = 8.0

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def find_font() -> str | None:
    """A font that actually carries Turkish glyphs, or None to skip captions."""
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


_FILTER_CACHE: dict[tuple[str, str], bool] = {}


def has_filter(ffmpeg: str, name: str) -> bool:
    """Whether this ffmpeg build actually carries a filter.

    Some widely used static builds ship without drawtext even though they
    report libfreetype. Asking for a missing filter fails the whole command,
    so a caption we cannot draw must be dropped from the graph rather than
    attempted — otherwise every Short fails and the user silently gets none.
    """
    key = (ffmpeg, name)
    if key not in _FILTER_CACHE:
        try:
            listing = subprocess.run(
                [ffmpeg, "-hide_banner", "-filters"],
                capture_output=True, text=True, check=True,
            ).stdout
        except (subprocess.CalledProcessError, OSError):
            return False
        _FILTER_CACHE[key] = parse_filter_list(listing, name)
    return _FILTER_CACHE[key]


def parse_filter_list(listing: str, name: str) -> bool:
    """Whether `name` appears as a filter in `ffmpeg -filters` output.

    Lines look like "  TS. boxblur  V->V  Blur the input." — the name is the
    second field. Matching the raw text instead would match a filter whose
    description merely mentions another one.
    """
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == name:
            return True
    return False


def probe_duration(ffprobe: str, path: Path) -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def normalise_clips(
    clips: list[Path],
    work_dir: Path,
    *,
    ffmpeg: str,
    width: int,
    height: int,
    fps: int = 30,
) -> list[Path]:
    """Re-encode every clip to one identical format so concat can stream-copy."""
    work_dir.mkdir(parents=True, exist_ok=True)
    normalised: list[Path] = []

    for index, clip in enumerate(clips):
        target = work_dir / f"norm_{index:03d}.mp4"
        if target.exists() and target.stat().st_size > 0:
            normalised.append(target)
            continue

        # Scale to fit, then pad — never stretch the source aspect.
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,fps={fps},format=yuv420p"
        )
        try:
            _run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                  "-i", str(clip), "-an", "-vf", vf,
                  "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                  "-g", str(fps * 2), str(target)])
        except subprocess.CalledProcessError:
            print(f"   ! klip atlandı (çözülemedi): {clip.name}")
            target.unlink(missing_ok=True)
            continue

        normalised.append(target)
        print(f"   normalize {len(normalised)}/{len(clips)}")

    return normalised


def build_long_video(
    clips: list[Path],
    narration: Path,
    destination: Path,
    work_dir: Path,
    *,
    ffmpeg: str,
    ffprobe: str,
) -> Path:
    """Lay normalised clips end to end, repeating until the narration is covered."""
    if not clips:
        raise RuntimeError("Montaj için hiç klip yok.")

    target_seconds = probe_duration(ffprobe, narration)
    clip_seconds = [probe_duration(ffprobe, c) for c in clips]

    # Repeat the clip sequence until it outlasts the narration, then trim.
    sequence: list[Path] = []
    total = 0.0
    index = 0
    while total < target_seconds:
        sequence.append(clips[index % len(clips)])
        total += clip_seconds[index % len(clips)]
        index += 1
        if index > 500:  # pathological guard: clips too short to ever cover it
            break

    listing = work_dir / "video_concat.txt"
    listing.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in sequence),
        encoding="utf-8",
    )

    silent = work_dir / "silent.mp4"
    _run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
          "-f", "concat", "-safe", "0", "-i", str(listing),
          "-c", "copy", str(silent)])

    destination.parent.mkdir(parents=True, exist_ok=True)
    _run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
          "-i", str(silent), "-i", str(narration),
          "-map", "0:v:0", "-map", "1:a:0",
          "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
          "-t", f"{target_seconds:.3f}", "-shortest",
          "-movflags", "+faststart", str(destination)])
    return destination


def short_start_times(total: float, count: int, duration: int) -> list[float]:
    """Evenly spaced start points, clamped so no cut runs past the end.

    Spreading the cuts across the whole video gives five distinct Shorts;
    taking them back-to-back from the opening would just re-post the intro.
    """
    if count < 1:
        return []
    usable = total - duration
    if usable <= 0:
        return [0.0]
    if count == 1:
        return [round(usable / 2, 2)]
    step = usable / (count - 1)
    return [round(i * step, 2) for i in range(count)]


def choose_short_starts(
    boundaries: list[float],
    total: float,
    count: int,
    duration: int,
) -> list[float]:
    """Pick cut points on real paragraph boundaries, spread across the video.

    Cutting on a stopwatch opens a Short mid-sentence with no hook, which is
    where most of them lose the viewer. These offsets were measured from the
    rendered narration parts, so each one is the moment a paragraph begins.

    The final boundary is dropped because it is the outro — a Short that opens
    with "thanks for watching" is wasted. Falls back to even spacing when
    there are no usable boundaries.
    """
    usable = [b for b in boundaries[:-1] if b + duration <= total]
    if not usable:
        return short_start_times(total, count, duration)
    if len(usable) <= count:
        return usable
    # Spread the picks over the available boundaries rather than taking the
    # first `count`, which would cluster every Short in the opening minutes.
    step = (len(usable) - 1) / (count - 1) if count > 1 else 0
    return [usable[round(i * step)] for i in range(count)]


def _escape_drawtext(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019")


def escape_font_path(path: str) -> str:
    """Make a font path safe to embed in a filter description.

    ffmpeg splits filter arguments on ':' and a Windows path carries one right
    after the drive letter, which quoting does not protect in this parser:
    fontfile='C:/Windows/...' is read as fontfile='C' and the rest is rejected
    as a nameless option. Backslashes are normalised first so the escape is
    not itself mistaken for one.
    """
    return path.replace("\\", "/").replace(":", "\\:")


def build_shorts(
    source: Path,
    destination_dir: Path,
    title: str,
    *,
    ffmpeg: str,
    ffprobe: str,
    count: int,
    duration: int,
    boundaries: list[float] | None = None,
) -> list[Path]:
    """Cut vertical Shorts, spaced across the whole video rather than the front.

    The 16:9 frame is fitted into 9:16 over a blurred copy of itself, so the
    full composition survives instead of being centre-cropped to a slice.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    total = probe_duration(ffprobe, source)

    if boundaries:
        starts = choose_short_starts(boundaries, total, count, duration)
    else:
        starts = short_start_times(total, count, duration)

    font = find_font()
    caption = ""
    if font and not has_filter(ffmpeg, "drawtext"):
        print("   ! bu ffmpeg derlemesinde drawtext yok, başlık yazısı atlanıyor")
        font = None
    if font:
        caption = (
            f",drawtext=fontfile='{escape_font_path(font)}'"
            f":text='{_escape_drawtext(title)}'"
            ":fontcolor=white:fontsize=52:borderw=3:bordercolor=black@0.8"
            ":x=(w-text_w)/2:y=180"
        )

    vf = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=luma_radius=40:luma_power=2[bgb];"
        "[fg]scale=1080:-2[fgs];"
        "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1" + caption
    )

    # A Short can still end mid-sentence; fading the last second makes that
    # read as a deliberate stop rather than a dropped connection.
    afade = f"afade=t=out:st={max(duration - 1, 0)}:d=1"

    base_vf = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=luma_radius=40:luma_power=2[bgb];"
        "[fg]scale=1080:-2[fgs];"
        "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1"
    )

    produced: list[Path] = []
    caption_failed = False
    for index, start in enumerate(starts, start=1):
        target = destination_dir / f"shorts_{index}.mp4"
        # Seeking on the input alone snaps to the nearest keyframe, which
        # overshoots the requested length by seconds on a concatenated file.
        # Seeking on the output is exact but decodes from the start. Do both:
        # jump most of the way cheaply, then seek the last few seconds exactly.
        coarse = max(start - SEEK_PREROLL, 0.0)
        fine = start - coarse
        def render(graph: str) -> None:
            _run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                  "-ss", f"{coarse:.2f}", "-i", str(source),
                  "-ss", f"{fine:.2f}", "-t", str(duration),
                  "-filter_complex", graph,
                  "-af", afade,
                  "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                  "-c:a", "aac", "-b:a", "160k",
                  "-movflags", "+faststart", str(target)])

        try:
            render(base_vf if caption_failed else vf)
        except subprocess.CalledProcessError:
            # A caption that will not draw must never cost the whole clip:
            # drop the title and keep the Short.
            if caption_failed or vf == base_vf:
                print(f"   ! Shorts #{index} oluşturulamadı, atlanıyor")
                continue
            print("   ! başlık yazısı çizilemedi, Shorts yazısız üretiliyor")
            caption_failed = True
            try:
                render(base_vf)
            except subprocess.CalledProcessError:
                print(f"   ! Shorts #{index} oluşturulamadı, atlanıyor")
                continue
        produced.append(target)
        print(f"   Shorts {index}/{len(starts)} hazır ({start:.0f}s)")

    return produced
