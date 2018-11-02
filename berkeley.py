import requests
import re
from bs4 import BeautifulSoup
import os
import pandas as pd


class BerkeleyTeacher(object):
    def __init__(self):
        self.url = 'http://facultybio.haas.berkeley.edu/faculty-photo/'
        self.headers = self.get_header("facultybio.haas.berkeley.edu")
        self.req = requests.session()
        self.path = '../ComputeNetwork/file/'
        self.page_list = []
        self.faculty_pattern = re.compile('http://facultybio\.haas\.berkeley\.edu/faculty-list/[a-z]+-?[a-z]+/')
        self.title_list = ['Associate Professor', 'Assistant Professor', 'Professor Emeritus', 'Professor']
        self.title_pattern = re.compile('(?:Associate|Assistant)? ?Professor ?(?:Emeritus)?', re.I)
        self.wrong_title_pattern = re.compile('(Adjunct Professor)|(Visiting Associate Professor)', re.I)
        self.phone_pattern = re.compile('[0-9]{3}-[0-9]{3}-[0-9]{4}')
        self.email_pattern = re.compile('var email_addr = (.*?\.(?:com|edu)");')
        self.result_list = []
        self.interest = re.compile('Current Research and Interests</strong></p><br><ul><li>([\s\S]*?)</li></ul><br>')
        self.name_pattern = re.compile('<span><strong>([\s\S]*?)</strong></span>')
        self.homepage_pattern = re.compile('Homepage:.*(http://.*?)==', re.I)
        self.teaching_pattern = re.compile('Teaching</strong></p><br><ul><li>(.*?)</li></ul><br><br><p><strong>', re.I)
        self.background_pattern = re.compile('Positions Held</strong></p> +<br><p>(.*?)</p><br><br><p><strong>', re.I)
        self.waste_tag = re.compile('<em>|</em>|</p>|</li>|</ul>|<p>|</span>|&#822[0-9];|</a>|', re.I)
        self.extract_from_li = re.compile('<span.*?>|<li.*?>|<div.*?>|<a.*?>|<!--.*?>|<script.*?>.*?</script>|<noscript>.*?</noscript>', re.I)
        self.subn_split = re.compile('<br>|</br>|<br />')
        self.subn_split2 = re.compile('&#821[0-9];')

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
        res = self.req.get(self.url, headers=self.headers).content.decode("UTF-8")

        faculty_list = re.findall(self.faculty_pattern, res)
        print(len(faculty_list))
        text = "\n".join(faculty_list)
        self.save_file('list', text)
        print(faculty_list)
        for i in range(0, len(faculty_list), 2):
            faculty_url = faculty_list[i]
            faculty_page = self.req.get(faculty_url, headers=self.headers)
            try:
                faculty_text = faculty_page.content.decode('utf-8')
                name = re.findall(self.name_pattern, faculty_text)[0].replace('\n',
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
                    name = re.findall(self.name_pattern, faculty_text)[0].replace(
                        '\n',
                        '').replace(
                        '\t', '')
                    print(name)
                except BaseException as e:
                    self.format_error(e, 'name 出错')
                try:
                    main_content = soup.find_all(valign="top")[1]
                    main_text = main_content.text
                    title_text = re.findall(self.title_pattern, main_text)
                    print(title_text)
                    wrong_title = re.findall(self.wrong_title_pattern, main_text)
                    if len(title_text) > 0 and len(wrong_title) == 0:
                        title = title_text[0]
                        try:
                            telephone = re.findall(self.phone_pattern, faculty_text)[0]
                            print(telephone)
                        except BaseException as e:
                            telephone = ''
                            self.format_error(e, name + "电话出错")
                        try:
                            email_str = re.findall(self.email_pattern, faculty_text)[0]
                            email = self.parse_email(email_str)
                            print(email)
                        except BaseException as e:
                            email = ''
                            self.format_error(e, name + 'email出错')

                        interest = self.parse_interest(faculty_text)
                        homepage = self.parse_homepage(main_text)
                        teaching = self.parse_teaching(faculty_text)
                        background = self.parse_background(faculty_text)
                        self.result_list.append(
                            dict(name=name, title=title, telephone=telephone, email=email, interest=interest, homepage=homepage, teaching=teaching, background=background))
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
        interest = re.findall(self.interest, main_text)
        if len(interest) > 0:
            return self.remove_waste_tag(interest[0])
        else:
            return ''

    def parse_homepage(self, text):
        main_text = text.replace('\t', '==').replace('\n', '==')
        homepage = re.findall(self.homepage_pattern, main_text)
        if len(homepage) > 0:
            res = self.remove_waste_tag(homepage[0])
            return res
        else:
            return ''

    def parse_teaching(self, text):
        main_text = text.replace('\t', '').replace('\n', '')
        teaching = re.findall(self.teaching_pattern, main_text)
        if (len(teaching)) > 0:
            res = self.remove_waste_tag(teaching[0])
            return res
        else:
            return ''

    def parse_background(self, text):
        main_text = text.replace('\t', '').replace('\n', '')
        back = re.findall(self.background_pattern, main_text)
        if (len(back)) > 0:
            res = self.remove_waste_tag(back[0])
            return res
        else:
            return ''

    def remove_waste_tag(self, text):
        res = re.subn(self.subn_split, ';', text)[0]
        res = re.subn(self.extract_from_li,'', res)[0]
        res = re.subn(self.waste_tag,'', res)[0]
        res = re.subn(self.subn_split2, '-', res)[0]
        res = res.replace('&nbsp;', ' ')
        return res
def test_subn():
    b = BerkeleyTeacher()
    text1 = 'At Haas since 20122012 &#8211; present, Willis H. Booth Chair in Bankin'
    text = 'Organizational Theory</div>;<div class="gmail_default">Economic Sociology</div>;<div class="gmail_default">Categorization and Markets</div>;<div class="gmail_default">Labor markets and hiring</div>;<div class="gmail_default">Career choice</div>'
    print(b.remove_waste_tag(text1))


if __name__ == '__main__':
    berkeley = BerkeleyTeacher()
    # berkeley.parse_photo_url()
    berkeley.open_file_list()
    berkeley.parse_page()
    # test_subn()
