import requests, re, json, time
from bs4 import BeautifulSoup

class BiteBot:
    URL_MAP = {
        'login' : 'https://s3-br.bitefight.gameforge.com/user/login',
        'training' : 'https://s3-br.bitefight.gameforge.com:443/profile/training/',
        'token'    : 'https://s3-br.bitefight.gameforge.com/profile/index',
        'grotte' : 'https://s3-br.bitefight.gameforge.com:443/city/grotte/',
        'humanhunt' : 'https://s3-br.bitefight.gameforge.com/robbery/humanhunt/'
    }

    BASE_HEADERS = {
        'Host': 's3-br.bitefight.gameforge.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://s3-br.bitefight.gameforge.com',
        'Connection': 'keep-alive',
        'Referer': 'https://s3-br.bitefight.gameforge.com/user/login',
        'Cookie': 'gf-cookie-consent-4449562312=|7|1; SID=pprH3hCVZMfpFuFgQb2tX0',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Sec-GPC': '1'
    }

    CHAR_INFO_LIST = ['gold', '', 'hellstones', '', 'fragments', '', 'currAP', 'maxAP', '', 'currVit', 'maxVit', '', 'level', 'battle']
    CHAR_SKILL_NAME = ['Force', '', 'Defense', '', 'Dexterity', '', 'Endurance', '', 'Charisma']
    def __init__(self, user, pwd, sv):
        self.user = user
        self.pwd = pwd
        self.server = sv

        self.loggedIn = self.isLoggedIn()

        while self.loggedIn == False:
            self.loggedIn = self.login()        
            time.sleep(5)

    def login(self):
        body = {
            'user': self.user,
            'pass': self.pwd,
            'server': self.server,
        }

        res = self.request(self.URL_MAP['login'], form_data = body)
        print(f'Tried logging in to [{self.user}].')
        
        return self.isLoggedIn()
        
    def isLoggedIn(self):
        res = self.request(self.URL_MAP['login'])

        logged_in = res.text.find('id="pwlostLink"') == -1
        print(f'Login status: {logged_in}')
        return logged_in

    def request(self, url, headers = None, form_data = None):
        return requests.post(url, headers = headers or self.BASE_HEADERS, data = form_data)

    def getToken(self):
        res = self.request(self.URL_MAP['token'])

        if res.status_code != 200:
            print("well we're fucked", res.status_code)
            return False
        
        return self.extractToken(res.text)

    def extractToken(self, data):
        s = data.find('token=')
    
        if s == -1:
            return False

        s += 6
        e = data[s:].find('"')

        return data[s:s+e]

    def _saveHTML(self, name, text):
        with open(f'{name}.html', 'w', encoding='utf-8') as f:
            f.write(text)
    
    def train(self, skill):
        token = self.getToken()

        res = self.request(f'{self.URL_MAP["training"]}{skill}?__token={token}')

        print(f'Training skill {skill}. Status: {res.status_code}')

    def hunt(self, level):
        res = self.request(f'{self.URL_MAP["humanhunt"]}{level}')

        return res.status_code == 200

    def grotte(self, level):
        token = self.getToken()
        res = self.request(f'{self.URL_MAP["grotte"]}?__token={token}', form_data = {'difficulty' : level})

        return res.status_code == 200

    def updateCharacterInfo(self):
        res = self.request(self.URL_MAP['token'])
        
        self._saveHTML('char', res.text)
        soup = BeautifulSoup(res.text, 'html.parser')
        info = re.findall("[0-9. ]+", soup.find(class_='gold').getText())

        self.character = {}

        # main info
        for t in range(len(info)):
            if info[t].strip() == '':
                continue

            d = info[t].strip()
            if '.' in d:
                d = ''.join(d.split('.'))
            
            if t < len(self.CHAR_INFO_LIST) and self.CHAR_INFO_LIST[t] != '':
                self.character[self.CHAR_INFO_LIST[t]] = int(d)
        
        # skills info
        info = soup.select('#skills_tab .tooltip table')
        self.character['skills'] = {}
        for i in range(0, len(info)-1, 2):
            values = re.findall('[0-9]+', info[i].getText())
            price = int(''.join(re.findall('[0-9]+', info[i+1].getText())))
            
            self.character['skills'][self.CHAR_SKILL_NAME[i]] = {
                'value' : int(values[0]),
                'baseValue' : int(values[1]),
                'price' : price
            }

        return self.character                

    def trainSkillChoice(self):
        self.updateCharacterInfo()
        chosen = ''
        chosen_id = -1
        i = 1
        for skill_name in self.character['skills']:
            if skill_name == 'Charisma':
                i += 1
                continue
            
            skill = self.character['skills'][skill_name]
            if (chosen == '' and skill['price'] <= self.character['gold']) or (chosen != '' and self.character['skills'][chosen]['price'] > skill['price']):
                chosen = skill_name
                chosen_id = i
            
            i += 1

        if chosen == '' and self.character['skills']['Charisma']['price']/self.character['gold'] <= 0.05:
            chosen_id = 5
        
        return chosen_id
    
    def spendGoldOnSkills(self):
        while True:
            skill = self.trainSkillChoice()
            
            if skill == -1:
                print('Done training')
                break

            self.train(skill)
            time.sleep(1)