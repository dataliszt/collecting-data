import re
import csv
import json
import time
import MySQLdb
import datetime
import db_model
import requests
import pandas as pd

from selenium import webdriver as wd
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class glowpickcrawler():
    def __init__(self):


        self.category_list = []

        #print(category_list)


        self.db_model = db_model.DB_model()

    def get_post_info(self):
        db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="devasdf4112", db="videorighter",
                             charset="utf8mb4",
                             init_command="SET NAMES UTF8MB4")
        c = db.cursor(MySQLdb.cursors.DictCursor)
        c.execute("SELECT DISTINCT category_name FROM videorighter.glowpick_product_list")
        creater_name = c.fetchall()
        for i in creater_name:
            for j in i.values():
                self.category_list.append(j)


        for keyword in self.category_list:
            self.post_urls = []
            row_id = self.db_model.set_daily_log(keyword, 4)
            # DB에 쌓인 product_id 활용해서 keyword에 해당하는 제품 url수집
            # db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="devasdf4112", db="videorighter",
            #                      charset="utf8mb4",
            #                      init_command="SET NAMES UTF8MB4")
            c = db.cursor(MySQLdb.cursors.DictCursor)
            c.execute(
                "SELECT product_id FROM videorighter.glowpick_product_list WHERE category_name = %s ",
                [keyword])
            product_num = c.fetchall()

            for i in product_num:
                for j in i.values():
                    post_url = 'https://www.glowpick.com/products/' + str(j)
                    self.post_urls.append(post_url)

            print(self.post_urls)

            chrome_options = wd.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            driver = wd.Chrome(ChromeDriverManager(version="87.0.4280.88").install(), chrome_options=chrome_options)

            for post_url in self.post_urls:
                print(post_url)
                driver.maximize_window()
                driver.get(post_url)
                driver.implicitly_wait(20)

                # 팝업1 제거
                try:
                    driver.find_element_by_css_selector(
                        '#default-layout > div > div.modals > span > div.popup > div.popup__container > div.popup__container__buttons.buttons > button.buttons__button.buttons__close').click()
                except:
                    None
                #
                # # 팝업2 제거
                # try:
                #     driver.find_element_by_css_selector(
                #         '#default-layout > div > div.modals > span > aside > div.contents.screen__box > div > button.contents__to-web').click()
                # except:
                #     None

                # 제품 설명 전체보기 클릭 (제품 상세정보 크롤링)
                driver.find_element_by_css_selector(
                    '#contents > section > div.product__info.info > article.info__article.description > h3 > button').send_keys(
                    Keys.ENTER)
                # 컬러/타입
                try:
                    color_type = self.db_model.addslashes(driver.find_element_by_css_selector(
                        "#default-layout > div > div.modals > span > div > div.details__contents.awards > div > article:nth-child(2) > div").text)
                except:
                    color_type = None
                # print(color_type)
                # 태그
                try:
                    tags = ", ".join(
                        [x.text for x in driver.find_elements_by_class_name("descriptions__article__keywords")])
                except AttributeError:
                    tags = None
                # print(tags)
                # 소분류 카테고리
                try:
                    category = driver.find_elements_by_class_name(
                        'descriptions__article__category.descriptions__article__category-link')[1].text
                except:
                    category = None
                # print(category)
                # 제품 상세 설명
                try:
                    detail = driver.find_element_by_css_selector(
                        '#default-layout > div > div.modals > span > div > div.details__contents.awards > div > article:nth-child(1) > pre').text
                except:
                    detail = None
                # print(detail)
                # 판매처
                try:
                    sellers = ",".join([x.text for x in driver.find_elements_by_class_name("stores__store__name")])
                except:
                    sellers = None
                # print(sellers)

                # 제품 설명 전체보기 닫기
                driver.find_element_by_css_selector(
                    '#default-layout > div > div.modals > span > div > div.details__contents.awards > h1 > button').send_keys(
                    Keys.ENTER)

                time.sleep(2)

                # 리뷰 크롤링
                # 네트워크 인터셉터 스크립트 삽입
                # 인터셉터 활성화 해놓은 상태에서 리뷰를 다시 불러오면 암호화된 리뷰 데이터 가로챌 수 있음
                driver.execute_script('''
                    function interceptNetworkRequests(ee) {
                        const open = XMLHttpRequest.prototype.open;
                        const send = XMLHttpRequest.prototype.send;
    
                        const isRegularXHR = open.toString().indexOf('native code') !== -1;
    
                        // don't hijack if already hijacked - this will mess up with frameworks like Angular with zones
                        // we work if we load first there which we can.
                        if (isRegularXHR) {
                            XMLHttpRequest.prototype.open = function() {
                                ee.onOpen && ee.onOpen(this, arguments);
                                if (ee.onLoad) {
                                    this.addEventListener('load', ee.onLoad.bind(ee));
                                }
                                if (ee.onError) {
                                    this.addEventListener('error', ee.onError.bind(ee));
                                }
                                return open.apply(this, arguments);
                            };
                            XMLHttpRequest.prototype.send = function() {
                                ee.onSend && ee.onSend(this, arguments);
                                return send.apply(this, arguments);
                            };
                        }
    
                        const fetch = window.fetch || "";
                        // don't hijack twice, if fetch is built with XHR no need to decorate, if already hijacked
                        // then this is dangerous and we opt out
                        const isFetchNative = fetch.toString().indexOf('native code') !== -1;
                        if(isFetchNative) {
                            window.fetch = function () {
                                ee.onFetch && ee.onFetch(arguments);
                                const p = fetch.apply(this, arguments);
                                p.then(ee.onFetchResponse, ee.onFetchError);
                                return p;
                            };
                            // at the moment, we don't listen to streams which are likely video
                            const json = Response.prototype.json;
                            const text = Response.prototype.text;
                            const blob = Response.prototype.blob;
                            Response.prototype.json = function () {
                                const p = json.apply(this.arguments);
                                p.then(ee.onFetchLoad && ee.onFetchLoad.bind(ee, "json"));
                                return p;
                            };
                            Response.prototype.text = function () {
                                const p = text.apply(this.arguments);
                                p.then(ee.onFetchLoad && ee.onFetchLoad.bind(ee, "text"));
                                return p;
                            };
                            Response.prototype.blob = function () {
                                const p = blob.apply(this.arguments);
                                p.then(ee.onFetchLoad && ee.onFetchLoad.bind(ee, "blob"));
                                return p;
                            };
                        }
                        return ee;
                    }
    
                    const filter = (req) => {
    
                        //console.log(req);
                        let data=JSON.parse(req.srcElement.response);
    
                        if(req.srcElement.responseURL.indexOf('reviews') && data.data){
    
                            console.log(data.data);
                            document.write('<div id="find_me">'+data.data+'</div>');
    
                        }
                    }
    
                    interceptNetworkRequests({
                        // onFetch: console.log,
                        // onFetchResponse: console.log,
                        // onFetchLoad: console.log,
                        // onOpen: console.log,
                        // onSend: console.log,
                        // onError: console.log,`
                        onLoad: filter
                    });
                ''')
                time.sleep(2)
                # 필터버튼 클릭
                try :
                    driver.find_element_by_css_selector(
                        "#review > div.reviews__sticky > div.reviews__search > button").send_keys(
                        Keys.ENTER)
                except :
                    None
                time.sleep(2)
                # 적용버튼 클릭
                try:
                    driver.execute_script('document.querySelector(".filters__submit").dispatchEvent(new Event("click"));')
                except :
                    None
                time.sleep(2)
                main = driver.find_elements_by_css_selector('#find_me')

                # post 통신 파라미터 생성
                txt_dict = {}
                txt_dict['data'] = main[0].text

                # 아이패밀리 내부 Decoding API로 post 방식 request
                response = requests.post("http://58.229.150.199:2048/v1/parser/list", data=txt_dict, verify=False)
                json_result = f'[{response.text}]'
                parsed = json.loads(json_result)

                post_dict = {
                    'product_id': post_url.split("/")[-1],
                    'color_type': color_type,
                    'product_description': self.db_model.addslashes(detail),
                    'tags': tags,
                    'sub_category_name': category,
                    'seller': sellers
                }

                time.sleep(1)
                # 쿼리
                body_is_new = self.db_model.set_glowpick_data_body(post_dict)

                # for i in range(len(parsed[0]['reviews'])):
                # print(len(parsed[0]['reviews']))
                for i in range(len(parsed[0]['reviews'])):
                    try:
                        review_title = self.db_model.addslashes(parsed[0]['reviews'][i]['title']['value'])
                    except:
                        review_title = None

                    try:
                        birth_year = parsed[0]['reviews'][i]['editor']['birthYear']
                    except:
                        birth_year = None

                    try:
                        nick_name = self.db_model.addslashes(parsed[0]['reviews'][i]['editor']['nickName'])
                    except:
                        nick_name = None
                    comment_dict = {
                        "keyword": keyword,
                        "product_id": post_url.split("/")[-1],
                        "review_id": parsed[0]['reviews'][i]['idreviewcomment'],
                        "review_text": self.db_model.addslashes(parsed[0]['reviews'][i]['reviewText']),
                        "rating": parsed[0]['reviews'][i]['rating'],
                        "create_date": parsed[0]['reviews'][i]['createDate'],
                        "review_title": review_title,
                        "nick_name": nick_name,
                        "birth_year": birth_year,
                        "skin_type": parsed[0]['reviews'][i]['editor']['skinType'],
                        "gender": parsed[0]['reviews'][i]['editor']['gender']
                    }
                    # 쿼리
                    self.db_model.set_glowpick_data_comment(comment_dict, body_is_new['is_new'],
                                                            body_is_new['last_time_update'])

            self.db_model.set_daily_log('', '', row_id)
            driver.quit()


if __name__ == "__main__":
    import time

    start = time.time()
    crawler = glowpickcrawler()
    crawler.get_post_info()
    print("Crawler Running Time: ", time.time() - start)
