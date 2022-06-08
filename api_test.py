import requests
import re
from bs4 import BeautifulSoup

key = 'f+y6b9MNtXGHxo4MYGssKF1xmNUgO6s0KhaleUpx7Fcp7hmcKgNE8wik3p0amAuHSi+lr8Ms9i5V74zMzd39HA=='
url = 'http://apis.data.go.kr/1400119/BirdService/birdIlstrInfo'

for i in range(1100,1111):
    code = 'A00000' + str(i)
    params ={'serviceKey' : key, 'q1' : code }
    res = requests.get(url, params=params).content.decode()
    soup= BeautifulSoup(res,'lxml')
    for item in soup.find_all("item"):
        i = str(item.find('anmlgnrlnm'))
        j = str(item.find('gnrlspftrcont'))
        j = re.sub('<.+?>', '', j, 0).strip()
        i = re.sub('<.+?>', '', i, 0).strip()
        print('이름 : ' + i)
        print('설명 : ' + j)