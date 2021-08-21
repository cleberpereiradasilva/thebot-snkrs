import scrapy
import json, time
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Updater, Deleter
    from crawler.data.database import Database
except:
    from crawler.items import Inserter, Updater, Deleter
    from data.database import Database

class ArtwalkRestockSpider(scrapy.Spider):
    name = "artwalk_restock"
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
            'https://www.artwalk.com.br/nike-air-max?O=OrderByPriceASC&PS=24',
            'https://www.artwalk.com.br/nike-air-force?O=OrderByPriceASC&PS=24',
            'https://www.artwalk.com.br/T%C3%AAnis/Jordan?O=OrderByReleaseDateDESC&&PS=24&map=specificationFilter_16,specificationFilter_15',
        ]
        for url in urls:
            yield scrapy.Request(dont_filter=True, url =url, callback=self.extract_sl)  
        
       
    def add_name(self, key, id):
        if key in  self.encontrados:
            self.encontrados[key].append(id)
        else:
            self.encontrados[key] = [id]

    def extract_sl(self, response):
        scripts = response.xpath('//script/text()').getall()
        for script in scripts:
            if '&sl=' in script:
                sl=script.split('load(\'')[1].split('\'')[0]               
                url='https://www.artwalk.com.br{}1'.format(script.split('load(\'')[1].split('\'')[0])               
                yield scrapy.Request(dont_filter=True, url =url, callback=self.parse, meta=dict(sl=sl))    

    def parse(self, response):    
        finish  = True                        
        tab=""
        if 'Air+Max' in response.url :
            tab = 'air-max'          
        elif 'air-force' in response.url: 
            tab = 'air-force'          
        elif 'Jordan' in response.url:
            tab = 'air-jordan'        

        categoria="artwalk_restock"       
        sl = response.meta['sl'].split('sl=')[1].split('&')[0]
        
        #pega todos os ites da pagina, apenas os nomes dos tenis
        nodes = [ name for name in response.xpath('//div[@class="product-item-container"]') ]

        if(len(nodes) > 0 ):
            finish=True

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in nodes:
            name = item.xpath('.//h3//text()').get()
            prod_url = item.xpath('.//a/@href').get()
            price = item.xpath('.//span[@class="product-item__price"]/text()').get()    
            disponivel = item.xpath('.//span[@class="product-item__installments"]/text()').get()              
            if disponivel: 
                if not "Produto indis" in disponivel:                
                    codigo_parts = prod_url.split('-')            
                    id = 'ID{}-{}$'.format(''.join(codigo_parts[-3:]), tab)
                    record = Inserter()
                    record['id']=id
                    record['codigo']=''
                    record['created_at']=datetime.now().strftime('%Y-%m-%d %H:%M') 
                    record['spider']=self.name              
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
                        yield scrapy.Request(dont_filter=True, url =prod_url, callback=self.details,  meta=dict(record=record, sl=sl))
        
        if(finish == False):
            uri = response.url.split('&PageNumber=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&PageNumber={}'.format(part, str(page))
            yield scrapy.Request(dont_filter=True, url =url, callback=self.parse, meta=dict(sl=response.meta['sl']))             
      
    def details(self, response):
        record = Inserter()
        record = response.meta['record']        
        sl = response.meta['sl']      
        images_list = []
        opcoes_list = []
        items = response.xpath('//script/text()').getall() 
        record['codigo'] = response.xpath('.//div[contains(@class,"productReference")]/text()').get()
        productReference = '-'.join(record['codigo'].split('-')[:-1])
        for item in items:   
            if 'skuJson_' in item and 'productId' in item and '"Tamanho"' in item and not '@context' in item:                 
                tamanhos = '{' + item.split('= {')[1].split('};')[0].strip() + '}'   
                data = json.loads(tamanhos)                 
                skus = data['skus']                
                for sku in skus:                                                             
                    try:     
                        if sku['available'] == True:
                            opcoes_list.append({'tamanho': sku['dimensions']['Tamanho'] })
                    except: 
                        pass                

        images = response.xpath('//a[@id="botaoZoom"]/@rel').getall()
        for imagem in images:                        
            images_list.append(imagem)
        
        record['imagens']="|".join(images_list) 
        record['tamanhos']=json.dumps(opcoes_list)
        url = 'https://www.artwalk.com.br/buscapagina?PS=999&sl={}&cc=999&sm=0&fq=spec_fct_11:{}'.format(sl,productReference)
        yield scrapy.Request(dont_filter=True, url =url, callback=self.other_links,  meta=dict(record=record))
    
   
    def other_links(self, response):
        others = set()
        record = Inserter()
        record = response.meta['record']                
        for item in response.xpath('//a/@href').getall():
            if item != record['prod_url']:
                others.add(item)
        record['outros']='|'.join([o for o in others])
        yield record

        

      
        


        