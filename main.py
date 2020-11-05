from PyQt5 import QtWidgets
from window import Window
import sys

app = QtWidgets.QApplication([])
application = Window()
application.show()
sys.exit(app.exec())