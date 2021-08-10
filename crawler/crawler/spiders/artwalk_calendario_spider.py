import scrapy
import sqlite3
import os, json, requests
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


class ArtwalkCalendarioSpider(scrapy.Spider):
    name = "artwalk_calendario"
    encontrados = {}   
    allowed_domains = ['artwalk.com.br']
    def start_requests(self):  
            
        urls = [
            'https://www.artwalk.com.br/calendario-sneaker',           
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)  


    def add_name(self, tab, name):
        if tab in  self.encontrados:
            self.encontrados[tab].append(name)
        else:
            self.encontrados[tab] = [name]   

    def details(self, response):
        images_list = []
        opcoes_list = []
        images = response.xpath('//div[@class="box-banner"]//img/@src').getall()
        for imagem in images:            
            images_list.append(imagem)             
        id_prod = response.xpath('//div[@class="id-prod"]/text()').get()
        if id_prod:
            url = 'https://www.artwalk.com.br/api/catalog_system/pub/products/variations/{}'.format(id_prod)           
            #usei o request porque estava dando erro 500 com o scrapy
            items = requests.get(url=url).json()
            for item in items['skus']:
                if item['available'] == True:
                    if int(item['availablequantity']) == 1:                        
                        opcoes_list.append('1 par tamanho {} por {}'.format(item['dimensions']['Tamanho'], item['bestPriceFormated']))
                    if int(item['availablequantity']) > 1:                        
                        opcoes_list.append('{} pares tamanho {} por {}'.format(item['availablequantity'], item['dimensions']['Tamanho'], item['bestPriceFormated']))                                    

        print("|".join(images_list))
        print("|".join(opcoes_list))      
        
        

    def parse(self, response):                        
        tab = 'calendario' 
        categoria = 'restock' 
        
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//div[@class="box-banner"]') ]
       
        #pega todos os nomes da tabela, apenas os nomes    
        rows = [str(row[0]).strip() for row in cursor.execute('SELECT id FROM products where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'"')]

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in items:  
            prod_url = 'https://www.artwalk.com.br{}'.format(item.xpath('.//a/@href').get())
            name = item.xpath('.//a//img/@alt').get()
            codigo = 'ID{}$'.format(name.replace(' ',''))


            self.add_name(tab, str(codigo))
            if len( [id for id in rows if str(id) == str(codigo)]) == 0:                
                cursor.execute("insert into products values (?, ?, ?, ?, ?, ?, ?, ?)", (datetime.now().strftime('%Y-%m-%d %H:%M'), self.name, codigo, prod_url, name, categoria, tab, 'avisar'))

        
        database.commit()
        #checa se algum item do banco nao foi encontrado, nesse caso atualiza com o status de remover            
        rows = [str(row[0]).strip() for row in cursor.execute('SELECT id FROM products where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'"')]                        
        for row in rows:                    
            if len( [id for id in self.encontrados[tab] if str(id) == str(row)]) == 0 :                                     
                cursor.execute('update products set send="remover" where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'" and id="'+row+'"')
                database.commit()
        rows = [str(row[0]).strip() for row in cursor.execute('SELECT url FROM products where send="avisar" and spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'" group by url')]
        for row in rows:                                
            yield scrapy.Request(url=row, callback=self.details)

        

      
        


        