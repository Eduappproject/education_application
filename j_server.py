from multiprocessing import set_forkserver_preload
import requests
import re
from bs4 import BeautifulSoup
import string
import random
import socket
import threading
import sqlite3
import datetime
from datetime import date
import sys

PORT = 2090
BUF_SIZE = 2048
lock = threading.Lock()
clnt_imfor = []  # [[소켓, id, type, name]]
chat_rooms = {}  # ["교사 아이디":[교사 소켓,학생 소켓], ["교사 아이디":[교사 소켓,학생 소캣]]


class Worker(threading.Thread):
    def __init__(self, sock):
        super().__init__()
        self.clnt_sock = sock

    def run(self):
        for clnt_imfo in clnt_imfor:
            if clnt_imfo[0] == self.clnt_sock:
                clnt_num = clnt_imfor.index(clnt_imfo)
                break  # 접속한 클라이언트 소켓이 리스트 몇번째에 있는지 저장

        while True:
            sys.stdout.flush()  # 버퍼 비워주는거
            try:
                clnt_msg = self.clnt_sock.recv(BUF_SIZE)  # 클라이언트에서 메세지 수신
            except ConnectionResetError as e:
                print("(self.clnt_sock)오류 프린트:↲\n\t",e) # 오류표시
                break
            print(f"clnt_sock가 보낸값:{clnt_msg.decode()}")  # 받는값 확인
            if not clnt_msg:  # 연결상태 확인 - 연결 종료시 삭제
                lock.acquire()  # 쓰레드 락
                self.delete_imfor()
                lock.release()
                break
            clnt_msg = clnt_msg.decode()  # 숫자->문자열로 바꾸는거 맞나?  데이터 보낼때 incode 로 하고

            sys.stdin.flush()



            if 'signup' == clnt_msg:
                self.sign_up()
            elif clnt_msg.startswith('login/'):  # startswitch -->문자열중에 특정 문자를 찾고싶거나, 특정문자로 시작하는 문자열, 특정문자로 끝이나는 문자열 등
                clnt_msg = clnt_msg.replace('login/', '')  # clnt_msg에서 login/ 자름
                self.log_in(clnt_msg, clnt_num)
            elif clnt_msg.startswith('find_id/'):
                clnt_msg = clnt_msg.replace('find_id/', '')
                self.find_id(clnt_msg)
            elif clnt_msg.startswith('find_pw/'):
                clnt_msg = clnt_msg.replace('find_pw/', '')
                self.find_pw(clnt_msg)
            elif clnt_msg.startswith('myinfo'):
                clnt_msg = clnt_msg.replace('myinfo', '')
                self.send_user_information(clnt_num)
            elif clnt_msg.startswith('edit_data'):
                clnt_msg = clnt_msg.replace('edit_data', '')
                self.edit_data(clnt_num, clnt_msg)
            elif clnt_msg.startswith('remove'):
                self.remove(clnt_num)  # 전달받은 내용에따라 해당하는 함수 실행
            # 1대1 상담 입장(지금은 전체 채팅방으로 구현)
            elif clnt_msg.startswith('chat_request'):
                print("상담버튼클릭 확인됨")
                clnt_msg = clnt_msg.replace('chat_request', '')  # 상담버튼클릭이라는 단어가 있는 메시지를 받으면
                # 그뒤에는 해당 사용자의 이름을 같이 받는다
                self.chat_wait(clnt_msg, clnt_num)  # 채팅방 입장(함수의 인수로 소켓과 사용자의 이름을 넣는다)
            elif clnt_msg.startswith('question_request/'):  # question_request/주제명 (bird, mammal)
                clnt_msg = clnt_msg.replace('question_request/', '')
                self.question_send(clnt_msg)
            elif clnt_msg.startswith('quesiton_complete/'):  # quetion_complete/과목명/정답률/포인트/주제종류(api, teachques)
                clnt_msg = clnt_msg.replace('quesiton_complete/', '')
                self.test_result_handle(clnt_msg, clnt_num)
            elif clnt_msg.startswith('교사문제출제/'):  # 
                clnt_msg = clnt_msg.replace('교사문제출제/', '')
                self.teacher_quetion_update(clnt_msg, clnt_num)
            elif clnt_msg.startswith('교사문제요청/'):  # 
                clnt_msg = clnt_msg.replace('교사문제요청/', '')
                self.teacher_question_send(clnt_msg, clnt_num)
            elif clnt_msg.startswith('통계요청/'):  # 
                clnt_msg = clnt_msg.replace('통계요청/', '')
                self.scoredata_send(clnt_msg, clnt_num)

            # QnA게시글작성시 버퍼사이즈 문제로 추가한 조건문
            elif "작성할 Q&A게시글 크기:" == clnt_msg[:14]:
                one_buf_size = int(clnt_msg[14:])
                self.clnt_sock.send(str(one_buf_size).encode())
                clnt_msg = self.clnt_sock.recv(one_buf_size).decode()
                print(f"clnt_sock이 게시글 작성을 위해 보낸값:\n\t{clnt_msg}")  # 받는값 확인
                self.qna_write(clnt_msg[6:])  # 'Q&A작성/' 문자 제외하고 함수에 넣기(문자열 슬라이싱)

            elif clnt_msg.startswith('Q&A게시글목록요청'):
                clnt_msg = clnt_msg.replace('Q&A게시글목록요청', '')
                self.posts_list_send()
            elif clnt_msg.startswith('Q&A게시글보기/'):  # /게시글번호
                clnt_msg = clnt_msg.replace('Q&A게시글보기/', '')
                self.show_qna(clnt_msg)
            elif clnt_msg.startswith('Q&A댓글작성/'):
                clnt_msg = clnt_msg.replace('Q&A댓글작성/', '')
                self.qna_comment_update(clnt_msg)
            else:
                continue

    def dbcon(self):  # db연결
        con = sqlite3.connect('serverDB.db')  # DB 연결
        c = con.cursor()  # 커서
        return (con, c)

    def edit_data(self, clnt_num, clnt_msg):  # 데이터 베이스 정보변경
        print(clnt_msg)
        id = clnt_imfor[clnt_num][1]
        con, c = self.dbcon()
        if clnt_msg.startswith('_name/'):
            clnt_msg = clnt_msg.replace('_name/', '')
            lock.acquire()
            c.execute("UPDATE usertbl SET username = ? WHERE userid = ?", (clnt_msg, id))
            con.commit()
            lock.release()
            con.close()
        elif clnt_msg.startswith('_pw/'):
            clnt_msg = clnt_msg.replace('_pw/', '')
            lock.acquire()
            c.execute("UPDATE usertbl SET userpw = ? WHERE userid = ?", (clnt_msg, id))
            con.commit()
            lock.release()
            con.close()
        else:
            con.close()
            return
            # 전달받은 메세지에서 구분자를 통해 해당 DB에 데이터 저장

    def sign_up(self):  # 회원가입
        con, c = self.dbcon()
        user_data = []

        while True:
            print("비로그인 회원가입 페이지 입장")
            imfor = self.clnt_sock.recv(BUF_SIZE)
            imfor = imfor.decode()
            if imfor == "Q_reg":  # 회원가입 창 닫을 때 함수 종료
                con.close()
                break
            c.execute("SELECT userid FROM usertbl where userid = ?", (imfor,))  # usertbl 테이블에서 id 컬럼 추출
            row = c.fetchone()
            if row != None:  # DB에 없는 id면 None
                self.clnt_sock.send('!NO'.encode())
                print('id_overlap')
                con.close()
                return

            self.clnt_sock.send('!OK'.encode())  # 중복된 id 없으면 !OK 전송

            lock.acquire()
            user_data.append(imfor)  # user_data에 id 추가
            imfor = self.clnt_sock.recv(BUF_SIZE)  # password/name/email/usertype
            imfor = imfor.decode()
            if imfor == "Q_reg":  # 회원가입 창 닫을 때 함수 종료
                con.close()
                break
            print("회원가입 정보" + imfor)
            imfor = imfor.split('/')  # 구분자 /로 잘라서 리스트 생성
            for imfo in imfor:
                user_data.append(imfo)  # user_data 리스트에 추가
            if user_data[4] == "student":
                c.execute("insert into studtbl(userid, point) values(?,?,?) ", (user_data[0], "0"))

            query = "INSERT INTO usertbl(userid, userpw, username, email, usertype) VALUES(?, ?, ?, ?, ?)"

            c.executemany(query, (user_data,))  # DB에 user_data 추가
            con.commit()  # DB에 커밋
            con.close()
            lock.release()
            break

    def log_in(self, data, clnt_num):  # 로그인
        con, c = self.dbcon()
        data = data.split('/')
        user_id = data[0]
        user_type = data[2]

        c.execute("SELECT userpw FROM usertbl where userid=? and usertype=?",
                  (user_id, user_type))  # DB에서 id 같은 password 컬럼 선택
        user_pw = c.fetchone()  # 한 행 추출

        c.execute("SELECT username FROM usertbl where userid=? and usertype=?",
                  (user_id, user_type))
        user_name = c.fetchone()
        print("user_name",user_name)
        if not user_pw:  # DB에 없는 id 입력시
            self.clnt_sock.send('iderror'.encode())
            con.close()
            return

        if (data[1],) == user_pw:
            # 로그인성공 시그널
            print("login sucess")
            clnt_imfor[clnt_num].append(data[0])
            clnt_imfor[clnt_num].append(data[2])
            # clnt_imfor[clnt_num].append(str(user_name))
            # 바로 위에 줄 코드 문제없죠? 해당값이 "('지엽학생1',)" 로 나와요 튜플안에 이름 문자열이 들어있고 그 튜플 자체를 문자열로 바꿔서 나옵니다
            clnt_imfor[clnt_num].append(user_name[0])
            print(f"clnt_imfor[clnt_num]: {clnt_imfor[clnt_num]}\nclnt_num: {clnt_num}")
            self.send_user_information(clnt_num)
        else:
            # 로그인실패 시그널
            self.clnt_sock.send('!NO'.encode())
            print("login failure")

        con.close()
        return

    def remove(self, clnt_num):  # 회원탈퇴
        con, c = self.dbcon()
        id = clnt_imfor[clnt_num][1]
        lock.acquire()
        c.execute("DELETE FROM usertbl WHERE userid = ?", (id,))
        c.execute("DELETE FROM Return WHERE userid = ?", (id,))
        clnt_imfor[clnt_num].remove(id)
        con.commit()
        lock.release()
        con.close()

    def send_user_information(self, clnt_num):  # 유저정보 보내기
        con, c = self.dbcon()
        id = clnt_imfor[clnt_num][1]
        self.clnt_sock = clnt_imfor[clnt_num][0]

        c.execute(
            "SELECT username FROM usertbl where userid=?", (id,))  # 이름
        row = c.fetchone()
        row = list(row)
        c.execute(
            "SELECT point FROM studtbl where userid=?", (id,))  # 이름
        point_data = c.fetchone()
        if point_data:
            row.append(str(point_data[0]))
        user_data = row  # 이름
        user_data = '/'.join(user_data)
        self.clnt_sock.send(('!OK/' + user_data).encode())  # !OK/username/point
        con.close()

    def find_id(self, email):  # 아이디찾기
        con, c = self.dbcon()

        c.execute("SELECT userid FROM usertbl where email=?",
                  (email,))  # DB에 있는 email과 일치시 id 가져오기
        id = c.fetchone()

        if id == None:  # DB에 없는 email이면 None이므로 !NO 전송
            self.clnt_sock.send('!NO'.encode())
            print('fail')
            con.close()
            return
        else:
            self.clnt_sock.send('!OK'.encode())
            msg = self.clnt_sock.recv(BUF_SIZE)
            msg = msg.decode()
            if msg == "Q_id_Find":  # Q_id_Find 전송받으면 find_id 함수 종료
                pass
            elif msg == 'plz_id':  # plz_id 전송받으면 id 전송
                id = ''.join(id)  # ''<- 구분자로 사용  리스트->문자열로 바꾸기
                self.clnt_sock.send(id.encode())
                print('send_id')
            con.close()
            return

    def find_pw(self, id):  # 비번찾기
        con, c = self.dbcon()
        c.execute("SELECT userpw, email FROM usertbl where userid=?",
                  (id,))  # DB에 있는 id와 일치하면 비밀번호, 이메일 정보 가져오기
        row = c.fetchone()
        print(row)
        if row == None:  # DB에 없는 id면 None
            self.clnt_sock.send('!NO'.encode())
            print('iderror')
            con.close()
            return

        self.clnt_sock.send('!OK'.encode())  # DB에 id 있으면 !OK 전송
        email = self.clnt_sock.recv(BUF_SIZE)
        email = email.decode()
        if email == "Q_pw_Find":  # Q_pw_Find 전송받으면 find_pw 함수 종료
            con.close()
            return

        if row[1] == email:  # 전송받은 email변수 값이 DB에 있는 email과 같으면
            self.clnt_sock.send('!OK'.encode())
            msg = self.clnt_sock.recv(BUF_SIZE)
            msg = msg.decode()
            if msg == "Q_pw_Find":
                pass
            elif msg == 'plz_pw':  # plz_pw 전송받으면
                pw = ''.join(row[0])  # 비밀번호 문자열로 변환
                self.clnt_sock.send(pw.encode())
                print('send_pw')
            else:
                pass
        else:
            self.clnt_sock.send('!NO'.encode())
            print('emailerror')

        con.close()
        return

    def delete_imfor(self):  # 유저정보 삭제
        global clnt_cnt
        for clnt_imfo in clnt_imfor:
            if self.clnt_sock == clnt_imfo[0]:
                print('exit client')
                index = clnt_imfor.index(clnt_imfo)
                del clnt_imfor[index]

    def chat_wait(self, user_name, clnt_num):
        user_type = clnt_imfor[clnt_num][2]  # 유저 타입
        chat_room_name_list = []  # 채팅 대기중인 선생 아이디를 담는 리스트

        if user_type == "student":
            if not chat_rooms:  # 채팅방 리스트에 아무것도 없으면 찾을 수 없다고 보내줌
                self.clnt_sock.send("열려있는 상담방이 없습니다.".encode())
            else:
                room_id_list = ["열려있는 상담방 목록"]
                for T_name,room_socks in chat_rooms.items():
                    if len(room_socks) == 1:  # 학생이 있는 소캣만
                        room_id_list.append(T_name)
                msg = "\n".join(room_id_list)
                self.clnt_sock.send(msg.encode())

            teacher_name = self.clnt_sock.recv(1024).decode()  # 학생이 고른 클라이언트 찾기

            # T_name 상담방 선생아이디, chat_rooms[T_name] 상담방 소켓 리스트
            lock.acquire()
            T_name = ""
            for T_name in chat_rooms:
                if T_name == teacher_name:  # 학생이 고른 선생님의 채팅방에 들어간다는것이다
                    print(f"clnt_imfor[clnt_num]:{clnt_imfor[clnt_num]}")
                    teacher_name = True
                    chat_rooms[T_name].append(clnt_imfor[clnt_num][0])
                    for Sock in chat_rooms[T_name]:
                        Sock.send(f"{clnt_imfor[clnt_num][3]}({clnt_imfor[clnt_num][1]})님 상담방 입장".encode())
                    break
            lock.release()
            if teacher_name is True:
                self.chatwindow(user_name, clnt_num, T_name)
            else:
                self.clnt_sock.send("/나가기".encode())
        elif user_type == "teacher":  # 선생님일때는 바로 채팅방에 넣고 대기시킴
            print(' elif user_type == "teacher":  # 선생님일때는 바로 채팅방에 넣고 대기시킴')
            self.clnt_sock.send("상담방을 생성합니다.\n학생이 선생님의 아이디를 입력할때 까지 기달려주세요.".encode())
            T_name = self.clnt_sock.recv(1024).decode()
            lock.acquire()
            chat_rooms[T_name] = [clnt_imfor[clnt_num][0]] # 키값을 교사 소켓이 들어 있는 리스트로 선언
            lock.release()
            self.chatwindow(user_name, clnt_num,T_name)

    def chatwindow(self, user_name, clnt_num , T_name):

        user_id = clnt_imfor[clnt_num][1]  # 유저 아이디 찾아서 넣기
        user_type = clnt_imfor[clnt_num][2]  # 유저 타입
        T_name = T_name  # 교사 아이디 저장 학생이 메시지 를 주고받을때 구분하기 위해서(혹시 모르니 교사 클라이언트도 동일하게 선언)
        while True:  # 상담방 참여자의 메시지를 받기위해 무한반복
            try:
                msg = self.clnt_sock.recv(1024).decode()
                print(f"{user_name}({user_id}) {user_type}님이 보낸 메시지:{msg}")  # 받은 메시지 확인하기
                if not msg or msg == "/나가기":
                    print(f"{user_name}({user_id}) {user_type}님 상담방 나감")
                    break
            except:
                print(f"{user_name}({user_id}) {user_type}님 예외 처리로 상담방 함수종료(정상)")
                break
            else:
                msg = f"{user_name}({user_id}):{msg}"  # 다른사람에게 보내기위해 f포멧팅(이름,아이디,메시지)
                try:
                    for sock_send in chat_rooms[T_name]:
                        print(f"msg:{msg}")
                        sock_send.send(msg.encode())
                except:   # 이 예외처리가 실행되면 상담방이 삭제된것
                    self.clnt_sock.send("/상담방없음".encode())
        lock.acquire()
        try:
            for sock_send in chat_rooms[T_name]:
                sock_send.send("/나가기".encode())
            del chat_rooms[T_name]  # 깔끔하게 상담방 삭제
            print(f"{T_name}상담방 삭제")
        except:
            print(f"이미 삭제된 {T_name}상담방")
        lock.release()

    def question_send(self, clnt_msg):
        con, c = self.dbcon()
        subname = clnt_msg
        lock.acquire()
        c.execute("SELECT subkey, suburl, subrange FROM apitbl where subname = ?", (subname,))
        api = c.fetchone()
        print("api:",api)
        lock.release()
        con.commit()
        con.close()
        api = list(api)
        key = api[0]
        url = api[1]
        api[2] = api[2].split('/')
        range1 = int(api[2][0])
        range2 = int(api[2][1])
        Qlist = []
        Question = "!Question"
        Answer = "!Answer"
        for i in range(range1, range2):  # API마다 가져올 값의 범위가 다르기 때문에 DB에 따로 저장할 예정
            temp_list = []
            code = 'A00000' + str(i)  # API 접속 설정
            params = {'serviceKey': key, 'q1': code}
            res = requests.get(url, params=params).content.decode()
            soup = BeautifulSoup(res, 'lxml')
            for item in soup.find_all("item"):  # API에서 데이터를 받아와 필요한 부분만 추출
                i = str(item.find('anmlgnrlnm'))
                j = str(item.find('gnrlspftrcont'))
                j = re.sub('<.+?>', '', j, 0).strip()
                i = re.sub('<.+?>', '', i, 0).strip()
                temp_list.append(j)
                temp_list.append(i)
                Qlist.append(temp_list)

        for item in Qlist:  # 문제에 정답이 들어있을때 빈칸으로 치환
            if item[1] in item[0]:
                item[0] = item[0].replace(item[1], "[" + "  " * len(item[1]) + "]")
            Question = Question + '//' + item[0]
            Answer = Answer + '//' + item[1]
            print('문제: ' + item[0] + "\n")  # 얘는 문제라는것!
            print('정답: ' + item[1] + "\n\n")  # 얘가 정답이라는것!
        self.clnt_sock.send(str(Question + Answer).encode())

    def test_result_handle(self, clnt_msg, clnt_num):
        con, c = self.dbcon()
        print("(test_result_handle 함수) 학생이 문제를 풀었어요.",clnt_msg)
        subname, score_avr, point, subtype = clnt_msg.split('/')
        score_avr = int(score_avr)
        lock.acquire()
        if subtype == "api":
            c.execute("SELECT score_avr FROM apitbl where subname=?", (subname,))
        elif subtype == "teachques":
            c.execute("SELECT score_avr FROM teachques where subname=?", (subname,))
        score_list = c.fetchone()  # score_list 가 튜플로 생성되어서 밑에 += 연산자가 안먹혀서
        c.execute("SELECT score_avr FROM studtbl where userid = ?", (clnt_imfor[clnt_num][1],) )
        clnt_avr = c.fetchone()
        lock.release()
        print(locals())
        score_list = int(score_list[0])
        clnt_avr = int(clnt_avr[0])
        score_list = int((score_list + score_avr)/2)
        clnt_avr = int((clnt_avr + score_avr)/2)

        lock.acquire()
        if subtype == "api":
            c.execute("UPDATE apitbl SET score_avr=?, score_cnt=score_cnt+1 where subname=?",
                     (score_list, subname,))
        elif subtype == "teacques":
            c.execute("UPDATE teachques SET score_avr=?, score_cnt=score_cnt+1 where subname=?",
                      (score_list, subname,))

        # clnt_imfor[clnt_num] = [소켓, 아이디, 유저 타입, 이름]
        c.execute("UPDATE studtbl SET score_avr = ?, point = ?, score_cnt = score_cnt + 1 where userid=?",
                  (clnt_avr, int(point), clnt_imfor[clnt_num][1]))
        lock.release()
        con.commit()
        con.close()

    def teacher_question_update(self, clnt_msg): #주제/문제명/문제내용 teachques 에 저장
        con, c = self.dbcon()
        teacher_Q=[]                            #교사가 만든 문제 리스트
        msg = clnt_msg.split('/')
        teacher_Q.append(msg)
        lock.acquire()
        c.execute("insert into teachques(subname, question, anser) values(?,?,?) ", (teacher_Q[0],teacher_Q[1], teacher_Q[2])) #받은 내용 table에 저장
        con.commit()
        con.close()
        lock.release()

    def teacher_question_send(self,clnt_msg):  # 주제를 받아서 해당되는 문제&정답을 db에서 찾아서 보내기
        con, c=self.dbcon()
        subname=clnt_msg   # 주제  만 짤라서 받아서 따로 split을 안함
        lock.acquire()
        c.execute("SELECT question FROM teachques where subname = ?", (subname,)) # 문제받기
        teacher_Q=c.fetchall()
        c.execute("SELECT answer FROM teachques where subname = ?", (subname,))   # 정답 받기
        teacher_A=c.fetchall()
        lock.release()
        con.close()
        teacher_Q=list(teacher_Q)       #문제 리스트화
        teacher_A=list(teacher_A)       #정답 리스트화
        teacher_Q = '/'.join(teacher_Q) #앞에 '/' 붙임
        teacher_A = '/'.join(teacher_A) #앞에 '/' 붙임
        self.clnt_sock.send((teacher_Q +teacher_A).encode()) # 리스트화 시킨 문제 및 정답을 보냄

    def scoredata_send(self, clnt_msg):
        con, c=self.dbcon()
        lock.acquire()
        api_data_list = []
        teach_data_list = []
        score_data_list = []
        c.execute("SELECT subname, score_avr from apitbl")
        api_avr_list=c.fetchall()
        for row in api_avr_list:
            row = list(row)
            row = '/'.join(row)
            api_data_list.append(row)
        c.execute("SELECT subname, score_avr from teachques")
        teach_avr_list = c.fetchall()
        for row in teach_avr_list:
            row = list(row)
            row = '/'.join(row)
            teach_data_list.append(row)
        c.execute('SELECT  user_id ,score_avr, score_cnt from studtbl')
        score_avr_list = c.fetchall()
        for row in score_avr_list:
            row = list(row)
            row = '/'.join(row)
            score_data_list.append(row)

        lock.release()
        con.close()

        api_data='/'.join(api_data_list)
        teach_data='/'.join(teach_data_list)
        score_data='/'.join(score_data_list)
        self.clnt_sock.send('api/'+api_data.encode())
        self.clnt_sock.send('teachques/'+teach_data.encode())
        self.clnt_sock.send('stud/'+score_data.encode())

    def qna_write(self, clnt_msg):
        con, c = self.dbcon()
        comments_list = clnt_msg.split("/")
        print(f"comments_list:{comments_list}")
        lock.acquire()
        c.execute("INSERT INTO qnatbl(qnawritername, qnawriterid, Q, A) VALUES(?, ?, ?, ?)",
                  (comments_list[0], comments_list[1], comments_list[2], comments_list[3]))
        lock.release()
        con.commit()
        con.close()

    def posts_list_send(self):
        con, c = self.dbcon()
        post_data_list = []
        lock.acquire()
        c.execute("SELECT qnanum, Q FROM qnatbl")
        posts_lists = c.fetchall()
        lock.release()
        for post_list in posts_lists:
            post_list = list(post_list)
            post_list[0] = str(post_list[0])
            post_list = '.'.join(post_list)
            post_data_list.append(post_list)

        post_data = '/'.join(post_data_list)
        if post_data:  # 게시글이 있다면 게시글을 보냄
            self.clnt_sock.send(post_data.encode())
        else: # 게시글이 없으면 없다고 보냄
            self.clnt_sock.send("게시글 없음".encode())
        con.close()

    def show_qna(self, clnt_msg):
        con, c= self.dbcon()
        QnAnum = int(clnt_msg)
        comment_data_list = []
        lock.acquire()
        c.execute("SELECT A, qnawritername, qnawriterid FROM qnatbl where qnanum = ?", (QnAnum, ))
        post_data = c.fetchone()
        c.execute("SELECT writername, writerid, comment FROM commenttbl where qnanum = ?", (QnAnum, ))
        comment_data_lists = c.fetchall()
        lock.release()

        for comment_list in comment_data_lists:
            comment_list = list(comment_list)
            comment_list = '&#'.join(comment_list)
            comment_data_list.append(comment_list)

        post_data = list(post_data)
        post_msg = '/'.join(post_data)
        comment_data = '/'.join(comment_data_list)
        data = post_msg+"<-post/comment->"+comment_data
        # 클라이언트에서 .split("<-post/comment->") 을 사용하면 간단하게 게시글과 댓글 분리가능

        # send는 연속으로 쓰지 말아주세요!
        # 왜냐면 2번연속으로 보내면 데이터가 이어진 상태로 한번에 들어옵니다.
        # self.clnt_sock.send('post/'+post_msg.encode())
        # self.clnt.sock.send('comment/'+comment_data.encode())

        # send 사이 recv 를 넣으면 데이터가 겹치는걸 방지할수있습니다
        # 이런 경우에 함수안에 recv 를 쓰기는 해요
        self.clnt_sock.send(str(len(data.encode())).encode()) # 지금 한번에 보낼려는 문자의 길이를 미리 클라이언트에게 보낸다
        print("(show_qna 함수)클라이언트 응답:↲\n\t"
              ,self.clnt_sock.recv(1024).decode()) # 클라이언트의 버퍼 사이즈 확인을 받는다
        self.clnt_sock.send(data.encode()) # 데이터를 보낸다
        con.close()

    def qna_comment_update(self, clnt_msg):
        con, c = self.dbcon()
        comments_list = clnt_msg.split('/')

        lock.acquire()
        c.execute("INSERT INTO commenttbl(qnanum, comment, writername, writerid) VALUES(?, ?, ?, ?)",
                  (int(comments_list[0]), comments_list[1], comments_list[2], comments_list[3]))
        lock.release()
        con.commit()
        con.close()


if __name__ == '__main__':  # 메인? 기본설정같은 칸지
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    i = 0
    while i < 3:
        try:
            sock.bind(('', PORT+i))
            print(f"서버 생성 성공 포트:{PORT+i}")
            break
        except:
            print(f"서버 생성 실패 포트:{PORT + i}")
            i+=1

    sock.listen(5)

    while True:
        clnt_sock, addr = sock.accept()

        lock.acquire()
        clnt_imfor.append([clnt_sock])
        print(clnt_sock)
        lock.release()

        t = Worker(clnt_sock)
        t.daemon = True
        t.start()