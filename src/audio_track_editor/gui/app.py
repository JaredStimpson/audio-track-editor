from __future__ import annotations

import sys
from pathlib import Path

from audio_track_editor.analysis import AnalyzeOptions, Analyzer
from audio_track_editor.config import load_settings
from audio_track_editor.doctor import format_checks, run_doctor
from audio_track_editor.media import probe_media
from audio_track_editor.preview import ensure_segment_preview
from audio_track_editor.renderer import render_project
from audio_track_editor.schemas import Project, load_project, save_project


def _missing_pyside() -> int:
    print("PySide6 is not installed. Run scripts/setup.ps1 or install audio-track-editor[gui].")
    return 1


try:
    from PySide6 import QtCore, QtMultimedia, QtWidgets
except ImportError:  # pragma: no cover - exercised by users without GUI deps
    QtCore = None
    QtMultimedia = None
    QtWidgets = None


if QtWidgets is not None:

    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.settings = load_settings()
            self.current_project: Project | None = None
            self.current_project_path: Path | None = None
            self.player = None
            self.audio_output = None
            if QtMultimedia is not None:
                self.player = QtMultimedia.QMediaPlayer(self)
                self.audio_output = QtMultimedia.QAudioOutput(self)
                self.player.setAudioOutput(self.audio_output)
            self.setWindowTitle("Audio Track Editor")
            self.resize(1240, 780)
            self._build_ui()
            self._refresh_status()

        def _build_ui(self) -> None:
            central = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(central)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(10)

            header = QtWidgets.QHBoxLayout()
            self.media_path = QtWidgets.QLineEdit()
            self.media_path.setPlaceholderText(str(self.settings.media_dir))
            browse = self._tool_button(
                "Browse Media",
                QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon,
            )
            browse.clicked.connect(self._browse_media)
            doctor = self._tool_button(
                "Doctor",
                QtWidgets.QStyle.StandardPixmap.SP_MessageBoxInformation,
            )
            doctor.clicked.connect(self._show_doctor)
            header.addWidget(self.media_path, 1)
            header.addWidget(browse)
            header.addWidget(doctor)

            splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
            splitter.addWidget(self._build_left_panel())
            splitter.addWidget(self._build_timeline_panel())
            splitter.addWidget(self._build_right_panel())
            splitter.setSizes([280, 680, 360])

            layout.addLayout(header)
            layout.addWidget(splitter, 1)
            self.status = QtWidgets.QStatusBar()
            self.setStatusBar(self.status)
            self.progress = QtWidgets.QProgressBar()
            self.progress.setMaximumWidth(170)
            self.progress.setVisible(False)
            self.status.addPermanentWidget(self.progress)
            self.setCentralWidget(central)

        def _tool_button(
            self,
            label: str,
            icon: QtWidgets.QStyle.StandardPixmap,
        ) -> QtWidgets.QPushButton:
            button = QtWidgets.QPushButton(label)
            button.setIcon(self.style().standardIcon(icon))
            return button

        def _build_left_panel(self) -> QtWidgets.QWidget:
            panel = QtWidgets.QGroupBox("Streams")
            layout = QtWidgets.QVBoxLayout(panel)
            self.audio_stream = QtWidgets.QComboBox()
            layout.addWidget(self.audio_stream)
            self.streams = QtWidgets.QListWidget()
            self.streams.addItem("Import media to inspect streams")
            layout.addWidget(self.streams, 1)
            self.project_path = QtWidgets.QLineEdit()
            self.project_path.setPlaceholderText("Project path")
            layout.addWidget(self.project_path)
            analyze = self._tool_button("Analyze", QtWidgets.QStyle.StandardPixmap.SP_MediaPlay)
            analyze.clicked.connect(self._analyze_media)
            layout.addWidget(analyze)
            return panel

        def _build_timeline_panel(self) -> QtWidgets.QWidget:
            panel = QtWidgets.QGroupBox("Detected Voice Sections")
            layout = QtWidgets.QVBoxLayout(panel)
            self.timeline = QtWidgets.QTableWidget(0, 9)
            self.timeline.setHorizontalHeaderLabels(
                [
                    "Start",
                    "End",
                    "Speaker",
                    "Name",
                    "Target",
                    "Confidence",
                    "Subtitle",
                    "Overlap",
                    "Notes",
                ]
            )
            self.timeline.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            self.timeline.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
            self.timeline.horizontalHeader().setStretchLastSection(True)
            layout.addWidget(self.timeline, 1)
            controls = QtWidgets.QHBoxLayout()
            play = self._tool_button("Play Section", QtWidgets.QStyle.StandardPixmap.SP_MediaPlay)
            play.clicked.connect(self._play_selected_segment)
            stop = self._tool_button("Stop", QtWidgets.QStyle.StandardPixmap.SP_MediaStop)
            stop.clicked.connect(self._stop_playback)
            controls.addWidget(play)
            controls.addWidget(stop)
            controls.addStretch(1)
            layout.addLayout(controls)
            return panel

        def _build_right_panel(self) -> QtWidgets.QWidget:
            panel = QtWidgets.QGroupBox("Profiles And Export")
            layout = QtWidgets.QVBoxLayout(panel)
            self.speakers = QtWidgets.QTableWidget(0, 6)
            self.speakers.setHorizontalHeaderLabels(
                ["Speaker", "Name", "Mute", "Time", "Segments", "Subtitles"]
            )
            self.speakers.horizontalHeader().setStretchLastSection(True)
            layout.addWidget(self.speakers, 1)
            save_labels = self._tool_button(
                "Save Speaker Names",
                QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton,
            )
            save_labels.clicked.connect(self._save_speaker_labels)
            layout.addWidget(save_labels)

            self.doctor_summary = QtWidgets.QPlainTextEdit()
            self.doctor_summary.setReadOnly(True)
            self.doctor_summary.setMaximumHeight(150)
            layout.addWidget(self.doctor_summary)

            self.output_path = QtWidgets.QLineEdit(str(self.settings.output_dir))
            layout.addWidget(self.output_path)
            self.dry_run = QtWidgets.QCheckBox("Dry run")
            self.dry_run.setChecked(False)
            layout.addWidget(self.dry_run)
            export = self._tool_button(
                "Export MKV",
                QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton,
            )
            export.clicked.connect(self._export_project)
            layout.addWidget(export)
            return panel

        def _browse_media(self) -> None:
            selected, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open media",
                str(self.settings.media_dir),
                "Video files (*.mkv *.mp4);;All files (*.*)",
            )
            if selected:
                self.media_path.setText(selected)
                stem = Path(selected).stem
                project = self.settings.output_dir / f"{stem}.ateproj.json"
                output = self.settings.output_dir / f"{stem}-mixed.mkv"
                self.project_path.setText(str(project))
                self.output_path.setText(str(output))
                self.streams.clear()
                self.streams.addItem(f"Selected: {Path(selected).name}")
                self._probe_selected_media(Path(selected))
                self.streams.addItem("Choose one audio track, then click Analyze.")
                self.status.showMessage("Media selected")

        def _probe_selected_media(self, media_path: Path) -> None:
            self.audio_stream.clear()
            try:
                streams = probe_media(media_path, self.settings.ffprobe_bin)
            except Exception as exc:  # pragma: no cover - GUI protection
                self.streams.addItem(f"ffprobe failed: {exc}")
                return

            for stream in streams:
                title = f" - {stream.title}" if stream.title else ""
                lang = f" [{stream.language}]" if stream.language else ""
                text = (
                    f"#{stream.index} {stream.type} "
                    f"{stream.codec_name or 'unknown'}{lang}{title}"
                )
                self.streams.addItem(text)
                if stream.type == "audio":
                    self.audio_stream.addItem(text, stream.index)

        def _show_doctor(self) -> None:
            self._refresh_status()
            QtWidgets.QMessageBox.information(
                self,
                "Environment Doctor",
                format_checks(run_doctor(self.settings)),
            )

        def _refresh_status(self) -> None:
            checks = run_doctor(self.settings)
            warnings = sum(1 for check in checks if not check.ok)
            self.doctor_summary.setPlainText(format_checks(checks))
            self.status.showMessage(f"Ready; {warnings} setup warning(s)")

        def _set_busy(self, busy: bool, message: str) -> None:
            if busy:
                self.progress.setRange(0, 0)
                self.progress.setVisible(True)
            else:
                self.progress.setVisible(False)
                self.progress.setRange(0, 1)
            self.status.showMessage(message)
            QtWidgets.QApplication.processEvents()

        def _analyze_media(self) -> None:
            media_text = self.media_path.text().strip()
            project_text = self.project_path.text().strip()
            if not media_text:
                QtWidgets.QMessageBox.warning(self, "Missing media", "Choose an MKV or MP4 first.")
                return
            if not project_text:
                project_text = str(
                    self.settings.output_dir / f"{Path(media_text).stem}.ateproj.json"
                )
                self.project_path.setText(project_text)

            try:
                self._set_busy(True, "Analyzing selected audio track...")
                base_stream = self.audio_stream.currentData()
                project = Analyzer(self.settings).analyze(
                    AnalyzeOptions(
                        media_path=Path(media_text),
                        project_path=Path(project_text),
                        base_audio_stream=int(base_stream) if base_stream is not None else None,
                    )
                )
            except Exception as exc:  # pragma: no cover - GUI protection
                QtWidgets.QMessageBox.critical(self, "Analyze failed", str(exc))
                return
            finally:
                self._set_busy(False, "Analyze finished")

            self.current_project = project
            self.current_project_path = Path(project_text)
            self._load_project(project)
            self.status.showMessage(f"Project saved: {project_text}")
            if not project.analysis_model and project.segments:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Voice Detection Fallback",
                    project.segments[0].notes or "Voice detection did not produce model output.",
                )

        def _load_project(self, project: Project) -> None:
            self.streams.clear()
            model = project.analysis_model or "metadata-only fallback"
            device = project.analysis_device or "unknown"
            self.streams.addItem(f"Analysis: {model} ({device})")
            for stream in project.streams:
                title = f" - {stream.title}" if stream.title else ""
                lang = f" [{stream.language}]" if stream.language else ""
                self.streams.addItem(
                    f"#{stream.index} {stream.type} {stream.codec_name or 'unknown'}{lang}{title}"
                )

            speaker_labels = {
                speaker.speaker_id: speaker.label or speaker.speaker_id
                for speaker in project.speakers
            }
            speaker_segments = {
                speaker.speaker_id: [
                    segment
                    for segment in project.segments
                    if segment.speaker_id == speaker.speaker_id
                ]
                for speaker in project.speakers
            }
            self.speakers.setRowCount(len(project.speakers))
            for row, speaker in enumerate(project.speakers):
                segments = speaker_segments.get(speaker.speaker_id, [])
                total = sum(segment.duration for segment in segments)
                values = [
                    speaker.speaker_id,
                    speaker.label or speaker.speaker_id,
                    "yes" if speaker.muted else "no",
                    f"{total:.1f}s",
                    str(len(segments)),
                    speaker.subtitles,
                ]
                for column, value in enumerate(values):
                    item = QtWidgets.QTableWidgetItem(value)
                    if column == 0:
                        item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    if column in {3, 4}:
                        item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    if column == 2:
                        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(
                            QtCore.Qt.CheckState.Checked
                            if speaker.muted
                            else QtCore.Qt.CheckState.Unchecked
                        )
                    self.speakers.setItem(row, column, item)

            self.timeline.setRowCount(len(project.segments))
            for row, segment in enumerate(project.segments):
                values = [
                    f"{segment.start:.3f}",
                    f"{segment.end:.3f}",
                    segment.speaker_id,
                    speaker_labels.get(segment.speaker_id, segment.speaker_id),
                    "" if segment.target_audio_stream is None else str(segment.target_audio_stream),
                    f"{segment.confidence:.2f}",
                    "yes" if segment.subtitle_required else "no",
                    "yes" if segment.overlap else "no",
                    segment.notes,
                ]
                for column, value in enumerate(values):
                    self.timeline.setItem(row, column, QtWidgets.QTableWidgetItem(value))

        def _export_project(self) -> None:
            project_text = self.project_path.text().strip()
            output_text = self.output_path.text().strip()
            if not project_text:
                QtWidgets.QMessageBox.warning(self, "Missing project", "Analyze media first.")
                return
            if not output_text:
                output_text = str(self.settings.output_dir / "audio-track-editor-export.mkv")
                self.output_path.setText(output_text)

            try:
                self._set_busy(True, "Rendering muted audio/export...")
                if self.current_project_path != Path(project_text):
                    self.current_project = load_project(Path(project_text))
                    self.current_project_path = Path(project_text)
                result = render_project(
                    Path(project_text),
                    Path(output_text),
                    settings=self.settings,
                    dry_run=self.dry_run.isChecked(),
                )
            except Exception as exc:  # pragma: no cover - GUI protection
                QtWidgets.QMessageBox.critical(self, "Export failed", str(exc))
                return
            finally:
                self._set_busy(False, "Export finished")

            mode = "Dry run planned" if self.dry_run.isChecked() else "Export complete"
            self.status.showMessage(f"{mode}: {result.output_file}")
            QtWidgets.QMessageBox.information(
                self,
                mode,
                (
                    f"{mode}\n\nSubtitle track:\n{result.subtitle_file}"
                    f"\n\nMuted audio:\n{result.muted_audio_file}"
                    f"\n\nMuted regions: {len(result.muted_regions)}"
                    f"\n\nOutput:\n{result.output_file}"
                ),
            )

        def _selected_segment(self):
            if self.current_project is None:
                return None
            row = self.timeline.currentRow()
            if row < 0 or row >= len(self.current_project.segments):
                return None
            return self.current_project.segments[row]

        def _play_selected_segment(self) -> None:
            if self.player is None:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Playback unavailable",
                    "PySide6 multimedia support is not available in this environment.",
                )
                return
            if self.current_project is None or self.current_project_path is None:
                QtWidgets.QMessageBox.warning(self, "No project", "Analyze media first.")
                return
            segment = self._selected_segment()
            if segment is None:
                QtWidgets.QMessageBox.warning(
                    self,
                    "No section",
                    "Select a detected voice section.",
                )
                return

            try:
                preview = ensure_segment_preview(
                    self.current_project,
                    segment,
                    self.current_project_path,
                    self.settings,
                )
            except Exception as exc:  # pragma: no cover - GUI protection
                QtWidgets.QMessageBox.critical(self, "Preview failed", str(exc))
                return

            self.player.setSource(QtCore.QUrl.fromLocalFile(str(preview)))
            self.player.play()
            self.status.showMessage(f"Playing {segment.segment_id} ({segment.speaker_id})")

        def _stop_playback(self) -> None:
            if self.player is not None:
                self.player.stop()

        def _save_speaker_labels(self) -> None:
            if self.current_project is None or self.current_project_path is None:
                QtWidgets.QMessageBox.warning(self, "No project", "Analyze media first.")
                return

            for row, speaker in enumerate(self.current_project.speakers):
                name_item = self.speakers.item(row, 1)
                mute_item = self.speakers.item(row, 2)
                subtitles_item = self.speakers.item(row, 5)

                speaker.label = name_item.text().strip() if name_item else speaker.speaker_id
                speaker.muted = (
                    mute_item.checkState() == QtCore.Qt.CheckState.Checked if mute_item else False
                )
                speaker.subtitles = subtitles_item.text().strip() if subtitles_item else "auto"

            save_project(self.current_project, self.current_project_path)
            self._load_project(self.current_project)
            self.status.showMessage("Speaker names and mute choices saved")


def main(argv: list[str] | None = None) -> int:
    if QtWidgets is None:
        return _missing_pyside()

    app = QtWidgets.QApplication(argv or sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
