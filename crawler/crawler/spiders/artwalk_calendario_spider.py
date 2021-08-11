import scrapy
import requests
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

    def details(self, response):
        images_list = []
        opcoes_list = []
        images = response.xpath('//div[@class="box-banner"]//img/@src').getall()
        for imagem in images:            
            images_list.append(imagem)             
        id_prod = response.xpath('//div[@class="id-prod"]/text()').get()
        if id_prod:
            url = 'https://www.artwalk.com.br/api/catalog_system/pub/products/variations/{}'.format(id_prod)           
            #usei o request porque estava dando erro 500 com o scrapy
            items = requests.get(url=url).json()
            for item in items['skus']:
                if item['available'] == True:
                    if int(item['availablequantity']) == 1:                        
                        opcoes_list.append('1 par tamanho {} por {}'.format(item['dimensions']['Tamanho'], item['bestPriceFormated']))
                    if int(item['availablequantity']) > 1:                        
                        opcoes_list.append('{} pares tamanho {} por {}'.format(item['availablequantity'], item['dimensions']['Tamanho'], item['bestPriceFormated']))                                    

        record = Updater()        
        record['prod_url']=response.url 
        record['imagens']="|".join(images_list) 
        record['tamanhos']="|".join(opcoes_list) 
        yield record     
        
        

    def parse(self, response):                        
        tab = 'artwalker_snkrs' 
        categoria = 'artwalker_snkrs' 
        
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
            name = item.xpath('.//a//img/@alt').get()
            codigo = 'ID{}$'.format(name.replace(' ',''))

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
            record['price']=''
            self.add_name(tab, str(codigo))
            if len( [id for id in rows if str(id) == str(codigo)]) == 0:     
                yield record
        
        
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

        

      
        


        