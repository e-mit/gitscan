"""Main file for GUI app."""
import sys
from typing import Any, Union, Callable
from pathlib import Path
import threading
import multiprocessing
import multiprocessing.synchronize

import arrow

from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PyQt6.QtWidgets import QDialog, QLineEdit, QInputDialog
from PyQt6.QtWidgets import QAbstractItemView, QAbstractScrollArea
from PyQt6.QtCore import Qt, QModelIndex, QProcess, QAbstractTableModel
from PyQt6.QtCore import QUrl, pyqtSignal, QObject, QThread, pyqtBoundSignal
from PyQt6.QtGui import QFont, QColor, QIcon, QDesktopServices, QPainter
from PyQt6.QtGui import QPen, QTextCursor

from gui.test_table import Ui_MainWindow
from gui.settings_dialog import Ui_Dialog
from scanner import search, read, settings
from scanner.settings import AppSettings

PYQT_SLOT = Union[Callable[..., None], pyqtBoundSignal]
EVENT_TYPE = Union[threading.Event, multiprocessing.synchronize.Event]

APP_TITLE = "Gitscan"
APP_SUBTITLE = "a git repository status viewer"
APP_VERSION = "0.1.0"
PROJECT_GITHUB_URL = "https://github.com/e-mit/gitscan"
VIEW_COMMIT_COUNT = 3  # Show (at most) this many commits in the lower pane
OPEN_FOLDER_COLUMN = 15
OPEN_DIFFTOOL_COLUMN = OPEN_FOLDER_COLUMN + 1
OPEN_TERMINAL_COLUMN = OPEN_FOLDER_COLUMN + 2
OPEN_IDE_COLUMN = OPEN_FOLDER_COLUMN + 3
REFRESH_COLUMN = OPEN_FOLDER_COLUMN + 4
WARNING_COLUMN = OPEN_FOLDER_COLUMN + 5
TOTAL_COLUMNS = WARNING_COLUMN + 1
OPEN_FOLDER_ICON = "resources/folder.svg"
OPEN_DIFFTOOL_ICON = "resources/diff.svg"
OPEN_TERMINAL_ICON = "resources/terminal.svg"
OPEN_IDE_ICON = "resources/window.svg"
WARNING_ICON = "resources/warning.svg"
REFRESH_ICON = "resources/refresh.svg"
ICON_SCALE_FACTOR = 0.7
ROW_SCALE_FACTOR = 1.5
COLUMN_SCALE_FACTOR = 1.1
ROW_SHADING_ALPHA = 100


class StyleDelegate(QStyledItemDelegate):
    """Custom delegate to insert icons with H and V centering."""

    def __init__(self, model, *args, **kwargs):
        self.model = model
        super().__init__(*args, **kwargs)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem,
              index: QModelIndex) -> None:
        super().paint(painter, option, index)
        icon = None
        if (index.column() == OPEN_FOLDER_COLUMN):
            icon = QIcon(OPEN_FOLDER_ICON)
        elif (index.column() == OPEN_DIFFTOOL_COLUMN):
            if ((not self.model.repo_data[index.row()]['bare']) and
                (self.model.repo_data[index.row()]['working_tree_changes'] or
                 self.model.repo_data[index.row()]['commit_count'] > 1)):
                icon = QIcon(OPEN_DIFFTOOL_ICON)
        elif (index.column() == OPEN_TERMINAL_COLUMN):
            icon = QIcon(OPEN_TERMINAL_ICON)
        elif (index.column() == OPEN_IDE_COLUMN):
            icon = QIcon(OPEN_IDE_ICON)
        elif (index.column() == REFRESH_COLUMN):
            icon = QIcon(REFRESH_ICON)
        elif (index.column() == WARNING_COLUMN):
            if self.model.repo_data[index.row()]['warning'] is not None:
                icon = QIcon(WARNING_ICON)

        if icon is not None:
            size = option.rect.size()
            size.setHeight(int(size.height()*ICON_SCALE_FACTOR))
            size.setWidth(int(size.width()*ICON_SCALE_FACTOR))
            option.widget.style(
                ).drawItemPixmap(painter, option.rect,
                                 Qt.AlignmentFlag.AlignCenter,
                                 icon.pixmap(size))

        oldPen = painter.pen()
        painter.setPen(QPen(QColor(200, 200, 200, 100), 1))
        painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
        painter.drawLine(option.rect.topLeft(), option.rect.bottomLeft())
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.setPen(oldPen)


class TableModel(QAbstractTableModel):
    """The model part of Qt model-view, for containing data."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo_data = []

    def load_and_refresh_saved_data(self):
        self.settings = settings.AppSettings()
        self.refresh_all_data()

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> Any:
        """Part of the Qt model interface."""
        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_data(index, Qt.ItemDataRole.DisplayRole)
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._display_data(index, Qt.ItemDataRole.ToolTipRole)
        elif role == Qt.ItemDataRole.BackgroundRole:
            return self.row_shading_colour(index)
        elif (role == Qt.ItemDataRole.TextAlignmentRole and
              ((index.column() >= OPEN_FOLDER_COLUMN and
                index.column() <= WARNING_COLUMN) or
               (index.column() >= 2 and
                index.column() <= 12))):
            return Qt.AlignmentFlag.AlignCenter

    @staticmethod
    def _add_s_if_plural(count: int) -> str:
        if count == 1:
            return ""
        else:
            return "s"

    def valid_index(self, index: QModelIndex) -> bool:
        """Determine if index is out of table range."""
        if index.row() < 0 or index.row() >= self.rowCount(None):
            return False
        if index.column() < 0 or index.column() >= self.columnCount(None):
            return False
        return True

    def _display_data(self, index: QModelIndex,
                      role: Qt.ItemDataRole) -> str:
        data = " "
        tooltip = ""
        if (index.column() == 0):
            data = str(self.repo_data[index.row()]['containing_dir'])
            tooltip = "Parent directory"
        elif (index.column() == 1):
            data = self.repo_data[index.row()]['name']
            tooltip = "Repository name"
        elif (index.column() == 2):
            untracked_count = self.repo_data[index.row()]['untracked_count']
            if untracked_count > 0:
                data = "U"
                tooltip = (str(untracked_count) + " untracked file"
                           + self._add_s_if_plural(untracked_count))
        elif (index.column() == 3):
            if self.repo_data[index.row()]['working_tree_changes']:
                data = "M"
                tooltip = "Modified working tree"
        elif (index.column() == 4):
            if self.repo_data[index.row()]['bare']:
                data = "B"
                tooltip = "Bare/mirror repository"
        elif (index.column() == 5):
            if self.repo_data[index.row()]['stash']:
                data = "S"
                tooltip = "At least one stash"
        elif (index.column() == 6):
            if self.repo_data[index.row()]['index_changes']:
                data = "I"
                tooltip = "Uncommitted index change(s)"
        elif (index.column() == 7):
            count = self.repo_data[index.row()]['ahead_count']
            if count > 0:
                data = "▲"
                tooltip = ("Local branches are ahead of remotes by "
                           f"{count} commit" + self._add_s_if_plural(count))
        elif (index.column() == 8):
            count = self.repo_data[index.row()]['behind_count']
            if count > 0:
                data = "▼"
                tooltip = ("Local branches are behind remotes by "
                           f"{count} commit" + self._add_s_if_plural(count))
        elif (index.column() == 9):
            tag_count = self.repo_data[index.row()]['tag_count']
            if tag_count > 0:
                data = "T"
                tooltip = (str(tag_count) + " tag"
                           + self._add_s_if_plural(tag_count))
        elif (index.column() == 10):
            submodule_count = len(self.repo_data[index.row()]['submodule_names'])
            if submodule_count > 0:
                data = str(submodule_count)
                tooltip = (str(submodule_count) + " submodule"
                           + self._add_s_if_plural(submodule_count) + ": "
                    + ", ".join(self.repo_data[index.row()]['submodule_names']))
        elif (index.column() == 11):
            remote_count = self.repo_data[index.row()]['remote_count']
            if remote_count > 0:
                tooltip = (str(remote_count) + " remote"
                           + self._add_s_if_plural(remote_count) + ": "
                           + ", ".join(self.repo_data[index.row()]['remote_names']))
                data = str(remote_count)
        elif (index.column() == 12):
            branch_count = self.repo_data[index.row()]['branch_count']
            data = str(branch_count)
            if branch_count == 0:
                tooltip = "No local branches"
            else:
                tooltip = str(branch_count) + " local "
                tooltip += "branch" if (branch_count == 1) else "branches"
                tooltip += (": "
                    + ", ".join(self.repo_data[index.row()]['branch_names']))
        elif (index.column() == 13):
            data = self.repo_data[index.row()]['branch_name']
            if self.repo_data[index.row()]['detached_head']:
                tooltip = "Detached HEAD state"
            elif self.repo_data[index.row()]['branch_count'] == 0:
                tooltip = "No local branches"
            else:
                tooltip = "Active branch"
        elif (index.column() == 14):
            last_commit_datetime = self.repo_data[index.row()]['last_commit_datetime']
            if last_commit_datetime is None:
                data = "-"
            else:
                data = arrow.get(last_commit_datetime).humanize().capitalize()
            tooltip = "Last commit on local branches"
        elif (index.column() == OPEN_FOLDER_COLUMN):
            tooltip = "Open directory"
        elif (index.column() == OPEN_DIFFTOOL_COLUMN):
            if self.repo_data[index.row()]['working_tree_changes']:
                tooltip = "View working tree in difftool"
            elif (self.repo_data[index.row()]['bare'] or
                  self.repo_data[index.row()]['commit_count'] > 1):
                tooltip = "View last commit in difftool"
        elif (index.column() == OPEN_TERMINAL_COLUMN):
            tooltip = "Open in terminal"
        elif (index.column() == OPEN_IDE_COLUMN):
            tooltip = "Open in IDE"
        elif (index.column() == REFRESH_COLUMN):
            tooltip = "Refresh"
        elif (index.column() == WARNING_COLUMN):
            if self.repo_data[index.row()]['warning'] is not None:
                tooltip = self.repo_data[index.row()]['warning']
            else:
                tooltip = ""
        if role == Qt.ItemDataRole.DisplayRole:
            return data
        elif role == Qt.ItemDataRole.ToolTipRole:
            return tooltip
        else:
            raise ValueError("Only supports Display and Tooltip roles.")

    def rowCount(self, index: QModelIndex) -> int:
        """Part of the Qt model interface."""
        return len(self.repo_data)

    def columnCount(self, index: QModelIndex) -> int:
        """Part of the Qt model interface."""
        return TOTAL_COLUMNS

    def row_shading_colour(self, index: QModelIndex) -> QColor:
        """Get row colour for the repo list to indicate status."""
        if not self.valid_index(index):
            return QColor()
        if ((self.repo_data[index.row()]['untracked_count'] > 0)
                or self.repo_data[index.row()]['working_tree_changes']
                or self.repo_data[index.row()]['index_changes']):
            return QColor(255, 0, 0, ROW_SHADING_ALPHA)
        elif (self.repo_data[index.row()]['behind_count'] > 0):
            return QColor(255, 255, 0, ROW_SHADING_ALPHA)
        elif self.repo_data[index.row()]['stash']:
            return QColor(255, 0, 255, ROW_SHADING_ALPHA)
        elif (self.repo_data[index.row()]['ahead_count'] > 0):
            return QColor(0, 255, 255, ROW_SHADING_ALPHA)
        else:
            return QColor("white")

    def get_commit_html(self, index: QModelIndex) -> str:
        """Provide a formatted view of the most recent commits."""
        if not self.valid_index(index):
            return ""
        commit_data = read.read_commits(self.settings.repo_list[index.row()],
                                        VIEW_COMMIT_COUNT)
        summary = "" if commit_data else "No commits"
        for c in commit_data:
            summary += (
                "<pre>"
                f"<a style='color:orange;'>Commit: {c['hash']}</a>"
                f"<p>Author: {c['author']}</p>"
                f"<a>Date:   {c['date']}</a><br>"
                f"<p>        {c['summary']}</p>"
                "<a> </a><br>"
                "</pre>"
            )
        return summary

    def _refresh_complete(self, results):
        if not self.cd.cancelled:
            repo_data = []
            retained_paths = []
            for i, data in enumerate(results):
                if data is not None:
                    repo_data.append(data)
                    retained_paths.append(self.settings.repo_list[i])
            if (len(retained_paths) != len(self.settings.repo_list)):
                self.settings.set_repo_list(retained_paths)
            self.repo_data = repo_data
            self.layoutChanged.emit()

    def refresh_all_data(self) -> None:
        """Re-read all listed repos and store the data."""
        self.cd = CancellableDialog(ReadWorker(self.settings.repo_list,
                                               self.settings.fetch_remotes),
                                    self._refresh_complete)
        self.cd.launch("Updating", "Repo update in progress...")

    def refresh_row(self, index: QModelIndex) -> None:
        """Re-read one repo and update the data."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        data = read.read_repo(self.settings.repo_list[index.row()],
                              self.settings.fetch_remotes)
        if data is not None:
            self.repo_data[index.row()] = data
        else:
            pass  # TODO
        self.dataChanged.emit(self.createIndex(index.row(), 0),
                              self.createIndex(index.row(),
                                               TOTAL_COLUMNS - 1))
        QApplication.restoreOverrideCursor()

    def table_clicked(self, index: QModelIndex):
        """Launch processes when certain columns are clicked."""
        if index.column() == OPEN_FOLDER_COLUMN:
            QDesktopServices.openUrl(
                QUrl("file://"
                     + str(self.repo_data[index.row()]['repo_dir'])))
        elif index.column() == OPEN_DIFFTOOL_COLUMN:
            git_args = None
            if self.repo_data[index.row()]['bare']:
                pass  # TODO: diff using last 2 commit hashes
            elif self.repo_data[index.row()]['working_tree_changes']:
                git_args = ["difftool", "--dir-diff"]
            elif (self.repo_data[index.row()]['commit_count'] > 1):
                git_args = ["difftool", "--dir-diff", "HEAD~1..HEAD"]
            if git_args is not None:
                myProcess = QProcess()
                myProcess.setWorkingDirectory(
                    str(self.repo_data[index.row()]['repo_dir']))
                myProcess.start("git", git_args)
                myProcess.waitForFinished(-1)
        elif index.column() == OPEN_TERMINAL_COLUMN:
            myProcess = QProcess()
            myProcess.setWorkingDirectory(
                str(self.repo_data[index.row()]['repo_dir']))
            myProcess.start(self.settings.terminal_command)
            myProcess.waitForFinished(-1)
        elif index.column() == OPEN_IDE_COLUMN:
            myProcess = QProcess()
            ide_args = self.settings.ide_command[1:]
            ide_args.append(str(self.repo_data[index.row()]['repo_dir']))
            myProcess.start(self.settings.ide_command[0], ide_args)
            myProcess.waitForFinished(-1)
        elif index.column() == REFRESH_COLUMN:
            self.refresh_row(index)

    def headerData(self, section: int, orient: Qt.Orientation,
                   role: Qt.ItemDataRole) -> Any:
        """Part of the Qt model interface."""
        col_titles = ["Parent directory", "Name", "U", "M", "B",
                      "S", "I", "▲", "▼", "T", "⦾", "R", "L"]
        col_tooltips = ["Parent directory", "Repository name",
                        "Untracked file(s)", "Modified file(s)",
                        "Bare/mirror repository", "At least one stash",
                        "Index has changes", "Local branches ahead of remotes",
                        "Local branches behind remotes", "Tag(s)",
                        "Submodule(s)", "Remote(s)", "Local branch(es)"]
        if (role == Qt.ItemDataRole.DisplayRole and
                orient == Qt.Orientation.Horizontal):
            if section < len(col_titles):
                return col_titles[section]
        elif (role == Qt.ItemDataRole.ToolTipRole and
                orient == Qt.Orientation.Horizontal):
            if section < len(col_titles):
                return col_tooltips[section]


class CancellableTaskWorker(QObject):
    finished = pyqtSignal(list)

    def run(self) -> None:
        raise NotImplementedError

    def get_stop_event(self) -> EVENT_TYPE:
        raise NotImplementedError


class SearchWorker(CancellableTaskWorker):

    def __init__(self,
                 start_dir: str | Path,
                 exclude_dirs: list[Path] = []):
        self.start_dir = start_dir
        self.exclude_dirs = exclude_dirs
        self.stop_event = threading.Event()
        super().__init__()

    def get_stop_event(self) -> EVENT_TYPE:
        return self.stop_event

    def run(self) -> None:
        list_path_to_git = search.find_git_repos(self.start_dir,
                                                 self.exclude_dirs,
                                                 self.stop_event)
        self.finished.emit(list_path_to_git)


class ReadWorker(CancellableTaskWorker):

    def __init__(self,
                 repo_list: list[str],
                 fetch_remotes: bool):
        self.repo_list = repo_list
        self.fetch_remotes = fetch_remotes
        self.stop_event = multiprocessing.Event()
        super().__init__()

    def get_stop_event(self) -> EVENT_TYPE:
        return self.stop_event

    def run(self) -> None:
        results = read.read_repo_parallel(self.repo_list,
                                          self.fetch_remotes,
                                          self.stop_event)
        self.finished.emit(results)


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window."""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(APP_TITLE + ":  " + APP_SUBTITLE)
        self._set_default_commit_text_format()
        self.model = TableModel()
        self.tableView.setModel(self.model)
        self._connect_signals()
        self.tableView.setItemDelegate(StyleDelegate(self.model,
                                                     self.tableView))
        self.model.load_and_refresh_saved_data()
        self._format_table()

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
        self._update_view()

    def _resize_rows_columns(self):
        self.tableView.verticalHeader().setMinimumSectionSize(0)
        self.tableView.resizeRowsToContents()
        v_size = self.tableView.verticalHeader().sectionSize(0)
        self.tableView.verticalHeader().setMinimumSectionSize(
            int(v_size * ROW_SCALE_FACTOR))
        # Horizontal:
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
        """Dialog for repository search."""
        (search_path_str, ok) = QInputDialog.getText(
            self, "Search for repositories",
            ("Choose the root directory. All directories\n"
             "below this will be searched (this may be slow)."),
            QLineEdit.EchoMode.Normal, self.model.settings.search_path,
            Qt.WindowType.Dialog,
            Qt.InputMethodHint.ImhNone)
        if ok and Path(search_path_str).is_dir():
            self.model.settings.set_search_path(search_path_str)
            self.launch_search(search_path_str)

    def _search_complete(self, repo_list):
        if not self.cd.cancelled:
            self.model.settings.set_repo_list(repo_list)
            self.model.refresh_all_data()

    def launch_search(self, search_path: str):
        self.cd = CancellableDialog(
                    SearchWorker(search_path,
                                 self.model.settings.exclude_dirs),
                    self._search_complete)
        self.cd.launch("Search", "Search in progress...")

    def _run_settings_dialog(self) -> None:
        """Launch dialog to get/update/display user-selected settings."""
        settings_ui = SettingsWindow(self.model.settings)
        settings_ui.exec()
        (ok, new_settings) = settings_ui.get_inputs()
        if ok:
            self.model.settings.set(new_settings)
        self._resize_rows_columns()


class CancellableDialog:
    """Show a dialog while doing a long task, allowing early cancellation."""

    def __init__(self, worker: CancellableTaskWorker,
                 on_worker_finish: PYQT_SLOT) -> None:
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

    def _cancel(self) -> None:
        self.cancelled = True
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.stop_event.set()

    def launch(self, title: str, text: str) -> None:
        """Start the task and show the wait dialog box."""
        self.thread.start()
        self.box = QMessageBox(QMessageBox.Icon.NoIcon, title,
                               text, QMessageBox.StandardButton.Cancel)
        self.box.rejected.connect(self._cancel)
        self.worker.finished.connect(self.box.close)  # type: ignore
        self.worker.finished.connect(QApplication.restoreOverrideCursor)
        self.box.finished.connect(self.box.deleteLater)
        self.box.show()


class SettingsWindow(QDialog, Ui_Dialog):
    """Allow user to view and/or choose application settings via a GUI."""

    def __init__(self, existing_settings: AppSettings) -> None:
        """Input the existing settings to display in the dialog."""
        super().__init__()
        self.setupUi(self)
        self._set_existing_settings(existing_settings)

    def _set_existing_settings(self, existing_settings: AppSettings) -> None:
        """Set existing/default app settings in user input widgets."""
        self.checkBox_fetches.setChecked(existing_settings.fetch_remotes)
        self.lineEdit_IDE.setText(" ".join(existing_settings.ide_command))
        self.lineEdit_terminal.setText(existing_settings.terminal_command)
        self.label_settings_location.setText(
            "Application settings will be saved in\n"
            + str(existing_settings.settings_directory))

    def get_inputs(self) -> tuple[bool, dict[str, str | bool]]:
        """Get app settings from user input widgets."""
        new_settings = {}
        if (self.exec_ok):
            new_settings['ide_command'] = self.lineEdit_IDE.text().strip().split(" ")
            new_settings['terminal_command'] = self.lineEdit_terminal.text()
            new_settings['fetch_remotes'] = self.checkBox_fetches.isChecked()
        return (self.exec_ok, new_settings)

    def exec(self) -> int:
        """Show the dialog and wait for the user to close it."""
        self.exec_ok = super().exec() == 1
        return 1 if self.exec_ok else 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
