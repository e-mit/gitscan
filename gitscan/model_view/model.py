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
from . import dialogs, workers, columns
from .columns import Column

VIEW_COMMIT_COUNT = 3  # Show (at most) this many commits in the lower pane
ROW_SHADING_ALPHA = 100
BAD_DATA_WARNING = "Could not load repository"


class TableModel(QAbstractTableModel):
    """The model part of Qt model-view, for containing table data."""

    def __init__(self, parent: QWidget | None):
        super().__init__()
        self.repo_data: list[dict[str, Any]] = []
        self.settings = settings.AppSettings()
        self.parentWidget = parent
        self._bad_data_entry = 'bad_data'

    def data(self, index: QModelIndex,  # type: ignore
             role: Qt.ItemDataRole) -> Any:
        """Part of the Qt model interface."""
        if not self.repo_data:
            return
        elif (role == Qt.ItemDataRole.DisplayRole
              or role == Qt.ItemDataRole.ToolTipRole):
            return self._display_data(index, role)
        elif role == Qt.ItemDataRole.BackgroundRole:
            return self.row_shading_colour(index)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if Column(index.column()) in columns.left_align:
                return (Qt.AlignmentFlag.AlignLeft
                        | Qt.AlignmentFlag.AlignVCenter)
            else:
                return (Qt.AlignmentFlag.AlignCenter
                        | Qt.AlignmentFlag.AlignVCenter)

    @staticmethod
    def _add_s_if_plural(count: int) -> str:
        return "" if count == 1 else "s"

    def bad_data(self, index: QModelIndex) -> bool:
        """Identify repositores which could not be read correctly."""
        return self._bad_data_entry in self.repo_data[index.row()]

    def _valid_index(self, index: QModelIndex) -> bool:
        """Determine if index is out of table range."""
        if index.row() < 0 or index.row() >= self.rowCount():
            return False
        if index.column() < 0 or index.column() >= self.columnCount():
            return False
        return True

    def _display_data(self, index: QModelIndex,
                      role: Qt.ItemDataRole) -> str:
        try:
            column = Column(index.column())
        except ValueError:
            # Column out of range
            return ""
        if (self.bad_data(index)
            and (column not in [Column.FOLDER, Column.REPO_NAME,
                                Column.REFRESH, Column.WARNING])):
            return ""
        data = " "
        tooltip = ""
        if (column == Column.FOLDER):
            data = str(self.repo_data[index.row()]['containing_dir'])
            tooltip = "Parent directory"
        elif (column == Column.REPO_NAME):
            data = self.repo_data[index.row()]['name']
            tooltip = "Repository name"
        elif (column == Column.UNTRACKED):
            untracked_count = self.repo_data[index.row()]['untracked_count']
            if untracked_count > 0:
                data = "U"
                tooltip = (str(untracked_count) + " untracked file"
                           + self._add_s_if_plural(untracked_count))
        elif (column == Column.MODIFIED):
            if self.repo_data[index.row()]['working_tree_changes']:
                data = "M"
                tooltip = "Modified working tree"
        elif (column == Column.BARE):
            if self.repo_data[index.row()]['bare']:
                data = "B"
                tooltip = "Bare/mirror repository"
        elif (column == Column.STASH):
            if self.repo_data[index.row()]['stash']:
                data = "S"
                tooltip = "At least one stash"
        elif (column == Column.INDEX):
            if self.repo_data[index.row()]['index_changes']:
                data = "I"
                tooltip = "Uncommitted index change(s)"
        elif (column == Column.AHEAD):
            count = self.repo_data[index.row()]['ahead_count']
            if count > 0:
                data = "▲"
                tooltip = ("Local branches are ahead of remotes by "
                           f"{count} commit" + self._add_s_if_plural(count))
        elif (column == Column.BEHIND):
            count = self.repo_data[index.row()]['behind_count']
            if count > 0:
                data = "▼"
                tooltip = ("Local branches are behind remotes by "
                           f"{count} commit" + self._add_s_if_plural(count))
        elif (column == Column.TAGS):
            tag_count = self.repo_data[index.row()]['tag_count']
            if tag_count > 0:
                data = "T"
                tooltip = (str(tag_count) + " tag"
                           + self._add_s_if_plural(tag_count))
        elif (column == Column.SUBMODULES):
            submodule_count = len(
                self.repo_data[index.row()]['submodule_names'])
            if submodule_count > 0:
                data = str(submodule_count)
                tooltip = (str(submodule_count) + " submodule"
                           + self._add_s_if_plural(submodule_count) + ": "
                           + ", ".join(
                               self.repo_data[index.row()]['submodule_names']))
        elif (column == Column.REMOTES):
            remote_count = self.repo_data[index.row()]['remote_count']
            if remote_count > 0:
                tooltip = (str(remote_count) + " remote"
                           + self._add_s_if_plural(remote_count) + ": "
                           + ", ".join(
                               self.repo_data[index.row()]['remote_names']))
                data = str(remote_count)
        elif (column == Column.BRANCHES):
            branch_count = self.repo_data[index.row()]['branch_count']
            data = str(branch_count)
            if branch_count == 0:
                tooltip = "No local branches"
            else:
                tooltip = str(branch_count) + " local "
                tooltip += "branch" if (branch_count == 1) else "branches"
                tooltip += (": "
                            + ", ".join(
                                self.repo_data[index.row()]['branch_names']))
        elif (column == Column.BRANCH_NAME):
            data = self.repo_data[index.row()]['branch_name']
            if self.repo_data[index.row()]['detached_head']:
                tooltip = "Detached HEAD state"
            elif self.repo_data[index.row()]['branch_count'] == 0:
                tooltip = "No local branches"
            else:
                tooltip = "Active branch"
        elif (column == Column.LAST_COMMIT):
            last_commit_datetime = self.repo_data[index.row()]['last_commit_datetime']
            if last_commit_datetime is None:
                data = "-"
            else:
                data = arrow.get(last_commit_datetime).humanize().capitalize()
            tooltip = "Last commit on local branches"
        elif (column == Column.OPEN_FOLDER):
            tooltip = "Open directory"
        elif (column == Column.OPEN_DIFFTOOL):
            if self.repo_data[index.row()]['working_tree_changes']:
                tooltip = "View working tree in difftool"
            elif (self.repo_data[index.row()]['bare']
                  or self.repo_data[index.row()]['commit_count'] > 1):
                tooltip = "View last commit in difftool"
        elif (column == Column.OPEN_TERMINAL):
            tooltip = "Open in terminal"
        elif (column == Column.OPEN_IDE):
            tooltip = "Open in IDE"
        elif (column == Column.REFRESH):
            tooltip = "Refresh"
        elif (column == Column.WARNING):
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

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Part of the Qt model interface."""
        return len(self.repo_data)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Part of the Qt model interface."""
        return len(columns.Column)

    def row_shading_colour(self, index: QModelIndex) -> QColor:
        """Get row colour for the repo list to indicate status."""
        if not self._valid_index(index):
            return QColor()
        if self.bad_data(index):
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
        if (not self._valid_index(index)) or self.bad_data(index):
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

    def _label_bad_data(self, path_to_git: str | Path) -> dict[str, Any]:
        d: dict[str, Any] = {}
        d[self._bad_data_entry] = True
        d['warning'] = BAD_DATA_WARNING
        (d['name'], _, d['containing_dir']) = read.extract_repo_name(
            path_to_git)
        return d

    def _refresh_complete(self, results: list[dict[str, Any]]) -> None:
        if not self.cd.cancelled:
            repo_data: list[dict[str, Any]] = []
            for i, data in enumerate(results):
                if data is None:
                    repo_data.append(self._label_bad_data(
                        self.settings.repo_list[i]))
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
            self.repo_data[index.row()] = self._label_bad_data(
                self.settings.repo_list[index.row()])
        self.dataChanged.emit(self.createIndex(index.row(), 0),
                              self.createIndex(index.row(),
                                               len(Column) - 1))
        QApplication.restoreOverrideCursor()

    def _launch_git_diff(self, index: QModelIndex) -> None:
        git_args = None
        if self.repo_data[index.row()]['bare']:
            pass  # TODO: diff using last 2 commit hashes
        elif self.repo_data[index.row()]['working_tree_changes']:
            git_args = ["git", "difftool", "--dir-diff"]
        elif (self.repo_data[index.row()]['commit_count'] > 1):
            git_args = ["git", "difftool", "--dir-diff", "HEAD~1..HEAD"]
        if git_args is not None:
            subprocess.Popen(
                git_args,  # nosec
                cwd=str(self.repo_data[index.row()]['repo_dir']))

    def table_clicked(self, index: QModelIndex) -> None:
        """Launch processes when certain columns are clicked."""
        try:
            column = Column(index.column())
        except ValueError:
            # Column out of range
            return
        if self.bad_data(index) and (column != Column.REFRESH):
            return
        if column == Column.OPEN_FOLDER:
            QDesktopServices.openUrl(
                QUrl(Path(self.repo_data[index.row()]['repo_dir']).as_uri()))
        elif column == Column.OPEN_DIFFTOOL:
            self._launch_git_diff(index)
        elif column == Column.OPEN_TERMINAL:
            subprocess.Popen(self.settings.terminal_command,  # nosec
                             cwd=str(self.repo_data[index.row()]['repo_dir']))
        elif column == Column.OPEN_IDE:
            subprocess.Popen([self.settings.ide_command,  # nosec
                              str(self.repo_data[index.row()]['repo_dir'])])
        elif column == Column.REFRESH:
            self.refresh_row(index)

    def headerData(self, section: int, orient: Qt.Orientation,  # type:ignore
                   role: Qt.ItemDataRole) -> Any:
        """Provide data for column headers (standard Qt model interface)."""
        if orient != Qt.Orientation.Horizontal:
            return
        try:
            column = Column(section)
        except ValueError:
            # Column out of range
            return
        if column in columns.column_text:
            title = columns.column_text[column][0]
            tooltip = columns.column_text[column][1]
        else:
            return
        if role == Qt.ItemDataRole.DisplayRole:
            return title
        elif role == Qt.ItemDataRole.ToolTipRole:
            return tooltip
        elif (role == Qt.ItemDataRole.TextAlignmentRole):
            if column in columns.left_align:
                return Qt.AlignmentFlag.AlignLeft
