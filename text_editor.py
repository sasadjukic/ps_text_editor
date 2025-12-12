import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QFileDialog, QMessageBox, QToolBar,
    QToolButton, QMenu
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My Modern Text Editor")
        self.setGeometry(200, 100, 900, 600)

        self.editor = QPlainTextEdit()
        self.setCentralWidget(self.editor)

        # create actions first so toolbar and menubar can reuse them
        self.create_actions()
        self.create_menubar()
        self.create_toolbar()
        self.current_file = None

    def create_actions(self):
    # Open File
        self.open_action = QAction("Open...", self)
        self.open_action.setShortcut(QKeySequence.Open)  # Ctrl+O
        self.open_action.triggered.connect(self.open_file)

        # Save File
        self.save_action = QAction("Save", self)
        self.save_action.setShortcut(QKeySequence.Save)  # Ctrl+S
        self.save_action.triggered.connect(self.save_file)

        # Save As
        self.save_as_action = QAction("Save As...", self)
        self.save_as_action.setShortcut(QKeySequence.SaveAs)  # Ctrl+Shift+S
        self.save_as_action.triggered.connect(self.save_file_as)

        # Close File
        self.close_action = QAction("Close", self)
        self.close_action.setShortcut(QKeySequence.Close)  # Ctrl+W
        self.close_action.triggered.connect(self.close_file)

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

    # We no longer create a top menu bar; the File menu is a drop-down on the toolbar

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        # Add quick toolbar actions (Open/Save/SaveAs/Close) as buttons
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.save_as_action)
        toolbar.addAction(self.close_action)

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
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.close_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addAction(self.cut_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.repeat_action)

    # --- Edit action handlers ---
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
        # Re-run the last edit action when possible
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
        # Keep last action as repeat-able

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as file:
                    self.editor.setPlainText(file.read())
                self.current_file = path
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
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            return
        self.current_file = path
        self.save_file()

    def close_file(self):
        self.editor.clear()
        self.current_file = None

def load_stylesheet(app, path):
    with open(path, "r") as f:
        app.setStyleSheet(f.read())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_stylesheet(app, "dark_theme.qss")
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec())
