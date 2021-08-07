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
               (date text, spider text, id text, url text, name text, categoria text, tab text, send text)''')
    database.commit()
except:
    pass


class ArtwakerSnkrsSpider(scrapy.Spider):
    name = "artwalk_snkrs"
    encontrados = {}   

    def start_requests(self):       
        urls = [
            'https://www.artwalk.com.br/nike-air-max?O=OrderByPriceASC&PS=24',
            'https://www.artwalk.com.br/nike-air-force?O=OrderByPriceASC&PS=24',
            'https://www.artwalk.com.br/T%C3%AAnis/Jordan?O=OrderByReleaseDateDESC&&PS=24&map=specificationFilter_16,specificationFilter_15',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.extract_sl)  


    def add_name(self, tab, name):
        if tab in  self.encontrados:
            self.encontrados[tab].append(name)
        else:
            self.encontrados[tab] = [name]

    def extract_sl(self, response):
        scripts = response.xpath('//script/text()').getall()
        for script in scripts:
            if '&sl=' in script:
                url='https://www.artwalk.com.br{}1'.format(script.split('load(\'')[1].split('\'')[0])               
                yield scrapy.Request(url=url, callback=self.parse)  



    def parse(self, response):       
        finish  = True                
        if 'Air+Max' in response.url :
            tab = 'air-max' 
            categoria = 'restock'
        elif 'air-force' in response.url: 
            tab = 'air-force' 
            categoria = 'restock'
        elif 'Jordan' in response.url:
            tab = 'air-jordan' 
            categoria = 'restock'       
        
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//div[@class="product-item-container"]') ]

        if(len(items) > 0 ):
            finish = False

        #pega todos os nomes da tabela, apenas os nomes    
        rows = [str(row[0]).strip() for row in cursor.execute('SELECT id FROM products where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'"')]

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in items:  
            name = item.xpath('.//h3//text()').get()
            prod_url = item.xpath('.//a/@href').get()
            codigo_parts = prod_url.split('-')            
            codigo = 'ID{}$'.format(''.join(codigo_parts[-3:]))

            self.add_name(tab, str(codigo))
            if len( [id for id in rows if str(id) == str(codigo)]) == 0:                
                cursor.execute("insert into products values (?, ?, ?, ?, ?, ?, ?, ?)", (datetime.now().strftime('%Y-%m-%d %H:%M'), self.name, codigo, prod_url, name, categoria, tab, 'avisar'))

        
        database.commit()
        if(finish == False):
            uri = response.url.split('&PageNumber=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&PageNumber={}'.format(part, str(page))
            yield scrapy.Request(url=url, callback=self.parse)
        else:
            #checa se algum item do banco nao foi encontrado, nesse caso atualiza com o status de remover            
            rows = [str(row[0]).strip() for row in cursor.execute('SELECT id FROM products where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'"')]                        
            for row in rows:                    
                if len( [id for id in self.encontrados[tab] if str(id) == str(row)]) == 0 :                                     
                    cursor.execute('update products set send="remover" where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'" and id="'+row+'"')
                    database.commit()

        

      
        


        