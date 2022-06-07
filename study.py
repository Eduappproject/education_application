import requests
import pprint
encoding_key = "v52Ye5BHQ%2FQLx6v1jK%2Bc6cuRGFSpSE4KlOAzbR%2BaOiqNFSOplwmzT1yBUuGTmuD%2FQ4kJmx5Zd0L%2FdiAMKoJ7HQ%3D%3D"
decoding_key = 'v52Ye5BHQ/QLx6v1jK+c6cuRGFSpSE4KlOAzbR+aOiqNFSOplwmzT1yBUuGTmuD/Q4kJmx5Zd0L/diAMKoJ7HQ=='

url = 'http://openapi.nature.go.kr/openapi/service/rest/InsectService/isctIlstrSearch'
param = {'serviceKey': decoding_key,
          'st': 1,
          'sw': '밤나방',
          'numOfRows': 5,
          'pageNo': 1
          }

response = requests.get(url, params = param)

content = response.text
pp = pprint.PrettyPrinter(ident = 4)