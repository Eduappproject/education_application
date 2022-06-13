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

form_class = uic.loadUiType("student_client.ui")[0]
port_num = 2090


# 상담 채팅 클라이언트 스레드
class ClientWorker(QThread):
    client_data_emit = pyqtSignal(str)

    def run(self):
        print("Q스레드 실행됨")
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
        self.backButton_2.clicked.connect(self.backButton_2_event)
        self.idFindButton.clicked.connect(self.idFindButton_event)
        self.pwFindButton.clicked.connect(self.pwFindButton_event)
        self.idFindPageEmailButton.clicked.connect(self.idFindPageEmailButton_event)
        self.pwFindPageIdButton.clicked.connect(self.pwFindPageIdButton_event)
        self.pwFindPageEmailButton.clicked.connect(self.pwFindPageEmailButton_event)


        self.chatLineEdit.returnPressed.connect(self.chat_msg_input)  # 상담방에서 채팅메시지 입력시
        self.chatBackButton.clicked.connect(self.chatBackButton_event)  # 상담방에서 나가기 버튼 누를시
        # 아이디 비밀번호 미리 입력(디버그 용,삭제해도 상관없음)
        self.loginLineEdit.setText("wwdS")
        self.loginLineEdit_2.setText("ppp")
        # 메인 화면
        self.mainPageCounselButton.clicked.connect(self.mainPageCounselButton_event)  # 상담 버튼
        self.mainPageQuestionButton.clicked.connect(self.mainPageQuestionButton_event)  # 문제 풀기 버튼
        # 커밋용
        # 문제 풀기 페이지
        self.questionListWidget.itemClicked.connect(self.questionListWidget_event)  # 문제 주제 리스트를 클릭했을때 실행되는 함수
        self.questionChoiceButton.clicked.connect(self.questionChoiceButton_event)  # 문제의 주제를 선택하면 실행되는 함수
        self.answerLineEdit.returnPressed.connect(self.answerLineEdit_event) # 답을 입력하고 엔터를 누르면 실행되는 함수

        # 회원가입화면 lineEdit
        self.lineEdit_text_changed()
        self.lineEdit_new_name.textChanged[str].connect(self.lineEdit_text_changed)
        self.lineEdit_new_id.textChanged[str].connect(self.lineEdit_text_changed)
        self.lineEdit_new_pw.textChanged[str].connect(self.lineEdit_text_changed)
        self.lineEdit_new_pw_check.textChanged[str].connect(self.lineEdit_text_changed)
        self.lineEdit_email.textChanged[str].connect(self.lineEdit_text_changed)

        # 소켓 생성
        self.sock = socket(AF_INET, SOCK_STREAM)
        i = 0
        while True:
            try:
                self.sock.connect(('127.0.0.1', port_num + i))
                print(f'클라이언트에서 포트번호 {port_num + i} 에 서버 연결 성공')
                break  # 서버 생성에 성공하면 반복문 멈춤
            except:
                pass
                print(f'클라이언트에서 포트번호 {port_num + i} 에 서버 연결 실패')
                # 생성에 실패(오류)하면 반복문 멈추지 않음
            i += 1
            if i > 3:
                print("서버 연결에 실패했습니다.")
                input("엔터키를 누를시 재시도 합니다")
                i = 0

        # self.user = ClientWorker()
        # self.user.sock = self.sock
        # self.user.client_data_emit.connect(self.sock_msg)
        # self.user.start()

    # 로그인 화면
    def loginPushButton_event(self):
        if not self.loginLineEdit.text() or not self.loginLineEdit_2.text():
            print("아이디와 비밀번호를 입력하세요.")
            return
        self.sock.send(f"login/{self.loginLineEdit.text()}/{self.loginLineEdit_2.text()}/student".encode())
        self.loginLineEdit.setText("")
        self.loginLineEdit_2.setText("")

        msg = self.sock.recv(1024).decode()
        self.sock_msg(msg)

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
        user_data = [self.lineEdit_new_pw.text()
            , self.lineEdit_new_name.text()
            , self.lineEdit_email.text()
            , "student"]  # 서버로 보낼 가입자 데이터를 순서에 맞게 리스트로 만든다
        # 서버에서 "/" 를 기준으로 구분하기때문에 그에 맞춰서 "/".join 을 이용해서 각데이터 사이에 "/" 넣고 보낸다
        self.sock.send("/".join(user_data).encode())
        self.login_page()

    # 회원가입 창을 닫는 버튼
    def BackButton_event(self):
        self.sock.send("Q_reg".encode())
        self.login_page()

    # 아이디 중복확인 버튼
    def SignUpCheckButton_event(self):
        input_id = self.lineEdit_new_id.text()
        self.sock.send(input_id.encode())

        msg = self.sock.recv(1024).decode()
        self.sock_msg(msg)

    def backButton_2_event(self):
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

        self.check_msg = str(random.randrange(1000, 10000))
        print(f"인증번호:{self.check_msg}")
        # ses = smtplib.SMTP('smtp.gmail.com', 587)  # smtp 세션 설정
        # ses.starttls()
        # # 이메일을 보낼 gmail 계정에 접속
        # ses.login('uihyeon.bookstore@gmail.com', 'ttqe mztd lljo tguh')
        # msg = MIMEText('인증번호: ' + self.check_msg)  # 보낼 메세지 내용을 적는다
        # msg['subject'] = 'PyQt5 에서 인증코드를 발송했습니다.'  # 보낼 이메일의 제목을 적는다
        # # 앞에는 위에서 설정한 계정, 두번째에는 이메일을 보낼 계정을 입력
        # ses.sendmail('uihyeon.bookstore@gmail.com', email, msg.as_string())
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

    def login_page(self):
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

    def idFindButton_event(self):
        """
        이메일 전송 find_id/email
        """
        print("id 찾기 버튼 누름")
        self.stackedWidget.setCurrentIndex(2)

    def pwFindButton_event(self):
        """
        아이디 확인 find_pw/id
        이메일 전송 email
        """
        print("pw 찾기 버튼 누름")
        self.stackedWidget.setCurrentIndex(3)
        self.pwFindPageIdLineEdit.setEnabled(True)
        self.pwFindPageEmailLineEdit.setEnabled(False)
        self.pwFindPageIdButton.setEnabled(True)
        self.pwFindPageEmailButton.setEnabled(False)

    def idFindPageEmailButton_event(self):
        id_find_page_email = self.idFindPageEmailLineEdit.text()
        self.sock.send(f"find_id/{id_find_page_email}".encode())

        msg = self.sock.recv(1024).decode()
        self.sock_msg(msg)

    def pwFindPageIdButton_event(self):
        pw_find_id_text = self.pwFindPageIdLineEdit.text()
        self.sock.send(f"find_pw/{pw_find_id_text}".encode())
        recv_msg = self.sock.recv(1024).decode()
        if "!NO" == recv_msg:
            print("iderror")
        else:  # !NO 가 아니라면 무조건 !OK 로 판정한다
            self.pwFindPageIdLineEdit.setEnabled(False)
            self.pwFindPageEmailLineEdit.setEnabled(True)
            self.pwFindPageIdButton.setEnabled(False)
            self.pwFindPageEmailButton.setEnabled(True)

    def pwFindPageEmailButton_event(self):
        pw_find_email_text = self.pwFindPageEmailLineEdit.text()
        self.sock.send(pw_find_email_text.encode())
        recv_msg = self.sock.recv(1024).decode()
        if "!NO" == recv_msg:
            print("iderror")
        else:
            self.sock.send("plz_pw".encode())
            pw_find_pw_text = self.sock.recv(1024).decode()
            print(f"이메일로 보낸 비밀번호{pw_find_pw_text}")
            email = self.pwFindPageEmailLineEdit.text()
            self.pwFindPageIdLineEdit.setText("")
            self.pwFindPageEmailLineEdit.setText("")
            self.stackedWidget.setCurrentIndex(0)
            self.loginLabel.setText(f"이메일로 비밀번호가 전송되었습니다.")

            # # 이메일로 아이디 보내기
            # ses = smtplib.SMTP('smtp.gmail.com', 587)  # smtp 세션 설정
            # ses.starttls()
            # # 이메일을 보낼 gmail 계정에 접속
            # ses.login('uihyeon.bookstore@gmail.com', 'ttqe mztd lljo tguh')
            # self.check_msg = pw_find_pw_text
            # msg = MIMEText('찾으시는 비밀번호: ' + self.check_msg)  # 보낼 메세지 내용을 적는다
            # msg['subject'] = 'PyQt5 에서 찾으시는 비밀번호를 발송했습니다.'  # 보낼 이메일의 제목을 적는다
            # # 앞에는 위에서 설정한 계정, 두번째에는 이메일을 보낼 계정을 입력
            # ses.sendmail('uihyeon.bookstore@gmail.com', email, msg.as_string())
            # # 이메일로 아이디 보냈다

    def mainPageCounselButton_event(self):
        # 상담버튼을 눌렀다
        self.stackedWidget.setCurrentIndex(5)
        self.sock.send(f"chat_request{self.userNameLabel.text()}".encode())
        self.T = ClientWorker()
        self.T.client_data_emit.connect(self.chat_msg)
        self.T.sock = self.sock
        self.T.start()

    def chatBackButton_event(self):
        self.chatTextBrowser.clear()
        self.chatLineEdit.setText("")
        self.sock.send("/나가기".encode())
        self.stackedWidget.setCurrentIndex(4)

    def chat_msg_input(self):
        msg = self.chatLineEdit.text()
        if msg == "/나가기":
            self.chatTextBrowser.clear()
            self.chatLineEdit.setText("")
            self.sock.send("/나가기".encode())
            self.stackedWidget.setCurrentIndex(4)
            return
        self.chatLineEdit.setText("")
        self.sock.send(msg.encode())

    # 문제 풀기 주제 선택 실행되는 함수
    def questionListWidget_event(self):
        text_data = self.questionListWidget.currentItem().text()
        self.questionChoiceButton.setText(text_data)
        self.questionChoiceButton.setEnabled(True)

    def mainPageQuestionButton_event(self):
        self.stackedWidget.setCurrentIndex(6)
        self.questionChoiceButton.setText("주제를 선택해주세요.")
        self.questionChoiceButton.setEnabled(False)

    # 문제 주제를 선택하고 문제 푸는 페이지로 넘어가는 버튼을 눌렀을때 실행되는 함수
    def questionChoiceButton_event(self):
        self.question_num = 0
        print(self.questionChoiceButton.text(), "주제 선택됨\n해당 주제를 서버로 보내서 문제를 받아옴")
        self.stackedWidget.setCurrentIndex(7)
        question_request_dict = {
            "조류": "bird"
            , "포유류": "mammal"
        }
        question_request_text = self.questionChoiceButton.text()
        self.answerLineEdit.setEnabled(False)
        self.sock.send(f"question_request/{question_request_dict[question_request_text]}".encode())
        question_data = self.sock.recv(16384).decode()
        question_data_1 = question_data[len("!Question//"):question_data.find("!Answer//")]
        question_data_2 = question_data[question_data.find("!Answer//") + len("!Answer//"):]
        question_data_1 = question_data_1.split("//")
        question_data_2 = question_data_2.split("//")
        print(len(question_data_1), len(question_data_2))
        self.question_data_base = list(zip(question_data_1, question_data_2))
        self.answerLineEdit.setEnabled(True)
        self.answerLineEdit.setText("")
        for q, a in self.question_data_base:
            print(f"문제:{q}\n정답:{a}")
        random.shuffle(self.question_data_base)
        print("len self.question_data_base", len(self.question_data_base))
        self.question_page()

    def question_page(self):
        if len(self.question_data_base) <= self.question_num:
            print("축하합니다 모든문제를 풀었습니다\n이제 서버로 푼문제의 개수와 원래있던 포인트를 전송합니다")
            return False
        Q, A = self.question_data_base[self.question_num]
        split_n = 35
        for i in range(1, (len(Q) // split_n) + 1):
            Q = f"{Q[:i * split_n]}\n{Q[i * split_n:]}"  # 단어가 화면을 삐져나오는걸 방지하기위해 일정간격으로 줄바꿈을 줌
        self.questionLabel.setText(Q)
        self.questionLabel.adjustSize()
        self.answerLabel.setText(A)
        self.answerLabel.adjustSize()

        # 화면에 표시된 문제 라벨의 세로 위치 + 높이
        question_height = self.questionLabel.height() + self.questionLabel.y()
        self.answerLabel_3.move(self.answerLabel.x() - 30, question_height) # '정답'이라 적힌 라벨
        self.answerLabel.move(self.answerLabel.x(), question_height + 5) # 정답이 적히는 라벨
        self.answerLabel_4.move(self.answerLineEdit.x() - 30, question_height + 50) # '답'이라 적힌 라벨
        self.answerLineEdit.move(self.answerLineEdit.x(), question_height + 50) # 답을 입력하는 라인에딧
        self.questionNumLabel.setText(f"{self.question_num + 1}/{len(self.question_data_base)}")
        self.question_num += 1

    def answerLineEdit_event(self):
        stident_result = self.answerLineEdit.text()
        question_answer = self.answerLabel.text()
        self.answerLineEdit.setText("")
        if not self.question_page():
            print("문제풀이 끝남")


    @pyqtSlot(str)
    def chat_msg(self, msg):
        self.chatTextBrowser.append(msg)

    # 클라이언트가 서버로 받은 메시지를 메인스레드 에서 처리하기 위해 만든 함수
    def sock_msg(self, msg):
        if "!OK" in msg:
            page_index = self.stackedWidget.currentIndex()
            if 0 == page_index:  # 로그인 페이지
                user_data = msg.split("/")
                print(f"로그인해서 받은 유저정보 {user_data}")
                # 할일:유저정보를 저장해야한다
                self.loginLabel.setText("")
                self.userNameLabel.setText(user_data[1])
                self.userPointLabel.setText(user_data[2])
                self.stackedWidget.setCurrentIndex(4)
            if 1 == page_index:  # 회원가입 페이지
                self.lineEdit_new_id.setEnabled(False)
                self.SignUpCheckButton.setEnabled(False)
                self.lineEdit_email.setEnabled(True)
            if 2 == page_index:  # 아이디 찾기 페이지
                print("id 찾기 페이지 이메일 전송")
                self.sock.send("plz_id".encode())
                find_id = self.sock.recv(1024).decode()
                print(f"이메일로 보내질 아이디:{find_id}")
                email = self.idFindPageEmailLineEdit.text()
                self.idFindPageEmailLineEdit.setText("")
                self.stackedWidget.setCurrentIndex(0)
                self.loginLabel.setText(f"이메일로 아이디가 전송되었습니다.")
                self.loginLabel.adjustSize()

                # # 이메일로 아이디 보내기
                # ses = smtplib.SMTP('smtp.gmail.com', 587)  # smtp 세션 설정
                # ses.starttls()
                # # 이메일을 보낼 gmail 계정에 접속
                # ses.login('uihyeon.bookstore@gmail.com', 'ttqe mztd lljo tguh')
                #
                # self.check_msg = find_id
                # msg = MIMEText('찾으시는 아이디: ' + self.check_msg)  # 보낼 메세지 내용을 적는다
                # msg['subject'] = 'PyQt5 에서 찾으시는 아이디를 발송했습니다.'  # 보낼 이메일의 제목을 적는다
                # # 앞에는 위에서 설정한 계정, 두번째에는 이메일을 보낼 계정을 입력
                # ses.sendmail('uihyeon.bookstore@gmail.com', email, msg.as_string())
                # # 이메일로 아이디 보냈다

            if 3 == page_index:  # 비밀번호 찾기 페이지
                print("pw 찾기 페이지 id 찾기 성공")

        if msg == "!NO":
            page_index = self.stackedWidget.currentIndex()
            if 0 == page_index:  # 로그인 페이지
                self.loginLabel.setText(f"로그인에 실패했습니다.")
                self.loginLabel.adjustSize()
            if 1 == page_index:  # 회원가입 페이지
                print("중복된 아이디가 있습니다")
            if 2 == page_index:  # 아이디 찾기 페이지
                print("id 찾기 페이지 실패")
                self.stackedWidget.setCurrentIndex(0)
                self.loginLabel.setText(f"아이디를 찾을수없습니다.")
                self.loginLabel.adjustSize()
            if 3 == page_index:  # 비밀번호 찾기 페이지
                print("pw 찾기 페이지 실패")
                self.stackedWidget.setCurrentIndex(0)
                self.loginLabel.setText(f"비밀번호를 찾을수없습니다.")
                self.loginLabel.adjustSize()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
