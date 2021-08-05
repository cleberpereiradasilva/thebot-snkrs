import scrapy
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from spiders.nike_feed_spider import NikeSpiderFeed
from spiders.nike_calendario_spider import NikeSpiderCalendar


configure_logging()
runner = CrawlerRunner()
runner.crawl(NikeSpiderFeed)
runner.crawl(NikeSpiderCalendar)
d = runner.join()
d.addBoth(lambda _: reactor.stop())

reactor.run()