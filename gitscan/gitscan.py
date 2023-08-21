import sys
from typing import Any
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import Qt, QStringListModel, QAbstractListModel, QModelIndex, pyqtSlot, QAbstractTableModel
from PyQt6.QtGui import QFont, QColor

import arrow

from gui.test_table import Ui_MainWindow
from scanner import search, read

VIEW_COMMIT_COUNT = 3

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
            tooltip = "Last commit"
        if role == Qt.ItemDataRole.DisplayRole:
            return data
        elif role == Qt.ItemDataRole.ToolTipRole:
            return tooltip
        else:
            raise ValueError("Only supports Display and Tooltip roles.")

    def rowCount(self, index) -> int:
        return len(self.repo_list)
    
    def columnCount(self, index) -> int:
        return 14

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

    def get_data(self) -> None:
        self.repo_list = search.find_git_repos("/tmp")
        for repo in self.repo_list:
            self.repo_data_list.append(read.read_repo(repo))
        self.layoutChanged.emit()


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window."""
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Gitscan:  a git repository status viewer")
        self.set_default_commit_text_format()
        self.model = MyModel()
        self.tableView.setModel(self.model)
        self.tableView.selectionModel().selectionChanged.connect(
                                           self.selection_changed)
        self.model.get_data()

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
