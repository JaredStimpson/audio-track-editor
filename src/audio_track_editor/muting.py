from __future__ import annotations

import shutil
import subprocess
import sys
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path

from audio_track_editor.config import Settings
from audio_track_editor.media import MediaToolError, build_extract_render_audio_command
from audio_track_editor.schemas import Project, RenderSettings


@dataclass(frozen=True)
class MuteRegion:
    start: float
    end: float

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(frozen=True)
class MutedAudioResult:
    source_wav: Path
    output_wav: Path
    muted_regions: list[MuteRegion]


def collect_muted_speaker_ids(project: Project) -> set[str]:
    return {speaker.speaker_id for speaker in project.speakers if speaker.muted}


def collect_mute_regions(project: Project) -> list[MuteRegion]:
    muted_speakers = collect_muted_speaker_ids(project)
    if not muted_speakers:
        return []

    render = project.render_settings
    pre = render.pre_padding_ms / 1000.0
    post = render.post_padding_ms / 1000.0
    regions = [
        MuteRegion(max(0.0, segment.start - pre), max(0.0, segment.end + post))
        for segment in project.segments
        if segment.speaker_id in muted_speakers and segment.end > segment.start
    ]
    return merge_mute_regions(regions, render.merge_gap_ms / 1000.0)


def merge_mute_regions(regions: list[MuteRegion], merge_gap_seconds: float) -> list[MuteRegion]:
    if not regions:
        return []

    ordered = sorted(regions, key=lambda item: (item.start, item.end))
    merged = [ordered[0]]
    for region in ordered[1:]:
        previous = merged[-1]
        if region.start <= previous.end + merge_gap_seconds:
            merged[-1] = MuteRegion(previous.start, max(previous.end, region.end))
        else:
            merged.append(region)
    return merged


def _gain_at_time(
    seconds: float,
    regions: list[MuteRegion],
    region_index: int,
    render: RenderSettings,
) -> tuple[float, int]:
    fade = render.fade_ms / 1000.0
    mute_gain = max(0.0, min(1.0, render.mute_gain))

    while region_index < len(regions) and seconds > regions[region_index].end + fade:
        region_index += 1

    if region_index >= len(regions):
        return 1.0, region_index

    region = regions[region_index]
    fade_start = max(0.0, region.start - fade)
    fade_end = region.end + fade

    if seconds < fade_start or seconds > fade_end:
        return 1.0, region_index
    if fade > 0 and fade_start <= seconds < region.start:
        progress = (seconds - fade_start) / fade
        return 1.0 + (mute_gain - 1.0) * progress, region_index
    if region.start <= seconds <= region.end:
        return mute_gain, region_index
    if fade > 0 and region.end < seconds <= fade_end:
        progress = (seconds - region.end) / fade
        return mute_gain + (1.0 - mute_gain) * progress, region_index
    return 1.0, region_index


def apply_mute_envelope(
    input_wav: Path,
    output_wav: Path,
    regions: list[MuteRegion],
    render: RenderSettings,
) -> None:
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    if not regions:
        shutil.copyfile(input_wav, output_wav)
        return

    with wave.open(str(input_wav), "rb") as source:
        params = source.getparams()
        channels = source.getnchannels()
        sample_width = source.getsampwidth()
        sample_rate = source.getframerate()
        if sample_width != 2:
            raise MediaToolError("Muted rendering currently expects 16-bit PCM WAV input.")

        with wave.open(str(output_wav), "wb") as target:
            target.setparams(params)
            frame_offset = 0
            region_index = 0
            while True:
                frames = source.readframes(4096)
                if not frames:
                    break

                samples = array("h")
                samples.frombytes(frames)
                if sys.byteorder == "big":
                    samples.byteswap()

                frame_count = len(samples) // channels
                for frame in range(frame_count):
                    seconds = (frame_offset + frame) / sample_rate
                    gain, region_index = _gain_at_time(
                        seconds,
                        regions,
                        region_index,
                        render,
                    )
                    if gain == 1.0:
                        continue
                    for channel in range(channels):
                        sample_index = frame * channels + channel
                        samples[sample_index] = int(samples[sample_index] * gain)

                if sys.byteorder == "big":
                    samples.byteswap()
                target.writeframes(samples.tobytes())
                frame_offset += frame_count


def render_muted_audio(
    project: Project,
    output_wav: Path,
    settings: Settings,
    work_dir: Path,
) -> MutedAudioResult:
    if project.base_audio_stream is None:
        raise MediaToolError("Project has no selected audio stream to render.")

    work_dir.mkdir(parents=True, exist_ok=True)
    source_wav = work_dir / f"stream-{project.base_audio_stream}.render.wav"
    command = build_extract_render_audio_command(
        Path(project.media_path),
        project.base_audio_stream,
        source_wav,
        settings.ffmpeg_bin,
    )
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise MediaToolError(completed.stderr.strip() or "FFmpeg render audio extraction failed")

    regions = collect_mute_regions(project)
    apply_mute_envelope(source_wav, output_wav, regions, project.render_settings)
    return MutedAudioResult(source_wav=source_wav, output_wav=output_wav, muted_regions=regions)
