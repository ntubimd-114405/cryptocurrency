from data_collector.new_scraper.site_yahoo import YahooWebsite,YahooArticle
from data_collector.new_scraper.site_investing import InvestingWebsite,InvestingArticle
from data_collector.new_scraper.site_coindesk import CoindeskWebsite,CoindeskArticle



def website():
    return [YahooWebsite(),InvestingWebsite(),CoindeskWebsite()]


def article(a):
    if "yahoo" in a.url:
        return YahooArticle(a)
    elif "investing" in a.url:
        return InvestingArticle(a)
    elif "coindesk" in a.url:
        return CoindeskArticle(a)
