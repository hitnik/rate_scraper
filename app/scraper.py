import os
from app import settings
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import time
import datetime
import pytz
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

class RateScraper ():

    def get_html(self):

        os.environ['MOZ_HEADLESS'] = '1'
        binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe')
        driver = webdriver.Firefox(firefox_binary=binary,
                                   executable_path="C:\\geckodriver.exe")
        driver.get(settings.STOCK_URL)
        time.sleep(5)
        html = driver.page_source
        driver.close()
        return html

    def scrape_rates(self):
        data = {}
        data['date'] = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        html = self.get_html()
        soup = BeautifulSoup(html, 'html.parser')
        div_main = soup.find('div', 'containerCenter')
        tbody = div_main.find('tbody')
        rows = tbody.find_all('tr')
        for row in rows:
            tds = row.find_all('td')
            curr_name = tds[0].find('a').text.lstrip().rstrip().replace('/BYN_TOD','')
            curr_rate = tds[1].text
            data[curr_name] = curr_rate

        return data

    @classmethod
    def put_to_db(cls, data):
        engine = create_engine(settings.CONN_STR)
        Base = automap_base()
        Base.prepare(engine, reflect=True)
        Currency = Base.classes.rates_currency
        Rate = Base.classes.rates_rate
        session = Session(engine)
        date = data['date']
        for k, v in data.items():
            if session.query(Currency.query.filter(Currency.short == k).
                            exists()).scalar():
                currency = Currency()

