import scrapy
import sqlite3
import os
from datetime import datetime

print("nike_snkrs")
print(os.path.abspath(os.path.dirname(__file__)))
db_path = '{}data/nike_database.db'.format(os.path.abspath(os.path.dirname(__file__)).split('crawler/crawler')[0])
print(db_path)
database = sqlite3.connect(db_path)
cursor = database.cursor()
try:
    cursor.execute('''CREATE TABLE products
               (date text, url text, name text, tab text, status text, send text)''')
    database.commit()
except:
    pass


class NikeSnkrsSpider(scrapy.Spider):
    name = "nike_snkrs"
    encontrados = {}

    def start_requests(self):       
        urls = [
            'https://www.nike.com.br/Snkrs/Calendario?demanda=true&p=1',
            'https://www.nike.com.br/Snkrs/Feed?demanda=true&p=1',
            'https://www.nike.com.br/Snkrs/Estoque?demanda=true&p=1',            
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)  


    def add_name(self, tab, name):
        if tab in  self.encontrados:
            self.encontrados[tab].append(name)
        else:
            self.encontrados[tab] = [name]


    def parse(self, response):             
        situacoes = ['aviseme', 'comprar', 'esgotado']  
        finish  = True
        tab = response.url.replace('?','/').split('/')[4]       
        for situacao in situacoes:

            #pega todos os ites da pagina, apenas os nomes dos tenis
            items = [ name for name in response.xpath('//div[@class="produto produto--'+situacao+'"]') ]
            if(len(items) > 0 ):
                finish = False

            #pega todos os nomes da tabela, apenas os nomes    
            rows = [str(row[0]).strip() for row in cursor.execute('SELECT url FROM products where tab="'+tab+'" and status="'+situacao+'"')]

            #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
            for content in items:  
                name = content.xpath('.//h2//span/text()').get()
                prod_url = content.xpath('.//a/@href').get()

                self.add_name(tab, prod_url)
                if len( [url for url in rows if url == prod_url]) == 0:
                    print('Inserir ', name)
                    cursor.execute("insert into products values (?, ?, ?, ?, ?, ?)", (datetime.now().strftime('%Y-%m-%d %H:%M'), prod_url, name, tab, situacao, 'avisar'))

            
        database.commit()
        if(finish == False):
            uri = response.url.split('&p=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&p={}'.format(part, str(page))
            yield scrapy.Request(url=url, callback=self.parse)
        else:
            rows = [[str(row[0]).strip(),str(row[1]).strip()] for row in cursor.execute('SELECT url,status FROM products where tab="'+tab+'" and status="'+situacao+'"')]
            

            #checa se algum item do banco nao foi encontrado, nesse caso atualiza com o status de remover            
            for row in rows:                    
                if len( [url for url in self.encontrados[tab] if row[0] == url and row[1] == situacao]) == 0 :
                    print('Remover ', row[0], tab)                   
                    cursor.execute('update products set send="remover" where tab="'+tab+'" and status="'+situacao+'" and url="'+row[0]+'"')
                    database.commit()

        

      
        


        