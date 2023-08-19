import sys
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import Qt, QStringListModel, QAbstractListModel, QModelIndex, pyqtSlot

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

    def get_commit(self, index) -> str:
        # self.string_list[index.row()] = "hi"
        # NB: the gui will update automatically after data changes
        # but can do it quicker with: 
        # self.dataChanged.emit(index, index)
        return read.make_commit_summary(self.repo_list[index.row()],
                                        VIEW_COMMIT_COUNT)

    def get_data(self) -> None:
        self.repo_list = search.find_git_repos("/tmp")


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window."""
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Gitscan:  a git repository status viewer")
        self.model = MyModel()
        self.listView.setModel(self.model)
        self.listView.selectionModel().selectionChanged.connect(
                                            self.selection_changed)
        self.model.get_data()

    def selection_changed(self) -> None:
        commit_text = self.model.get_commit(
                            self.listView.selectionModel().currentIndex())
        self.plainTextEdit.setPlainText(commit_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
