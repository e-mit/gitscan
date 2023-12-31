"""Custom delegate to insert SVG icons and format the gridlines."""
import pkgutil

from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PyQt6.QtCore import Qt, QModelIndex, QRectF
from PyQt6.QtGui import QPen, QColor, QPainter
from PyQt6.QtSvgWidgets import QSvgWidget

from .columns import Column

FOLDER_ICON = "../resources/folder.svg"
DIFFTOOL_ICON = "../resources/diff.svg"
TERMINAL_ICON = "../resources/terminal.svg"
WARNING_ICON = "../resources/warning.svg"
IDE_ICON = "../resources/window.svg"
REFRESH_ICON = "../resources/refresh.svg"
ICON_SCALE_FACTOR = 0.7  # Relative to table cell size
GRIDLINE_COLOUR = QColor(100, 100, 100, 100)


class StyleDelegate(QStyledItemDelegate):
    """Custom delegate to insert SVG icons and format the gridlines."""

    def __init__(self, model, *args, **kwargs):
        self.model = model
        self.folder_icon = self._load_svg_from_resource(FOLDER_ICON)
        self.difftool_icon = self._load_svg_from_resource(DIFFTOOL_ICON)
        self.terminal_icon = self._load_svg_from_resource(TERMINAL_ICON)
        self.ide_icon = self._load_svg_from_resource(IDE_ICON)
        self.warn_icon = self._load_svg_from_resource(WARNING_ICON)
        self.refresh_icon = self._load_svg_from_resource(REFRESH_ICON)
        super().__init__(*args, **kwargs)

    def _load_svg_from_resource(self, resource_file: str) -> QSvgWidget:
        svg = QSvgWidget()
        svg.load(pkgutil.get_data(__name__, resource_file))  # type: ignore
        svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        return svg

    def paint(self, painter: QPainter, option: QStyleOptionViewItem,
              index: QModelIndex) -> None:
        """Override default delegate paint method for icons and gridlines."""
        super().paint(painter, option, index)
        if not self.model.repo_data:
            return
        try:
            column = Column(index.column())
        except ValueError:
            # Column out of range
            return
        if (self.model.bad_data(index) and column != Column.WARNING
           and column != Column.REFRESH):
            return
        icon = None
        if column == Column.OPEN_FOLDER:
            icon = self.folder_icon
        elif column == Column.OPEN_DIFFTOOL:
            if ((not self.model.repo_data[index.row()]['bare'])
                and (self.model.repo_data[index.row()]['working_tree_changes']
                     or self.model.repo_data[index.row()]['commit_count'] > 1)):
                icon = self.difftool_icon
        elif column == Column.OPEN_TERMINAL:
            icon = self.terminal_icon
        elif column == Column.OPEN_IDE:
            icon = self.ide_icon
        elif column == Column.REFRESH:
            icon = self.refresh_icon
        elif column == Column.WARNING:
            if self.model.repo_data[index.row()]['warning'] is not None:
                icon = self.warn_icon

        if icon is not None:
            size = option.rect.toRectF().size()
            size.scale(size.width() * ICON_SCALE_FACTOR,
                       size.height() * ICON_SCALE_FACTOR,
                       Qt.AspectRatioMode.KeepAspectRatio)
            rect = QRectF(option.rect.toRectF().topLeft(), size)
            rect.moveCenter(option.rect.toRectF().center())
            icon.renderer().render(painter, rect)

        oldPen = painter.pen()
        painter.setPen(QPen(GRIDLINE_COLOUR, 1))
        painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
        painter.drawLine(option.rect.topLeft(), option.rect.bottomLeft())
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.drawLine(option.rect.topLeft(), option.rect.topRight())
        painter.setPen(oldPen)
