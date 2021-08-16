import time
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.log import configure_logging

from crawler.crawler.spiders.nike_calendario_spider import NikeCalendarioSpider
from crawler.crawler.spiders.nike_novidades_spider import NikeNovidadesSpider
from crawler.crawler.spiders.nike_restock_spider import NikeRestockSpider
from crawler.data.database import Database
from crawler.crawler import nike_settings as nike_settings 
from scrapy.settings import Settings

configure_logging()
crawler_settings = Settings()
configure_logging()
crawler_settings.setmodule(nike_settings)
runner = CrawlerRunner(settings=crawler_settings)                 


@defer.inlineCallbacks
def crawl():
    database = Database()
    spiders = [
        NikeRestockSpider,         
        NikeNovidadesSpider,                
        NikeCalendarioSpider
    ]

    for spider in spiders:          
        yield runner.crawl(spider, database)        
    reactor.stop()
crawl()
reactor.run()

