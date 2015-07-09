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

class HotkeyManager(QtCore.QObject):
    def __init__(self,parentWidget):
        super(HotkeyManager,self).__init__()
        self.hotkeys = {}
        self.parentWidget = parentWidget

    def defineHotkeys(self,hotkeys):
        toDelete = []
        for voltage,hk in self.hotkeys.items():
            for hk2 in hotkeys.keys():
                if hk2 in hk.keys():
                    toDelete.append(voltage)
                    QtGui.QMessageBox.warning(self.parentWidget, "Hotkey Conflict",\
                """Hotkey conflict. Removed keys for {}.""".format(voltage.name))
                    voltage.hasHotkeys = False
                    break

        for td in toDelete:
            del self.hotkeys[td]

        self.hotkeys[self.sender().voltage] = hotkeys

    def keyPressed(self,key):
        for voltage,hotkeys in self.hotkeys.items():
            if key.key() in hotkeys:
                if hotkeys[key.key()] == "Increase Voltage":
                    voltage.increase()
                elif hotkeys[key.key()] == "Decrease Voltage":
                    voltage.decrease()
                elif hotkeys[key.key()] == "Increase Stepsize":
                    voltage.increaseStep()
                elif hotkeys[key.key()] == "Decrease Stepsize":
                    voltage.decreaseStep()