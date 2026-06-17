from __future__ import annotations

import argparse
from pathlib import Path

from audio_track_editor.analysis import AnalyzeOptions, Analyzer
from audio_track_editor.config import load_settings
from audio_track_editor.doctor import format_checks, run_doctor
from audio_track_editor.model_setup import cache_diarization_model
from audio_track_editor.renderer import render_project
from audio_track_editor.schemas import load_project, save_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ate",
        description="Audio Track Editor development CLI.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("doctor", help="Check local tools, paths, and optional model deps.")

    cache_model = subparsers.add_parser(
        "cache-model",
        help="Download/cache or validate the selected local diarization model.",
    )
    cache_model.add_argument(
        "--allow-download",
        action="store_true",
        help="Permit network download for the first model cache step.",
    )

    analyze = subparsers.add_parser("analyze", help="Inspect media and create an analysis project.")
    analyze.add_argument("media", type=Path)
    analyze.add_argument("--project", type=Path, required=True)
    analyze.add_argument("--base-audio-stream", type=int)

    speakers = subparsers.add_parser("speakers", help="List speakers in a project.")
    speakers.add_argument("project", type=Path)

    set_speaker = subparsers.add_parser("set-speaker", help="Rename or mute/unmute a speaker.")
    set_speaker.add_argument("project", type=Path)
    set_speaker.add_argument("--speaker", required=True)
    set_speaker.add_argument("--name")
    mute_group = set_speaker.add_mutually_exclusive_group()
    mute_group.add_argument("--mute", action="store_true")
    mute_group.add_argument("--unmute", action="store_true")

    export = subparsers.add_parser("export", help="Render a project to MKV.")
    export.add_argument("project", type=Path)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument(
        "--dry-run",
        action="store_true",
        help="Write subtitle file and print command only.",
    )

    subparsers.add_parser("gui", help="Launch the desktop GUI.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = load_settings()

    if args.command in {None, "gui"}:
        from audio_track_editor.gui.app import main as gui_main

        return gui_main([])

    if args.command == "doctor":
        print(format_checks(run_doctor(settings)))
        return 0

    if args.command == "cache-model":
        model = cache_diarization_model(settings, allow_download=args.allow_download)
        print(f"Diarization model ready: {model}")
        print(f"Model cache: {settings.model_cache_dir}")
        return 0

    if args.command == "analyze":
        project = Analyzer(settings).analyze(
            AnalyzeOptions(
                media_path=args.media,
                project_path=args.project,
                base_audio_stream=args.base_audio_stream,
            )
        )
        print(f"Project saved: {args.project}")
        print(f"Streams found: {len(project.streams)}")
        return 0

    if args.command == "speakers":
        project = load_project(args.project)
        for speaker in project.speakers:
            segments = [item for item in project.segments if item.speaker_id == speaker.speaker_id]
            duration = sum(item.duration for item in segments)
            muted = "muted" if speaker.muted else "active"
            label = speaker.label or speaker.speaker_id
            print(
                f"{speaker.speaker_id}\t{label}\t{muted}\t"
                f"{duration:.1f}s\t{len(segments)} segments"
            )
        return 0

    if args.command == "set-speaker":
        project = load_project(args.project)
        speaker = next((item for item in project.speakers if item.speaker_id == args.speaker), None)
        if speaker is None:
            parser.error(f"Speaker not found: {args.speaker}")
            return 2
        if args.name:
            speaker.label = args.name
        if args.mute:
            speaker.muted = True
        if args.unmute:
            speaker.muted = False
        save_project(project, args.project)
        label = speaker.label or speaker.speaker_id
        print(f"Updated {speaker.speaker_id}: {label}, muted={speaker.muted}")
        return 0

    if args.command == "export":
        result = render_project(args.project, args.output, settings=settings, dry_run=args.dry_run)
        print(f"Subtitle fallback track: {result.subtitle_file}")
        print(f"Muted audio: {result.muted_audio_file}")
        print(f"Muted regions: {len(result.muted_regions)}")
        if result.command:
            print("FFmpeg command:")
            print(" ".join(result.command))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
