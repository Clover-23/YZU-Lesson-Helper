'''
作品:   元智選課小幫手
作者:   Lucky Clover
完成日: 2023/02/18
版本:   v1.0.0

'''
import cv2, numpy, requests, threading
from configparser import ConfigParser
from bs4 import BeautifulSoup as BS
from tensorflow import keras
from time import ctime, sleep

class webBot:
    def __init__(self, debug = False):
        load_model_thread = threading.Thread(target=self.__loading_model)
        load_model_thread.start()
        self.__label_code = '9876543210ZYXWVUTSRQPONMLKJIHGFEDCBA'

        self.__read_setting_file()
        with open(self.__input_file_name, 'r', encoding='utf-8') as r:
            self.__ID = r.readline().strip()
            self.__password = r.readline().strip()
            self.__lessonList = [line.strip() for line in r.readlines()]

        self.__session = requests.Session()
        self.__session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.78'
        self.__login_data = {
            '__VIEWSTATE': '',
            'DPL_SelCosType': '',
            '__EVENTVALIDATION': '',
            '__VIEWSTATEGENERATOR': '',
            'btnOK': '確定',
            
            'Txt_User': self.__ID,
            'Txt_Password': self.__password,
            'Txt_CheckCode': '',
        }

        self.__select_data_template = {
            '__EVENTTARGET': 'DPL_Degree',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',

            '__VIEWSTATE': '',
            '__VIEWSTATEENCRYPTED': '',
            '__EVENTVALIDATION': '',
            '__VIEWSTATEGENERATOR': '',
            
            'Hidden1': '',
            'Hid_SchTime': '',
            'DPL_DeptName': '',
            'DPL_Degree': '6',
        }

        self.__login_url = 'https://isdna1.yzu.edu.tw/CnStdSel/Index.aspx'
        self.__captcha_png = 'https://isdna1.yzu.edu.tw/CnStdSel/SelRandomImage.aspx'
        self.__lesson_data_base_url = 'https://isdna1.yzu.edu.tw/CnStdSel/SelCurr/CosList.aspx'
        self.__select_lesson_url = 'https://isdna1.yzu.edu.tw/CnStdSel/SelCurr/CurrMainTrans.aspx?mSelType=SelCos&mUrl='

        self.__debug = debug
        load_model_thread.join()

    def __captcha_to_str(self):
        img_gray = numpy.array([cv2.cvtColor(cv2.imread('login.png'), cv2.COLOR_BGR2GRAY).reshape(20, 60, 1) / 255.0])
        pred = self.__model.predict(img_gray)
        ans = [self.__label_code[numpy.argmax(ele[0])] for ele in pred]

        return '{}{}{}{}'.format(ans[0],ans[1],ans[2],ans[3])

    def __loading_model(self):
        self.__model = keras.models.load_model('captcha_model.h5')

    def __read_setting_file(self):
        parser = ConfigParser()
        parser.read('SETTING.ini')
        self.__select_bot_mode = bool(parser['Setting']['select-lesson-mode'] == '1')
        self.__get_lesson_mode = bool(parser['Setting']['get-lesson-info-mode'] == '1')
        self.__delay_per_cycle = float(parser['Setting']['delay-per-cycle'])
        self.__delay_per_lesson = float(parser['Setting']['delay-per-lesson'])
        self.__input_file_name = parser['Setting']['input-file-name']
        self.__output_file_name = parser['Setting']['output-file-name']

    def __yzu_login(self) -> bool:
        self.__session.cookies.clear()
        with open('login.png', 'wb+') as captcha:
            captcha.write(self.__session.get(self.__captcha_png, stream=True).content)
        captcha_str = self.__captcha_to_str()

        login_page = self.__session.get(self.__login_url)
        if self.__debug:
            with open('login_page.html', 'w+', encoding='utf-8') as w:
                w.write(login_page.text)

        if '尚未開放!' in login_page.text:
            print('{}\t選課系統尚未開放!'.format(ctime()))
            return False
        
        bs = BS(login_page.text, 'lxml')
        self.__login_data['__VIEWSTATE'] = bs.select("#__VIEWSTATE")[0]['value']
        self.__login_data['DPL_SelCosType'] = bs.select("#DPL_SelCosType option")[1]['value']
        self.__login_data['__EVENTVALIDATION'] = bs.select("#__EVENTVALIDATION")[0]['value']
        self.__login_data['__VIEWSTATEGENERATOR'] = bs.select("#__VIEWSTATEGENERATOR")[0]['value']
        self.__login_data['Txt_CheckCode'] = captcha_str

        login_resp = self.__session.post(self.__login_url, data = self.__login_data)
        if "location ='SelCurr.aspx?Culture=zh-tw'" in login_resp.text:
            if self.__debug:
                with open('login_success.html', 'w+', encoding='utf-8') as w:
                    w.write(login_resp.text)
            print('Success! Captcha: {}'.format(captcha_str))
            return True
        else:
            if self.__debug:
                with open('login_fault.html', 'w+', encoding='utf-8') as w:
                    w.write(login_resp.text)
            print('Fault!')
            return False

    def __get_lesson_data(self) -> bool:
        department_set = set([e.split(':')[0] for e in self.__lessonList])
        self.__select_data = {}
        self.__lesson_data_base = {}

        for id in department_set:
            resp = self.__session.get(self.__lesson_data_base_url)
            if "異常登入" in resp.text:
                print("異常登入")
                self.session.cookies.clear()
                return False

            bs = BS(resp.text, 'lxml')
            if self.__debug:
                with open('pre-lesson.html', 'w+', encoding='utf-8') as w:
                    w.write(resp.text)
            self.__select_data[id] = self.__select_data_template.copy()
            self.__select_data[id]['DPL_DeptName'] = id
            self.__select_data[id]['__VIEWSTATE'] = bs.select("#__VIEWSTATE")[0]['value']
            self.__select_data[id]['__EVENTVALIDATION'] = bs.select("#__EVENTVALIDATION")[0]['value']
            self.__select_data[id]['__VIEWSTATEGENERATOR'] = bs.select("#__VIEWSTATEGENERATOR")[0]['value']

            resp = self.__session.post(self.__lesson_data_base_url, data = self.__select_data[id])
            if self.__debug:
                with open('lesson.html', 'w+', encoding='utf-8') as w:
                    w.write(resp.text)

            if 'Error' in resp.text:
                print('Wrong ID:{}, pls check!'.format(id))
                return False
            
            for lessonInfo in BS(resp.text, 'lxml').select("#CosListTable input"):
                if self.__debug:
                    print(lessonInfo)
                data = lessonInfo.attrs['name'].split(',')

                lesson = data[1] + data[2]
                self.__lesson_data_base[lesson] = {
                    'name': '{} {}'.format(lesson, data[-1].split(' ')[1]),
                    'mUrl': lessonInfo.attrs['name'],
                    'token': '{},{},{}'.format(data[3], data[1], data[2]),
                    'info': None
                }
        return True

    def __select_lesson(self, delay) -> bool:
        for lesson in self.__lessons:
            try:
                if not (lesson[1] in self.__lesson_data_base):
                    print('{}, wrong class id.'.format(lesson[1]))
                    self.__lessons.remove(lesson)
                    continue
                
                # get class information
                if self.__get_lesson_mode and self.__lesson_data_base[lesson[1]]['info'] == None:
                    bs = BS(self.__session.get('https://isdna1.yzu.edu.tw/CnStdSel/SelCurr/CosInfo.aspx?mCosInfo={}'.format(self.__lesson_data_base[lesson[1]]['token'])).text, 'lxml')
                    self.__lesson_data_base[lesson[1]]['info'] = []
                    # output lesson info to file
                    with open(self.__output_file_name, 'a', encoding='utf-8') as w:
                        for ele in bs.find_all(class_ = 'cls_info_main'):
                            buf = ele.text.replace(',', ' ').strip()
                            self.__lesson_data_base[lesson[1]]['info'].append(buf)
                            w.write('{},'.format(buf))
                        w.write('\n')
                    print('Get lesson:\t{}\t{}'.format(self.__lesson_data_base[lesson[1]]['info'][1]+self.__lesson_data_base[lesson[1]]['info'][2], self.__lesson_data_base[lesson[1]]['info'][0]))

                # select lesson mode
                if self.__select_bot_mode:
                    bs = BS(self.__session.post(self.__lesson_data_base_url, data = self.__select_data[lesson[0]]).text, 'lxml')
                    # set payload
                    payload = self.__select_data_template.copy()
                    payload['__VIEWSTATE'] = bs.select("#__VIEWSTATE")[0]['value']
                    payload['__EVENTVALIDATION'] = bs.select("#__EVENTVALIDATION")[0]['value']
                    payload['__VIEWSTATEGENERATOR'] = bs.select("#__VIEWSTATEGENERATOR")[0]['value']
                    payload['DPL_DeptName'] = lesson[0]
                    payload[self.__lesson_data_base[lesson[1]]['mUrl'] + '.x'] = '0'
                    payload[self.__lesson_data_base[lesson[1]]['mUrl'] + '.y'] = '0'

                    # select lesson
                    sleep(0.2)
                    self.__session.post(self.__lesson_data_base_url, data = payload)
                    bs = BS(self.__session.get(self.__select_lesson_url + self.__lesson_data_base[lesson[1]]['mUrl'] + ',B,').text, 'lxml')

                    msgJS = bs.select("script")[0].string
                    msg = msgJS.split(';')[0]
                    # output log
                    if self.__lesson_data_base[lesson[1]]['info'] == None:
                        print('{} {}\t{}'.format(ctime(), self.__lesson_data_base[lesson[1]]['name'], msg))
                    else:
                        print('{} {}\t人數: {}\t{}'.format(ctime(), self.__lesson_data_base[lesson[1]]['name'], '{}/{}'.format(self.__lesson_data_base[lesson[1]]['info'][10], self.__lesson_data_base[lesson[1]]['info'][9]), msg))
                    # modify lesson list & test if log-out
                    if "加選訊息：" in msg or "已選過" in msg:
                        self.__lessons.remove(lesson)
                    elif "again!" in msg or "You" in msg:
                        print('{} {}'.format(ctime(), msgJS))
                        self.__yzu_login()
                        return
                else:
                    self.__lessons.remove(lesson)
            except:
                self.__yzu_login()
                return
            # delay
            sleep(delay)
            
    def run_bot(self):
        if not self.__select_bot_mode and not self.__get_lesson_mode:
            print('Both modes are not turn on!\nPleace check "SETTING.ini" and restart this program.')
            return
        
        if self.__yzu_login() and self.__get_lesson_data():
            self.__lessons = [e.split(':') for e in self.__lessonList]
            while len(self.__lessons) != 0:
                if self.__get_lesson_mode:
                    with open(self.__output_file_name, 'w+', encoding='utf-8') as w:
                        w.write('課名,課號,班別,學分,開課系所,授課教師,檢查下限,檢查上限,人數下限,人數上限,已選人數,選別,英語授課,英語授課推薦,網路教學,跨領域教學,服務學習,全外語教學,終端學習,EMBA,碩博士在職專班,數位應用課程,議題導向實作專題課程,上課時間,上課地點,\n')
                self.__select_lesson(self.__delay_per_lesson)
                sleep(self.__delay_per_cycle)
        else:
            print('Login or database error! Please try again!')