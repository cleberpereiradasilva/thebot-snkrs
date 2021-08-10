import scrapy
import json
from datetime import datetime
from crawler.items import Inserter, Updater, Deleter
from data.database import Database
class NikeSnkrsSpider(scrapy.Spider):
    name = "nike_restock"
    encontrados = {}   
    database = Database()

    def start_requests(self):       
        urls = [            
            'https://www.nike.com.br/Snkrs/Estoque?demanda=true&p=1',            
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)  


    def add_name(self, tab, name):
        if tab in  self.encontrados:
            self.encontrados[tab].append(name)
        else:
            self.encontrados[tab] = [name]

    def details(self, response):
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
                    opcoes_list.append('{} tamanho {} por {}'.format(data[k]['TemEstoque'],k, data[k]['PrecoPor']))

        record = Updater()        
        record['prod_url']=response.url 
        record['imagens']="|".join(images_list) 
        record['tamanhos']="|".join(opcoes_list) 
        yield record
        

    def parse(self, response):       
        finish  = True
        tab = response.url.replace('?','/').split('/')[4]  
        categoria = 'restock' if tab == 'Estoque' else 'nov-calcados'
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//div[contains(@class,"produto produto--")]') ]
        if(len(items) > 0 ):
            finish = True

        #pega todos os nomes da tabela, apenas os nomes    
        results = self.database.search(['id'],{
            'spider':self.name,
            'categoria':categoria,
            'tab': tab
        })        
        rows = [str(row[0]).strip() for row in results]

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in items:  
            name = item.xpath('.//h2//span/text()').get()           
            prod_url = item.xpath('.//a/@href').get()
            codigo = 'ID{}$'.format(item.xpath('.//a/img/@alt').get().split(".")[-1].strip())
            

            record = Inserter()
            record['created_at']=datetime.now().strftime('%Y-%m-%d %H:%M') 
            record['spider']=self.name 
            record['codigo']=codigo 
            record['prod_url']=prod_url 
            record['name']=name 
            record['categoria']=categoria 
            record['tab']=tab 
            record['send']='avisar'           
            self.add_name(tab, str(codigo))
            if len( [id for id in rows if str(id) == str(codigo)]) == 0:     
                yield record  

        
        if(finish == False):
            uri = response.url.split('&p=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&p={}'.format(part, str(page))
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
            
            

        

      
        


        