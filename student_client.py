import sys
import time
import random
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from socket import *
from email.mime.text import MIMEText  # 이메일 전송을 위한 라이브러리 import
import smtplib
import re  # 정규 표현식

form_class = uic.loadUiType("student.ui")[0]
port_num = 2090

# 클라이언트 스레드
class ClientWorker(QThread):
    client_data_emit = pyqtSignal(str)

    def run(self):
        while True:
            try:
                msg = self.sock.recv(1024).decode()
                print(msg)
                if not msg:
                    print("연결 종료(메시지 없음)")
                    break
            except:
                print("연결 종료(예외 처리)")
                break
            else:
                self.client_data_emit.emit(f"{msg}")
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
        # port_num = 8500

        self.sock.bind(('', port_num))
        self.server_data_emit.emit(f'포트번호 {port_num} 에 서버 생성됨')
        self.port_num = port_num

        self.sock.listen(5)
        while True:
            # c 에 소켓 객체를 넣고 a 에 주소를 넣는다
            c, a = self.sock.accept()
            while True:
                try:
                    msg = c.recv(1024).decode()
                    # 받은 메시지를 화면에 표현한다(디버그 용)
                    self.server_data_emit.emit(f"{msg}")
                    if msg == "signup":
                        while True:
                            id_check = c.recv(1024).decode()
                            if id_check == "Q_reg":
                                self.server_data_emit.emit(f"{id_check}")
                                break
                            self.server_data_emit.emit(f"{id_check}")
                            if id_check in ["qqq", "www", "eee"]:
                                c.send("!NO".encode())
                            else:
                                c.send("!OK".encode())

                except:
                    break


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
        self.SignUpCheckButton.clicked.connect(self.SignUpCheckButton_event)
        self.EmailCheckPushButton.clicked.connect(self.EmailCheckPushButton_event)  # 이메일 인증요청 버튼
        self.EmailCheckNumberPushButton.clicked.connect(self.EmailCheckNumberPushButton_event)  # 이메일에 도착한 인증번호 확인 버튼
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
        self.lineEdit_email.textChanged[str].connect(self.lineEdit_text_changed)


        # 서버 스레드 선언
        self.T = AcceptWorker()
        self.T.server_data_emit.connect(self.server_log)
        self.T.start()  # 서버 스레드 실행
        time.sleep(1)
        # 메모
        # from pprint import pprint  # 보기 편하게 프린트 해주는 함수
        # pprint(self.__dict__)  # 접근 가능한 객체의 변수를 표시(해당 변수에 접근해 메서드를 쓸수있다
        # self.__dict__['label'].setText("학생용 클라이이언트 로그인 화면")  # 예시
        # # 이를 이용해서 여러개의 이벤트 핸들러를 설정하거나 수십개의 라벨을 원하는 텍스트로 바꿀수 있다

        # 소켓 생성
        self.sock = socket(AF_INET, SOCK_STREAM)
        # 포트 번호 8500 ~ 8599 사이에 서버를 찾는다

        self.sock.connect(('127.0.0.1', port_num))
        self.logTextBrowser.append(f'클라이언트에서 포트번호 {port_num} 에 서버 연결 성공')

        self.user = ClientWorker()
        self.user.sock = self.sock
        self.user.client_data_emit.connect(self.sock_msg)
        self.user.start()
        # self.sock.recv(1024)

    # 로그인 화면
    def loginPushButton_event(self):
        # id = self.loginLineEdit.text()
        # pw = self.loginLineEdit_2.text()
        # if id == "":
        #     id = "아이디"
        # if pw == "":
        #     pw = "비밀번호"

        self.sock.send(f"{id},{pw}".encode())

        self.stackedWidget.setCurrentIndex(2)
        self.loginLineEdit.setText("")
        self.loginLineEdit_2.setText("")

    # 회원가입 페이지로 이동
    def SignUpPushButton_event(self):
        self.sock.send("signup".encode())  # 서버에게 회원가입 하겠다고 보냄
        self.loginLineEdit.setText("")
        self.loginLineEdit_2.setText("")
        self.stackedWidget.setCurrentIndex(1)

    # 회원가입 화면
    def lineEdit_text_changed(self):  # 이름과 비밀번호를 입력할때마다 실행됨
        # 아이디 중복확인 버튼 활성화 여부

        # text() 메서드는 lineEdit 에 입력된 글자를 가져옵니다fewfw
        # 하나라도 문자가 없다면(Faise) 문자를 입력해달라고합니다
        self.SignUpPushButton_2.setEnabled(False)
        label_text = []
        if not self.lineEdit_new_name.text():
            label_text.append("이름를 입력해주세요.")

        if not self.lineEdit_new_id.text():
            label_text.append("아이디를 입력해주세요.")
            self.SignUpCheckButton.setEnabled(False)
        elif not self.lineEdit_new_id.isEnabled():
            self.SignUpCheckButton.setEnabled(False)
        else:
            self.SignUpCheckButton.setEnabled(True)

        if not (self.lineEdit_new_pw.text() or self.lineEdit_new_pw_check.text()):
            label_text.append("비밀번호를 입력해 주세요.")
        elif self.lineEdit_new_pw.text() != self.lineEdit_new_pw_check.text():
            label_text.append("비밀번호가 동일하지 않습니다.")
        elif not self.lineEdit_email.text():
            label_text.append("이메일을 입력해주세요.")
            self.EmailCheckPushButton.setEnabled(False)
        else:
            if self.lineEdit_email.isEnabled():
                self.EmailCheckPushButton.setEnabled(True)
            else:
                self.EmailCheckPushButton.setEnabled(False)

        if not (self.lineEdit_email_check.text() and not self.EmailCheckNumberPushButton.isEnabled()):
            label_text.append("인증번호를 입력해주세요.")
        if not label_text and not self.lineEdit_new_id.isEnabled():
            # 위에있는 모든 조건을 통과했다면 정상적인 회원가입이 가능하다고 판단하고 회원가입 버튼을 활성화 합니다.
            self.SignUpPushButton_2.setEnabled(True)
            label_text.append("회원가입 버튼을 눌러주세요.")
        self.SignUpLabel.setText("\n".join(label_text))
        self.SignUpLabel.adjustSize()  # 라벨에 적힌 글자에맞춰서 라벨 사이즈를 조절해주는 메서드

    def SignUpPushButton_2_event(self):  # 회원가입 버튼
        user_data = [f"{self.lineEdit_new_name.text()}"
            ,f"{self.lineEdit_new_pw.text()}"
            ,f"{self.lineEdit_new_name.text()}"
            ,f"{self.lineEdit_email.text()}"
            ,f"student"]  # 서버로 보낼 가입자 데이터를 순서에 맞게 리스트로 만든다
        # 서버에서 "/" 를 기준으로 구분하기때문에 그에 맞춰서 "/".join 을 이용해서 각데이터 사이에 "/" 넣고 보낸다
        self.sock.send("/".join(user_data).encode())
        self.sign_up_back()

    # 회원가입 창을 닫는 버튼
    def BackButton_event(self):
        self.sock.send("Q_reg".encode())
        self.sign_up_back()

    # 아이디 중복확인 버튼
    def SignUpCheckButton_event(self):
        input_id = self.lineEdit_new_id.text()
        self.sock.send(input_id.encode())


    def beackButton_2_event(self):
        self.stackedWidget.setCurrentIndex(0)

    # 이메일 인증 요청 버튼을 눌렀을때
    # 해당 이메일에 인증번호 보내기
    # 이메일에 보낸 인증번호를 클라이언트에 저장하고
    # 인증번호 인증시 클라이언트에 저장된 인증번호와 일치하는지 확인하기
    def EmailCheckPushButton_event(self):
        email = self.lineEdit_email.text()
        re_text = re.compile(".+@\w+\.\w+\.*\w*")

        # 이메일 형식이 맞는지 검사합니다
        if re_text.match(email):
            print("사용가능한 이메일")
        else:
            print("잘못된 이메일")
            return

        ses = smtplib.SMTP('smtp.gmail.com', 587)  # smtp 세션 설정
        ses.starttls()
        # 이메일을 보낼 gmail 계정에 접속
        ses.login('uihyeon.bookstore@gmail.com', 'ttqe mztd lljo tguh')

        self.check_msg = str(random.randrange(1000, 10000))
        msg = MIMEText('인증번호: ' + self.check_msg)  # 보낼 메세지 내용을 적는다
        msg['subject'] = 'PyQt5 에서 인증코드를 발송했습니다.'  # 보낼 이메일의 제목을 적는다
        # 앞에는 위에서 설정한 계정, 두번째에는 이메일을 보낼 계정을 입력
        ses.sendmail('uihyeon.bookstore@gmail.com', email, msg.as_string())

        # 꺼야하는 버튼 끄기
        self.lineEdit_email.setEnabled(False)
        self.EmailCheckPushButton.setEnabled(False)
        self.lineEdit_email_check.setEnabled(True)
        self.EmailCheckNumberPushButton.setEnabled(True)

    # 인증번호 인증 버튼
    def EmailCheckNumberPushButton_event(self):
        if self.lineEdit_email_check.text() == self.check_msg:
            print("인증되었습니다")
            self.lineEdit_email_check.setEnabled(False)
            self.EmailCheckNumberPushButton.setEnabled(False)
            self.SignUpPushButton_2.setEnabled(True)

    def sign_up_back(self):
        self.stackedWidget.setCurrentIndex(0)
        # 회원가입이 끝나고 로그인페이지로 이동하면서 입력창을 빈칸으로 만든다
        self.lineEdit_new_name.setText("")
        self.lineEdit_new_id.setText("")
        self.lineEdit_new_pw.setText("")
        self.lineEdit_new_pw_check.setText("")
        self.lineEdit_email.setText("")
        self.lineEdit_email_check.setText("")
        self.lineEdit_new_id.setEnabled(True)
        self.SignUpCheckButton.setEnabled(True)
        self.EmailCheckPushButton.setEnabled(False)
        self.lineEdit_email_check.setEnabled(False)
        self.lineEdit_email.setEnabled(False)
        self.EmailCheckNumberPushButton.setEnabled(False)
        self.SignUpPushButton_2.setEnabled(False)
        self.check_msg = ""

    # 테스트용 서버의 동작읋 확인하기 위해서 만든 함수
    @pyqtSlot(str)
    def server_log(self, data):
        self.logTextBrowser.append(data)

    # 클라이언트가 서버로 받은 메시지를 메인스레드 에서 처리하기 위해 만든 함수
    @pyqtSlot(str)
    def sock_msg(self, msg):
        self.logTextBrowser_2.append(msg)
        if msg == "!OK":
            page_index = self.stackedWidget.currentIndex()
            if 1 == page_index:
                self.lineEdit_new_id.setEnabled(False)
                self.SignUpCheckButton.setEnabled(False)
                self.lineEdit_email.setEnabled(True)
        if msg == "!NO":
            page_index = self.stackedWidget.currentIndex()
            if 1 == page_index:
                self.logTextBrowser_2.append("중복된 아이디가 있습니다")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
