import scrapy

class NikeSpiderFeed(scrapy.Spider):
    name = "nike_feed"

    def start_requests(self):
        urls = [
            'https://www.nike.com.br/snkrs',            
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        comprar = response.xpath('//div[@id="DadosPaginacaoFeed"]//div[contains(@class,"produto produto--")]')        
        print(len(comprar))
        