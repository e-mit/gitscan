"""Main file for GUI app."""
import sys
from typing import Any
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt6.QtWidgets import QDialog, QLineEdit, QInputDialog
from PyQt6.QtCore import Qt, QModelIndex, QProcess, QAbstractTableModel, QUrl
from PyQt6.QtGui import QFont, QColor, QIcon, QDesktopServices

import arrow

from gui.test_table import Ui_MainWindow
from gui.settings_dialog import Ui_Dialog
from scanner import search, read, settings
from scanner.settings import AppSettings

APP_TITLE = "Gitscan"
APP_SUBTITLE = "a git repository status viewer"
APP_VERSION = "0.1.0"
PROJECT_GITHUB_URL = "https://github.com/e-mit/gitscan"
VIEW_COMMIT_COUNT = 3  # Show (at most) this many commits in the lower pane
OPEN_FOLDER_COLUMN = 14
OPEN_DIFFTOOL_COLUMN = OPEN_FOLDER_COLUMN + 1
OPEN_TERMINAL_COLUMN = OPEN_FOLDER_COLUMN + 2
OPEN_IDE_COLUMN = OPEN_FOLDER_COLUMN + 3
REFRESH_COLUMN = OPEN_FOLDER_COLUMN + 4
TOTAL_COLUMNS = REFRESH_COLUMN + 1
OPEN_FOLDER_ICON = "resources/folder.svg"
OPEN_DIFFTOOL_ICON = "resources/diff.svg"
OPEN_TERMINAL_ICON = "resources/terminal.svg"
OPEN_IDE_ICON = "resources/window.svg"
WARNING_ICON = "resources/warning.svg"
REFRESH_ICON = "resources/refresh.svg"


class MyModel(QAbstractTableModel):
    """Model part of Qt model-view, for containing data."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = settings.AppSettings()
        self.refresh_all_data()

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> Any:
        """Part of the Qt model interface."""
        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_data(index, Qt.ItemDataRole.DisplayRole)
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._display_data(index, Qt.ItemDataRole.ToolTipRole)
        elif role == Qt.ItemDataRole.BackgroundRole:
            return self.row_shading(index)
        elif role == Qt.ItemDataRole.DecorationRole:
            if (index.column() == OPEN_FOLDER_COLUMN):
                return QIcon(OPEN_FOLDER_ICON)
            elif (index.column() == OPEN_DIFFTOOL_COLUMN):
                return QIcon(OPEN_DIFFTOOL_ICON)
            elif (index.column() == OPEN_TERMINAL_COLUMN):
                return QIcon(OPEN_TERMINAL_ICON)
            elif (index.column() == OPEN_IDE_COLUMN):
                return QIcon(OPEN_IDE_ICON)
            elif (index.column() == REFRESH_COLUMN):
                return QIcon(REFRESH_ICON)

    def _display_data(self, index: QModelIndex,
                      role: Qt.ItemDataRole) -> str:
        data = " "
        tooltip = ""
        if (index.column() == 0):
            data = str(self.repo_data[index.row()]['containing_dir'])
            tooltip = "Containing directory"
        elif (index.column() == 1):
            data = self.repo_data[index.row()]['name']
            tooltip = "Repository name"
        elif (index.column() == 2):
            untracked_count = self.repo_data[index.row()]['untracked_count']
            if untracked_count > 0:
                data = "U"
                tooltip = str(untracked_count) + " untracked "
                tooltip += "file" if (untracked_count == 1) else "files"
        elif (index.column() == 3):
            if self.repo_data[index.row()]['working_tree_changes']:
                data = "M"
                tooltip = "Modified working tree"
        elif (index.column() == 4):
            if self.repo_data[index.row()]['bare']:
                data = "B"
                tooltip = "Bare repository"
        elif (index.column() == 5):
            if self.repo_data[index.row()]['stash']:
                data = "S"
                tooltip = "At least one stash"
        elif (index.column() == 6):
            if self.repo_data[index.row()]['index_changes']:
                data = "I"
                tooltip = "Uncommitted index change(s)"
        elif (index.column() == 7):
            if self.repo_data[index.row()]['ahead_count'] > 0:
                data = "˄"
                tooltip = ("Ahead of remote(s) by "
                           f"{self.repo_data[index.row()]['ahead_count']}"
                           " commits")
        elif (index.column() == 8):
            if self.repo_data[index.row()]['behind_count'] > 0:
                data = "˅"
                tooltip = ("Behind remote(s) by "
                           f"{self.repo_data[index.row()]['behind_count']}"
                           " commits")
        elif (index.column() == 9):
            tag_count = self.repo_data[index.row()]['tag_count']
            if tag_count > 0:
                data = "T"
                tooltip = str(tag_count)
                tooltip += " tag" if (tag_count == 1) else " tags"
        elif (index.column() == 10):
            remote_count = self.repo_data[index.row()]['remote_count']
            data = str(remote_count)
            data += " remote" if (remote_count == 1) else " remotes"
            if remote_count == 0:
                tooltip = "No remotes"
            else:
                tooltip = data
        elif (index.column() == 11):
            branch_count = self.repo_data[index.row()]['branch_count']
            data = str(branch_count)
            data += " branch" if (branch_count == 1) else " branches"
            if branch_count == 0:
                tooltip = "No branches"
            else:
                tooltip = data
        elif (index.column() == 12):
            data = self.repo_data[index.row()]['branch_name']
            if self.repo_data[index.row()]['detached_head']:
                tooltip = "Detached HEAD state"
            elif self.repo_data[index.row()]['branch_count'] == 0:
                tooltip = "No branches"
            else:
                tooltip = "Active branch"
        elif (index.column() == 13):
            last_commit_datetime = self.repo_data[index.row()]['last_commit_datetime']
            if last_commit_datetime is None:
                data = "-"
            else:
                data = arrow.get(last_commit_datetime).humanize().capitalize()
            tooltip = "Last commit on active branch"
        elif (index.column() == OPEN_FOLDER_COLUMN):
            tooltip = "Open in directory explorer"
        elif (index.column() == OPEN_DIFFTOOL_COLUMN):
            tooltip = "Open in difftool"
        elif (index.column() == OPEN_TERMINAL_COLUMN):
            tooltip = "Open in terminal"
        elif (index.column() == OPEN_IDE_COLUMN):
            tooltip = "Open in IDE"
        elif (index.column() == REFRESH_COLUMN):
            tooltip = "Refresh"
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

    def row_shading(self, index: QModelIndex) -> QColor:
        """Colour the rows of the repo list to indicate status."""
        if ((self.repo_data[index.row()]['untracked_count'] > 0)
                or self.repo_data[index.row()]['working_tree_changes']
                or self.repo_data[index.row()]['index_changes']):
            return QColor("red")
        elif (self.repo_data[index.row()]['behind_count'] > 0):
            return QColor("yellow")
        elif (self.repo_data[index.row()]['ahead_count'] > 0):
            return QColor("green")
        else:
            return QColor("white")

    def get_commit_html(self, index: QModelIndex) -> str:
        """Provide a formatted view of the most recent commits."""
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

    def search_and_read_repos(self, root_directory: str | Path) -> None:
        """Perform a search for repositories, then read their data/status."""
        self.settings.set_repo_list(search.find_git_repos(root_directory))
        self.refresh_all_data()

    def refresh_all_data(self) -> None:
        """Re-read all listed repos and store the data."""
        self.repo_data = []
        for repo in self.settings.repo_list:
            self.repo_data.append(read.read_repo(repo))
        self.layoutChanged.emit()

    def refresh_row(self, index: QModelIndex) -> None:
        """Re-read one repo and update the data."""
        self.repo_data[index.row()] = read.read_repo(
            self.settings.repo_list[index.row()])
        self.dataChanged.emit(self.createIndex(index.row(), 0),
                              self.createIndex(index.row(),
                                               TOTAL_COLUMNS - 1))

    def table_clicked(self, index: QModelIndex):
        """Launch processes when certain columns are clicked."""
        if index.column() == OPEN_FOLDER_COLUMN:
            QDesktopServices.openUrl(
                QUrl("file://"
                     + str(self.repo_data[index.row()]['repo_dir'])))
        elif index.column() == OPEN_DIFFTOOL_COLUMN:
            git_args = None
            if self.repo_data[index.row()]['working_tree_changes']:
                git_args = ["difftool", "--dir-diff"]
            elif (self.repo_data[index.row()]['last_commit_datetime']
                  is not None):
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
            myProcess.start(
                        self.settings.ide_command, ["-n",
                            str(self.repo_data[index.row()]['repo_dir'])])
            myProcess.waitForFinished(-1)
        elif index.column() == REFRESH_COLUMN:
            self.refresh_row(index)

    def headerData(self, section: int, orient: Qt.Orientation,
                   role: Qt.ItemDataRole) -> Any:
        """Part of the Qt model interface."""
        if (role == Qt.ItemDataRole.DisplayRole and
                orient == Qt.Orientation.Horizontal):
            return f"H {section}"


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window."""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(APP_TITLE + ":  " + APP_SUBTITLE)
        self.set_default_commit_text_format()
        self.model = MyModel()
        self.tableView.setModel(self.model)
        self.connect_signals()

    def set_default_commit_text_format(self) -> None:
        """Format the lower display pane appearance."""
        font = QFont()
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFamily('monospace')
        self.plainTextEdit.setFont(font)
        self.plainTextEdit.setStyleSheet("QPlainTextEdit {"
                                         "background-color: black;"
                                         "color : white;}")

    def display_commit_text(self) -> None:
        """Run when selected repo, or its data, changes."""
        commit_html_text = self.model.get_commit_html(
                            self.tableView.selectionModel().currentIndex())
        self.plainTextEdit.clear()
        self.plainTextEdit.appendHtml(commit_html_text)

    def connect_signals(self) -> None:
        """Connect all signals and slots."""
        self.tableView.selectionModel().selectionChanged.connect(
                                           self.display_commit_text)
        self.tableView.clicked.connect(self.model.table_clicked)
        self.actionExit.triggered.connect(self.close)  # type: ignore
        self.actionVisit_GitHub.triggered.connect(self._visit_github)
        self.actionAbout.triggered.connect(self._help_about)
        self.actionRefresh_all.triggered.connect(self.model.refresh_all_data)
        self.actionRefresh_all.setShortcut("F5")
        self.actionSearch_for_repositories.triggered.connect(
            self.run_search_dialog)
        self.actionSettings.triggered.connect(self.run_settings_dialog)
        self.model.dataChanged.connect(self.display_commit_text)
        self.model.layoutChanged.connect(self.display_commit_text)

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

    def run_search_dialog(self) -> None:
        """Dialog for repository search."""
        (search_path_str, ok) = QInputDialog.getText(
            self, "Search for repositories",
            ("Choose the root directory. All directories\n"
             "below this will be searched (this may be slow)."),
            QLineEdit.EchoMode.Normal, self.model.settings.search_path,
            Qt.WindowType.Dialog,
            Qt.InputMethodHint.ImhNone)
        if ok and Path(search_path_str).is_dir():
            self.model.search_and_read_repos(search_path_str)
            self.model.settings.set_search_path(search_path_str)

    def run_settings_dialog(self) -> None:
        """Launch dialog to get/update/display user-selected settings."""
        settings_ui = SettingsWindow(self.model.settings)
        settings_ui.exec()
        (ok, new_settings) = settings_ui.get_inputs()
        if ok:
            self.model.settings.set(new_settings)


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
        self.lineEdit_IDE.setText(existing_settings.ide_command)
        self.lineEdit_terminal.setText(existing_settings.terminal_command)
        self.label_settings_location.setText(
            "Application settings will be saved in\n"
            + str(existing_settings.settings_directory))

    def get_inputs(self) -> tuple[bool, dict[str, str | bool]]:
        """Get app settings from user input widgets."""
        new_settings = {}
        if (self.exec_ok):
            new_settings['ide_command'] = self.lineEdit_IDE.text()
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
