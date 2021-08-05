import scrapy

class NikeSpiderCalendar(scrapy.Spider):
    name = "nike_calendario"

    def start_requests(self):
        urls = [
            'https://www.nike.com.br/snkrs',            
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        comprar = response.xpath('//div[@id="calendario"]//div[contains(@class,"produto produto--")]')        
        print(len(comprar))
        