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
        return self.string_list[index.row()]


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window."""
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.model = MyModel()
        self.listView.setModel(self.model)
        self.plainTextEdit.setPlainText("Welcome")
        self.listView.clicked[QModelIndex].connect(self.on_clicked)

    def on_clicked(self, index):
        self.plainTextEdit.setPlainText(self.model.get_commit(index))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
