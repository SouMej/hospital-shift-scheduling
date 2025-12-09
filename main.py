import sys
from PyQt5 import QtWidgets
from gui import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()