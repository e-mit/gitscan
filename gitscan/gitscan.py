"""Main file for GUI app."""
import sys
from pathlib import Path
import pkgutil
import logging

from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt6.QtWidgets import QLineEdit, QInputDialog
from PyQt6.QtWidgets import QAbstractItemView, QAbstractScrollArea
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtGui import QTextCursor, QPixmap, QIcon

from .gui.main_window import Ui_MainWindow
from .model_view import model, delegate, dialogs, workers

APP_TITLE = "Gitscan"
APP_SUBTITLE = "a git repository status viewer"
APP_VERSION = "0.1.0"
PROJECT_GITHUB_URL = "https://github.com/e-mit/gitscan"
APP_ICON = "resources/G.png"
ROW_SCALE_FACTOR = 1.5
COLUMN_SCALE_FACTOR = 1.1


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window for application."""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(APP_TITLE + ":  " + APP_SUBTITLE)
        self._set_default_commit_text_format()
        self.model = model.TableModel(self)
        self.tableView.setModel(self.model)
        self._connect_signals()
        pix_map = QPixmap()
        pix_map.loadFromData(
            pkgutil.get_data(__name__, APP_ICON))  # type: ignore
        self.setWindowIcon(QIcon(pix_map))
        self.tableView.setItemDelegate(delegate.StyleDelegate(self.model,
                                                              self.tableView))

    def show(self) -> None:
        """Show the main window; this is non-blocking."""
        super().show()
        if self.model.settings.first_run:
            self._show_welcome_message()
            self._run_search_dialog()
        self.model.refresh_all_data()
        self._format_table()

    def _show_welcome_message(self) -> None:
        self.box = QMessageBox(QMessageBox.Icon.NoIcon, APP_TITLE,
                               "Welcome!", QMessageBox.StandardButton.Ok,
                               parent=self)
        self.box.rejected.connect(self.box.close)  # type: ignore
        self.box.finished.connect(self.box.deleteLater)
        self.box.exec()

    def _format_table(self) -> None:
        self.tableView.setShowGrid(False)
        self.tableView.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.tableView.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.splitter.setSizes([150, 100])
        self.tableView.horizontalHeader().setHighlightSections(False)
        self.tableView.horizontalHeader().setStyleSheet(
                                    "QHeaderView {"
                                    "background-color: lightgrey;}")
        self._update_view()

    def _resize_rows_columns(self):
        self.tableView.verticalHeader().setMinimumSectionSize(0)
        self.tableView.resizeRowsToContents()
        v_size = self.tableView.verticalHeader().sectionSize(0)
        self.tableView.verticalHeader().setMinimumSectionSize(
            int(v_size * ROW_SCALE_FACTOR))
        self.tableView.horizontalHeader().setMinimumSectionSize(0)
        self.tableView.resizeColumnsToContents()
        for col in range(self.model.columnCount(None)):
            self.tableView.horizontalHeader().resizeSection(
                col,
                int(self.tableView.horizontalHeader().sectionSize(col)
                    * COLUMN_SCALE_FACTOR))
        self.tableView.horizontalHeader().setMinimumSectionSize(
            self.tableView.horizontalHeader().sectionSize(3))

    def _set_default_commit_text_format(self) -> None:
        """Format the lower display pane appearance."""
        font = QFont()
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFamily('monospace')
        self.plainTextEdit.setFont(font)
        self.plainTextEdit.setStyleSheet("QPlainTextEdit {"
                                         "background-color: black;"
                                         "color : white;}")

    def _update_view(self):
        self._resize_rows_columns()
        self._row_selection_shading()
        self._display_commit_text()
        self._resize_rows_columns()

    def _update_selection(self):
        self._row_selection_shading()
        self._display_commit_text()

    def _row_selection_shading(self):
        """Change selection colour when selection changes."""
        index = self.tableView.selectionModel().currentIndex()
        c = self.model.row_shading_colour(index)
        colour = f"{c.red()}, {c.green()}, {c.blue()}, {c.alphaF():.2f}"
        self.tableView.setStyleSheet("QTableView::item:selected {"
                                     "border-width: 4px 0 4px 0;"
                                     "border-style: solid;"
                                     "border-color: black;}"
                                     "QTableView {"
                                     "selection-color: black;"
                                     "selection-background-color: rgba("
                                     f"{colour});}}")

    def _display_commit_text(self) -> None:
        """Get and display the commit text in lower pane."""
        index = self.tableView.selectionModel().currentIndex()
        commit_html_text = self.model.get_commit_html(index)
        self.plainTextEdit.clear()
        self.plainTextEdit.appendHtml(commit_html_text)
        self.plainTextEdit.moveCursor(QTextCursor.MoveOperation.Start)
        self.plainTextEdit.ensureCursorVisible()

    def _connect_signals(self) -> None:
        """Connect all signals and slots."""
        self.tableView.selectionModel().selectionChanged.connect(
            self._update_selection)
        self.tableView.clicked.connect(self.model.table_clicked)
        self.actionExit.triggered.connect(self.close)  # type: ignore
        self.actionVisit_GitHub.triggered.connect(self._visit_github)
        self.actionAbout.triggered.connect(self._help_about)
        self.actionRefresh_all.triggered.connect(self.model.refresh_all_data)
        self.actionRefresh_all.setShortcut("F5")
        self.actionSearch_for_repositories.triggered.connect(
            self._run_search_dialog)
        self.actionSettings.triggered.connect(self._run_settings_dialog)
        self.model.dataChanged.connect(self._update_view)
        self.model.layoutChanged.connect(self._update_view)

    def _visit_github(self) -> None:
        QDesktopServices.openUrl(QUrl(PROJECT_GITHUB_URL))

    def _help_about(self) -> None:
        QMessageBox.about(
            self,
            "About",
            f"<p>{APP_TITLE}</p>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>{APP_SUBTITLE.capitalize()}</p>"
            "<p>Made with PyQt and Qt Designer</p>"
            f"<a href='{PROJECT_GITHUB_URL}'>View the code on GitHub</a>"
        )

    def _run_search_dialog(self) -> None:
        """Dialog to get user choice of root directory for repo search."""
        (search_path_str, ok) = QInputDialog.getText(
            self, "Search for local repositories",
            ("Choose the root directory. All directories\n"
             "below this will be searched (this may be slow)."),
            QLineEdit.EchoMode.Normal, self.model.settings.search_path,
            Qt.WindowType.Dialog,
            Qt.InputMethodHint.ImhNone)
        if ok and Path(search_path_str).is_dir():
            self.model.settings.set_search_path(search_path_str)
            self._launch_search(search_path_str)

    def _search_complete(self, repo_list):
        if not self.cd.cancelled:
            self.model.repo_data = []
            self.model.settings.set_repo_list(repo_list)
            self.model.refresh_all_data()

    def _launch_search(self, search_path: str):
        """Show a dialog while doing repo search, allowing cancellation."""
        self.cd = dialogs.CancellableDialog(
                    workers.SearchWorker(search_path,
                                         self.model.settings.exclude_dirs),
                    self._search_complete, self)
        self.cd.launch("Search", "Search in progress...")

    def _run_settings_dialog(self) -> None:
        """Launch dialog to get/update/display user-selected settings."""
        settings_ui = dialogs.SettingsWindow(self.model.settings)
        settings_ui.exec()
        (ok, new_settings) = settings_ui.get_inputs()
        if ok:
            self.model.settings.set_preferences(new_settings)
        self._resize_rows_columns()


def setup_logging(log_level: str):
    """Format the modular logger."""
    if log_level not in logging._nameToLevel.keys():
        raise ValueError(f"'{log_level}' is not a valid log level. "
                         "Use one of: "
                         + ', '.join(logging._nameToLevel.keys()))
    logger = logging.getLogger(__package__)
    logger.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(("%(asctime)s %(levelname)s : "
                                   "line %(lineno)d in %(module)s : "
                                   "%(message)s"), datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def main(log_level: str) -> None:
    """Application entry point."""
    setup_logging(log_level)
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
