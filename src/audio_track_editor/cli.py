from __future__ import annotations

import argparse
from pathlib import Path

from audio_track_editor.analysis import AnalyzeOptions, Analyzer
from audio_track_editor.config import load_settings
from audio_track_editor.doctor import format_checks, run_doctor
from audio_track_editor.renderer import render_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ate",
        description="Audio Track Editor development CLI.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("doctor", help="Check local tools, paths, and optional model deps.")

    analyze = subparsers.add_parser("analyze", help="Inspect media and create an analysis project.")
    analyze.add_argument("media", type=Path)
    analyze.add_argument("--project", type=Path, required=True)
    analyze.add_argument("--base-audio-stream", type=int)

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

    if args.command == "export":
        result = render_project(args.project, args.output, settings=settings, dry_run=args.dry_run)
        print(f"Subtitle fallback track: {result.subtitle_file}")
        print("FFmpeg command:")
        print(" ".join(result.command))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
