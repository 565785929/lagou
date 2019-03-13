import requests
from bs4 import BeautifulSoup
import json
import os
import logging
import xlwt

logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler("log.txt")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class LagouCrawler:
    """lagou crawler"""
    def __init__(self):
        self.session = requests.session()
        self.host = "https://www.lagou.com/"
        self.soup = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
        }

    def get_one(self):
        """ get title one """
        lagou_one = self.soup.select("#sidebar > div > div > div.menu_main.job_hopping > div > h2")
        return [i.text.strip() for i in lagou_one]

    def get_two(self):
        """ get title two """
        lagou_two = self.soup.select("#sidebar > div > div > div.menu_sub.dn > dl > dt > span")
        return [i.text.strip() for i in lagou_two]

    def get_three(self):
        """ get title three """
        lagou_three = (self.soup.select("#sidebar > div > div > div.menu_sub.dn > dl > dd > a"))
        # for i in lagou_three:
        #     title_dic = {"tone": i['data-lg-tj-id'], "ttwo": i['data-lg-tj-no'], "tthree": i.text, "url": i['href']}
        return [{"tone": i['data-lg-tj-id'], "ttwo": i['data-lg-tj-no'], "three": i.text, "url": i['href']}
                for i in lagou_three]

    def make_title(self, title_one, title_two, title_three):
        """ title three remix """
        title_len = title_three.__len__()
        j = 0
        k = 0
        for i in range(title_len - 1):
            title_three[i]['one'] = title_one[j]
            title_three[i]['two'] = title_two[k]
            if title_three[i]['tone'] != title_three[i + 1]['tone']:
                j += 1
            if title_three[i]['ttwo'][1] != title_three[i + 1]['ttwo'][1] or title_three[i]['ttwo'][0] != \
                    title_three[i + 1]['ttwo'][0]:
                k += 1
        title_three[title_len - 1]['one'] = title_one[j]
        title_three[title_len - 1]['two'] = title_two[k]

        return title_three

    def get_url_list(self, url, page_no=0):
        url_list = []
        html = self.session.get(url, headers=self.headers).text
        soup = BeautifulSoup(html, 'lxml')
        if page_no == 0:
            page_no = soup.findAll('a', class_="page_no")[-2].text
        for i in soup.findAll('a', class_="position_link"):
            try:
                url_list.append(i['href'])
            except Exception as e:
                print(e)
        for page in range(2, int(page_no)+1):
            html = requests.get(url+str(page), headers=self.headers).text
            soup = BeautifulSoup(html, 'lxml')
            for i in soup.findAll('a', class_="position_link"):
                try:
                    url_list.append(i['href'])
                except Exception as e:
                    print(e)
        return url_list

    def get_page(self, url):
        """ detail information but not clean """
        session = requests.session()
        session.get(self.host)
        resp = session.get(url, headers=self.headers)
        if resp.status_code != 200:
            # status code not success
            logger.error(resp.status_code)
            logger.error(url)
        else:
            html = resp.text
            soup = BeautifulSoup(html, 'lxml')
            name = soup.select("body > div.position-head > div > div.position-content-l > div > span")
            if name:
                name = name[0].text

                salary = soup.select("body > div.position-head > div > div.position-content-l > dd > p > span")
                money = salary[0].text
                addr = salary[1].text
                times = salary[2].text
                experience = salary[3].text
                part_time = salary[4].text

                advantage = soup.select("#job_detail > dd.job-advantage > p")
                advantage = advantage[0].text

                job_detail = soup.select("#job_detail > dd.job_bt > div")
                job_detail = job_detail[0].text
                # print(job_detail)

                work_addr = soup.select("#job_detail > dd.job-address.clearfix > div.work_addr")
                work_addr = work_addr[0].text.replace(' ', '').replace('\n', ' ')

                com_name = soup.select("#job_company > dt > a > div > h2 > em")
                com_name = com_name[0].text.strip()

                com_feature = soup.select("#job_company > dd > ul")
                com_feature = com_feature[0].text.replace(' ', '').replace('\n', ' ')
                return {"name": name, "money": money, "advantage": advantage, "job_detail": job_detail,
                        "work_addr": work_addr, "com_name": com_name, "com_feature": com_feature, "addr": addr,
                        "times": times, "expertence": experience, "part_time": part_time}

        return None

    def lagou_format(self, result, tag):
        return result['one']+tag+result['two']+tag+result['three']+tag


    def main(self):

        lagou_html = self.session.get(self.host).text
        self.soup = BeautifulSoup(lagou_html, 'lxml')
        results = self.make_title(self.get_one(), self.get_two(), self.get_three())
        print(results)
        # self.save_xls(results)  # save excel

        for result in results[:5]:     # 解除限制
            url_list = self.get_url_list(result['url'], 1)      # 1页，解除限制
            for url in url_list[:5]:    # 解除限制
                try:
                    detail = self.get_page(url)
                    if detail != None:
                        detail['title'] = self.lagou_format(result, '-') + detail['name']
                        js = self.get_json(detail)

                        print(detail['title'])
                        print(js)
                        self.save_json(self.lagou_format(result, '/'), detail['name'].replace('/', '')+'.json', js)
                    else:
                        print("error")
                except Exception as e:
                    logger.error(e)
                    logger.error(result['url'])

    def get_json(self, dic):
        """ json 格式化输出 """
        import json
        # demoDictList is the value we want format to output
        str = json.dumps(dic, indent=4,  ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        return str

    def save_json(self, path, name, json_data):
        """ 存储到json文件中 """
        print(os.path.exists(path))
        if not os.path.exists(path):
            os.makedirs(path)
        f = open(path + name, "w+", encoding='utf-8')
        f.write(json_data)
        f.close()

    def save_xls(self, result):
        """ 存储到excel中 """
        len = result.__len__()
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('lagou')
        for i in range(len):
            worksheet.write(i, 0, label=result[i]['one'])
            worksheet.write(i, 1, label=result[i]['two'])
            worksheet.write(i, 2, label=result[i]['three'])
            worksheet.write(i, 3, label=result[i]['url'])
        workbook.save('lagou.xls')

lg = LagouCrawler()
lg.main()
