"""Dialog windows."""
from typing import Union, Callable

from PyQt6.QtWidgets import QDialog, QApplication, QMessageBox, QWidget
from PyQt6.QtCore import Qt, QThread, pyqtBoundSignal

from ..gui.settings_dialog import Ui_Dialog as SettingsDialog
from ..scanner.settings import AppSettings
from . import workers

PYQT_SLOT = Union[Callable[..., None], pyqtBoundSignal]


class CancellableDialog:
    """Show a dialog while doing a long task, allowing early cancellation."""

    def __init__(self, worker: workers.CancellableTaskWorker,
                 on_worker_finish: PYQT_SLOT, parent: QWidget | None) -> None:
        """Supply the worker object and a function to execute when done."""
        self.thread = QThread()
        self.worker = worker
        self.stop_event = worker.get_stop_event()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(on_worker_finish)
        self.cancelled = False
        self.parent = parent

    def _cancel(self) -> None:
        self.cancelled = True
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.stop_event.set()

    def launch(self, title: str, text: str) -> None:
        """Start the task and show the wait dialog box."""
        self.thread.start()
        self.box = QMessageBox(QMessageBox.Icon.NoIcon, title,
                               text, QMessageBox.StandardButton.Cancel,
                               parent=self.parent)
        self.box.rejected.connect(self._cancel)
        self.worker.finished.connect(self.box.close)  # type: ignore
        self.worker.finished.connect(QApplication.restoreOverrideCursor)
        self.box.finished.connect(self.box.deleteLater)
        self.box.show()


class SettingsWindow(QDialog, SettingsDialog):
    """Allow user to view and/or choose application settings via a GUI."""

    def __init__(self, existing_settings: AppSettings) -> None:
        """Input the existing settings to display in the dialog."""
        super().__init__()
        self.setupUi(self)
        self._set_existing_settings(existing_settings)

    def _set_existing_settings(self, existing_settings: AppSettings) -> None:
        """Set existing/default app settings in user input widgets."""
        self.checkBox_fetches.setChecked(existing_settings.fetch_remotes)
        self.lineEdit_IDE.setText(existing_settings.ide_command)
        self.lineEdit_terminal.setText(existing_settings.terminal_command)
        self.label_settings_location.setText(
            "Application settings will be saved in\n"
            + str(existing_settings.settings_directory))

    def get_inputs(self) -> tuple[bool, dict[str, str | bool]]:
        """Get app settings from user input widgets."""
        new_settings = {}
        if (self.exec_ok):
            new_settings['ide_command'] = self.lineEdit_IDE.text().strip()
            new_settings['terminal_command'] = self.lineEdit_terminal.text().strip()
            new_settings['fetch_remotes'] = self.checkBox_fetches.isChecked()
        return (self.exec_ok, new_settings)

    def exec(self) -> int:
        """Show the dialog and wait for the user to close it."""
        self.exec_ok = super().exec() == 1
        return 1 if self.exec_ok else 0
