import requests
import re
from bs4 import BeautifulSoup
import os
import pandas as pd


class BerKeleyTeacher(object):
    def __init__(self):
        self.url = 'http://facultybio.haas.berkeley.edu/faculty-photo/'
        self.headers = self.get_header("facultybio.haas.berkeley.edu")
        self.req = requests.session()
        self.path = '../ComputeNetwork/file/'
        self.page_list = []
        self.title_list = ['Associate Professor', 'Assistant Professor', 'Professor Emeritus', 'Professor']
        self.wrong_title = ['Adjunct Professor', 'Visiting Associate Professor']
        self.result_list = []
        self.interest = 'Current Research and Interests</strong></p><br><ul>([\s\S]*?)</ul><br>'
    def get_header(self, host):
        header = {
            'Host': host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-encoding': 'gzip, deflate',
            'Accept-language': 'zh-CN,zh;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1'
        }
        return header

    def parse_photo_url(self):
        res = self.req.get(self.url, headers = self.headers).content.decode("UTF-8")
        faculty_pattern = 'http:\/\/facultybio\.haas\.berkeley\.edu\/faculty-list\/[a-z]+\-?[a-z]+\/'
        faculty_list = re.findall(re.compile(faculty_pattern), res)
        print(len(faculty_list))
        text = "\n".join(faculty_list)
        self.save_file('list', text)
        print(faculty_list)
        for i in range(0, len(faculty_list), 2):
            faculty_url = faculty_list[i]
            faculty_page = self.req.get(faculty_url, headers = self.headers)
            try:
                faculty_text = faculty_page.content.decode('utf-8')
                name = re.findall(re.compile('<span><strong>([\s\S]*?)</strong></span>'), faculty_text)[0].replace('\n',
                                                                                                                   '').replace(
                    '\t', '')
                print(name)
                self.save_file(name.replace(' ', '_'), faculty_text)
            except BaseException as e:
                print(e)
                print('error')

            print('=======')

    def save_file(self, file_name, data):
        with open(self.path + file_name + '.html', 'w', encoding='utf-8') as w:
            w.write(data)

    def open_file_list(self):
        path_dir = os.listdir(self.path)
        for dir in path_dir:
            file_name = self.path + dir

            self.do_open_file(file_name=file_name)

    def do_open_file(self, file_name):
        with open(file_name, 'r', encoding='utf-8') as r:
            try:
                data = r.read()
                print(file_name)
                self.page_list.append(data)
            except BaseException as e:
                self.format_error(e, file_name + "file error")

    def parse_page(self):
        for faculty_text in self.page_list:
            try:
                soup = BeautifulSoup(faculty_text, 'html5lib')

                try:
                    name = re.findall(re.compile('<span><strong>([\s\S]*?)</strong></span>'), faculty_text)[0].replace(
                        '\n',
                        '').replace(
                        '\t', '')
                    print(name)
                except BaseException as e:
                    self.format_error(e, 'name 出错')
                try:
                    main_content = soup.find_all(valign="top")[1]
                    main_text = main_content.text
                    title_text = re.findall(re.compile('(?:Associate|Assistant)? ?Professor ?(?:Emeritus)?', re.I),
                                            main_text)
                    print(title_text)
                    wrong_title = re.findall(re.compile('(Adjunct Professor)|(Visiting Associate Professor)', re.I), main_text)
                    if len(title_text) > 0 and len(wrong_title) == 0:
                        title = title_text[0]
                        try:
                            telephone = re.findall(re.compile('[0-9]{3}\-[0-9]{3}\-[0-9]{4}'), faculty_text)[0]
                            print(telephone)
                        except BaseException as e:
                            telephone = ''
                            self.format_error(e, name + "电话出错")
                        try:
                            email_str = re.findall(re.compile('var email_addr = (.*?\.(?:com|edu)");'), faculty_text)[0]
                            email = self.parse_email(email_str)
                            print(email)
                        except BaseException as e:
                            email = ''
                            self.format_error(e, name + 'email出错')

                        self.parse_interest(faculty_text)
                        self.result_list.append(dict(name=name, title=title, telephone=telephone, email=email))
                        print('##############')
                except BaseException as e:
                    self.format_error(e, 'title')


            except BaseException as e:
                self.format_error(e, 'nothing')

            # self.save_file(name.replace(' ', '_'), faculty_text)

        result_list_df = pd.DataFrame(self.result_list)
        result_list_df.to_csv(self.path + 'result.csv')

    def parse_email(self, email_str):
        split_email = email_str.split('+')
        split_email = "".join(map(lambda x: x.replace("\"", "").strip(), split_email))
        print(split_email)
        return split_email

    def format_error(self, e, msg):
        print('===================')
        print(e)
        print(msg)
        print('===================')

    def parse_interest(self, text):
        main_text = text.replace('\t', '').replace('\n', '')
        interest = re.findall(re.compile(self.interest), main_text)
        print('interest', interest)


if __name__ == '__main__':
    berkeley = BerKeleyTeacher()
    # berkeley.parse_photo_url()
    berkeley.open_file_list()
    berkeley.parse_page()
