import scrapy
import sqlite3
import os, json
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


class MazeSnkrsSpider(scrapy.Spider):
    name = "maze_snkrs"
    encontrados = {}   

    def start_requests(self):       
        urls = [            
            'https://www.maze.com.br/',            
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.extract_links)  


    def add_name(self, tab, name):
        if tab in  self.encontrados:
            self.encontrados[tab].append(name)
        else:
            self.encontrados[tab] = [name]

    def extract_links(self, response):
        for categoria in ['nike', 'adidas']:
            hrefs = response.xpath('//a[@href="/categoria/{}"]/parent::*//div[contains(@class,"ui list")]//a/@href'.format(categoria)).getall()        
            for href in hrefs:                                 
                url = 'https://www.maze.com.br{}'.format(href)
                yield scrapy.Request(url=url, callback=self.extract_filter)

    def details(self, response):
        print(response.url)
        opcoes_list = []
        images_list = []
        images = response.xpath('//div[contains(@class,"car-gallery")]//img/@src').getall()
        for imagem in images:
            images_list.append('https:{}'.format(imagem))        
        items = response.xpath('//input[@id="principal-lista-sku"]/@value').get()
        options = json.loads(items)                
        for item in options:               
            for variation in item['Variations']:                                
                opcoes_list.append(('Tamanho {} por R$ {:.2f}'.format(variation['Name'], item['Price'])))
            
        print("|".join(images_list))
        print("|".join(opcoes_list))    

    def extract_filter(self, response):
        path = response.url.replace('https://www.maze.com.br','')
        filter = response.xpath('//input[@id="GenericPageFilter"]/@value').get()        
        url='https://www.maze.com.br/product/getproductscategory/?path={}&viewList=g&pageSize=12&order=&brand=&category={}&group=&keyWord=&initialPrice=&finalPrice=&variations=&idAttribute=&idEventList=&idCategories=&idGroupingType=&pageNumber=1'.format(path,filter)
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):       
        finish  = True                
        tab = response.url.split('=')[1].split('&')[0]
        categoria = 'maze_snkrs' 
        
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//div[@class="ui card produto product-in-card"]') ]

        if(len(items) > 0 ):
            finish = True

        #pega todos os nomes da tabela, apenas os nomes    
        rows = [str(row[0]).strip() for row in cursor.execute('SELECT id FROM products where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'"')]

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in items:  
            name = item.xpath('.//a/@title').get()
            prod_url = 'https://www.maze.com.br{}'.format(item.xpath('.//a/@href').get())
            codigo = 'ID{}$'.format(item.xpath('.//meta[@itemprop="productID"]/@content').get())           

            self.add_name(tab, str(codigo))
            if len( [id for id in rows if str(id) == str(codigo)]) == 0:                
                cursor.execute("insert into products values (?, ?, ?, ?, ?, ?, ?, ?)", (datetime.now().strftime('%Y-%m-%d %H:%M'), self.name, codigo, prod_url, name, categoria, tab, 'avisar'))

        
        database.commit()
        if(finish == False):
            uri = response.url.split('&pageNumber=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&pageNumber={}'.format(part, str(page))
            yield scrapy.Request(url=url, callback=self.parse)
        else:
            #checa se algum item do banco nao foi encontrado, nesse caso atualiza com o status de remover            
            rows = [str(row[0]).strip() for row in cursor.execute('SELECT id FROM products where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'"')]                        
            for row in rows:                    
                if len( [id for id in self.encontrados[tab] if str(id) == str(row)]) == 0 :                                     
                    cursor.execute('update products set send="remover" where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'" and id="'+row+'"')
                    database.commit()
            rows = [str(row[0]).strip() for row in cursor.execute('SELECT url FROM products where send="avisar" and spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'" group by url')]
            for row in rows:                                
                yield scrapy.Request(url=row, callback=self.details)
        

      
        


        