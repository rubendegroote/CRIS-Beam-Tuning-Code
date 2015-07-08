from PyQt4 import QtCore,QtGui
from collections import OrderedDict

class HotkeyPrompt(QtGui.QDialog):
    """docstring for HotkeyPrompt"""
    def __init__(self,parent):
        super(HotkeyPrompt, self).__init__(parent)

        self.target = "Increase Voltage"
        self.keys = OrderedDict()
        self.keys["Increase Voltage"] = None
        self.keys["Decrease Voltage"] = None
        self.keys["Increase Stepsize"] = None
        self.keys["Decrease Stepsize"] = None

        self.labels = {}
        self.buttons = {}

        self.init_UI()


    def init_UI(self):
        self.layout = QtGui.QGridLayout(self)

        for i,n in enumerate(self.keys.keys()):
            self.buttons[n] = QtGui.QPushButton(n)
            self.buttons[n].clicked.connect(self.changeKeyTarget)
            self.layout.addWidget(self.buttons[n],i,0)
            self.labels[n] = QtGui.QLabel("")
            self.layout.addWidget(self.labels[n],i,1)

    def changeKeyTarget(self,target):
        self.target = self.sender().text()

    def keyPressEvent(self,e):
        self.keys[self.target] = e.key()
        self.labels[self.target].setText(e.text())


    @staticmethod
    def hotkeys(parent):
        hotkey = HotkeyPrompt(parent)
        result = hotkey.exec_()
        return hotkey.keys
