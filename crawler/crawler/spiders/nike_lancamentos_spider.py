import scrapy
import json
from datetime import datetime
from crawler.items import Inserter, Updater, Deleter
from data.database import Database


class NikeNovidadesSpider(scrapy.Spider):
    name = "nike_lancamentos"    
    encontrados = {}
    database = Database()

    def start_requests(self):
        urls = [
            'https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3ACalcados&demanda=true&p=1',
            # 'https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3ACalcados&demanda=true&p=1',

            # 'https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3AAcess%F3rios&demanda=true&p=1',
            # 'https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3AAcess%F3rios&demanda=true&p=1',

            # 'https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3ARoupas&demanda=true&p=1',
            # 'https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3ARoupas&demanda=true&p=1',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def add_name(self, tab, id):
        if tab in  self.encontrados:
            self.encontrados[tab].append(id)
        else:
            self.encontrados[tab] = [id]
            
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
        items = response.xpath('//div[@data-codigo]')  
        finish  = True
        tab = 'Feminino' if 'fem' in response.url else 'Masculino'
        categoria = 'nov-calcados' if 'Calcados' in response.url else 'nov-roupas' if 'Roupas' in response.url else 'nov-acessorios'
        if(len(items) > 0 ):
            finish = True   

        #pega todos os nomes da tabela, apenas os nomes
        results = self.database.search(['id'],{
            'spider':self.name,
            'categoria':categoria,
            'tab': tab
        })        
        rows = [str(row[0]).strip() for row in results]        

        for item in items:                      
            codigo = 'ID{}$'.format(item.xpath('./@data-codigo').get().strip())            
            name = item.xpath('.//a[@class="produto__nome"]/text()').get()
            prod_url = item.xpath('.//a/@href').get()           
            comprar = False if item.xpath('.//a//div[contains(@style,"display:none")]/text()').get() == None else True
            self.add_name(tab, str(codigo))

            if comprar == True:                
                #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar                            
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
                
           

       
        