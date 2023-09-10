"""Model for table data."""
from typing import Any
from pathlib import Path
import subprocess

import arrow

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QModelIndex, QAbstractTableModel
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QColor, QDesktopServices

from ..scanner import read, settings
from . import dialogs, workers

VIEW_COMMIT_COUNT = 3  # Show (at most) this many commits in the lower pane
FOLDER_COLUMN = 15
DIFFTOOL_COLUMN = FOLDER_COLUMN + 1
TERMINAL_COLUMN = FOLDER_COLUMN + 2
IDE_COLUMN = FOLDER_COLUMN + 3
REFRESH_COLUMN = FOLDER_COLUMN + 4
WARNING_COLUMN = FOLDER_COLUMN + 5
TOTAL_COLUMNS = WARNING_COLUMN + 1
ROW_SHADING_ALPHA = 100
BAD_REPO_FLAG = 'bad_repo_flag'


class TableModel(QAbstractTableModel):
    """The model part of Qt model-view, for containing table data."""

    def __init__(self, parent: QWidget | None):
        super().__init__()
        self.repo_data: list[dict[str, Any]] = []
        self.settings = settings.AppSettings()
        self.parentWidget = parent
        self.bad_data_entry = {BAD_REPO_FLAG: True,
                               'warning': "Could not load repository"}

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> Any:
        """Part of the Qt model interface."""
        if not self.repo_data:
            return
        elif role == Qt.ItemDataRole.DisplayRole:
            return self._display_data(index, Qt.ItemDataRole.DisplayRole)
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._display_data(index, Qt.ItemDataRole.ToolTipRole)
        elif role == Qt.ItemDataRole.BackgroundRole:
            return self.row_shading_colour(index)
        elif (role == Qt.ItemDataRole.TextAlignmentRole and
              ((index.column() >= FOLDER_COLUMN and
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

    def _valid_index(self, index: QModelIndex) -> bool:
        """Determine if index is out of table range."""
        if index.row() < 0 or index.row() >= self.rowCount(None):
            return False
        if index.column() < 0 or index.column() >= self.columnCount(None):
            return False
        return True

    def _display_data(self, index: QModelIndex,
                      role: Qt.ItemDataRole) -> str:
        if (BAD_REPO_FLAG in self.repo_data[index.row()]
            and (index.column() not in
                 [0, 1, REFRESH_COLUMN, WARNING_COLUMN])):
            return ""
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
        elif (index.column() == FOLDER_COLUMN):
            tooltip = "Open directory"
        elif (index.column() == DIFFTOOL_COLUMN):
            if self.repo_data[index.row()]['working_tree_changes']:
                tooltip = "View working tree in difftool"
            elif (self.repo_data[index.row()]['bare'] or
                  self.repo_data[index.row()]['commit_count'] > 1):
                tooltip = "View last commit in difftool"
        elif (index.column() == TERMINAL_COLUMN):
            tooltip = "Open in terminal"
        elif (index.column() == IDE_COLUMN):
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
        if not self._valid_index(index):
            return QColor()
        if BAD_REPO_FLAG in self.repo_data[index.row()]:
            return QColor(0, 0, 0, ROW_SHADING_ALPHA)
        elif ((self.repo_data[index.row()]['untracked_count'] > 0)
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
        if ((not self._valid_index(index))
           or (BAD_REPO_FLAG in self.repo_data[index.row()])):
            return ""
        commit_data = read.read_commits(self.settings.repo_list[index.row()],
                                        VIEW_COMMIT_COUNT)
        if commit_data is None:
            return ""
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
            for i, data in enumerate(results):
                if data is None:
                    d = dict(self.bad_data_entry)
                    (d['name'], _,
                     d['containing_dir']) = read.extract_repo_name(
                         self.settings.repo_list[i])
                    repo_data.append(d)
                else:
                    repo_data.append(data)
            self.repo_data = repo_data
            self.layoutChanged.emit()

    def refresh_all_data(self) -> None:
        """Re-read all listed repos and store the data."""
        self.cd = dialogs.CancellableDialog(
                    workers.ReadWorker(self.settings.repo_list,
                                       self.settings.fetch_remotes),
                    self._refresh_complete,
                    self.parentWidget)
        self.cd.launch("Updating", "Repo update in progress...")

    def refresh_row(self, index: QModelIndex) -> None:
        """Re-read one repo and update the data."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        data = read.read_repo(self.settings.repo_list[index.row()],
                              self.settings.fetch_remotes)
        if data is not None:
            self.repo_data[index.row()] = data
        else:
            d = dict(self.bad_data_entry)
            (d['name'], _,
             d['containing_dir']) = read.extract_repo_name(
                    self.settings.repo_list[index.row()])
            self.repo_data[index.row()] = d
        self.dataChanged.emit(self.createIndex(index.row(), 0),
                              self.createIndex(index.row(),
                                               TOTAL_COLUMNS - 1))
        QApplication.restoreOverrideCursor()

    def table_clicked(self, index: QModelIndex):
        """Launch processes when certain columns are clicked."""
        if ((BAD_REPO_FLAG in self.repo_data[index.row()])
           and (index.column() != REFRESH_COLUMN)):
            return
        if index.column() == FOLDER_COLUMN:
            QDesktopServices.openUrl(
                QUrl(Path(self.repo_data[index.row()]['repo_dir']).as_uri()))
        elif index.column() == DIFFTOOL_COLUMN:
            git_args = None
            if self.repo_data[index.row()]['bare']:
                pass  # TODO: diff using last 2 commit hashes
            elif self.repo_data[index.row()]['working_tree_changes']:
                git_args = ["git", "difftool", "--dir-diff"]
            elif (self.repo_data[index.row()]['commit_count'] > 1):
                git_args = ["git", "difftool", "--dir-diff", "HEAD~1..HEAD"]
            if git_args is not None:
                subprocess.Popen(git_args,  # nosec
                                 cwd=str(
                                     self.repo_data[index.row()]['repo_dir']))
        elif index.column() == TERMINAL_COLUMN:
            subprocess.Popen(self.settings.terminal_command,  # nosec
                             shell=True,
                             cwd=str(self.repo_data[index.row()]['repo_dir']))
        elif index.column() == IDE_COLUMN:
            cmd = self.settings.ide_command + " ."
            subprocess.Popen(cmd, shell=True,  # nosec
                             cwd=str(self.repo_data[index.row()]['repo_dir']))
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
        left_align = [True, True]
        if (role == Qt.ItemDataRole.DisplayRole and
                orient == Qt.Orientation.Horizontal):
            if section < len(col_titles):
                return col_titles[section]
        elif (role == Qt.ItemDataRole.ToolTipRole and
                orient == Qt.Orientation.Horizontal):
            if section < len(col_titles):
                return col_tooltips[section]
        elif (role == Qt.ItemDataRole.TextAlignmentRole):
            if section < len(left_align) and left_align[section]:
                return Qt.AlignmentFlag.AlignLeft
