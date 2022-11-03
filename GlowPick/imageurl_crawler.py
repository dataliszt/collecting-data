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


file_list = [ 
    '립글로스_data.json', '립베이스_data.json', '립스틱_data.json', '립틴트_라커_data.json', 
    '립펜슬_data.json', '마스카라_data.json', '멀티팔레트_data.json', '블러셔_data.json', '쉐딩_data.json', 
    '아이라이너_data.json', '아이브로우_data.json', '아이섀도우_data.json', '컨실러_data.json', '컨투어링팔레트_data.json', 
    '파운데이션_data.json', '피니시파우더_data.json', '하이라이터_data.json'
]

def image_crawler():
    no_img = []
    for file in file_list[:]:
        start = time.time()
        with open('./' + file, 'r',encoding='utf-8') as f:
            data = json.load(f)
        for idx, product in enumerate(data[:]):
            # Get url 
            url = 'https://www.glowpick.com/products/' + str(product['product_id'])
            print(url)
            # Get window
            option = webdriver.ChromeOptions()  
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
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 제품 이미지 url 얻기 
            img_url = soup.select("img[alt='제품 이미지']")[0]['src'].strip()
            if img_url:
                product['img_url'] = img_url
            else:
                no_img.append((file, product['product_id']))
                
            driver.close()
        with open('./' + file, 'w',encoding='utf-8') as f:
            json.dump(data, f)
        print(round(time.time() - start, 3))
        print(f'{file} is done!')
        
if __name__ == "__main__":
    image_crawler()