import scrapy
import json, time
from datetime import datetime
try:
    from crawler.crawler.items import Inserter,  Deleter
    from crawler.data.database import Database
except:
    from crawler.items import Inserter,  Deleter
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
        
        self.first_time = len(results) 

    def start_requests(self):       
        urls = [            
            'https://www.nike.com.br/Snkrs/Estoque?demanda=true&p=1',            
        ]       

        for url in urls:
            yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)  
       
    def add_name(self, key, id):
        if key in  self.encontrados:
            self.encontrados[key].append(id)
        else:
            self.encontrados[key] = [id]

    def _parse(self, response):     
        finish  = True
        tab = response.url.replace('?','/').split('/')[4]  
        categoria = 'nike_restock'
        
        send = 'avisar' if int(self.first_time) > 0 else 'avisado'

        #pega todos os ites da pagina, apenas os nomes dos tenis
        nodes = [ name for name in response.xpath('//div[contains(@class,"produto produto--")]') ]
        if(len(nodes) > 0 ):
            finish=False       

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in nodes: 
            name = item.xpath('.//h2//span/text()').get()           
            prod_url = item.xpath('.//a/@href').get()
            id = 'ID{}-{}-{}$'.format(item.xpath('.//a/img/@alt').get().split(".")[-1].strip(), categoria, tab)
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
            record['price']=''             
            if len( [id_db for id_db in self.encontrados[self.name] if str(id_db) == str(id)]) == 0:     
                self.add_name(self.name, str(id))  
                yield scrapy.Request(dont_filter=True, url =prod_url, callback=self.details,  meta=dict(record=record))
        
        if(finish == False):
            uri = response.url.split('&p=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&p={}'.format(part, str(page))
            time.sleep(3)
            yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)
    
    def parse(self, response):
        try:
            self.parse(response)
        except Exception as e:
            print("########## ERROR ON PARSE ##########")
            print("########## ERROR ON PARSE ##########")
            print("########## ERROR ON PARSE ##########")
            print("########## ERROR ON PARSE ##########")
            print("########## ERROR ON PARSE ##########")
            print("########## ERROR ON PARSE ##########")
            print("########## ERROR ON PARSE ##########")
            print(e)
            print('################################################################')
            time.sleep(10)

            
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

        

      
        


        