import sys
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import Qt, QStringListModel, QAbstractListModel, QModelIndex, pyqtSlot
from PyQt6.QtGui import QFont

from gui.test1 import Ui_MainWindow
from scanner import search, read

VIEW_COMMIT_COUNT = 3

class MyModel(QAbstractListModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo_list = []

    def data(self, index, role) -> (str | None):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.repo_list[index.row()])
        elif role == Qt.ItemDataRole.ToolTipRole:
            return str(self.repo_list[index.row()])

    def rowCount(self, index) -> int:
        return len(self.repo_list)

    def get_commit_html(self, index) -> str:
        commit_data = read.read_commits(self.repo_list[index.row()],
                                        VIEW_COMMIT_COUNT)
        summary = ""
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


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window."""
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Gitscan:  a git repository status viewer")
        self.set_default_commit_text_format()
        self.model = MyModel()
        self.listView.setModel(self.model)
        self.listView.selectionModel().selectionChanged.connect(
                                            self.selection_changed)
        self.model.get_data()

    def set_default_commit_text_format(self):
        font = QFont()
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFamily('monospace')
        self.plainTextEdit.setFont(font)
        self.plainTextEdit.setStyleSheet("QPlainTextEdit {"
                                         "background-color: black;"
                                         "color : white;}")

    def selection_changed(self) -> None:
        commit_html_text = self.model.get_commit_html(
                            self.listView.selectionModel().currentIndex())
        self.plainTextEdit.clear()
        self.plainTextEdit.appendHtml(commit_html_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
