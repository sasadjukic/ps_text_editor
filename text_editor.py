import sys
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QFileDialog, QMessageBox, QToolBar,
    QToolButton, QMenu, QWidget, QLabel, QStatusBar, QInputDialog
)
from PySide6.QtGui import QAction, QKeySequence, QIcon, QPainter, QColor, QFont, QTextFormat, QPalette
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtWidgets import QApplication, QStyle, QTextEdit


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(200, 100, 900, 600)

        # Use a CodeEditor (QPlainTextEdit subclass) that supports line numbers
        self.editor = CodeEditor()
        self.setCentralWidget(self.editor)

        # create actions first so toolbar and menubar can reuse them
        self.create_actions()
        self.create_menubar()
        self.create_toolbar()
        # create status bar showing Ln/Col and word count
        self.create_statusbar()
        self.current_file = None
        self.untitled_count = 1
        self.update_window_title()

    def create_actions(self):
        # New File
        self.new_action = QAction("New", self)
        self.new_action.setShortcut(QKeySequence.New)  # Ctrl+N
        self.new_action.triggered.connect(self.new_file)
        self.new_action.setStatusTip("Create a new document")
        self.new_action.setToolTip("New (Ctrl+N)")

        # Open File
        self.open_action = QAction("Open...", self)
        self.open_action.setShortcut(QKeySequence.Open)  # Ctrl+O
        self.open_action.triggered.connect(self.open_file)
        self.open_action.setStatusTip("Open an existing file")
        self.open_action.setToolTip("Open (Ctrl+O)")

        # Save File
        self.save_action = QAction("Save", self)
        self.save_action.setShortcut(QKeySequence.Save)  # Ctrl+S
        self.save_action.triggered.connect(self.save_file)
        self.save_action.setStatusTip("Save the current document")
        self.save_action.setToolTip("Save (Ctrl+S)")

        # Save As
        self.save_as_action = QAction("Save As...", self)
        self.save_as_action.setShortcut(QKeySequence.SaveAs)  # Ctrl+Shift+S
        self.save_as_action.triggered.connect(self.save_file_as)
        self.save_as_action.setStatusTip("Save the current document under a new name")
        self.save_as_action.setToolTip("Save As (Ctrl+Shift+S)")

        # Close File
        self.close_action = QAction("Close", self)
        self.close_action.setShortcut(QKeySequence.Close)  # Ctrl+W
        self.close_action.triggered.connect(self.close_file)
        self.close_action.setStatusTip("Close the current document")
        self.close_action.setToolTip("Close (Ctrl+W)")

        # Search
        self.search_action = QAction("Search", self)
        self.search_action.setShortcut(QKeySequence("Ctrl+F"))
        self.search_action.triggered.connect(self._on_search)
        self.search_action.setStatusTip("Find text in the document")
        self.search_action.setToolTip("Search (Ctrl+F)")

        # --- Edit actions ---
        # We'll track the last edit-related action so "Repeat" can re-run it
        self._last_edit_action = None

        self.copy_action = QAction("Copy", self)
        self.copy_action.setShortcut(QKeySequence.Copy)  # Ctrl+C
        self.copy_action.triggered.connect(self._on_copy)

        self.paste_action = QAction("Paste", self)
        self.paste_action.setShortcut(QKeySequence.Paste)  # Ctrl+V
        self.paste_action.triggered.connect(self._on_paste)

        self.cut_action = QAction("Cut", self)
        self.cut_action.setShortcut(QKeySequence.Cut)  # Ctrl+X
        self.cut_action.triggered.connect(self._on_cut)

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence.Undo)  # Ctrl+Z
        self.undo_action.triggered.connect(self._on_undo)

        # Redo: use Ctrl+Y
        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence("Ctrl+Y"))  # Ctrl+Y
        self.redo_action.triggered.connect(self._on_redo)

        # Repeat: Shift+Ctrl+Y
        self.repeat_action = QAction("Repeat", self)
        self.repeat_action.setShortcut(QKeySequence("Ctrl+Shift+Y"))  # Shift+Ctrl+Y
        self.repeat_action.triggered.connect(self._on_repeat)

        # Initial enable/disable states
        self.copy_action.setEnabled(False)
        self.cut_action.setEnabled(False)
        # Undo/redo availability will be driven by document signals
        self.undo_action.setEnabled(False)
        self.redo_action.setEnabled(False)

    def _load_icon(self, theme_name, fallback):
        icon = QIcon.fromTheme(theme_name)
        if not icon or icon.isNull():
            return QApplication.style().standardIcon(fallback)
        return icon

    # We no longer create a top menu bar; the File menu is a drop-down on the toolbar

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        # Make toolbar vertical and dock it to the left area
        toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        # Add quick toolbar actions: New, Open, Save, Close in this order
        # Set icons if available
        # Helper to retrieve themed or fallback icons
        # Use the shared icon loader
        def _icon(theme_name, fallback):
            return self._load_icon(theme_name, fallback)

        self.new_action.setIcon(_icon("document-new", QStyle.SP_FileIcon))
        self.open_action.setIcon(_icon("document-open", QStyle.SP_DialogOpenButton))
        self.save_action.setIcon(_icon("document-save", QStyle.SP_DialogSaveButton))
        self.close_action.setIcon(_icon("window-close", QStyle.SP_DialogCloseButton))

        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.close_action)
        # Add Search icon below Close
        self.search_action.setIcon(self._load_icon("edit-find", QStyle.SP_FileDialogContentsView))
        toolbar.addAction(self.search_action)

        # Connect editor signals to enable/disable actions based on context
        # copyAvailable(bool) is emitted when a selection is present
        self.editor.copyAvailable.connect(self.copy_action.setEnabled)
        self.editor.copyAvailable.connect(self.cut_action.setEnabled)

        # Document signals for undo/redo availability
        doc = self.editor.document()
        try:
            doc.undoAvailable.connect(self.undo_action.setEnabled)
            doc.redoAvailable.connect(self.redo_action.setEnabled)
        except Exception:
            # In case the API differs, fallback to checking availability manually
            pass

        # Keep the UI in sync at startup
        self.copy_action.setEnabled(bool(self.editor.textCursor().hasSelection()))
        self.cut_action.setEnabled(bool(self.editor.textCursor().hasSelection()))
        self.undo_action.setEnabled(doc.isUndoAvailable())
        self.redo_action.setEnabled(doc.isRedoAvailable())

    def create_menubar(self):
        """Create a proper menubar with File and Edit menus."""
        menubar = self.menuBar()
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        # add Save As with an icon if available
        self.save_as_action.setIcon(self._load_icon("document-save-as", QStyle.SP_DialogSaveButton))
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.close_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        # add icons to edit menu actions
        self.copy_action.setIcon(self._load_icon("edit-copy", QStyle.SP_DialogOpenButton))
        self.cut_action.setIcon(self._load_icon("edit-cut", QStyle.SP_DialogOpenButton))
        self.paste_action.setIcon(self._load_icon("edit-paste", QStyle.SP_DialogOpenButton))
        self.undo_action.setIcon(self._load_icon("edit-undo", QStyle.SP_ArrowBack))
        self.redo_action.setIcon(self._load_icon("edit-redo", QStyle.SP_ArrowForward))
        self.repeat_action.setIcon(self._load_icon("view-refresh", QStyle.SP_BrowserReload))
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addAction(self.cut_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.repeat_action)

    def create_statusbar(self):
        """Create status bar with line/column and word count indicators."""
        sb = self.statusBar()
        # Left part can show messages; we add two permanent widgets to the right
        self._status_word = QLabel("Words: 0")
        self._status_pos = QLabel("Ln 1, Col 1")
        # Slight padding
        self._status_word.setMargin(4)
        self._status_pos.setMargin(8)
        # Use editor text color for status labels so they are visible in dark theme
        try:
            status_color = self.editor._get_editor_text_color().name()
        except Exception:
            status_color = "#ffffff"
        self._status_word.setStyleSheet(f"color: {status_color};")
        self._status_pos.setStyleSheet(f"color: {status_color};")
        sb.addPermanentWidget(self._status_word)
        sb.addPermanentWidget(self._status_pos)

        # Connect editor signals to update status
        self.editor.cursorPositionChanged.connect(self._update_cursor_position)
        self.editor.textChanged.connect(self._update_word_count)

        # Initialize values
        self._update_cursor_position()
        self._update_word_count()

    def _update_cursor_position(self):
        cursor = self.editor.textCursor()
        # blockNumber() is zero-based
        ln = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self._status_pos.setText(f"Ln {ln}, Col {col}")

    def _update_word_count(self):
        text = self.editor.toPlainText()
        # count words using word boundaries
        words = re.findall(r"\b\w+\b", text)
        self._status_word.setText(f"Words: {len(words)}")

    def _on_search(self):
        # Prompt the user for a search string and find it in the document
        text, ok = QInputDialog.getText(self, "Find", "Find:")
        if not ok or not text:
            return
        found = self.editor.find(text)
        if not found:
            QMessageBox.information(self, "Not found", f"'{text}' was not found.")

    # --- Edit action handlers (TextEditor forwards to the editor widget) ---
    def _on_copy(self):
        self.editor.copy()
        self._last_edit_action = "copy"

    def _on_paste(self):
        self.editor.paste()
        self._last_edit_action = "paste"

    def _on_cut(self):
        self.editor.cut()
        self._last_edit_action = "cut"

    def _on_undo(self):
        self.editor.undo()
        self._last_edit_action = "undo"

    def _on_redo(self):
        self.editor.redo()
        self._last_edit_action = "redo"

    def _on_repeat(self):
        action = self._last_edit_action
        if not action:
            return
        if action == "copy":
            self.editor.copy()
        elif action == "paste":
            self.editor.paste()
        elif action == "cut":
            self.editor.cut()
        elif action == "undo":
            self.editor.undo()
        elif action == "redo":
            self.editor.redo()

    # --- File operations ---
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as file:
                    self.editor.setPlainText(file.read())
                self.current_file = path
                self.update_window_title()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def save_file(self):
        if not self.current_file:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt)")
            if not path:
                return
            self.current_file = path

        try:
            with open(self.current_file, "w", encoding="utf-8") as file:
                file.write(self.editor.toPlainText())
            self.update_window_title()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            return
        self.current_file = path
        self.save_file()
        self.update_window_title()

    def close_file(self):
        self.editor.clear()
        self.current_file = None
        self.untitled_count += 1
        self.update_window_title()

    def new_file(self):
        self.editor.clear()
        self.current_file = None
        self.untitled_count += 1
        self.update_window_title()

    def update_window_title(self):
        """Update the window title to show document name and editor name."""
        if self.current_file:
            import os
            doc_name = os.path.basename(self.current_file)
        else:
            doc_name = f"Untitled {self.untitled_count}"
        
        self.setWindowTitle(f"{doc_name} - My Modern Text Editor")


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self._editor.lineNumberAreaPaintEvent(event)


from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import QRect, QSize


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        # Calculate space needed for line numbers
        digits = len(str(max(1, self.blockCount())))
        space = self.fontMetrics().horizontalAdvance('9') * digits + 12
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def _get_editor_background_color(self):
        ss = QApplication.instance().styleSheet() or ""
        m = re.search(r"QPlainTextEdit\s*\{[^}]*background-color\s*:\s*([^;]+);", ss)
        if m:
            try:
                return QColor(m.group(1).strip())
            except Exception:
                pass
        return self.palette().color(QPalette.Base)

    def _get_editor_text_color(self):
        ss = QApplication.instance().styleSheet() or ""
        m = re.search(r"QPlainTextEdit\s*\{[^}]*(?<!-)color\s*:\s*([^;]+);", ss)
        if m:
            try:
                return QColor(m.group(1).strip())
            except Exception:
                pass
        return self.palette().color(QPalette.Text)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        # Removing the yellow highlight to avoid low-contrast issues with dark themes.
        # We intentionally do not set any extra selections here so the current line
        # remains unhighlighted and text visibility is preserved.
        self.setExtraSelections([])

    def lineNumberAreaPaintEvent(self, event):
        # Determine editor background and text color before creating the painter
        bg_color = self._get_editor_background_color()
        text_color = self._get_editor_text_color()
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), bg_color)
        
        # Set the painter font to match the editor's font
        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        height = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                # Use the editor's text color so numbers contrast correctly
                painter.setPen(text_color)
                painter.drawText(0, top, self.lineNumberArea.width() - 4, height, Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1


    # Note: file operation methods (open/save/close/new) and edit action handlers
    # are implemented on the TextEditor container and forward to this widget.

def load_stylesheet(app, path):
    with open(path, "r") as f:
        app.setStyleSheet(f.read())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_stylesheet(app, "dark_theme.qss")
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec())
