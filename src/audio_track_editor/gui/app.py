from __future__ import annotations

import sys
from pathlib import Path

from audio_track_editor.analysis import AnalyzeOptions, Analyzer
from audio_track_editor.config import load_settings
from audio_track_editor.doctor import format_checks, run_doctor
from audio_track_editor.renderer import render_project
from audio_track_editor.schemas import Project, load_project


def _missing_pyside() -> int:
    print("PySide6 is not installed. Run scripts/setup.ps1 or install audio-track-editor[gui].")
    return 1


try:
    from PySide6 import QtCore, QtWidgets
except ImportError:  # pragma: no cover - exercised by users without GUI deps
    QtCore = None
    QtWidgets = None


if QtWidgets is not None:

    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.settings = load_settings()
            self.current_project: Project | None = None
            self.current_project_path: Path | None = None
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
            splitter.setSizes([260, 640, 280])

            layout.addLayout(header)
            layout.addWidget(splitter, 1)
            self.status = QtWidgets.QStatusBar()
            self.setStatusBar(self.status)
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
            panel = QtWidgets.QGroupBox("Speaker Timeline")
            layout = QtWidgets.QVBoxLayout(panel)
            self.timeline = QtWidgets.QTableWidget(0, 6)
            self.timeline.setHorizontalHeaderLabels(
                ["Start", "End", "Speaker", "Target Track", "Confidence", "Subtitle"]
            )
            self.timeline.horizontalHeader().setStretchLastSection(True)
            layout.addWidget(self.timeline, 1)
            return panel

        def _build_right_panel(self) -> QtWidgets.QWidget:
            panel = QtWidgets.QGroupBox("Profiles And Export")
            layout = QtWidgets.QVBoxLayout(panel)
            self.profile_notes = QtWidgets.QPlainTextEdit()
            self.profile_notes.setPlaceholderText(
                "Speaker labels and language preferences will be saved per show profile."
            )
            layout.addWidget(self.profile_notes, 1)

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
                self.streams.addItem("Click Analyze to inspect streams and create a project.")
                self.status.showMessage("Media selected")

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
                project = Analyzer(self.settings).analyze(
                    AnalyzeOptions(media_path=Path(media_text), project_path=Path(project_text))
                )
            except Exception as exc:  # pragma: no cover - GUI protection
                QtWidgets.QMessageBox.critical(self, "Analyze failed", str(exc))
                return

            self.current_project = project
            self.current_project_path = Path(project_text)
            self._load_project(project)
            self.status.showMessage(f"Project saved: {project_text}")

        def _load_project(self, project: Project) -> None:
            self.streams.clear()
            for stream in project.streams:
                title = f" - {stream.title}" if stream.title else ""
                lang = f" [{stream.language}]" if stream.language else ""
                self.streams.addItem(
                    f"#{stream.index} {stream.type} {stream.codec_name or 'unknown'}{lang}{title}"
                )

            self.timeline.setRowCount(len(project.segments))
            for row, segment in enumerate(project.segments):
                values = [
                    f"{segment.start:.3f}",
                    f"{segment.end:.3f}",
                    segment.speaker_id,
                    "" if segment.target_audio_stream is None else str(segment.target_audio_stream),
                    f"{segment.confidence:.2f}",
                    "yes" if segment.subtitle_required else "no",
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

            mode = "Dry run planned" if self.dry_run.isChecked() else "Export complete"
            self.status.showMessage(f"{mode}: {result.output_file}")
            QtWidgets.QMessageBox.information(
                self,
                mode,
                (
                    f"{mode}\n\nSubtitle track:\n{result.subtitle_file}"
                    f"\n\nOutput:\n{result.output_file}"
                ),
            )


def main(argv: list[str] | None = None) -> int:
    if QtWidgets is None:
        return _missing_pyside()

    app = QtWidgets.QApplication(argv or sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
