import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QFileDialog, QMessageBox, QToolBar
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My Modern Text Editor")
        self.setGeometry(200, 100, 900, 600)

        self.editor = QPlainTextEdit()
        self.setCentralWidget(self.editor)

        self.create_toolbar()
        self.current_file = None

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)

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

def load_stylesheet(app, path):
    with open(path, "r") as f:
        app.setStyleSheet(f.read())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_stylesheet(app, "dark_theme.qss")
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec())
