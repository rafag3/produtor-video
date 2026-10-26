import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
if __name__=="__main__":
    app=QApplication(sys.argv); app.setStyle("Fusion"); w=MainWindow(); w.show(); sys.exit(app.exec())
