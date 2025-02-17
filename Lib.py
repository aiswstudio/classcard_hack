# Copyright 2025 swstudio. All Rights Reserved.
from bs4 import BeautifulSoup
import requests, re

class Card:
    def __init__(self):
        self.id = None
        self.pw = None
        self.session_login = None
        self.session_login_url = None
        self.session_logout = requests.session()
        self.session_logout_used = 0

    def search_id(self, name):
        if 5 < self.session_logout_used:
            self.session_logout = requests.session()
            self.session_logout_used = 1
        else:
            self.session_logout_used += 1
        payload = {
            'id_find_name':name
        }
        data = self.session_logout.post('https://www.classcard.net/LoginProc/findIDList', payload).json()['id_list']
        return data

    def login(self, id:str, pw:str):
        self.session_login = requests.session()
        self.session_login.get('https://www.classcard.net/Login')
        payload = {
            'sess_key':self.session_login.cookies.get_dict()['ci_session'],
            'redirect':'',
            'login_id':id,
            'login_pwd':pw
        }
        data = self.session_login.post('https://www.classcard.net/LoginProc', payload, allow_redirects=True).json()
        self.session_login_url = data['go_first_class']
        if data['result'] == 'ok':
            return data, True
        else:
            return data, False
        
    def get_class(self):
        if not self.session_login:
            raise Exception('Not logged_in status. Login first.')
        data = self.session_login.get('https://www.classcard.net'+self.session_login_url).text
        data = BeautifulSoup(data, 'html.parser')
        class_name = data.find_all('div', class_ = 'cc-ellipsis l1')
        class_ = data.find_all('a', class_ = 'left-class-items')
        l = {}
        for name, id_ in zip(class_name, class_):
            l[name.contents[0]] = id_['href']
        return l
    
    def get_set(self, class_id):
        if not self.session_login:
            raise Exception('Not logged_in status. Login first.')
        data = self.session_login.get('https://www.classcard.net'+class_id).text
        data = BeautifulSoup(data, 'html.parser').find_all('div', class_='set-items')
        l = {}
        for id in data:
            l[id.find('a', class_ = 'anchor-underline set-name-a').contents[0]] = id.attrs['data-idx']
        return l
    
    def study_api(self, class_id, set_id, type):
        if not self.session_login:
            raise Exception('Not logged_in status. Login first.')
        data = self.session_login.get('https://www.classcard.net/set/'+set_id+'/'+class_id).text
        data = BeautifulSoup(data, 'html.parser')
        user_id = re.search(r'"user_idx":"(\d+)"', data.select('body > script:nth-child(2)')[0].string).group(1)
        num = re.search(r'(\d+) 카드', data.find('div', class_ = 'font-20 font-medium').contents[0]).group(1)
        csrf_token = re.search(r'var xscdvf = "([^"]+)";', data.find('script', {'id':'tmp_script2'}).contents[0]).group(1).replace('var xscdvf = ', '').replace('"', '')
        payload = {
            'set_idx':set_id,
            'activity':type,
            'user_idx':user_id,
            'view_cnt':num,
            'class_idx':class_id,
            'score':num,
            'csrf_token':csrf_token
        }
        self.session_login.post('https://www.classcard.net/ViewSetAsync/resetAllLog', payload)
    
    def study_test(self, class_id, set_id):
        if not self.session_login:
            raise Exception('Not logged_in status. Login first.')
        payload = {
            'p':'1',
            'ex':'1'
        }
        self.session_login.get('https://www.classcard.net/ClassTest/'+class_id+'/'+set_id, data=payload)
        self.session_login.cookies.set('is_std_start', '1')
        data = self.session_login.get('https://www.classcard.net/ClassTest/'+class_id+'/'+set_id, data=payload).text
        data = BeautifulSoup(data, 'html.parser')
        l = {
            'test_question':[],
            'user_answer':[],
            'gpt_correct':[],
            'subjective_yn':[],
            'first_letter_yn':[]
            }
        i = 0
        num = int(str(data.find('div', class_='font-16 text-success font-bold').find('span').contents[0]).replace('객관식', '').replace('문항', ''))
        for _answer_, _form_ in zip(data.find_all('div', class_ = 'answer hidden'), data.find_all('div', class_='flip-card')):
            for tag in _form_.find_all('label'):
                if _answer_.contents == tag.find('div').find('div').contents:
                    l['test_question'].append(_form_.find_all('input')[i].attrs['value'])
                    l['user_answer'].append(tag.parent.find('input').attrs['value'])
                    l['gpt_correct'].append(0)
                    l['subjective_yn'].append(0)
                    l['first_letter_yn'].append(0)

        payload = {
            'class_idx_2': class_id,
            'set_idx_2': set_id,
            'p_case_sensitive_yn': '0',
            'test_type': '2',
            'user_idx': '5391259',
            'is_only_wrong': '0',
            'set_type': '1',
            'is_print': '0',
            'mode': '',
            'test_q_type': '1',
            'test_q_cnt': num,
            'test_q_cnt_bm': num,
            'recall_condition_yn': '0'
        }
        for i in range(num):
            payload[f'test_question[{i}]'] = l['test_question'][i]
            payload[f'user_answer[{i}]'] = l['user_answer'][i]
            payload[f'gpt_correct[{i}]'] = l['gpt_correct'][i]
            payload[f'subjective_yn[{i}]'] = l['subjective_yn'][i]
            payload[f'first_letter_yn[{i}]'] = l['first_letter_yn'][i]
        print(self.session_login.post('https://www.classcard.net/ClassTest/submittest', payload).text)

if __name__ == '__main__':
    classcard = Card()
    classcard.login('2024hg3627', 'lucky090115')
    class_ = classcard.get_class()
    while True:
        print('학습할 클래스를 선택하세요.')
        l = []
        for i, name in zip(range(len(class_)), class_):
            print(i, name, class_[name])
            l.append(name)
        num = input('클래스 이름 왼쪽의 숫자 : ')
        if num.isdigit() and -1 < int(num) < len(class_):
            print(l[int(num)]+' 클래스 선택됨')
            id = class_[l[int(num)]]
            while True:
                l = []
                set_ = classcard.get_set(id)
                print('학습할 세트를 선택하세요.')
                for i, name in zip(range(len(set_)), set_):
                    print(i, name, set_[name])
                    l.append(name)
                num = input('세트 이름 왼쪽의 숫자 : ')
                if num.isdigit() and -1 < int(num) < len(set_):
                    print(l[int(num)]+' 세트 선택됨')
                    id = id.replace('/ClassMain/', '')
                    set_id = set_[l[int(num)]]
                    while True:
                        num = input('학습 메뉴를 선택하세요.\n공지. 테스트는 객관식만 가능하고, (5, 6) 메뉴는 추후 지원할 예정입니다.\n1. 암기\n2. 리콜\n3. 스펠\n4. 테스트\n5. 전부 완료(테스트 제외)\n6. 전부 완료(테스트 포함)\n7.나가기\n숫자 선택 : ')
                        if num.isdigit() and 0 < int(num) < 8:
                            match int(num):
                                case 1:
                                    classcard.study_api(id, set_id, 1)
                                case 2:
                                    classcard.study_api(id, set_id, 2)
                                case 3:
                                    classcard.study_api(id, set_id, 3)
                                case 4:
                                    classcard.study_test(id, set_id)
                                case _:
                                    print('잘못된 입력입니다.')
                        else:
                            print('잘못된 입력입니다.')
                else:
                    print('잘못된 입력입니다.')
                
        else:
            print('잘못된 입력입니다.')
