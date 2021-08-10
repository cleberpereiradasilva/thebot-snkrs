import scrapy
import json
from datetime import datetime
from crawler.items import Inserter, Updater, Deleter
from data.database import Database


class GdlpSnkrsSpider(scrapy.Spider):
    name = "gdlp_snkrs"
    encontrados = {}   
    database = Database()

    def start_requests(self):       
        urls = [            
            'https://gdlp.com.br/calcados/adidas',
            'https://gdlp.com.br/calcados/nike',
            'https://gdlp.com.br/calcados/air-jordan',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)  


    def add_name(self, tab, name):
        if tab in  self.encontrados:
            self.encontrados[tab].append(name)
        else:
            self.encontrados[tab] = [name]

    def details(self, response):
        print(response.url)
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
                            opcoes_list.append(('{} {} por {}'.format(options[k]['label'], option['label'], option['price'] if option['price'] != '0' else price)))

        record = Updater()        
        record['prod_url']=response.url 
        record['imagens']="|".join(images_list) 
        record['tamanhos']="|".join(opcoes_list) 
        yield record

    def parse(self, response):       
        finish  = True
        tab = response.url.replace('?','/').split('/')[4]  
        categoria = 'restock' 
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//li[@class="item last"]') ]
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
            name = item.xpath('.//h2//a/text()').get()
            prod_url = item.xpath('.//a/@href').get()
            codigo = 'ID{}$'.format(prod_url.split('/')[-1])

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
            paginacao = response.xpath('//div[@class="pages"]//li')
            if len(paginacao) > 0:
                url = response.xpath('//div[@class="pages"]//a[@class="next i-next"]/@href').get()
                if url:                
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

        

      
        


        