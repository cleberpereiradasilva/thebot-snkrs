import scrapy,random
import json, time
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Deleter
    from crawler.data.database import Database
except:
    from crawler.items import Inserter, Deleter
    from data.database import Database
class NikeNovidadesSpider(scrapy.Spider):    
    name = "nike_lancamentos"    
    encontrados = {}    
    def __init__(self, results, url=None, proxy_list=None):  
        self.url = url
        self.proxy_pool = proxy_list          
        self.encontrados[self.name] = []      
        [self.add_name(self.name, str(r['id']))  for r in results if r['spider'] == self.name]
        self.first_time = len(self.encontrados[self.name])   

    def make_request(self, url, cb, meta=None, handle_failure=None):
        request = scrapy.Request(dont_filter=True, url =url, callback=cb, meta=meta, errback=handle_failure)
        if self.proxy_pool:
            request.meta['proxy'] = random.choice(self.proxy_pool)              
            self.log('Using proxy {}'.format(request.meta['proxy']))
            self.log('----------------')
        return request 

    def detail_failure(self, failure):        
        record = Inserter()
        record = failure.request.meta['record']
        # try with a new proxy
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        request = self.make_request(failure.request.url, self.details, dict(record=record), self.detail_failure)
        yield request 

    def page_failure(self, failure):        
        # try with a new proxy
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))

        request = self.make_request(failure.request.url, self.parse, None, self.page_failure)
        yield request

    def start_requests(self):
        # urls = [
        #     'https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3ACalcados&demanda=true&p=1',
        #     'https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3ACalcados&demanda=true&p=1',

        #     'https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3AAcess%F3rios&demanda=true&p=1',
        #     'https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3AAcess%F3rios&demanda=true&p=1',

        #     'https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3ARoupas&demanda=true&p=1',
        #     'https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3ARoupas&demanda=true&p=1',
        # ]
        # for url in urls:
        #     yield scrapy.Request(dont_filter=True, url=url, callback=self.parse)
        request = self.make_request(self.url, self.parse, None, self.page_failure)            
        yield request 
        #yield scrapy.Request(dont_filter=True, url=self.url, callback=self.parse)
       
    def add_name(self, key, id):
        if key in  self.encontrados:
            self.encontrados[key].append(id)
        else:
            self.encontrados[key] = [id]

    def parse(self, response):
        nodes = response.xpath('//div[@data-codigo]')  
        finish  = True
        tab = 'Feminino' if 'fem' in response.url else 'Masculino'
        categoria = 'nike_lancamentos_snkrs' if 'Calcados' in response.url else 'nike_lancamentos'
        send = 'avisar' if int(self.first_time) > 0 else 'avisado'

        if(len(nodes) > 0 ):
            finish=False

        for item in nodes:
            id = 'ID{}-{}-{}$'.format(item.xpath('./@data-codigo').get().strip(), categoria,tab)            
            name = item.xpath('.//a[@class="produto__nome"]/text()').get()
            prod_url = item.xpath('.//a/@href').get()           
            comprar = False if item.xpath('.//a//div[contains(@style,"display:none")]/text()').get() == None else True

            if comprar == True:                
                #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar                            
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
                record['price']=item.xpath('.//span[contains(@class,"produto__preco_por")]/text()').get()                
                if len( [id_db for id_db in self.encontrados[self.name] if str(id_db) == str(id)]) == 0:
                    self.add_name(self.name, str(id))  
                    time.sleep(2)
                    request = self.make_request(prod_url, self.details, dict(record=record), self.detail_failure)            
                    yield request 
                    #yield scrapy.Request(dont_filter=True, url =prod_url, callback=self.details,  meta=dict(record=record))
                

        if(finish == False):
            uri = response.url.split('&p=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&p={}'.format(part, str(page))
            time.sleep(6)
            request = self.make_request(self.url, self.parse)            
            yield request 
            #yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)

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

        outros = response.xpath('//div[@class="variacoes-cores"]//ul//a/@href').getall()
        others = set()
        for item in outros:
            if item != record['prod_url']:
                others.add(item)
        record['outros']='|'.join([o for o in others])
        record['codigo'] ='-'.join(images_list[0].split('-')[-4:-2])
        record['prod_url']=response.url 
        record['imagens']="|".join(images_list[0:3])
        record['tamanhos']=json.dumps(opcoes_list)
        yield record      

       
        