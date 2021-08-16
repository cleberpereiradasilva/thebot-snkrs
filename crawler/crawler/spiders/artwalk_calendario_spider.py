import scrapy, json
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Updater, Deleter
    from crawler.data.database import Database
except:
    from crawler.items import Inserter, Updater, Deleter
    from data.database import Database

class ArtwalkCalendarioSpider(scrapy.Spider):
    name = "artwalk_calendario"
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
            'https://www.artwalk.com.br/calendario-sneaker',           
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
        tab = 'artwalk_snkrs' 
        categoria = 'artwalk_snkrs' 
        
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//div[@class="box-banner"]') ]      

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in items:  
            prod_url = 'https://www.artwalk.com.br{}'.format(item.xpath('.//a/@href').get())            
            id = 'ID{}$'.format(prod_url)                        
            record = Inserter()
            record['id']=id 
            record['created_at']=datetime.now().strftime('%Y-%m-%d %H:%M') 
            record['spider']=self.name 
            record['codigo']=''
            record['prod_url']=prod_url 
            record['name']='' 
            record['categoria']=categoria 
            record['tab']=tab 
            record['send']='avisar'    
            record['imagens']=''  
            record['tamanhos']=''    
            record['outros']=''
            record['price']=''                      
            if len( [id_db for id_db in self.encontrados[self.name] if str(id_db) == str(id)]) == 0:     
                self.add_name(self.name, str(id))
                yield scrapy.Request(url=prod_url, callback=self.details, meta=dict(record=record))

    def details(self, response):        
        record = Inserter()
        record = response.meta['record'] 
        images_list = []        
        images = response.xpath('//div[@class="box-banner"]//img/@src').getall()
        aguardando = response.xpath('//div[@class="data-lanc"]/text()').get()        
        record['name'] = response.xpath('//h1[@class="name-produto"]/text()').get()
        for imagem in images:            
            images_list.append(imagem) 
        record['imagens']="|".join(images_list)    
        quando = 'Aguarde...'.ljust(18, '\u200B')
        if aguardando:
            quando = 'Lançamento 10/10/2010 às 10H'.format(aguardando)        
            
        record['tamanhos']=json.dumps([{"aguardando": quando}])
        yield record              

        

      
        


        