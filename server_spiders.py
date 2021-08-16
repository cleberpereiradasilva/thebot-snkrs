import time
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.log import configure_logging

from crawler.crawler.spiders.maze_snkrs_spider import MazeSnkrsSpider
from crawler.crawler.spiders.artwalk_calendario_spider import ArtwalkCalendarioSpider
from crawler.crawler.spiders.artwalk_novidades_spider import ArtwalkNovidadesSpider
from crawler.crawler.spiders.artwalk_restock_spider import ArtwalkRestockSpider
from crawler.crawler.spiders.gdlp_novidades_spider import GdlpNovidadesSpider
from crawler.crawler.spiders.gdlp_restock_spider import GdlpRestockSpider
from crawler.crawler.spiders.magicfeet_novidades_spider import MagicfeetNovidadesSpider
from crawler.crawler.spiders.magicfeet_snkrs_spider import MagicfeetSnkrsSpider
from crawler.crawler.spiders.maze_novidades_spider import MazeNovidadesSpider
from crawler.crawler.spiders.maze_restock_spider import MazeRestockSpider
from crawler.crawler.spiders.maze_snkrs_spider import MazeSnkrsSpider
from crawler.data.database import Database
from crawler.crawler import normal_settings as my_settings 
from scrapy.settings import Settings

configure_logging()
crawler_settings = Settings()
configure_logging()
crawler_settings.setmodule(my_settings)
runner = CrawlerRunner(settings=crawler_settings)                 


@defer.inlineCallbacks
def crawl():
    database = Database()
    spiders = [
        ArtwalkCalendarioSpider,        
        ArtwalkNovidadesSpider,
        ArtwalkRestockSpider,            
        GdlpNovidadesSpider,
        GdlpRestockSpider,            
        MazeSnkrsSpider,
        MazeNovidadesSpider,
        MazeRestockSpider,
        MagicfeetNovidadesSpider,
        MagicfeetSnkrsSpider,        
    ]

    for spider in spiders:          
        yield runner.crawl(spider, database)        
    reactor.stop()
crawl()
reactor.run()



