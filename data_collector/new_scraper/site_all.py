from data_collector.new_scraper.site_yahoo import YahooWebsite,YahooArticle
from data_collector.new_scraper.site_investing import InvestingWebsite,InvestingArticle
from data_collector.new_scraper.site_coindesk import CoindeskWebsite,CoindeskArticle
from urllib.parse import urlparse


def website():
    return [CoindeskWebsite()]
    return [YahooWebsite(),CoindeskWebsite(),InvestingWebsite()]


def article(a):
    hostname = urlparse(a.url).hostname
    if hostname == "finance.yahoo.com":
        return None
        return YahooArticle(a)
    elif hostname == "hk.investing.com":
        return None
        return InvestingArticle(a)
    elif hostname == "coindesk.com" or hostname == "www.coindesk.com":    
        return CoindeskArticle(a)