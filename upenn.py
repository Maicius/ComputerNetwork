from berkeley import BerkeleyTeacher
from bs4 import BeautifulSoup
import re
import pandas as pd


class Uppen(BerkeleyTeacher):
    def __init__(self):
        BerkeleyTeacher.__init__(self)
        self.url = 'https://www.wharton.upenn.edu/faculty-directory/'
        self.host = 'www.wharton.upenn.edu'
        self.host2 = 'fnce.wharton.upenn.edu'
        self.headers = self.get_header(host=self.host)
        self.headers['TE'] = 'Trailers'
        self.headers[
            'cookie'] = '_ga=GA1.3.941405599.1541124764; _gid=GA1.3.198821962.1541124764; STYXKEY_wmarkops_consent=dismiss; _ga=GA1.4.941405599.1541124764; _gid=GA1.4.198821962.1541124764; visitor_id327371=100705601; visitor_id327371-hash=a22ca43ca8d90478df8261d7807da1a81c1200c8b1f0927a588eff312414b22b44c7e2a5a54cdfef4ccbe2596e3e6ae32b425044'
        self.href_list_all = []
        self.email_pattern = ''
        self.path = ''
        self.headers['Referer'] = 'https://www.wharton.upenn.edu/faculty-directory/'
        self.email_pattern = re.compile('mailto:(.*@.*\.edu|com?)\"')
        self.phone_pattern = re.compile('\(?[0-9]{3}\)? ?-?[0-9]{3}-[0-9]{4}')
        self.interest = re.compile('Research Interests: ?</strong>(.*?)</p><p><strong>', re.I)
        self.homepage_pattern = re.compile('<a href="(http://.*?)">Personal Website', re.I)

    def get_all_faculty_list(self):
        res = self.req.get(url=self.url, headers=self.headers)
        content = res.content.decode('utf-8')
        soup = BeautifulSoup(content, 'html5lib')
        all_href = soup.find_all(attrs={'class': 'wpb_content_element'})
        for i in range(7, len(all_href)):
            href_list = all_href[i].find_all('a')
            href_list = filter(lambda x: str(x).find('href') != -1, href_list)
            href_list = list(map(lambda x: x.attrs['href'], href_list))
            self.href_list_all.extend(href_list)
        print(len(self.href_list_all))

    def parse_profile(self):
        for url in self.href_list_all:
            try:
                host = url.split('/')[2]
                name = url.split('/')[-2]
                self.headers['Host'] = host
                url = url.replace('\"', '')
                res = self.req.get(url=url, headers=self.headers)
                content = res.content.decode('utf-8')
                # 保存网页到本地
                # self.save_file(name, content)
                print(res.status_code, name)
                self.do_parse_page(content)
            except BaseException as e:
                self.format_error(e, 'error')
        self.save_data_to_excel()

    def parse_page(self):
        for page in self.page_list:
            self.do_parse_page(page)

    def do_parse_page(self, page):
        soup = BeautifulSoup(page, 'html5lib')
        try:
            group = soup.find_all(attrs={'class':'brand-text'})[0].text
            title_text = soup.find_all(attrs={'class': 'wfp-header-titles'})[0].text
            title = re.findall(self.title_pattern, title_text)
            wrong_title = re.findall(self.wrong_title_pattern, title_text)
            if len(title) > 0 and len(wrong_title) == 0:
                title = title[0]
                print(title)
                name = soup.h1.text.strip()
                print(name)
                email = soup.find_all(attrs={'class': 'wfp-contact-information'})[0]
                email, phone = self.parse_phone_email(str(email))
                research = soup.find_all(attrs={'class': 'wfp-header-research'})[0]
                interest, website = self.parse_research_interest(str(research))

                background_text = soup.find_all(attrs={'id': 'wfp-tabbed-navigation-section--1'})[0].find_all(
                    attrs={'class', 'wfp-tabbed-navigation-section-container'})[0].text
                self.result_list.append(
                    dict(name=name, title=title, telephone=phone, email=email,group=group, interest=interest, homepage=website,
                         background=background_text))
        except BaseException as e:
            print(e, 'error')

    def save_data_to_excel(self):
        result_df = pd.DataFrame(self.result_list)
        cols = ['name', 'title', 'email', 'telephone', 'group', 'interest', 'homepage', 'background']
        result_list_df = result_df.ix[:, cols]
        result_list_df.to_csv(self.path + 'uppen2.csv')
        self.change_columns_name2(result_list_df)

    def parse_phone_email(self, text):
        email = re.findall(self.email_pattern, text)
        phone = re.findall(self.phone_pattern, text)
        return email[0] if len(email) > 0 else '', phone[0] if len(phone) > 0 else ''

    def change_columns_name2(self, df):
        df.columns=['姓名', '职称', '邮箱', '电话', '专业', '研究领域', '个人网站', '背景介绍']
        df.to_excel(self.path + 'uppen2.xlsx')


    def parse_research_interest(self, text):
        text = text.replace('\t', '').replace('\n', '')
        interest = re.findall(self.interest, text)
        website = re.findall(self.homepage_pattern, text)
        return interest[0] if len(interest) > 0 else '', website[0] if len(website) > 0 else ''


if __name__ == '__main__':
    uppen = Uppen()
    uppen.get_all_faculty_list()
    uppen.parse_profile()
