import scrapy
import sqlite3
import os

print(os.path.abspath(os.path.dirname(__file__)))
db_path = '{}crawler/data/nike_database.db'.format(os.path.abspath(os.path.dirname(__file__)).split('crawler/crawler')[0])
print(db_path)
database = sqlite3.connect(db_path)
cursor = database.cursor()
try:
    cursor.execute('''CREATE TABLE products
               (date text, name text, status text, send text)''')
    database.commit()
except:
    pass




class NikeSpiderFeed(scrapy.Spider):
    name = "nike_feed"

    def start_requests(self):
        urls = [
            'https://www.nike.com.br/snkrs',            
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)  


    def parse(self, response):
        group = response.xpath('//div[@id="DadosPaginacaoFeed"]')
        aviseme = [ '{}'.format(name.strip()) for name in group.xpath('.//div[@class="produto produto--aviseme"]//h2/text()').getall() ]
        comprar = [ name.strip() for name in group.xpath('.//div[@class="produto produto--comprar"]//h2/text()').getall() ]
        esgotado = [ name.strip() for name in group.xpath('.//div[@class="produto produto--esgotado"]//h2/text()').getall() ]


        rows = [str(row[0]).strip() for row in cursor.execute('SELECT name FROM products where status="aviseme"')]
                   
        for name in aviseme:            
            if len( [row for row in rows if row == name]) == 0 :
                cursor.execute("insert into products values (?, ?, ?, ?)", ('10-10-2021', name, 'aviseme', 'avisar'))
        
        for row in rows:
            if len( [product for product in aviseme if product == row]) == 0 :                               
                cursor.execute("update products set send='remover' where name='"+row+"'")
                
           

        #print(aviseme)
        # print(comprar)
        # print(esgotado)
        database.commit()


        # print("================================================================")
        # print("================================================================")
        # print(len(aviseme))
        # print(len(comprar))
        # print(len(esgotado))
        # print("================================================================")
        