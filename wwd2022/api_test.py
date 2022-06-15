# import requests
# import re
# from bs4 import BeautifulSoup
# import string

# key = 'f+y6b9MNtXGHxo4MYGssKF1xmNUgO6s0KhaleUpx7Fcp7hmcKgNE8wik3p0amAuHSi+lr8Ms9i5V74zMzd39HA=='
# url = 'http://apis.data.go.kr/1400119/BirdService/birdIlstrInfo'
# Qlist = []

# for i in range(1100,1133, 3):
#     temp_list = []
#     code = 'A00000' + str(i)
#     params ={'serviceKey' : key, 'q1' : code }
#     res = requests.get(url, params=params).content.decode()
#     soup= BeautifulSoup(res,'lxml')
#     for item in soup.find_all("item"):
#         i = str(item.find('anmlgnrlnm'))
#         j = str(item.find('gnrlspftrcont'))
#         j = re.sub('<.+?>', '', j, 0).strip()
#         i = re.sub('<.+?>', '', i, 0).strip()
#         temp_list.append(j)
#         temp_list.append(i)
#         Qlist.append(temp_list)
#         # print('문제 : ' + j)
#         # print('정답 : ' + i)
        

# for item in Qlist:
#     if item[1] in item[0]:
#         item[0] = item[0].replace(item[1], "["+"  "*len(item[1])+"]")
#     print('문제: '+item[0]+"\n") #얘는 문제라는것!
#     print('정답: '+item[1]+"\n\n") #얘가 정답이라는것!

# import requests
# import re
# from bs4 import BeautifulSoup
# import string

# key = 'toQf6rbcHJG/b0tXA6TtrS/N45JE5YPJqsEbqeqEGPVOctv3P/K41JQ8yoyrz1qvSvHshySUYuJii8rHzw5u0A=='
# url = 'http://apis.data.go.kr/1400119/MammService/mammIlstrInfo'
# Qlist = []

# for i in range(900,1012):
#     print(i)
#     temp_list = []
#     code = 'A00000' + str(i)
#     params ={'serviceKey' : key, 'q1' : code }
#     res = requests.get(url, params=params).content.decode()
#     soup= BeautifulSoup(res,'lxml')
#     for item in soup.find_all("item"):
#         i = str(item.find('anmlgnrlnm'))
#         j = str(item.find('gnrlspftrcont'))
#         j = re.sub('<.+?>', '', j, 0).strip()
#         i = re.sub('<.+?>', '', i, 0).strip()
#         temp_list.append(j)
#         temp_list.append(i)
#         Qlist.append(temp_list)
#         # print('문제 : ' + j)
#         # print('정답 : ' + i)
        

# for item in Qlist:
#     if item[1] in item[0]:
#         item[0] = item[0].replace(item[1], "["+"  "*len(item[1])+"]")
#     print('문제: '+item[0]+"\n") #얘는 문제라는것!
#     print('정답: '+item[1]+"\n\n") #얘가 정답이라는것!


######### 위에는 조류    //  아래는  포유류
import requests
import re
from bs4 import BeautifulSoup
import string

key = 'toQf6rbcHJG/b0tXA6TtrS/N45JE5YPJqsEbqeqEGPVOctv3P/K41JQ8yoyrz1qvSvHshySUYuJii8rHzw5u0A==' # 오픈 API 접속시 필요한 키 값
url = 'http://apis.data.go.kr/1400119/MammService/mammIlstrInfo' # 오픈 API에 접속할때 사용하는 url 값
Qlist = [] # 문제를 저장할 리스트

for i in range(900,1012): # API마다 가져올 값의 범위가 다르기 때문에 DB에 따로 저장할 예정
    print(i)
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
        print('문제 : ' + j)
        print('정답 : ' + i)


for item in Qlist:  # 문제에 정답이 들어있을때 빈칸으로 치환
    if item[1] in item[0]:
        item[0] = item[0].replace(item[1], "["+"  "*len(item[1])+"]")
    print('문제: '+item[0]+"\n") #얘는 문제라는것!
    print('정답: '+item[1]+"\n\n") #얘가 정답이라는것!