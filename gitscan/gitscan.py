import sys
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import Qt, QStringListModel, QAbstractListModel, QModelIndex, pyqtSlot

from gui.test1 import Ui_MainWindow


class MyModel(QAbstractListModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.string_list = ["Hello", "A note", "foo"]

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.string_list[index.row()]
        elif role == Qt.ItemDataRole.ToolTipRole:
            return "This is " + self.string_list[index.row()]

    def rowCount(self, index):
        return len(self.string_list)

    def get_commit(self, index):
        # self.string_list[index.row()] = "hi"
        # NB: the gui will update automatically after data changes
        # but can do it quicker with: 
        # self.dataChanged.emit(index, index)
        return ("Commit: " + self.string_list[index.row()])


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window."""
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Gitscan:  a git repository status viewer")
        self.model = MyModel()
        self.listView.setModel(self.model)
        self.listView.selectionModel().selectionChanged.connect(self.selection_changed)

    def selection_changed(self):
        commit_text = self.model.get_commit(self.listView.selectionModel().currentIndex())
        self.plainTextEdit.setPlainText(commit_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
