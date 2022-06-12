import requests
import re
from bs4 import BeautifulSoup
import string

key = 'f+y6b9MNtXGHxo4MYGssKF1xmNUgO6s0KhaleUpx7Fcp7hmcKgNE8wik3p0amAuHSi+lr8Ms9i5V74zMzd39HA=='
url = 'http://apis.data.go.kr/1400119/BirdService/birdIlstrInfo'
Qlist = []

for i in range(1100,1133, 3):
    temp_list = []
    code = 'A00000' + str(i)
    params ={'serviceKey' : key, 'q1' : code }
    res = requests.get(url, params=params).content.decode()
    soup= BeautifulSoup(res,'lxml')
    for item in soup.find_all("item"):
        i = str(item.find('anmlgnrlnm'))
        j = str(item.find('gnrlspftrcont'))
        j = re.sub('<.+?>', '', j, 0).strip()
        i = re.sub('<.+?>', '', i, 0).strip()
        temp_list.append(j)
        temp_list.append(i)
        Qlist.append(temp_list)
        # print('문제 : ' + j)
        # print('정답 : ' + i)
        

for item in Qlist:
    if item[1] in item[0]:
        item[0] = item[0].replace(item[1], "[\t\t]")
    print(item[0]+"\n\n") #얘는 문제라는것!
    #print(item[1]) #얘가 정답이라는것!