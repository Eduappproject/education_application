import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from socket import *

form_class = uic.loadUiType("untitled.ui")[0]

class WindowClass(QMainWindow, form_class):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.stackedWidget.setCurrentIndex(0)

        self.loginPushButton.clicked.connect(self.loginPushButton_event)  # 로그인 버튼
        self.SignUpPushButton.clicked.connect(self.SignUpPushButton_event)  # 회원가입(페이지로 이동) 버튼
        self.SignUpPushButton_2.clicked.connect(self.SignUpPushButton_2_event)  # 회원가입 버튼
        self.BackButton.clicked.connect(self.BackButton_event)  # 회원가입 취소 버튼
        # self.EmailCheckPushButton.clicked.connect()  # 이메일 인증요청 버튼
        # self.EmailCheckNumberPushButton.clicked.connect()  # 이메일에 도착한 인증번호 확인 버튼
        # # 메인 화면
        # self.mainButton_1.clicked.connect()  # 등급 버튼
        # self.mainButton_2.clicked.connect()  # 퀴즈 버튼
        # self.mainButton_3.clicked.connect()  # 상담 버튼
        # self.mainButton_4.clicked.connect()  # Q&A 버튼

        # 회원가입화면 lineEdit
        self.lineEdit_new_id.textChanged[str].connect(self.lineEdit_text_changed)
        self.lineEdit_new_pw.textChanged[str].connect(self.lineEdit_text_changed)
        self.lineEdit_new_pw_check.textChanged[str].connect(self.lineEdit_text_changed)

    # 로그인 화면
    def loginPushButton_event(self):
        self.stackedWidget.setCurrentIndex(2)
    def SignUpPushButton_event(self):
        self.stackedWidget.setCurrentIndex(1)
    # 회원가입 화면
    def lineEdit_text_changed(self):  # 이름과 비밀번호를 입력할때마다 실행됨
        text_check_1 = ""
        text_check_2 = ""
        text_check_3 = ""
        text_check_1 += self.lineEdit_new_id.text()
        text_check_2 += self.lineEdit_new_pw.text()
        text_check_3 += self.lineEdit_new_pw_check.text()
        # text() 메서드는 lineEdit 에 입력된 글자를 가져옵니다
        if text_check_1 and text_check_2 and text_check_3:  # 셋중하나ㅂ라도 문자가 없다면(Faise) 문자를 입력해달라고합니다
            self.SignUpLabel.setText("아이디와 비밀번호를 입력해주세요")
        else:
            self.SignUpLabel.setText("회원가입 버튼을 눌러주세요")
    def SignUpPushButton_2_event(self):
        self.stackedWidget.setCurrentIndex(0)
    def BackButton_event(self):
        self.stackedWidget.setCurrentIndex(0)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
