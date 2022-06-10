import socket
import threading
import sqlite3
import datetime
from datetime import date
import sys

PORT = 2090
BUF_SIZE = 2048
lock = threading.Lock()
clnt_imfor = []  # [[소켓, id]]
clnt_cnt = 0


def dbcon(): #db연결
    con = sqlite3.connect('serverDB.db')  # DB 연결
    c = con.cursor()                  # 커서
    return (con, c)


def handle_clnt(clnt_sock): #핸들클라
    for i in range(0, clnt_cnt):
        if clnt_imfor[i][0] == clnt_sock:
            clnt_num = i
            break  # 접속한 클라 저장

    while True:
        sys.stdout.flush()  # 버퍼 비워주는거
        clnt_msg = clnt_sock.recv(BUF_SIZE)

        if not clnt_msg:
            lock.acquire() #뮤텍스같은거
            delete_imfor(clnt_sock)
            lock.release()
            break
        clnt_msg = clnt_msg.decode()  #숫자->문자열로 바꾸는거 맞나?  데이터 보낼때 incode 로 하고 

        sys.stdin.flush()

        if 'signup' == clnt_msg:
            sign_up(clnt_sock, clnt_num)
        elif clnt_msg.startswith('login/'):  # startswitch -->문자열중에 특정 문자를 찾고싶거나, 특정문자로 시작하는 문자열, 특정문자로 끝이나는 문자열 등
            clnt_msg = clnt_msg.replace('login/', '')  # clnt_msg에서 login/ 자름
            log_in(clnt_sock, clnt_msg, clnt_num)
        elif clnt_msg.startswith('find_id/'):
            clnt_msg = clnt_msg.replace('find_id/', '')
            find_id(clnt_sock, clnt_msg)
        elif clnt_msg.startswith('find_pw/'):
            clnt_msg = clnt_msg.replace('find_pw/', '')
            find_pw(clnt_sock, clnt_msg)
        elif clnt_msg.startswith('myinfo'):
            clnt_msg = clnt_msg.replace('myinfo', '')
            send_user_information(clnt_num)
        elif clnt_msg.startswith('edit_data'):
            clnt_msg = clnt_msg.replace('edit_data', '')
            edit_data(clnt_num, clnt_msg)
        elif clnt_msg.startswith('remove'):
            remove(clnt_num)
        else:
            continue

 
def edit_data(clnt_num, clnt_msg): #데이터 베이스 정보변경
    print(clnt_msg)
    id = clnt_imfor[clnt_num][1]
    con, c = dbcon()
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


def sign_up(clnt_sock, clnt_num): #회원가입
    con, c = dbcon()
    user_data = []

    while True:
        imfor = clnt_sock.recv(BUF_SIZE)
        imfor = imfor.decode()
        if imfor == "Q_reg":      # 회원가입 창 닫을 때 함수 종료
            con.close()
            break
        c.execute("SELECT userid FROM usertbl where userid = ?", (imfor, ))  # usertbl 테이블에서 id 컬럼 추출
        row = c.fetchone()
        if row == None:                      # DB에 없는 id면 None
            clnt_sock.send('!NO'.encode())
            print('id_found_error')
            con.close()
            return

        clnt_sock.send('!OK'.encode())  # 중복된 id 없으면 !OK 전송

        lock.acquire()
        user_data.append(imfor)  # user_data에 id 추가
        imfor = clnt_sock.recv(BUF_SIZE)  # password/name/email/usertype
        imfor = imfor.decode()
        if imfor == "Q_reg":  # 회원가입 창 닫을 때 함수 종료
            con.close()
            break

        imfor = imfor.split('/')  # 구분자 /로 잘라서 리스트 생성
        for imfo in imfor:
            user_data.append(imfo)       # user_data 리스트에 추가
        query = "INSERT INTO usertbl(userid, userpw, username, email, usertype) VALUES(?, ?, ?, ?, ?)"

        c.executemany(query, (user_data,))  # DB에 user_data 추가
        con.commit()            # DB에 커밋
        con.close()
        lock.release()
        break


def log_in(clnt_sock, data, clnt_num): # 로그인
    con, c = dbcon()
    data = data.split('/')
    user_id = data[0]

    c.execute("SELECT userpw FROM usertbl where userid=?",
              (user_id,))  # DB에서 id 같은 password 컬럼 선택
    user_pw = c.fetchone()             # 한 행 추출

    if not user_pw:  # DB에 없는 id 입력시
        clnt_sock.send('iderror'.encode())
        con.close()
        return

    if (data[1],) == user_pw:
        # 로그인성공 시그널
        print("login sucess")
        clnt_imfor[clnt_num].append(data[0])
        send_user_information(clnt_num)
    else:
        # 로그인실패 시그널
        clnt_sock.send('!NO'.encode())
        print("login failure")

    con.close()
    return


def remove(clnt_num): # 회원탈퇴
    con, c = dbcon()
    id = clnt_imfor[clnt_num][1]
    lock.acquire()
    c.execute("DELETE FROM usertbl WHERE userid = ?", (id,))
    c.execute("DELETE FROM Return WHERE userid = ?", (id,))
    clnt_imfor[clnt_num].remove(id)
    con.commit()
    lock.release()
    con.close()


def send_user_information(clnt_num):  # 유저정보 보낸데
    con, c = dbcon()
    id = clnt_imfor[clnt_num][1]
    clnt_sock = clnt_imfor[clnt_num][0]
    books = []

    c.execute(
        "SELECT username FROM usertbl where id=?", (id,))  # 이름, 대여한 책 찾기
    row = c.fetchone()
    row = list(row)
    for i in range(0, len(row)):     # None인 항목 찾기
        if row[i] == None:
            row[i] = 'X'

    c.execute("SELECT book_name FROM Return where id=?", (id,))  # 반납한 책
    while 1:
        book = c.fetchone()        # 반납한 책 한 권씩 찾기
        if book is None:
            break
        book = list(book)         # 리스트로 변환
        books = books + book      # books 리스트에 추가

    user_data = row + books  # 이름,대여한 책 + 반납한 책
    user_data = '/'.join(user_data)
    # 버퍼 비우기

    clnt_sock.send(('!OK/'+user_data).encode())
    con.close()


def find_id(clnt_sock, email):  # 아이디찾기
    con, c = dbcon()

    c.execute("SELECT userid FROM usertbl where email=?",
              (email,))  # DB에 있는 email과 일치시 id 가져오기
    id = c.fetchone()
    

    if id == None:      # DB에 없는 email이면 None이므로 !NO 전송
        clnt_sock.send('!NO'.encode())
        print('fail')
        con.close()
        return
    else:
        clnt_sock.send('!OK'.encode())
        msg = clnt_sock.recv(BUF_SIZE)
        msg = msg.decode()
        if msg == "Q_id_Find":    # Q_id_Find 전송받으면 find_id 함수 종료
            pass
        elif msg == 'plz_id':     # plz_id 전송받으면 id 전송
            id = ''.join(id)  #  ''<- 여기에는 구분자임 ㅇㅇ  리스트->문자열로 바꾸기
            clnt_sock.send(id.encode())
            print('send_id')
        con.close()
        return


def find_pw(clnt_sock, id):  #비번찾기
    con, c = dbcon()
    c.execute("SELECT userpw, email FROM usertbl where userid=?",
              (id,))    # DB에 있는 id와 일치하면 비밀번호, 이메일 정보 가져오기
    row = c.fetchone()
    print(row)
    if row == None:                      # DB에 없는 id면 None
        clnt_sock.send('!NO'.encode())
        print('iderror')
        con.close()
        return

    clnt_sock.send('!OK'.encode())       # DB에 id 있으면 !OK 전송
    email = clnt_sock.recv(BUF_SIZE)
    email = email.decode()
    if email == "Q_pw_Find":             # Q_pw_Find 전송받으면 find_pw 함수 종료
        con.close()
        return

    if row[1] == email:                   # 전송받은 email변수 값이 DB에 있는 email과 같으면
        clnt_sock.send('!OK'.encode())
        msg = clnt_sock.recv(BUF_SIZE)
        msg = msg.decode()
        if msg == "Q_pw_Find":
            pass
        elif msg == 'plz_pw':             # plz_pw 전송받으면
            pw = ''.join(row[0])          # 비밀번호 문자열로 변환
            clnt_sock.send(pw.encode())
            print('send_pw')
        else:
            pass
    else:
        clnt_sock.send('!NO'.encode())
        print('emailerror')
        
    con.close()
    return


def delete_imfor(clnt_sock): #유저정보 삭제
    global clnt_cnt
    for i in range(0, clnt_cnt):
        if clnt_sock == clnt_imfor[i][0]:
            print('exit client')
            while i < clnt_cnt - 1:
                clnt_imfor[i] = clnt_imfor[i + 1]
                i += 1
            break
    clnt_cnt -= 1

#def recv_clnt_msg(clnt_sock):


if __name__ == '__main__': #메인? 기본설정같은 칸지
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', PORT))
    sock.listen(5)

    while True:
        clnt_sock, addr = sock.accept()

        lock.acquire()
        clnt_imfor.insert(clnt_cnt, [clnt_sock])
        clnt_cnt += 1
        print(clnt_sock)
        lock.release()
        t = threading.Thread(target=handle_clnt, args=(clnt_sock,))
        t.start()