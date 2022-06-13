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

PORT = 2090 + random.randint(0, 10)
BUF_SIZE = 2048
lock = threading.Lock()
clnt_imfor = []  # [[소켓, id, type, name]]
chat_rooms = [] # [[채팅1], [채팅방2]]

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
            clnt_msg = self.clnt_sock.recv(BUF_SIZE)  # 클라이언트에서 메세지 수신
            print(clnt_msg.decode())  # 받는값 확인
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
            elif clnt_msg.startswith('question_request/'): # question_request/주제명 (bird, mammal)
                clnt_msg = clnt_msg.replace('question_request/', '')
                self.question_send(clnt_msg)
            elif clnt_msg.startswith('quesiton_complete/'): # quetion_complete/과목명/점수/포인트
                clnt_msg = clnt_msg.replace('quetion_complete/', '')
                self.test_result_handle(clnt_msg, clnt_num)
            else:
                continue

    def dbcon(self):  # db연결
        con = sqlite3.connect('serverDB.db')  # DB 연결
        c = con.cursor()  # 커서
        return (con, c)

    def edit_data(self,clnt_num, clnt_msg):  # 데이터 베이스 정보변경
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
            print("회원가입 정보"+imfor)
            imfor = imfor.split('/')  # 구분자 /로 잘라서 리스트 생성
            for imfo in imfor:
                user_data.append(imfo)  # user_data 리스트에 추가
            if user_data[4] == "student":
                c.execute("insert into studtbl(userid, score, point) values(?,?,?) ", (user_data[0], "0", "0"))

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
        if not user_pw:  # DB에 없는 id 입력시
            self.clnt_sock.send('iderror'.encode())
            con.close()
            return

        if (data[1],) == user_pw:
            # 로그인성공 시그널
            print("login sucess")
            clnt_imfor[clnt_num].append(data[0])
            clnt_imfor[clnt_num].append(data[2])
            clnt_imfor[clnt_num].append(str(user_name))
            self.send_user_information(clnt_num)
        else:
            # 로그인실패 시그널
            self.clnt_sock.send('!NO'.encode())
            print("login failure")


        con.close()
        return

    def remove(self,clnt_num):  # 회원탈퇴
        con, c = self.dbcon()
        id = clnt_imfor[clnt_num][1]
        lock.acquire()
        c.execute("DELETE FROM usertbl WHERE userid = ?", (id,))
        c.execute("DELETE FROM Return WHERE userid = ?", (id,))
        clnt_imfor[clnt_num].remove(id)
        con.commit()
        lock.release()
        con.close()

    def send_user_information(self,clnt_num):  # 유저정보 보내기
        con, c = self.dbcon()
        id = clnt_imfor[clnt_num][1]
        self.clnt_sock = clnt_imfor[clnt_num][0]

        c.execute(
            "SELECT username FROM usertbl where userid=?", (id,))  # 이름
        row = c.fetchone()
        row = list(row)
        c.execute(
            "SELECT point FROM studtbl where userid=?", (id,))  # 이름

        user_data = row  # 이름
        user_data = '/'.join(user_data)
        self.clnt_sock.send(('!OK/' + user_data).encode()) # !OK/username/point
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
        user_type = clnt_imfor[clnt_num][2] # 유저 타입 
        chat_room_name_list = [] # 채팅 대기중인 선생 아이디를 담는 리스트
        if user_type == "student":
            if not chat_rooms: # 채팅방 리스트에 아무것도 없으면 찾을 수 없다고 보내줌
                self.clnt_sock.send("chat_not_found".encode()) 
            else:
                for chat_room in chat_rooms: 
                    if chat_room[1] == None: # 학생이 안 들어있는 채팅방만 고르기
                        chat_room_name_list.append(chat_room[0][3])
                chat_room_name_list = '/'.join(chat_room_name_list)
                self.clnt_sock.send(chat_room_name_list.encode())
            teacher_name = self.clnt_sock.recv(1024).decode() # 학생이 고른 클라이언트 찾기 
            
            for chat_room in chat_rooms:
                if chat_room[0][3] == teacher_name: # 학생이 고른 선생님의 채팅방에 들어간다는것이다
                    chat_rooms[chat_rooms.index(chat_room)][1] = clnt_imfor[clnt_num]
                    self.chatwindow(user_name, clnt_num)
                    return
        elif user_type == "teacher": # 선생님일때는 바로 채팅방에 넣고 대기시킴
            chat_rooms.append(clnt_imfor[clnt_num])
            self.chatwindow(user_name, clnt_num)
        

    def chatwindow(self, user_name, clnt_num):
        
        user_id = clnt_imfor[clnt_num][1]  # 유저 아이디 찾아서 넣기
        user_type = clnt_imfor[clnt_num][2] # 유저 타입 
        

        while True:  # 상담방 참여자의 메시지를 받기위해 무한반복
            try:
                msg = self.clnt_sock.recv(1024).decode()
                print(f"{user_name}({user_id}) {user_type}님이 보낸 메시지:{msg}")  # 받은 메시지 확인하기
                if not msg or msg == "/나가기":
                    print(f"{user_name}({user_id}) {user_type}님 상담방 나감")
                    self.clnt_sock.send(''.encode())
                    break
            except:
                print(f"{user_name}({user_id})님 예외 처리로 상담방 함수종료(정상)")
                break
            else:
                msg = f"{user_name}({user_id}):{msg}"  # 다른사람에게 보내기위해 f포멧팅(이름,아이디,메시지)
                for chat_room in chat_rooms:
                    if chat_room in self.clnt_sock:
                        for chat_clnt in chat_room:
                            if chat_clnt != self.clnt_sock:
                                self.clnt_sock.send(msg.encode())
                            


    def question_send(self, clnt_msg):
        con, c = self.dbcon()
        subname = clnt_msg
        lock.acquire()
        c.execute("SELECT subkey, suburl, subrange FROM apitbl where subname = ?", (subname, ))
        api = c.fetchone()
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
        for i in range(range1, range2): # API마다 가져올 값의 범위가 다르기 때문에 DB에 따로 저장할 예정
            temp_list = []
            code = 'A00000' + str(i)  # API 접속 설정
            params ={'serviceKey' : key, 'q1' : code }
            res = requests.get(url, params=params).content.decode()
            soup= BeautifulSoup(res,'lxml')
            for item in soup.find_all("item"): # API에서 데이터를 받아와 필요한 부분만 추출
                i = str(item.find('anmlgnrlnm'))
                j = str(item.find('gnrlspftrcont'))
                j = re.sub('<.+?>', '', j, 0).strip()
                i = re.sub('<.+?>', '', i, 0).strip()
                temp_list.append(j)
                temp_list.append(i)
                Qlist.append(temp_list)

        for item in Qlist:  # 문제에 정답이 들어있을때 빈칸으로 치환
            if item[1] in item[0]:
                item[0] = item[0].replace(item[1], "["+"  "*len(item[1])+"]")
            Question = Question + '/' + item[0]
            Answer = Answer + '/' + item[1]
            print('문제: '+item[0]+"\n") #얘는 문제라는것!
            print('정답: '+item[1]+"\n\n") #얘가 정답이라는것!
        self.clnt_sock.send(Question+Answer.encode())


    def test_result_handle(self, clnt_msg, clnt_num):
        con, c = self.dbcon()
        result = clnt_msg.split('/')
        result[1] = int(result[1])
        lock.acquire()
        c.execute("SELECT score_avr, score_cnt FROM apitbl where subname=?", (result[0], ))
        score_list = c.fetchone()
        lock.release()
        total_score = (score_list[0]*score_list[1]) + result[1]
        score_list[1]+=1
        score_list[0] = int(total_score / score_list[1])
        lock.acquire()
        c.execute("UPDATE apitbl SET score_avr=?, score_cnt=? where subname=?", (score_list[0], score_list[1], result[0], ))
        c.execute("UPDATE studtbl SET score=?, point=? where userid=?", (result[1], result[2], clnt_imfor[clnt_num], ))
        lock.release()

        con.commit()
        con.close()


if __name__ == '__main__':  # 메인? 기본설정같은 칸지
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', PORT))
    sock.listen(5)

    while True:
        clnt_sock, addr = sock.accept()

        lock.acquire()
        clnt_imfor.append([clnt_sock])
        print(clnt_sock)
        lock.release()

        t = Worker(clnt_sock)
        t.start()