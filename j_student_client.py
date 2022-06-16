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


# 문제집 데이터를 받는 스레드
class QuestionRecvWorker(QThread):
    question_recv_signal = pyqtSignal(list)

    def run(self):
        for i in range(3):
            print("Q스레드: 문제를 받기위한 Q스레드 실행함")
            question_data = self.sock.recv(2 ** 14).decode()
            print(f"Q스레드: 서버로부터 {len(question_data.encode())} 바이트의 문제를 받음")
            if len(question_data.encode()) < 30:  # 받은 메시지가 30바이트 미만일때 서버에 다시 요청
                self.sock.send(self.question_load.encode())
                continue
            question_data_1 = question_data[len("!Question//"):question_data.find("!Answer//")]
            question_data_2 = question_data[question_data.find("!Answer//") + len("!Answer//"):]
            question_data_1 = question_data_1.split("//")
            question_data_2 = question_data_2.split("//")
            recv_data = list(zip(question_data_1, question_data_2))
            print("Q스레드: 서버에서 받은 문제를 메인 스레드로 보냄")
            self.question_recv_signal.emit(recv_data)
            return
        print("Q스레드: API 에서 문제를 불러오는데 실패 했습니다")
        self.question_recv_signal.emit([("문제가 정상적으로 오지 않았습니다", "스미마세ㅇ")])
        return


# 상담 채팅 클라이언트 스레드
class ClientWorker(QThread):
    client_data_emit = pyqtSignal(str)

    def run(self):
        print("Q스레드 실행됨")
        while True:
            try:
                msg = self.sock.recv(1024).decode()
                print("msg:", msg)
                if not msg:
                    print("연결 종료(메시지 없음)")
                    break
            except:
                print("연결 종료(예외 처리)")
                break
            else:
                if msg[-4:] == "/나가기" or msg[-5:] == "상담방없음":
                    self.client_data_emit.emit("/나가기")
                    break
                self.client_data_emit.emit(msg)
        print("상담 스레드 종료")


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
        self.idFindButton.clicked.connect(self.idFindButton_event)  # id 찾기 페이지로 가기
        self.pwFindButton.clicked.connect(self.pwFindButton_event)  # pw 찾기 페이지로 가기
        self.idFindPageEmailButton.clicked.connect(self.idFindPageEmailButton_event)  # id 찾기 이메일 전송
        self.pwFindPageIdButton.clicked.connect(self.pwFindPageIdButton_event)  # pw 찾기 id 확인
        self.pwFindPageEmailButton.clicked.connect(self.pwFindPageEmailButton_event)  # pw 찾기 이메일 전송

        self.chatLineEdit.returnPressed.connect(self.chat_msg_input)  # 상담방에서 채팅메시지 입력시
        self.chatBackButton.clicked.connect(self.chatBackButton_event)  # 상담방에서 나가기 버튼 누를시
        # 아이디 비밀번호 미리 입력(디버그 용,삭제해도 상관없음)
        self.loginLineEdit.setText("wwdS")
        self.loginLineEdit_2.setText("ppp")
        # 메인 화면
        self.mainPageCounselButton.clicked.connect(self.mainPageCounselButton_event)  # 상담 버튼
        self.mainPageQuestionButton.clicked.connect(self.mainPageQuestionButton_event)  # 문제 풀기 버튼
        self.mainPageQandAButton.clicked.connect(lambda: self.QandA_list_load())  # QandA 게시판 버튼

        # QandA 게시판 화면
        self.QandAPageBackButton.clicked.connect(self.QandAPageBackButton_event)
        self.QandAPagePushButton.clicked.connect(self.QandAPagePushButton_enent)
        self.QandAPageTableWidget.cellClicked.connect(self.QandAPageTableWidget_event)

        # QandA 작성 화면
        self.QandAAddPagebackButton.clicked.connect(lambda: self.QandA_list_load())  # 뒤로가기 버튼(QandA 목록으로)
        self.QandAAddPagePushButton.clicked.connect(self.QandAAddPagePushButton_event)

        # QandA 게시글 보기 화면
        self.QandAViewPageBackButton.clicked.connect(lambda: self.QandA_list_load())  # 뒤로가기 버튼(QandA 목록으로)
        self.QandAViewPageCommentPushButton.clicked.connect(self.QandAViewPageCommentPushButton_event)

        # 학생 전용 기능
        # 문제 풀기 페이지
        self.questionListWidget.itemClicked.connect(self.questionListWidget_event)  # 문제 주제 리스트를 클릭했을때 실행되는 함수
        self.questionListWidget.itemDoubleClicked.connect(self.questionChoiceButton_event)
        self.questionChoiceButton.clicked.connect(self.questionChoiceButton_event)  # 문제의 주제를 선택하면 실행되는 함수
        self.QuestionPageListWidget.itemDoubleClicked.connect(self.answerLineEdit_event)  # 답 선택 버튼
        # self.answerLineEdit.returnPressed.connect(self.answerLineEdit_event)  # 답을 입력하고 엔터를 누르면 실행되는 함수
        # 문제 문답 결과 페이지
        self.goMainPageButton.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(4))

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
        self.user_id = self.loginLineEdit.text()
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
        ses = smtplib.SMTP('smtp.gmail.com', 587)  # smtp 세션 설정
        ses.starttls()
        # 이메일을 보낼 gmail 계정에 접속
        ses.login('uihyeon.bookstore@gmail.com', 'ttqe mztd lljo tguh')
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
        print("id 찾기 버튼 누름")
        self.stackedWidget.setCurrentIndex(2)

    def pwFindButton_event(self):
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

            # 이메일로 아이디 보내기
            ses = smtplib.SMTP('smtp.gmail.com', 587)  # smtp 세션 설정
            ses.starttls()
            # 이메일을 보낼 gmail 계정에 접속
            ses.login('uihyeon.bookstore@gmail.com', 'ttqe mztd lljo tguh')
            self.check_msg = pw_find_pw_text
            msg = MIMEText('찾으시는 비밀번호: ' + self.check_msg)  # 보낼 메세지 내용을 적는다
            msg['subject'] = 'PyQt5 에서 찾으시는 비밀번호를 발송했습니다.'  # 보낼 이메일의 제목을 적는다
            # 앞에는 위에서 설정한 계정, 두번째에는 이메일을 보낼 계정을 입력
            ses.sendmail('uihyeon.bookstore@gmail.com', email, msg.as_string())
            # 이메일로 아이디 보냈다

    def mainPageCounselButton_event(self):
        # 상담버튼을 눌렀다
        self.stackedWidget.setCurrentIndex(5)
        self.sock.send(f"chat_request{self.userNameLabel.text()}".encode())
        room_list = self.sock.recv(2 ** 14).decode()
        self.chat_msg(room_list)

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
        if msg == "/나가기" or msg == "/나가기":
            self.chat_exet()
            return
        self.chatLineEdit.setText("")
        self.sock.send(msg.encode())

    def chat_exet(self):
        self.chatTextBrowser.clear()
        self.chatLineEdit.setText("")
        self.sock.send("/나가기".encode())
        self.stackedWidget.setCurrentIndex(4)

    # 문제 풀기 주제 선택 실행되는 함수
    def questionListWidget_event(self):
        text_data = self.questionListWidget.currentItem().text()
        self.questionChoiceButton.setText(text_data)
        self.questionChoiceButton.setEnabled(True)

    def mainPageQuestionButton_event(self):
        self.stackedWidget.setCurrentIndex(6)
        self.questionChoiceButton.setText("주제를 선택해주세요.")
        self.questionChoiceButton.setEnabled(False)
        self.questionListWidget.setEnabled(True)

    # 문제 주제를 선택하고 문제 푸는 페이지로 넘어가는 버튼을 눌렀을때 실행되는 함수
    def questionChoiceButton_event(self):
        self.question_num = 0
        print(self.questionChoiceButton.text(), "주제 선택됨\n해당 주제를 서버로 보내서 문제를 받아옴")
        self.question_request_dict = {  # 객채 변수 선언을 매번 반복해 컴퓨터 자원낭비지만 구현목적으로 여기 작성하곘습니다.
            "조류(API)": "bird"
            , "포유류(API)": "mammal"
        }  # 리스트에 적힌 주제명에 따라서 서버로 보낼 메시지
        self.question_request = self.questionChoiceButton.text()
        self.questionChoiceButton.setText("서버에서 문제 불러오는중")
        self.questionChoiceButton.setEnabled(False)
        self.answerLineEdit.setEnabled(False)
        self.questionListWidget.setEnabled(False)
        question_load = f"question_request/{self.question_request_dict[self.question_request]}"
        self.sock.send(question_load.encode())
        self.recv_data = QuestionRecvWorker()
        self.recv_data.question_load = question_load
        self.recv_data.sock = self.sock
        self.recv_data.question_recv_signal.connect(self.recv_data_pyqt_slot)
        self.recv_data.start()

    @pyqtSlot(list)
    def recv_data_pyqt_slot(self, recv_data):
        self.stackedWidget.setCurrentIndex(7)
        self.question_data_base = recv_data
        self.answer_list = [A_data for Q_data,A_data in recv_data]
        print(f"문제 확인:{len(self.question_data_base)}개의 문제를 받음")
        self.answerLineEdit.setEnabled(True)
        self.answerLineEdit.setText("")
        random.shuffle(self.question_data_base)  # 문제 섞어 버리기ㅣㅣㅣㅣ
        self.questions_completion_list = []  # 정답과 오답을 기록할 리스트
        self.question_page()

    def question_page(self):
        if len(self.question_data_base) <= self.question_num:
            print("축하합니다 모든문제를 풀었습니다\n이제 서버로 맞춘 문제의 개수와 포인트를 전송합니다")
            return False
        Q, A = self.question_data_base[self.question_num]
        self.questionTextBrowser.clear()
        self.questionTextBrowser.append(Q)
        self.answer = A
        self.answerLabel.setText(A)
        self.answerLabel.adjustSize()

        answers = random.sample(list(set(self.answer_list)), 5)
        if self.answer not in answers:
            i = random.randint(0,len(answers)-1)
            answers[i] = self.answer
        for answer in answers:
            self.QuestionPageListWidget.addItem(answer)

        # 화면에 표시된 문제 라벨의 세로 위치 + 높이
        question_height = self.questionTextBrowser.height() + self.questionTextBrowser.y()
        self.answerLabel_3.move(self.answerLabel_2.x(), question_height)  # '정답'이라 적힌 라벨
        self.answerLabel.move(self.answerLabel.x(), question_height)  # 정답이 적히는 라벨
        self.answerLabel_4.move(self.answerLabel_2.x(), question_height + 57)  # '답'이라 적힌 라벨
        self.answerLineEdit.move(self.answerLineEdit.x(), question_height + 50)  # 답을 입력하는 라인에딧
        self.questionNumLabel.setText(f"남은 문제 {self.question_num + 1}/{len(self.question_data_base)}")
        self.questionNumLabel.adjustSize()
        self.question_num += 1
        return True



    """
    리스트 위젯 시그널,함수 모음
    self.QuestionPageListWidget.itemDoubleClicked.connect(함수) # 더블클릭시 해당 함수 실행
    obj = self.QuestionPageListWidget.currentItem() # 리스트위젯에서 선택한 항목을 객체로 반환
    obj.text() # 반환된 객체에서 텍스트 가져오기
    self.QuestionPageListWidget.addItem(문자열) # 리스트 위젯 항목 추가
    self.QuestionPageListWidget.clear() # 리스트 위젯 클리어
    """

    # 답 제출 버튼(답을 입력한 다음에 엔터입력)
    def answerLineEdit_event(self):
        obj = self.QuestionPageListWidget.currentItem()  # 리스트위젯에서 선택한 항목을 객체로 반환
        stident_result = obj.text()  # 반환된 객체에서 텍스트 가져오기
        self.QuestionPageListWidget.clear() # 리스트 위젯 클리어

        # stident_result = self.answerLineEdit.text()
        # question_answer = self.answerLabel.text()
        # self.answerLineEdit.setText("")
        # 답과 정답을 비교
        print(f"학생 답: {stident_result} == 정답: {self.answer}:{stident_result == self.answer}")
        # 정답이면 정답으로 저장
        if stident_result == self.answer:
            print("정답입니다")
            self.questions_completion_list.append(True)
        else:  # 아니면 오답
            print("오답입니다")
            self.questions_completion_list.append(False)
        # 모든 문제를 풀었다면
        if not self.question_page():
            self.stackedWidget.setCurrentIndex(8)  # 문제 결과 보기

            api_or_teachques = "api" if "API" in self.questionListWidget.currentItem().text() else "teachques"
            total = len(self.questions_completion_list)  # 총문제
            ok_question = len([i for i in self.questions_completion_list if i])  # 맞춘 개수
            add_point = ok_question * 10  # 흭득 포인트
            percent = int((ok_question / total) * 100)  # 이번 문제의 정답률

            self.questionsCompletionLabel_1.setText(
                f"주제:{self.question_request}({self.question_request_dict[self.question_request]})")
            self.questionsCompletionLabel_1.adjustSize()
            self.questionsCompletionLabel_2.setText(
                f"총 문제 {total}개 중 {ok_question}개 정답\n{add_point} 포인트 흭득")
            self.questionsCompletionLabel_2.adjustSize()

            msg = (
                "quesiton_complete"
                , self.question_request_dict[self.question_request]
                , str(percent)
                , str(self.user_point + add_point)
                , api_or_teachques
            )  # 서버로 보낼 데이터 튜플로 만들기
            msg = "/".join(msg)  # 문자 사이에 "/" 끼워넣기
            self.sock.send(msg.encode())  # quetion_complete/과목명/정답률/포인트/주제종류(api, teachques)
            print(f"문제 풀이완료 서버로 다음과 같은 메시지 전송:{msg}")  # quetion_complete/과목명/점수/포인트
            self.questionsCompletionLabel_3.setText("수고하셧습니다")
            self.questionsCompletionLabel_3.adjustSize()
            self.user_point = self.user_point + add_point  # 메인메뉴에 표시할 나의 포인트 계산
            self.userPointLabel.setText(str(self.user_point))

    # QandA 게시판에서 뒤로가기 눌렀을때
    def QandAPageBackButton_event(self):
        self.stackedWidget.setCurrentIndex(4)  # 메인페이지 페이지

    def QandAPagePushButton_enent(self):
        self.idLabel.setText(self.user_id)
        self.nameLabel.setText(self.user_name)
        self.stackedWidget.setCurrentWidget(self.QandAAddPage)

    # 게시글을 눌렀을때
    def QandAPageTableWidget_event(self):
        # 새로운 게시글을 위해 작성된 게시글 지우기
        self.QandAViewPageTextBrowser.clear()
        self.QandAViewPageTextEdit.clear()
        table_num = self.QandAPageTableWidget.currentRow()
        table_widget_item = self.QandAPageTableWidget.item(table_num, 0)
        num = table_widget_item.text()
        post_name = self.QandAPageTableWidget.item(table_num, 1).text()
        num = int(num)
        print(f"{num} 번 QnA 게시글 누름")
        self.sock.send(f"Q&A게시글보기/{num}".encode())
        buf_size = int(self.sock.recv(1024).decode())
        self.sock.send(f"게시글을 받기위한 버퍼사이즈 가 {buf_size} 로 설정됨".encode())
        data = self.sock.recv(buf_size).decode()
        post, comment_list = data.split("<-post/comment->")
        p_text, p_user_name, p_user_id = post.split("/")
        # 게시글 정보 화면에 출력하기
        self.QandAViewPageTextBrowser.append(f"글 제목:{post_name}")
        self.QandAViewPageTextBrowser.append(f"글쓴이:{p_user_name}({p_user_id})")
        self.QandAViewPageTextBrowser.append(f"{p_text}")
        comment_list = comment_list.split("/")
        print(f"comment_list 값:{comment_list}")
        for comment_data in comment_list:
            if comment_data:
                comment_name, comment_id, comment_text = comment_data.split("&#")
                comment = f"\n댓글 작성자:{comment_name}({comment_id})\n{comment_text}"
                self.QandAViewPageTextBrowser.append(comment)
        self.idLabel_2.setText(self.user_id)
        self.nameLabel_2.setText(self.user_name)
        self.stackedWidget.setCurrentWidget(self.QandAViewPage)  # 게시글을 보기위한 페이지로 이동

    # QandA 게시판 게시글 보기 페이지
    # 댓글 작성
    def QandAViewPageCommentPushButton_event(self):
        comment = self.QandAViewPageTextEdit.toPlainText()
        if not comment:
            print("입력된 댓글이 없습니다")
            QMessageBox.question(self, '입력 없음', '댓글에 문자를 작성해주세요', QMessageBox.Yes)
            return
        self.QandAViewPageTextEdit.clear()
        table_num = self.QandAPageTableWidget.currentRow()
        table_widget_item = self.QandAPageTableWidget.item(table_num, 0)
        qnanum = table_widget_item.text()
        writename = self.user_name
        writeid = self.user_id
        self.sock.send(f"Q&A댓글작성/{qnanum}/{comment}/{writename}/{writeid}".encode())
        self.QandAPageTableWidget_event()

    # QandA 게시판 Q&A 작성 페이지
    # 게시글 목록 요청
    def QandA_list_load(self):
        self.QandAPageTableWidget.clearContents()
        self.stackedWidget.setCurrentWidget(self.QandAPage)  # Q&A 게시판 페이지
        self.sock.send('Q&A게시글목록요청'.encode())
        load_data = self.sock.recv(2 ** 14).decode()
        print("load_data", load_data)
        if "게시글 없음" == load_data:
            QMessageBox.question(self, '데이터 없음', '작성된 QnA가 없습니다.', QMessageBox.Yes)
            print("QandA 게시글이 없습니다.")
        else:
            print("게시글 갱신중")
            load_data_list = load_data.split("/")
            self.QandAPageTableWidget.setRowCount(len(load_data_list))
            for i in range(len(load_data_list)):
                num, name = load_data_list[i].split(".")  # 글번호 와 글제목
                self.QandAPageTableWidget.setItem(i, 0, QTableWidgetItem(num))
                self.QandAPageTableWidget.setItem(i, 1, QTableWidgetItem(name))

    # 작성 버튼
    def QandAAddPagePushButton_event(self):
        Q = self.QandAAddPageeLineEdit.text()  # 제목
        A = self.QandAAddPageeTextEdit.toPlainText()  # 내용
        if not Q:
            QMessageBox.question(self, '데이터 없음', '제목을 입력해주세요.', QMessageBox.Yes)
            return
        elif not A:
            QMessageBox.question(self, '데이터 없음', '내용을 입력해주세요.', QMessageBox.Yes)
            return
        id = self.user_id
        name = self.user_name
        msg = "/".join(("Q&A작성", name, id, Q, A))
        self.sock.send(f"작성할 Q&A게시글 크기:{len(msg.encode())}".encode())
        self.sock.recv(255)  # 버퍼 사이즈 변경했다는 신호 받기
        self.sock.send(msg.encode())
        self.QandAAddPageeTextEdit.clear()
        self.QandAAddPageeLineEdit.clear()
        self.QandA_list_load()

    @pyqtSlot(str)
    def chat_msg(self, msg):
        self.chatTextBrowser.append(msg)
        if msg == "/상담방없음" or msg == "/나가기":
            self.chat_exet()

    # 클라이언트가 서버로 받은 메시지를 메인스레드 에서 처리하기 위해 만든 함수
    def sock_msg(self, msg):
        if "!OK" in msg:
            page_index = self.stackedWidget.currentIndex()
            if 0 == page_index:  # 로그인 페이지
                user_data = msg.split("/")
                print(f"로그인해서 받은 유저정보 {user_data}")
                self.loginLabel.setText("")
                self.user_name = user_data[1]
                self.userNameLabel.setText(self.user_name)
                self.userNameLabel.adjustSize()
                self.user_point = int(user_data[2])
                self.userPointLabel.setText(str(self.user_point))
                self.userPointLabel.adjustSize()
                self.stackedWidget.setCurrentIndex(4)  # 메인 화면
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

                # 이메일로 아이디 보내기
                ses = smtplib.SMTP('smtp.gmail.com', 587)  # smtp 세션 설정
                ses.starttls()
                # 이메일을 보낼 gmail 계정에 접속
                ses.login('uihyeon.bookstore@gmail.com', 'ttqe mztd lljo tguh')

                self.check_msg = find_id
                msg = MIMEText('찾으시는 아이디: ' + self.check_msg)  # 보낼 메세지 내용을 적는다
                msg['subject'] = 'PyQt5 에서 찾으시는 아이디를 발송했습니다.'  # 보낼 이메일의 제목을 적는다
                # 앞에는 위에서 설정한 계정, 두번째에는 이메일을 보낼 계정을 입력
                ses.sendmail('uihyeon.bookstore@gmail.com', email, msg.as_string())
                # 이메일로 아이디 보냈다

            if 3 == page_index:  # 비밀번호 찾기 페이지
                print("pw 찾기 페이지 id 찾기 성공")

        if msg == "!NO":
            page_index = self.stackedWidget.currentIndex()
            if 0 == page_index:  # 로그인 페이지
                self.loginLabel.setText(f"로그인에 실패했습니다.")
                self.loginLabel.adjustSize()
            if 1 == page_index:  # 회원가입 페이지
                self.SignUpLabel.setText("중복된 아이디가 있습니다")
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
