import scrapy, json
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Deleter
except:
    from crawler.items import Inserter, Deleter

class ArtwalkCalendarioSpider(scrapy.Spider):
    name = "artwalk_calendario"
    encontrados = {}       
    def __init__(self, results):            
        self.encontrados[self.name] = []      
        [self.add_name(self.name, str(r['id']))  for r in results if r['spider'] == self.name]
        self.first_time = len(self.encontrados[self.name])

    def start_requests(self):   
        urls = [
            'https://www.artwalk.com.br/calendario-sneaker',           
        ]
        for url in urls:
            yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)  
               
    def add_name(self, key, id):
        if key in  self.encontrados:
            self.encontrados[key].append(id)
        else:
            self.encontrados[key] = [id]

    def parse(self, response):                        
        tab = 'artwalk_calendario' 
        categoria = 'artwalk_calendario' 
        send = 'avisar' if int(self.first_time) > 0 else 'avisado'

        #pega todos os ites da pagina, apenas os nomes dos tenis
        nodes = [ name for name in response.xpath('//div[@class="box-banner"]') ]      

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in nodes:  
            prod_url = 'https://www.artwalk.com.br{}'.format(item.xpath('.//a/@href').get())            
            id = 'ID{}$'.format(prod_url)  
            deleter = Deleter()                      
            deleter['id']=id
            yield deleter
            record = Inserter()
            record['id']=id 
            record['created_at']=datetime.now().strftime('%Y-%m-%d %H:%M') 
            record['spider']=self.name 
            record['codigo']=''
            record['prod_url']=prod_url 
            record['name']='' 
            record['categoria']=categoria 
            record['tab']=tab 
            record['send']=send    
            record['imagens']=''  
            record['tamanhos']=''    
            record['outros']=''
            record['price']=''                      
            if len( [id_db for id_db in self.encontrados[self.name] if str(id_db) == str(id)]) == 0:     
                self.add_name(self.name, str(id))
                yield scrapy.Request(dont_filter=True, url =prod_url, callback=self.details,  meta=dict(record=record))

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
            quando = 'Lançamento {} às 10H'.format(aguardando)        
            
        record['tamanhos']=json.dumps([{"aguardando": quando}])
        yield record              

        

      
        


        