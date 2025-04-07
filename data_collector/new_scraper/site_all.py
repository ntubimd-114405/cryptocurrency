from data_collector.new_scraper.site_yahoo import YahooWebsite,YahooArticle
from data_collector.new_scraper.site_investing import InvestingWebsite,InvestingArticle
from data_collector.new_scraper.site_coindesk import CoindeskWebsite,CoindeskArticle
from urllib.parse import urlparse


def website():
    return [YahooWebsite(),CoindeskWebsite(),InvestingWebsite()]


def article(a):
    hostname = urlparse(a.url).hostname
    if hostname == "finance.yahoo.com":
        return YahooArticle(a)
    elif hostname == "hk.investing.com":
        return InvestingArticle(a)
    elif hostname == "www.coindesk.com":
        return CoindeskArticle(a)