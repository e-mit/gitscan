import sys
from typing import Any
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt6.QtCore import Qt, QModelIndex, QProcess, QAbstractTableModel, QUrl
from PyQt6.QtGui import QFont, QColor, QIcon, QDesktopServices

import arrow

from gui.test_table import Ui_MainWindow
from scanner import search, read

APP_TITLE = "Gitscan"
APP_SUBTITLE = "a git repository status viewer"
APP_VERSION = "0.1.0"
PROJECT_GITHUB_URL = "https://github.com/e-mit/gitscan"
VIEW_COMMIT_COUNT = 3  # Show (at most) this many commits in the lower pane
OPEN_FOLDER_COLUMN = 14
OPEN_DIFFTOOL_COLUMN = OPEN_FOLDER_COLUMN + 1
OPEN_TERMINAL_COLUMN = OPEN_FOLDER_COLUMN + 2
OPEN_IDE_COLUMN = OPEN_FOLDER_COLUMN + 3
OPEN_FOLDER_ICON = "resources/ex.svg"
OPEN_DIFFTOOL_ICON = "resources/tick.svg"
OPEN_TERMINAL_ICON = "resources/tick2.svg"
OPEN_IDE_ICON = "resources/bag.svg"


class MyModel(QAbstractTableModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo_list = []
        self.repo_data_list = []

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            return self.display_data(index, Qt.ItemDataRole.DisplayRole)
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self.display_data(index, Qt.ItemDataRole.ToolTipRole)
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

    def display_data(self, index: QModelIndex,
                     role: Qt.ItemDataRole) -> str:
        data = " "
        tooltip = ""
        if (index.column() == 0):
            data = str(self.repo_data_list[index.row()]['containing_dir'])
            tooltip = "Containing directory"
        elif (index.column() == 1):
            data = self.repo_data_list[index.row()]['name']
            tooltip = "Repository name"
        elif (index.column() == 2):
            untracked_count = self.repo_data_list[index.row()]['untracked_count']
            if untracked_count > 0:
                data = "U"
                tooltip = str(untracked_count) + " untracked "
                tooltip += "file" if (untracked_count == 1) else "files"
        elif (index.column() == 3):
            if self.repo_data_list[index.row()]['working_tree_changes']:
                data = "M"
                tooltip = "Modified working tree"
        elif (index.column() == 4):
            if self.repo_data_list[index.row()]['bare']:
                data = "B"
                tooltip = "Bare repository"
        elif (index.column() == 5):
            if self.repo_data_list[index.row()]['stash']:
                data = "S"
                tooltip = "At least one stash"
        elif (index.column() == 6):
            if self.repo_data_list[index.row()]['index_changes']:
                data = "I"
                tooltip = "Uncommitted index change(s)"
        elif (index.column() == 7):
            if self.repo_data_list[index.row()]['ahead_count'] > 0:
                data = "˄"
                tooltip = ("Ahead of remote(s) by "
                           f"{self.repo_data_list[index.row()]['ahead_count']}"
                           " commits")
        elif (index.column() == 8):
            if self.repo_data_list[index.row()]['behind_count'] > 0:
                data = "˅"
                tooltip = ("Behind remote(s) by "
                           f"{self.repo_data_list[index.row()]['behind_count']}"
                           " commits")
        elif (index.column() == 9):
            tag_count = self.repo_data_list[index.row()]['tag_count']
            if tag_count > 0:
                data = "T"
                tooltip = str(tag_count)
                tooltip += " tag" if (tag_count == 1) else " tags"
        elif (index.column() == 10):
            remote_count = self.repo_data_list[index.row()]['remote_count']
            data = str(remote_count)
            data += " remote" if (remote_count == 1) else " remotes"
            if remote_count == 0:
                tooltip = "No remotes"
            else:
                tooltip = data
        elif (index.column() == 11):
            branch_count = self.repo_data_list[index.row()]['branch_count']
            data = str(branch_count)
            data += " branch" if (branch_count == 1) else " branches"
            if branch_count == 0:
                tooltip = "No branches"
            else:
                tooltip = data
        elif (index.column() == 12):
            data = self.repo_data_list[index.row()]['branch_name']
            if self.repo_data_list[index.row()]['detached_head']:
                tooltip = "Detached HEAD state"
            elif self.repo_data_list[index.row()]['branch_count'] == 0:
                tooltip = "No branches"
            else:
                tooltip = "Active branch"
        elif (index.column() == 13):
            last_commit_datetime = self.repo_data_list[index.row()]['last_commit_datetime']
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
        if role == Qt.ItemDataRole.DisplayRole:
            return data
        elif role == Qt.ItemDataRole.ToolTipRole:
            return tooltip
        else:
            raise ValueError("Only supports Display and Tooltip roles.")

    def rowCount(self, index) -> int:
        return len(self.repo_data_list)
    
    def columnCount(self, index) -> int:
        return 18

    def row_shading(self, index: QModelIndex) -> QColor:
        if ((self.repo_data_list[index.row()]['untracked_count'] > 0)
                or self.repo_data_list[index.row()]['working_tree_changes']
                or self.repo_data_list[index.row()]['index_changes']):
            return QColor("red")
        elif (self.repo_data_list[index.row()]['behind_count'] > 0):
            return QColor("yellow")
        elif (self.repo_data_list[index.row()]['ahead_count'] > 0):
            return QColor("green")
        else:
            return QColor("white")

    def get_commit_html(self, index: QModelIndex) -> str:
        commit_data = read.read_commits(self.repo_list[index.row()],
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
    
    def search_and_read_repos(self) -> None:
        self.repo_list = search.find_git_repos("/tmp")
        self.refresh_data()

    def refresh_data(self) -> None:
        self.repo_data_list = []
        for repo in self.repo_list:
            self.repo_data_list.append(read.read_repo(repo))
        self.layoutChanged.emit()

    def table_clicked(self, index: QModelIndex):
        if index.column() == OPEN_FOLDER_COLUMN:
            QDesktopServices.openUrl(
                QUrl("file://"
                     + str(self.repo_data_list[index.row()]['repo_dir'])))
        elif index.column() == OPEN_DIFFTOOL_COLUMN:
            git_args = None
            if self.repo_data_list[index.row()]['working_tree_changes']:
                git_args = ["difftool", "--dir-diff"]
            elif self.repo_data_list[index.row()]['last_commit_datetime'] is not None:
                git_args = ["difftool", "--dir-diff", "HEAD~1..HEAD"]
            if git_args is not None:
                myProcess = QProcess()
                myProcess.setWorkingDirectory(
                    str(self.repo_data_list[index.row()]['repo_dir']))
                myProcess.start("git", git_args)
                myProcess.waitForFinished(-1)
        elif index.column() == OPEN_TERMINAL_COLUMN:
            myProcess = QProcess()
            myProcess.setWorkingDirectory(
                str(self.repo_data_list[index.row()]['repo_dir']))
            myProcess.start("gnome-terminal")
            myProcess.waitForFinished(-1)
        elif index.column() == OPEN_IDE_COLUMN:
            myProcess = QProcess()
            myProcess.start(
                "code", ["-n",
                         str(self.repo_data_list[index.row()]['repo_dir'])])
            myProcess.waitForFinished(-1)

class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window."""
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(APP_TITLE + ": " + APP_SUBTITLE)
        self.set_default_commit_text_format()
        self.model = MyModel()
        self.tableView.setModel(self.model)
        self.connect_gui_signals()
        self.model.search_and_read_repos()

    def set_default_commit_text_format(self) -> None:
        font = QFont()
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFamily('monospace')
        self.plainTextEdit.setFont(font)
        self.plainTextEdit.setStyleSheet("QPlainTextEdit {"
                                         "background-color: black;"
                                         "color : white;}")

    def selection_changed(self) -> None:
        commit_html_text = self.model.get_commit_html(
                            self.tableView.selectionModel().currentIndex())
        self.plainTextEdit.clear()
        self.plainTextEdit.appendHtml(commit_html_text)

    def connect_gui_signals(self):
        self.tableView.selectionModel().selectionChanged.connect(
                                           self.selection_changed)
        self.tableView.clicked.connect(self.model.table_clicked)
        self.actionExit.triggered.connect(self.close)  # type: ignore
        self.actionVisit_GitHub.triggered.connect(self.visit_github)
        self.actionAbout.triggered.connect(self.help_about)
        self.actionRefresh_all.triggered.connect(self.model.refresh_data)
        self.actionRefresh_all.setShortcut("F5")

    def visit_github(self):
        QDesktopServices.openUrl(QUrl(PROJECT_GITHUB_URL))

    def help_about(self):
        QMessageBox.about(
            self,
            "About",
            f"<p>{APP_TITLE}</p>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>{APP_SUBTITLE.capitalize()}</p>"
            "<p>Built with PyQt and Qt Designer</p>"
            f"<a href='{PROJECT_GITHUB_URL}'>View the code on GitHub</a>"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
