import scrapy,json
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Updater, Deleter
    from crawler.data.database import Database
except:
    from crawler.items import Inserter, Updater, Deleter
    from data.database import Database
class NikeCalendarioSpider(scrapy.Spider):
    name = "nike_calendario"
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
            'https://www.nike.com.br/Snkrs/Calendario?demanda=true&p=1',
        ]
        for url in urls:
            yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)  
       
    def add_name(self, key, id):
        if key in  self.encontrados:
            self.encontrados[key].append(id)
        else:
            self.encontrados[key] = [id]

    def parse(self, response):     
        finish  = True
        tab = response.url.replace('?','/').split('/')[4]  
        categoria = 'nike_calendario_snkrs'
        #pega todos os ites da pagina, apenas os nomes dos tenis
        nodes = [ name for name in response.xpath('//div[contains(@class,"produto produto--")]') ]
        if(len(nodes) > 0 ):
            finish=False
       
        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in nodes:
            name = item.xpath('.//h2/text()').get()            
            prod_url = item.xpath('.//a/@href').get()
            id = 'ID{}-{}$'.format(item.xpath('.//a/img/@alt').get().split(".")[-1].strip(), tab)            
            imagem = item.xpath('.//div[@class="produto__imagem"]//a//img/@data-src').get()
            release_full = item.xpath('.//h2[@class="produto__detalhe-titulo"]//span[descendant-or-self::text()]').get()
            quando = release_full.replace('<span class="snkr-release__mobile-date">','').replace('<span>','').replace('</span>','') .replace('Disponível às', 'Disponível em')
            record = Inserter()
            record['id']=id
            record['created_at']=datetime.now().strftime('%Y-%m-%d %H:%M') 
            record['spider']=self.name 
            record['codigo']='' 
            record['prod_url']=prod_url 
            record['name']=name 
            record['categoria']=categoria 
            record['tab']=tab 
            record['imagens']=imagem
            record['tamanhos']=json.dumps([{"aguardando": quando}]) 
            record['send']='avisar'    
            record['price']=''   
            record['outros']=''                
            if len( [id_db for id_db in self.encontrados[self.name] if str(id_db) == str(id)]) == 0:     
                self.add_name(self.name, str(id)) 
                yield record  
        
        if(finish == False):
            uri = response.url.split('&p=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&p={}'.format(part, str(page))
            yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)
         
        

      
        


        