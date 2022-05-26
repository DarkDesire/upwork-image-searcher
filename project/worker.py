
from __future__ import division
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd 
import gspread
from google.oauth2.service_account import Credentials
from celery import Celery
import io
import math
from io import BytesIO
from PIL import Image
import base64 
from celery.utils.log import get_task_logger

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")
logger = get_task_logger(__name__)


INPUT_FILE = './countries.csv'
path = './'
image_ext = '.png'

df = pd.read_csv(INPUT_FILE)
countries = dict(zip(df.Country.str.lower(), df.l2.str.lower()))

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

credentials = Credentials.from_service_account_file('service_account.json',scopes=scopes)

gc = gspread.authorize(credentials)

@celery.task(name="create_task")
def create_task(link, language,country):
    # PROXY = "11.456.448.110:8080"
    # chrome_options.add_argument(f'--proxy-server={PROXY}')
    
    chrome_options = Options()  
    chrome_options.add_argument("--headless")  
    url = os.environ.get("SELENIUM_SERVER_URL", "http://localhost:4444/wd/hub")
    try:
        driver = webdriver.Remote(command_executor=url,options=chrome_options)
        crawl(link, language, country, driver)
    except Exception as e:
        print(e)
        driver.quit()
    return True

def _make_query(word,language,country):
    base_url = 'https://www.google.com/search?q='
    query = word.replace(' ','%20')
    lr="&lr=lang_xx".replace('xx',language.lower())
    cr="&cr=countryXX".replace('XX',country.upper())
    return base_url+query+lr+cr

def crawl(link,language,country,driver):
    sh = gc.open_by_url(link)
    worksheet = sh.get_worksheet(0)
    df = pd.DataFrame(worksheet.get_all_records())
    logger.info(df)
    for index, row in df.iterrows():
        word = row['Words'].strip()
        link = _make_query(word,language,country)
        driver.get(link)
        S = lambda X: driver.execute_script('return document.body.parentNode.scroll'+X)
        driver.set_window_size(S('Width'),S('Height')) # May need manual adjustment
        screen_base64 = driver.find_element(by=By.TAG_NAME, value='body').screenshot_as_base64
        image = Image.open(io.BytesIO(base64.decodebytes(bytes(screen_base64, "utf-8"))))
        im_slices = long_slice(image)
        for slice_ind, slice in enumerate(im_slices):
            df.at[index,'Images'+str(slice_ind)] = str(slice)

    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    driver.quit()    
    return True

def long_slice(img, slice_size = 1080):
    logger.info('long_slice')
    """slice an image into parts slice_size tall"""
    width, height = img.size
    upper = 0
    left = 0
    slices = int(math.ceil(height/slice_size))

    count = 1
    im_slices = []
    for _ in range(slices):
        #if we are at the end, set the lower bound to be the bottom of the image
        if count == slices:
            lower = height
        else:
            lower = int(count * slice_size)  

        bbox = (left, upper, width, lower)
        working_slice = img.crop(bbox)
        upper += slice_size
        #save the slice
        im_slices.append(working_slice)
        count +=1
    
    return im_slices