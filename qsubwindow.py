import sys
from PyQt5 import uic
from PyQt5.QtWidgets import *
form_second = uic.loadUiType("subwindow.ui")[0]
print(form_second)
class qsubwindow(QDialog, QWidget,form_second):

    def __init__(self):
        super(qsubwindow, self).__init__()
        self.initUI()
        self.show() #두번째창 실행

    def initUI(self):
        self.setupUi(self)
        self.qbackbutton.clicked.connect(self.qbackbutton_clicked_event)
        self.qpushbutton2.clicked.connect(self.qpushbutton2_press_event)
###
    def qbackbutton_clicked_event(self):
        self.close()
    def qpushbutton2_press_event(self):
        print("버튼이 눌렷음")
        sendQe = self.qlineEdit.text()
        self.qtextBrowser.append(sendQe)
        self.qlineEdit.clear()



