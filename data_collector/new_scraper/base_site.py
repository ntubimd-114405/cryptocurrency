import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from abc import ABC, abstractmethod


class BaseWebsite(ABC):
    
    def __init__(self):
        self.name = None
        self.url = None
        self.icon_url = None
    
    @abstractmethod
    def fetch_page(self, url):
        """Extract details of a news article."""
        pass
    
class BaseArticle(ABC):
    def __init__(self, url=None, title=None, image_url=None):
        self.url = url
        self.title = title
        self.content = None
        self.image_url = image_url
        self.time = None
        self.website = None

    
    @abstractmethod
    def get_news_details(self, news_url):
        """Extract details of a news article."""
        pass

    

