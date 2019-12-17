import os
from app import settings
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import time
import datetime
import pytz
from sqlalchemy import create_engine, MetaData, Table


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
        engine = create_engine('sqlite:///db.sqlite3')

class DBcontrolller:
    def __init__(self, *args, **kwargs):
        self.engine = create_engine(*args, **kwargs)

        metadata = MetaData(self.engine)
        self.forum = Table('forumTopics_forums', metadata, autoload=True)
        mapper(ForumURL, self.forum)
        self.forumUsers = Table('forumTopics_forumusers', metadata, autoload=True)
        mapper(ForumUser, self.forumUsers)
        self.forumTopics = Table('forumTopics_topics', metadata, autoload=True)
        mapper(Topic, self.forumTopics)
        self.sites = Table('forumTopics_sites', metadata, autoload=True)
        mapper(Site, self.sites)

    def dispose(self):
        self.engine.dispose()

    def getSession(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        return session

    def selectListOfForumsFromDB(self):
        """
        get list of all URLs of forums
        :return: list of ForumURL
        """
        session = self.getSession()
        result = session.query(ForumURL).filter(ForumURL.isActive == '1').all()
        logger = logging.getLogger("parser")
        logger.info("get %d records of Forums from DB" % len(result))
        session.close()
        return result

    def insertForumUserToDB(self, userToSave : ForumUser, session):
        """
            try to insert ForumUser object to DB
        :param userToSave:
        :return: result of insert ForumUser object to DB
        """

        userFromDB = session.query(ForumUser).filter(and_(ForumUser.name == func.binary(userToSave.name),
                                                          ForumUser.site_id == userToSave.site_id)).scalar()
        if userFromDB == None:
            userFromDB = session.query(ForumUser).filter(ForumUser.id == userToSave.id).scalar()
            if userFromDB:
                userFromDB.name=userToSave.name
                session.commit()
                result = userFromDB.id
            else:
                session.add(userToSave)
                session.commit()
                result = userToSave.id
        else:
            result = userFromDB.id
        return result

    def insertTopicToDB(self, topic: Topic, session):
        topicFromDB = session.query(Topic).filter(Topic.id == topic.id).scalar()
        result = True
        if topicFromDB == None:
            session.add(topic)
            session.commit()
        else:
            result = False
        return result

    def updateForumEntry(self, forumURL: ForumURL, session):
        logger = logging.getLogger("parser")
        # session = self.getSession()
        query = session.query(ForumURL).filter(ForumURL.id == forumURL.id)
        query = query.update({self.forum.c.pages.name: forumURL.pages,
                              self.forum.c.pagesTotal: forumURL.pagesTotal})
        session.commit()
        session.close()
        logger.info('%s put to DB pages: %d, totalPages: %d' % (forumURL.name, forumURL.pages, forumURL.pagesTotal))

    def getSiteByID(self, id):
        session = self.getSession()
        query = session.query(Site).filter(Site.id == id)
        result = query.one()
        session.close()
        return result

    def clearMappers(self):
        sqlalchemy.orm.clear_mappers()

sc = RateScraper()
print(sc.scrape_rates())
