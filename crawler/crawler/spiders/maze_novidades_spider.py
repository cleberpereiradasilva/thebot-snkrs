import scrapy
import json, time
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Updater, Deleter
    from crawler.data.database import Database
except:
    from crawler.items import Inserter, Updater, Deleter
    from data.database import Database

class MazeNovidadesSpider(scrapy.Spider):
    name = "maze_lancamentos"
    encontrados = {}   
    def __init__(self, database=None, url=None):
        self.url = url
        if database == None:
            self.database = Database()
        else:    
            self.database = database
        self.encontrados[self.name] = []

        results = self.database.search(['id'],{
            'spider':self.name,
        })        
        for h in [str(row[0]).strip() for row in results]:
            self.add_name(self.name, str(h)) 
        
        self.first_time = len(results) 

    def start_requests(self):       
        # urls = [                        
        #     'https://www.maze.com.br/categoria/roupas/camisetas',
        #     'https://www.maze.com.br/categoria/roupas/calcas',
        #     'https://www.maze.com.br/categoria/roupas/saia',
        #     'https://www.maze.com.br/categoria/acessorios/meias',
        #     'https://www.maze.com.br/categoria/acessorios/gorros',
        #     'https://www.maze.com.br/categoria/acessorios/bones',
        # ]
        # for url in urls:
        #     yield scrapy.Request(dont_filter=True, url =url, callback=self.extract_filter)  
        yield scrapy.Request(dont_filter=True, url=self.url, callback=self.extract_filter)
    

    def add_name(self, key, id):
        if key in  self.encontrados:
            self.encontrados[key].append(id)
        else:
            self.encontrados[key] = [id]

    def extract_filter(self, response):
        path = response.url.replace('https://www.maze.com.br','')
        filter = response.xpath('//input[@id="GenericPageFilter"]/@value').get()        
        url='https://www.maze.com.br/product/getproductscategory/?path={}&viewList=g&pageSize=12&order=&brand=&category={}&group=&keyWord=&initialPrice=&finalPrice=&variations=&idAttribute=&idEventList=&idCategories=&idGroupingType=&pageNumber=1'.format(path,filter)        
        yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)

    def parse(self, response): 
        finish  = True                
        tab = response.url.split('=')[1].split('&')[0]        
        categoria = 'maze_lancamentos'
              
        
        send = 'avisar' if int(self.first_time) > 0 else 'avisado'

        #pega todos os ites da pagina, apenas os nomes dos tenis
        nodes = [ name for name in response.xpath('//div[@class="ui card produto product-in-card"]') ]

        if(len(nodes) > 0 ):
            finish=False

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in nodes:           
            name = item.xpath('.//a/@title').get()
            prod_url = 'https://www.maze.com.br{}'.format(item.xpath('.//a/@href').get())
            id = 'ID{}-{}$'.format(item.xpath('.//meta[@itemprop="productID"]/@content').get(), tab)   
            price = item.xpath('.//meta[@itemprop="price"]/@content').get().replace(',','').replace('.',',')  
            deleter = Deleter()                      
            deleter['id']=id
            yield deleter          
            record = Inserter()
            record['id']=id 
            record['created_at']=datetime.now().strftime('%Y-%m-%d %H:%M') 
            record['spider']=self.name 
            record['codigo']='' 
            record['prod_url']=prod_url 
            record['name']=name 
            record['categoria']=categoria 
            record['tab']=tab 
            record['send']=send    
            record['imagens']=''  
            record['tamanhos']=''    
            record['outros']=''
            record['price']='R$ {}'.format(price)
            if len( [id_db for id_db in self.encontrados[self.name] if str(id_db) == str(id)]) == 0:     
                self.add_name(self.name, str(id))                  
                yield scrapy.Request(dont_filter=True, url =prod_url, callback=self.details,  meta=(dict(record=record)))

        if(finish == False):
            uri = response.url.split('&pageNumber=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&pageNumber={}'.format(part, str(page))
            time.sleep(1)
            yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)

    def details(self, response):  
        record = Inserter()
        record = response.meta['record']          
        opcoes_list = []
        images_list = []
        images = response.xpath('//div[contains(@class,"car-gallery")]//img/@src').getall()
        for imagem in images:
            images_list.append('https:{}'.format(imagem))        
        items = response.xpath('//input[@id="principal-lista-sku"]/@value').get()
        options = json.loads(items)                
        for item in options:               
            for variation in item['Variations']:  
                opcoes_list.append({'tamanho': variation['Name'] })                              
        record['codigo']=response.xpath('//h6[@class="codProduto"]/text()').get()
        record['prod_url']=response.url 
        record['imagens']="|".join(images_list) 
        record['tamanhos']=json.dumps(opcoes_list)
        yield record   

      
        


        