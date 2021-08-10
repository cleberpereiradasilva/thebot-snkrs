import scrapy
import json
from datetime import datetime
from crawler.items import Inserter, Updater, Deleter
from data.database import Database

class ArtwalkNovidadesSpider(scrapy.Spider):
    name = "artwalk_novidades"
    encontrados = {}   
    database = Database()

    def start_requests(self):       
        urls = [            
            'https://www.artwalk.com.br/novidades?PS=24&O=OrderByReleaseDateDESC',            
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.extract_sl)  


    def add_name(self, tab, name):
        if tab in  self.encontrados:
            self.encontrados[tab].append(name)
        else:
            self.encontrados[tab] = [name]

    def extract_sl(self, response):
        scripts = response.xpath('//script/text()').getall()
        for script in scripts:
            if '&sl=' in script:
                url='https://www.artwalk.com.br{}1'.format(script.split('load(\'')[1].split('\'')[0])               
                yield scrapy.Request(url=url, callback=self.parse)  

    def details(self, response):
        images_list = []
        opcoes_list = []
        items = response.xpath('//script/text()').getall() 
        for item in items:   
            if 'skuJson_' in item and 'productId' in item and not '@context' in item:                
                tamanhos = '{' + item.split('= {')[1].split('};')[0].strip() + '}'   
                data = json.loads(tamanhos)                 
                skus = data['skus']                
                for sku in skus:                     
                    if int(sku['availablequantity']) == 1:                        
                        opcoes_list.append('1 par tamanho {} por {}'.format(sku['dimensions']['Tamanho'], sku['availablequantity']))
                    if int(sku['availablequantity']) > 1:                        
                        opcoes_list.append('{} pares tamanho {} por {}'.format(sku['availablequantity'],sku['dimensions']['Tamanho'], sku['bestPriceFormated']))                

        images = response.xpath('////a[@id="botaoZoom"]/@rel').getall()
        for imagem in images:                        
            images_list.append(imagem)             
       
        record = Updater()        
        record['prod_url']=response.url 
        record['imagens']="|".join(images_list) 
        record['tamanhos']="|".join(opcoes_list) 
        yield record
       

    def parse(self, response):       
        finish  = True                
        tab = 'novidades' 
        categoria = 'novidades' 
        
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//div[@class="product-item-container"]') ]

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
            name = item.xpath('.//h3//text()').get()
            prod_url = item.xpath('.//a/@href').get()
            codigo_parts = prod_url.split('-')            
            codigo = 'ID{}$'.format(''.join(codigo_parts[-3:]))

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
            uri = response.url.split('&PageNumber=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&PageNumber={}'.format(part, str(page))
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

        

      
        


        