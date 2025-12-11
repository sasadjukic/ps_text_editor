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

        # create actions first so toolbar can reuse them
        self.create_actions()
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

    # We no longer create a top menu bar; the File menu is a drop-down on the toolbar

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        # Add a File drop-down button to the toolbar using the actions created in create_actions
        file_button = QToolButton(self)
        file_button.setText("File")
        file_menu = QMenu(self)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.close_action)
        file_button.setMenu(file_menu)
        # Make button show the menu immediately on click
        file_button.setPopupMode(QToolButton.InstantPopup)
        toolbar.addWidget(file_button)

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
