from __future__ import annotations

import sys
from pathlib import Path

from audio_track_editor.config import load_settings
from audio_track_editor.doctor import format_checks, run_doctor


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
            self.setWindowTitle("Audio Track Editor")
            self.resize(1180, 760)
            self._build_ui()

        def _build_ui(self) -> None:
            central = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(central)

            header = QtWidgets.QHBoxLayout()
            self.media_path = QtWidgets.QLineEdit()
            self.media_path.setPlaceholderText(str(self.settings.media_dir))
            browse = QtWidgets.QPushButton("Browse Media")
            browse.clicked.connect(self._browse_media)
            doctor = QtWidgets.QPushButton("Doctor")
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
            self.setCentralWidget(central)

        def _build_left_panel(self) -> QtWidgets.QWidget:
            panel = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(panel)
            layout.addWidget(QtWidgets.QLabel("Streams"))
            self.streams = QtWidgets.QListWidget()
            self.streams.addItem("Import media to inspect streams")
            layout.addWidget(self.streams, 1)
            analyze = QtWidgets.QPushButton("Analyze")
            analyze.clicked.connect(self._not_ready)
            layout.addWidget(analyze)
            return panel

        def _build_timeline_panel(self) -> QtWidgets.QWidget:
            panel = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(panel)
            layout.addWidget(QtWidgets.QLabel("Speaker Timeline"))
            self.timeline = QtWidgets.QTableWidget(0, 6)
            self.timeline.setHorizontalHeaderLabels(
                ["Start", "End", "Speaker", "Target Track", "Confidence", "Subtitle"]
            )
            self.timeline.horizontalHeader().setStretchLastSection(True)
            layout.addWidget(self.timeline, 1)
            return panel

        def _build_right_panel(self) -> QtWidgets.QWidget:
            panel = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(panel)
            layout.addWidget(QtWidgets.QLabel("Profiles"))
            self.profile_notes = QtWidgets.QPlainTextEdit()
            self.profile_notes.setPlaceholderText(
                "Speaker labels and language preferences will be saved per show profile."
            )
            layout.addWidget(self.profile_notes, 1)

            layout.addWidget(QtWidgets.QLabel("Export"))
            self.output_path = QtWidgets.QLineEdit(str(self.settings.output_dir))
            layout.addWidget(self.output_path)
            export = QtWidgets.QPushButton("Export MKV")
            export.clicked.connect(self._not_ready)
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
                self.streams.clear()
                self.streams.addItem(f"Selected: {Path(selected).name}")
                self.streams.addItem("Run ate analyze to create a project file.")

        def _show_doctor(self) -> None:
            QtWidgets.QMessageBox.information(
                self,
                "Environment Doctor",
                format_checks(run_doctor(self.settings)),
            )

        def _not_ready(self) -> None:
            QtWidgets.QMessageBox.information(
                self,
                "Coming next",
                "The UI shell is ready. Use the ate CLI for scaffolded analyze/export commands.",
            )


def main(argv: list[str] | None = None) -> int:
    if QtWidgets is None:
        return _missing_pyside()

    app = QtWidgets.QApplication(argv or sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
