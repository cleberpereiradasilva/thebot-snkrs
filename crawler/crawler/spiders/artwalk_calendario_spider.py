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


    def parse(self, response):                        
        tab = 'artwalk_snkrs' 
        categoria = 'artwalk_snkrs' 
        
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//div[@class="box-banner"]') ]
       
        #pega todos os nomes da tabela, apenas os nomes    
        results = self.database.search(['id'],{
            'spider':self.name,
            'categoria':categoria,
            'tab': tab
        })        
        rows = [str(row[0]).strip() for row in results]

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in items:  
            prod_url = 'https://www.artwalk.com.br{}'.format(item.xpath('.//a/@href').get())            
            codigo = 'ID{}$'.format(prod_url)                        
            record = Inserter()
            record['id']=codigo 
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
            self.add_name(tab, str(codigo))            
            if len( [id for id in rows if str(id) == str(codigo)]) == 0:     
                yield scrapy.Request(url=prod_url, callback=self.details, meta=dict(record=record))
        
        
        #checa se algum item do banco nao foi encontrado, nesse caso atualiza com o status de remover            
        results = self.database.search(['id'],{
                'spider':self.name,
                'categoria':categoria,
                'tab': tab
        })   
        rows = [str(row[0]).strip() for row in results]
        for row in rows:                    
            if len( [id_enc for id_enc in self.encontrados[tab] if str(id_enc) == str(row)]) == 0 :                                                         
                record = Deleter()
                record['id']=row                     
                yield record

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

        

      
        


        