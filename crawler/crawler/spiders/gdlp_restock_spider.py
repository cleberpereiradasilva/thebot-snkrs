import scrapy
import json
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Updater, Deleter
    from crawler.data.database import Database
except:
    from crawler.items import Inserter, Updater, Deleter
    from data.database import Database


class GdlpRestockSpider(scrapy.Spider):
    name = "gdlp_restock"
    encontrados = {}   
    def __init__(self, database=None):
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

    def start_requests(self): 
        urls = [            
            'https://gdlp.com.br/calcados/adidas',
            'https://gdlp.com.br/calcados/nike',
            'https://gdlp.com.br/calcados/air-jordan',
            'https://gdlp.com.br/calcados/new-balance'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)  
        self.remove()
       
    def add_name(self, key, id):
        if key in  self.encontrados:
            self.encontrados[key].append(id)
        else:
            self.encontrados[key] = [id]

    def remove(self):
        #checa se algum item do banco nao foi encontrado, nesse caso atualiza com o status de remover            
        results = self.database.search(['id'],{
            'spider':self.name                        
        })        
        rows = [str(row[0]).strip() for row in results]            
        for row in rows:                    
            if len( [id for id in self.encontrados[self.name] if str(id) == str(row)]) == 0 :                  
                record = Deleter()
                record['id']=row                     
                yield record  

    def parse(self, response):     
        finish  = True
        tab = response.url.replace('?','/').split('/')[4]  
        categoria = 'gdlp_restock' 
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//li[@class="item last"]') ]
        if(len(items) > 0 ):
            finish = False
      
        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in items: 
            name = item.xpath('.//h2//a/text()').get()
            prod_url = item.xpath('.//a/@href').get()
            id_price = item.xpath('.//span[@class="regular-price"]/@id').get()           
            id = 'ID{}-{}$'.format(id_price.split('-')[-1].split('_')[0], tab)
            price = item.xpath('.//span[@class="price"]/text()').get()
            record = Inserter()
            record['id']=id 
            record['created_at']=datetime.now().strftime('%Y-%m-%d %H:%M') 
            record['spider']=self.name 
            record['codigo']=id_price.split('-')[-1].split('_')[0] 
            record['prod_url']=prod_url 
            record['name']=name 
            record['categoria']=categoria 
            record['tab']=tab 
            record['send']='avisar'      
            record['imagens']=''  
            record['tamanhos']=''    
            record['price']=price          
            record['outros']=''      
            if len( [id_db for id_db in self.encontrados[self.name] if str(id_db) == str(id)]) == 0:     
                self.add_name(self.name, str(id))
                yield scrapy.Request(url=prod_url, callback=self.details, meta=(dict(record=record)))
        
        if(finish == False):
            paginacao = response.xpath('//div[@class="pages"]//li')
            if len(paginacao) > 0:
                url = response.xpath('//div[@class="pages"]//a[@class="next i-next"]/@href').get()
                if url:                
                    yield scrapy.Request(url=url, callback=self.parse)

    def details(self, response):   
        record = Inserter()
        record = response.meta['record']       
        opcoes_list = []
        images_list = []
        images = response.xpath('//div[@class="product-img-box"]//a/@data-image').getall()
        for imagem in images:
            images_list.append(imagem)        
        items = response.xpath('//script/text()').getall()  
        price = response.xpath('//span[@class="price"]/text()').get()        
        for item in items:   
            if('new Product.Config(' in item):                
                tamanhos = item.split('(')[1].split(');')[0].strip()                                
                options = json.loads(tamanhos)['attributes']                
                for k in options.keys():
                    for option in options[k]['options']:
                        if len(option['products']) > 0:
                            opcoes_list.append({'tamanho' : option['label']})
        record['price']=price
        record['prod_url']=response.url 
        record['imagens']="|".join(images_list) 
        record['tamanhos']=json.dumps(opcoes_list)
        yield record    

      
        


        