import requests, re, json
from bs4 import BeautifulSoup

class BiteBot:
    URL_MAP = {
        'training' : 'https://s3-br.bitefight.gameforge.com:443/profile/training/',
        'token'    : 'https://s3-br.bitefight.gameforge.com/profile/index'
    }

    def __init__(self):
        with open('../config/headers.json') as f:
            self.BASE_HEADERS = json.loads(f.read())


    def request(self, url, headers = None, form_data = None):
        return requests.post(url, headers = headers or self.BASE_HEADERS, data = form_data)

    def getToken(self):
        res = self.request(self.URL_MAP['token'])

        if res.status_code != 200:
            print("well we're fucked", res.status_code)
            return
        
        s = res.text.find('token=')
    
        if s == -1:
            print("token not found", res.status_code)
            return

        s += 6
        e = res.text[s:].find('"')

        return res.text[s:s+e]

    def train(self, skill):
        token = self.getToken()

        res = self.request(f'{self.URL_MAP["training"]}{skill}?__token={token}')

        print(f'Training skill {skill}. Status: {res.status_code}')

    def hunt(self, level):
        res = self.request(f'https://s3-br.bitefight.gameforge.com/robbery/humanhunt/{level}')

        return res.status_code == 200

    def getCharacterInfo(self):
        res = self.request(self.URL_MAP['token'])
        soup = BeautifulSoup(res.text, 'html.parser')
        info = re.findall("[0-9. ]+", soup.find(class_='gold').getText())

        for t in range(len(info)):
            if info[t].strip() == '':
                continue
            
            print(info[t].strip())


#bot = BiteBot()
#bot.getCharacterInfo()


#skill = 1
#for i in range(50):
    #print('Hunting', bot.hunt(1))
    #bot.train(skill)
    #skill = 3 if skill+1 == 5 else skill+1
    #time.sleep(1)