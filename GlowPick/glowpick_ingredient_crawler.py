import os
import re
import csv
import time
import json
import MySQLdb
import pymysql
import requests
import datetime
import db_model
import pickle
import pyautogui
import pandas as pd

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

from typing import collections, Dict, Tuple, List


os.chdir('C:/Users/user/Desktop/code blue/아이웨딩/data')
with open("C:/Users/user/Desktop/code blue/아이웨딩/data/glowpick_comment_list.json", "r", encoding="UTF-8") as f:
    p_list = json.load(f)

keyword_list = set()
for i in p_list:
    if i['keyword'] != '마스카라':
        keyword_list.add(i['keyword'])
keyword_list = list(keyword_list)
print(keyword_list)


def ingredient_crawler():
    for word in keyword_list[11:]:
        unique_product = set()
        for product in p_list:
            if product['keyword'] == word:
                unique_product.add(product['product_id'])
    temp_product = list(unique_product)
    
    ##################### 크롤링 시작 ####################
    cnt = 0
    temp_dict = []
    
    for id in temp_product:
        # dict형태의 자료형 선언
        p = {}
        p['product_id'] = str(id)

        # Get url 
        url = 'https://www.glowpick.com/products/' + str(id)
        print(url)
        # Get window
        option = webdriver.ChromeOptions()  
        #option.add_argument('--headless') 
        option.add_argument('--no-sandbox') 
        option.add_argument('--disable-dev-shm-usage')
        option.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko")
        option.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 1})

        driver = webdriver.Chrome(ChromeDriverManager(version='96.0.4664.45').install(), options = option)

		# wait until someid is clickable
        wait = WebDriverWait(driver, 10)
        wait2 = WebDriverWait(driver, 2)

        driver.maximize_window()
        driver.get(url)
        try:
            wait2.until(EC.element_to_be_clickable((By.CLASS_NAME, 'buttons__button.buttons__close')))
        except:
            pass
        
        # 크롤링 
        #  popup이 있으면 제거 없으면 pass
        try:
            driver.find_element_by_class_name('popup')
            driver.find_element_by_css_selector('#default-layout > div > div.modals > span > div >\
                    div.popup__container > div.popup__container__buttons.buttons > button.buttons__button.buttons__close').click()
        except:
            pass
        # 좌표 객체 얻기 
        position = pyautogui.position()
        # 화면 전체 크기 확인하기
        #print(pyautogui.size())

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 성분구성의 article tab 번호 찾기
        for idx, article in enumerate(soup.find_all('article', 'info__article')):
            if article.get_text().strip().split('\n')[0] == '성분 구성':
                new_idx = idx+1
                driver.find_element_by_xpath(f'//*[@id="contents"]/section/div[3]/article[{new_idx}]/h3/button').click()
                wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="contents"]/section/div[3]/article[{new_idx}]/h3/button')))

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'details__contents__h1__button')))

                # 위험도 지표 크롤링
                p['harmness'] = {}
                harmness_label = soup.find_all('div', 'tag legends__legend')
                for label in harmness_label:
                    name = label.find('p').get_text().strip()
                    grade = label.find('span').get_text().strip().split('개')[0]
                    p['harmness'][name] = grade
                print('---------------harness---------------------')

                # ingredient 크롤링 
                p['ingredient'] = {}
                ingredients = soup.find('ul','ingredient__list').find_all('li')
                count = 1
                for ingre in ingredients: 
                    kor = ingre.find('p', 'item__wrapper__text__kor').get_text().strip()
                    eng = ingre.find('p', 'item__wrapper__text__eng').get_text().strip()
                    desc = ingre.find('p', 'item__wrapper__text__desc').get_text().strip()

                    if ingre.find('p','tag__label'):
                        tag_label = ingre.find('p','tag__label').get_text().strip()
                    else: 
                        tag_label = None

                    p['ingredient'][str(count)] = {}
                    p['ingredient'][str(count)]['kor'] = kor
                    p['ingredient'][str(count)]['eng'] = eng
                    p['ingredient'][str(count)]['desc'] = desc
                    p['ingredient'][str(count)]['tag_label'] = tag_label
                    count += 1
                print('---------------ingredient---------------------')

             # 마우스 이동 (x 좌표, y 좌표)
            pyautogui.moveTo(1500, 500)

            # 마우스 클릭
            pyautogui.click()
            pyautogui.click()

            if article.get_text().strip().split('\n')[0] == '제품 설명':
                new_idx = idx+1
                driver.find_element_by_xpath(f'//*[@id="contents"]/section/div[3]/article[{new_idx}]/h3/button').click()
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'details__contents__h1__button')))
                sub_name = soup.find_all('span', 'descriptions__article__category descriptions__article__category-link')[-1].get_text()
                p['subcategory_name'] = sub_name
                print('---------------subname---------------------')
        cnt +=1
        temp_dict.append(p)
        driver.close()
        if cnt % 10 == 0 :
            print(cnt)

    with open(f"./{word.replace('/', '_')}_data.json", "w") as f:
        json.dump(temp_dict, f)
        
        
if __name__ == "__main__":
    ingredient_crawler()