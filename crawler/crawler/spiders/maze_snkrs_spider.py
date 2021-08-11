import scrapy
import json
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Updater, Deleter
    from crawler.data.database import Database
except:
    from crawler.items import Inserter, Updater, Deleter
    from data.database import Database
class MazeSnkrsSpider(scrapy.Spider):
    name = "maze_snkrs"
    encontrados = {}   
    def __init__(self, database=None):
        if database == None:
            self.database = Database()
        else:    
            self.database = database

    def start_requests(self):       
        urls = [            
            'https://www.maze.com.br/categoria/tenis/nike',
            'https://www.maze.com.br/categoria/tenis/adidas',           
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.extract_filter)  


    def add_name(self, tab, name):
        if tab in  self.encontrados:
            self.encontrados[tab].append(name)
        else:
            self.encontrados[tab] = [name]

    def extract_filter(self, response):
        path = response.url.replace('https://www.maze.com.br','')
        filter = response.xpath('//input[@id="GenericPageFilter"]/@value').get()        
        url='https://www.maze.com.br/product/getproductscategory/?path={}&viewList=g&pageSize=12&order=&brand=&category={}&group=&keyWord=&initialPrice=&finalPrice=&variations=&idAttribute=&idEventList=&idCategories=&idGroupingType=&pageNumber=1'.format(path,filter)        
        yield scrapy.Request(url=url, callback=self.parse)
        
    def details(self, response):        
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

        record = Updater()        
        record['prod_url']=response.url 
        record['imagens']="|".join(images_list) 
        record['tamanhos']="|".join(opcoes_list) 
        yield record

    def parse(self, response):       
        finish  = True                
        tab = response.url.split('=')[1].split('&')[0]        
        categoria = 'maze_snkrs'
              
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//div[@class="ui card produto product-in-card"]') ]

        if(len(items) > 0 ):
            finish = False

        #pega todos os nomes da tabela, apenas os nomes    
        results = self.database.search(['id'],{
            'spider':self.name,
            'categoria':categoria,
            'tab': tab
        })        
        rows = [str(row[0]).strip() for row in results]

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in items:            
            name = item.xpath('.//a/@title').get()
            prod_url = 'https://www.maze.com.br{}'.format(item.xpath('.//a/@href').get())
            codigo = 'ID{}$'.format(item.xpath('.//meta[@itemprop="productID"]/@content').get())   
            price = item.xpath('.//meta[@itemprop="price"]/@content').get()           
            record = Inserter()
            record['created_at']=datetime.now().strftime('%Y-%m-%d %H:%M') 
            record['spider']=self.name 
            record['codigo']=codigo 
            record['prod_url']=prod_url 
            record['name']=name 
            record['categoria']=categoria 
            record['tab']=tab 
            record['send']='avisar'    
            record['imagens']=''  
            record['tamanhos']=''         
            record['price']='R$ {}'.format(price)
            self.add_name(tab, str(codigo))
            if len( [id for id in rows if str(id) == str(codigo)]) == 0:     
                yield record

        if(finish == False):
            uri = response.url.split('&pageNumber=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&pageNumber={}'.format(part, str(page))
            yield scrapy.Request(url=url, callback=self.parse)
        else:
            #checa se algum item do banco nao foi encontrado, nesse caso atualiza com o status de remover            
            results = self.database.search(['id'],{
                'spider':self.name,
                'categoria':categoria,
                'tab': tab
            })        
            rows = [str(row[0]).strip() for row in results]            
            for row in rows:                    
                if len( [id for id in self.encontrados[tab] if str(id) == str(row)]) == 0 :                                                         
                    record = Deleter()
                    record['id']=row                     
                    yield record
            
            results = self.database.search(['url'],{
                'spider':self.name,
                'categoria':categoria,
                'tab': tab,
                'send':'avisar'
            })        
            rows = [str(row[0]).strip() for row in results]      
            for row in rows:                                
                yield scrapy.Request(url=row, callback=self.details)

        

      
        


        