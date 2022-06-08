import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from socket import *

form_class = uic.loadUiType("untitled.ui")[0]


# 클라이언트 스레드
class ClientWorker(QThread):

    def run(self):
        pass
        # 서버에서 오는 값을 받을 준비 해야한다


# 서버 스레드(테스트 용)
class AcceptWorker(QThread):
    # 메인 스레드에 보낼 시그널 설정 (emit 로 데이터를 메인스레드에 전달)
    server_data_emit = pyqtSignal(str)

    def run(self):
        # 여기서 서버열기(서버 소켓 생성)
        self.sock = socket(AF_INET, SOCK_STREAM)
        # 유저 소켓 리스트 관리
        self.user_list = []
        # 포트 번호 8500 ~ 8599 사이에 서버를 연다
        port_num = 8500
        i = 0
        while i < 100:
            try:
                self.sock.bind(('', port_num + i))
                self.server_data_emit.emit(f'포트번호 {port_num + i} 에 서버 생성됨')
                self.port_num = port_num + i
                break  # 서버 생성에 성공하면 반복문 멈춤
            except:
                self.server_data_emit.emit(f'포트번호 {port_num + i} 에 서버 생성 실패')
                # 생성에 실패(오류)하면 반복문 멈추지 않음
            i += 1
            if i >= 100:
                input("\n\n서버를 열수 없습니다.\n엔터키를 누를시 재시도 합니다")
                i = 0

        self.sock.listen(5)

        while True:
            # c 에 소켓 객체를 넣고 a 에 주소를 넣는다
            c, a = self.sock.accept()
            # 접속하자마자 접속한 클라이언트가 자신의 정보를 표현하는 메시지를 서버로 보낸다
            # 그걸 서버가 받는다
            msg = c.recv(1024).decode()
            # 받은 메시지를 화면에 표현한다(디버그 용)
            self.server_data_emit.emit(f"msg:{msg}")


# 여기서 서버와 연결할 클라이언트 실행하기(클라이언트 소켓 생성)

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
        self.beackButton_2.clicked.connect(self.beackButton_2_event)
        # # 메인 화면
        # self.mainButton_1.clicked.connect()  # 등급 버튼
        # self.mainButton_2.clicked.connect()  # 퀴즈 버튼
        # self.mainButton_3.clicked.connect()  # 상담 버튼
        # self.mainButton_4.clicked.connect()  # Q&A 버튼

        # 회원가입화면 lineEdit
        self.lineEdit_text_changed()
        self.lineEdit_new_name.textChanged[str].connect(self.lineEdit_text_changed)
        self.lineEdit_new_id.textChanged[str].connect(self.lineEdit_text_changed)
        self.lineEdit_new_pw.textChanged[str].connect(self.lineEdit_text_changed)
        self.lineEdit_new_pw_check.textChanged[str].connect(self.lineEdit_text_changed)

        # 서버 스레드 선언
        self.T = AcceptWorker()
        self.T.server_data_emit.connect(self.server_log)
        self.T.start()  # 서버 스레드 실행

        # 메모
        # from pprint import pprint  # 보기 편하게 프린트 해주는 함수
        # pprint(self.__dict__)  # 접근 가능한 객체의 변수를 표시(해당 변수에 접근해 메서드를 쓸수있다
        # self.__dict__['label'].setText("학생용 클라이이언트 로그인 화면")  # 예시
        # # 이를 이용해서 여러개의 이벤트 핸들러를 설정하거나 수십개의 라벨을 원하는 텍스트로 바꿀수 있다

    # 로그인 화면
    def loginPushButton_event(self):
        id = self.loginLineEdit.text()
        pw = self.loginLineEdit_2.text()
        if id == "":
            id = "아이디"
        if pw == "":
            pw = "비밀번호"
        # 소켓 생성
        self.sock = socket(AF_INET, SOCK_STREAM)
        # 포트 번호 8500 ~ 8599 사이에 서버를 찾는다
        port_num = 8500
        i = 0
        while i < 100:
            try:
                self.sock.connect(('127.0.0.1', port_num + i))
                self.logTextBrowser.append(f'클라이언트에서 포트번호 {port_num + i} 에 서버 연결 성공')
                break  # 연결에 성공하면 반복문 멈춤
            except:
                self.logTextBrowser.append(f'클라이언트에서 포트번호 {port_num + i} 에 연결 실패')
                # 연결에 실패(오류)하면 반복문 멈추지 않음
            i += 1
            if i == 100:
                print("서버를 찾을수 없습니다")
                input("엔터키를 누를시 다시 검색합니다")
                i = 0
        self.sock.send(f"{id},{pw}".encode())

        self.stackedWidget.setCurrentIndex(2)
    def SignUpPushButton_event(self):
        self.stackedWidget.setCurrentIndex(1)

    # 회원가입 화면
    def lineEdit_text_changed(self):  # 이름과 비밀번호를 입력할때마다 실행됨
        # text() 메서드는 lineEdit 에 입력된 글자를 가져옵니다fewfw
        # 셋중하나라도 문자가 없다면(Faise) 문자를 입력해달라고합니다
        self.SignUpPushButton_2.setEnabled(False)
        label_text = []
        if not self.lineEdit_new_name.text():
            label_text.append("이름를 입력해주세요.")
        if not self.lineEdit_new_id.text():
            label_text.append("아이디를 입력해주세요.")
        if not (self.lineEdit_new_pw.text() or self.lineEdit_new_pw_check.text()):
            label_text.append("비밀번호를 입력해 주세요.")
        elif self.lineEdit_new_pw.text() != self.lineEdit_new_pw_check.text():
            label_text.append("비밀번호가 동일하지 않습니다.")
        if not label_text:
            # 위에있는 모든 조건을 통과했다면 정상적인 회원가입이 가능하다고 판단하고 회원가입 버튼을 활성화 합니다.
            self.SignUpPushButton_2.setEnabled(True)
            label_text.append("회원가입 버튼을 눌러주세요.")
        self.SignUpLabel.setText("\n".join(label_text))
        self.SignUpLabel.adjustSize()  # 라벨에 적힌 글자에맞춰서 라벨 사이즈를 조절해주는 메서드

    def SignUpPushButton_2_event(self):  # 회원가입 버튼
        self.lineEdit_new_name.text()
        self.lineEdit_new_id.text()
        self.lineEdit_new_pw_check.text()

        self.stackedWidget.setCurrentIndex(0)
        # 회원가입이 끝나고 로그인페이지로 이동하면서 입력창을 빈칸으로 만든다
        self.lineEdit_new_name.setText("")
        self.lineEdit_new_id.setText("")
        self.lineEdit_new_pw.setText("")
        self.lineEdit_new_pw_check.setText("")
        self.lineEdit_email.setText("")
        self.lineEdit_email_check.setText("")

    def BackButton_event(self):
        self.stackedWidget.setCurrentIndex(0)
        # 로그인페이지로 이동하면서 입력창을 빈칸으로 만든다
        self.lineEdit_new_name.setText("")
        self.lineEdit_new_id.setText("")
        self.lineEdit_new_pw.setText("")
        self.lineEdit_new_pw_check.setText("")
        self.lineEdit_email.setText("")
        self.lineEdit_email_check.setText("")

    @pyqtSlot(str)
    def server_log(self, data):
        self.logTextBrowser.append(data)

    def beackButton_2_event(self):
        self.stackedWidget.setCurrentIndex(0)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
