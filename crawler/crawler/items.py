# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class Inserter(scrapy.Item):    
    id = scrapy.Field()
    created_at = scrapy.Field()
    spider = scrapy.Field()
    codigo = scrapy.Field()
    prod_url = scrapy.Field()
    name = scrapy.Field()
    categoria = scrapy.Field()
    tab = scrapy.Field()
    send = scrapy.Field()
    imagens = scrapy.Field()
    tamanhos = scrapy.Field()
    outros = scrapy.Field()
    price = scrapy.Field()

class Updater(scrapy.Item):
    prod_url = scrapy.Field()
    imagens = scrapy.Field()
    tamanhos = scrapy.Field()

class Deleter(scrapy.Item):
    id = scrapy.Field()

