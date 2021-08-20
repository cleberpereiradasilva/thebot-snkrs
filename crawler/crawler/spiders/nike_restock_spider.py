import scrapy
import json
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Updater, Deleter
    from crawler.data.database import Database
except:
    from crawler.items import Inserter, Updater, Deleter
    from data.database import Database
class NikeRestockSpider(scrapy.Spider):
    name = "nike_restock"
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
            'https://www.nike.com.br/Snkrs/Estoque?demanda=true&p=1',            
        ]       

        for url in urls:
            yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)  
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
        categoria = 'nike_restock' if tab == 'Estoque' else 'nov-calcados'
        #pega todos os ites da pagina, apenas os nomes dos tenis
        nodes = [ name for name in response.xpath('//div[contains(@class,"produto produto--")]') ]
        if(len(nodes) > 0 ):
            finish=True       

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in nodes[0:10]: 
            name = item.xpath('.//h2//span/text()').get()           
            prod_url = item.xpath('.//a/@href').get()
            id = 'ID{}-{}-{}$'.format(item.xpath('.//a/img/@alt').get().split(".")[-1].strip(), categoria, tab)
            record = Inserter()
            record['id']=id
            record['created_at']=datetime.now().strftime('%Y-%m-%d %H:%M') 
            record['spider']=self.name 
            record['codigo']='' 
            record['prod_url']=prod_url 
            record['name']=name 
            record['categoria']=categoria 
            record['tab']=tab 
            record['send']='avisar'
            record['imagens']=''  
            record['tamanhos']=''    
            record['outros']=''
            record['price']=''             
            if len( [id_db for id_db in self.encontrados[self.name] if str(id_db) == str(id)]) == 0:     
                self.add_name(self.name, str(id))  
                yield scrapy.Request(dont_filter=True, url =prod_url, callback=self.details,  meta=dict(record=record))
        
        if(finish == False):
            uri = response.url.split('&p=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&p={}'.format(part, str(page))
            yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)
            
    def details(self, response):
        record = Inserter()
        record = response.meta['record']       
        opcoes_list = []
        images_list = []
        images = response.xpath('//ul[@class="js-thumb-list"]//img/@src').getall()

        for imagem in images:
            images_list.append(imagem)        
        items = response.xpath('//script/text()').getall()        
        for item in items:   
            if('SKUsCorTamanho' in item):                
                tamanhos = item.split('=')[1].strip()
                data = json.loads(tamanhos) 
                for k in data.keys():
                    url = '{}-{}'.format('-'.join(response.url.split('-')[0:-1]), data[k]['ProdutoId'])
                    opcoes_list.append({'tamanho': k, 'url': {'label': data[k]['ProdutoId'], 'href' : url }})
        
        record['codigo'] ='-'.join(images_list[0].split('-')[-4:-2])
        record['prod_url']=response.url 
        record['imagens']="|".join(images_list[0:3])
        record['tamanhos']=json.dumps(opcoes_list)
        yield record         

        

      
        


        