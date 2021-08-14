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


    def start_requests(self):       
        urls = [
            'https://www.nike.com.br/Snkrs/Calendario?demanda=true&p=1',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)  
        self.remove()
       
    def add_name(self, key, id):
        if key in  self.encontrados:
            self.encontrados[key].append(id)
        else:
            self.encontrados[key] = [id]

    def remove(self):
        #checa se algum item do banco nao foi encontrado, nesse caso atualiza com o status de remover            
        results = self.database.search(['id'],{
            'spider':self.name                        
        })        
        rows = [str(row[0]).strip() for row in results]            
        for row in rows:                    
            if len( [id for id in self.encontrados[self.name] if str(id) == str(row)]) == 0 :                  
                record = Deleter()
                record['id']=row                     
                yield record   

    def parse(self, response):               
        finish  = True
        tab = response.url.replace('?','/').split('/')[4]  
        categoria = 'nike_calendario_snkrs'
        #pega todos os ites da pagina, apenas os nomes dos tenis
        items = [ name for name in response.xpath('//div[contains(@class,"produto produto--")]') ]
        if(len(items) > 0 ):
            finish = True

        #pega todos os nomes da tabela, apenas os nomes    
        results = self.database.search(['id'],{
            'spider':self.name,
            'categoria':categoria            
        })        
        rows = [str(row[0]).strip() for row in results]

        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in items[0:5]:
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
            self.add_name(self.name, str(id))
            if len( [id_db for id_db in rows if str(id_db) == str(id)]) == 0:  
                yield record  
        
        if(finish == False):
            uri = response.url.split('&p=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&p={}'.format(part, str(page))
            yield scrapy.Request(url=url, callback=self.parse)
         
        

      
        


        