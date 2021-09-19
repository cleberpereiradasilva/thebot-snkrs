import scrapy
import json
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Deleter
except:
    from crawler.items import Inserter, Deleter

class MagicfeetNovidadesSpider(scrapy.Spider):
    name = "magicfeet_lancamentos"
    encontrados = {}   
    def __init__(self, results):            
        self.encontrados[self.name] = []      
        [self.add_name(self.name, str(r['id']))  for r in results if r['spider'] == self.name]
        self.first_time = len(self.encontrados[self.name])  

    def start_requests(self):
        urls = [
            'https://www.magicfeet.com.br/lancamentos',              
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
                url='https://www.magicfeet.com.br{}1'.format(sl) 
                yield scrapy.Request(dont_filter=True, url =url, callback=self.parse,  meta=dict(sl=sl))  

    def parse(self, response): 
        finish  = True   
        tab="magicfeet_lancamentos"           
        categoria = 'magicfeet_lancamentos'
        sl = response.meta['sl'].split('sl=')[1].split('&')[0]       
        
        
        send = 'avisar' if int(self.first_time) > 0 else 'avisado'

        #pega todos os ites da pagina, apenas os nomes dos tenis
        nodes = [ name for name in response.xpath('//div[@class="shelf-item"]') ]

        if(len(nodes) > 0 ):
            finish=False
        
        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in nodes:
            in_stock = 'esgotado' not in str(item.xpath('.//div[@class="product-item__no-stock"]//span/text()').get())            
            name = item.xpath('.//h3//a/@title').get()
            prod_url = item.xpath('.//a/@href').get()            
            if in_stock:               
                id = 'ID{}-{}$'.format(item.xpath('./@data-product-id').get(), tab)
                price = item.xpath('.//span[@itemprop="price"]/text()').get()
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
                record['price']=format(price)
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
        for item in items:   
            if 'skuJson_' in item and 'productId' in item and not '@context' in item:                
                tamanhos = '{' + item.split('= {')[1].split('};')[0].strip() + '}'                   
                data = json.loads(tamanhos)                 
                skus = data['skus']                                
                for sku in skus:                     
                    if sku['available'] and len(sku['dimensions'].keys())>0:
                        opcoes_list.append({'tamanho':sku['dimensions'][list(sku['dimensions'].keys())[0]]})                            
        images = response.xpath('//div[@class="product-images"]//li//a/@rel').getall()
        for imagem in images:                        
            images_list.append(imagem) 
       
        record['codigo'] = response.xpath('.//div[contains(@class,"productReference")]/text()').get()        
        productReference = '-'.join(record['codigo'].split('-')[:-1])
            
        record['prod_url']=response.url 
        record['imagens']="|".join(images_list) 
        record['tamanhos']=json.dumps(opcoes_list)       
        url = 'https://www.magicfeet.com.br/buscapagina?PS=999&sl={}&cc=999&sm=0&fq=spec_fct_15:{}'.format(sl,productReference)
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


      
        



        