import scrapy
import sqlite3
import os
from datetime import datetime


print("nike_novidades")
print(os.path.abspath(os.path.dirname(__file__)))
db_path = '{}data/nike_database.db'.format(os.path.abspath(os.path.dirname(__file__)).split('crawler/crawler')[0])
print(db_path)
database = sqlite3.connect(db_path)
cursor = database.cursor()
try:
    cursor.execute('''CREATE TABLE products
               (date text, spider text, id text, url text, name text, tab text, status text, send text)''')
    database.commit()
except:
    pass

class NikeNovidadesSpider(scrapy.Spider):
    name = "nike_novidades"    
    encontrados = {}

    def start_requests(self):
        urls = [
            'https://www.nike.com.br/lancamento-fem-26?demanda=true&p=1',
            'https://www.nike.com.br/lancamento-masc-28?demanda=true&p=1',            
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def add_name(self, tab, id, situacao):
        if tab in  self.encontrados:
            self.encontrados[tab].append({
                'id': id,
                'situacao': situacao
             })
        else:
            self.encontrados[tab] = [{
                'id': id,
                'situacao': situacao
             }]

    def parse(self, response):
        items = response.xpath('//div[@data-codigo]')  
        finish  = True
        tab = 'Feminino' if 'fem' in response.url else 'Masculino'
        if(len(items) > 0 ):
            finish = False
        for item in items:            
            codigo = item.xpath('./@data-codigo').get()                 
            name = item.xpath('.//a[@class="produto__nome"]/text()').get()
            prod_url = item.xpath('.//a/@href').get()
            situacao = 'Comprar' if item.xpath('.//a//div[contains(@style,"display:none")]/text()').get() == None else 'Em breve'
            
            #pega todos os nomes da tabela, apenas os nomes    
            rows = [str(row[0]).strip() for row in cursor.execute('SELECT id FROM products where spider="'+self.name+'" and tab="'+tab+'" and status="'+situacao+'"')]

            #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
          
            self.add_name(tab, codigo, situacao)
            if len( [id for id in rows if id == codigo]) == 0:                   
                cursor.execute("insert into products values (?, ?, ?, ?, ?, ?, ?, ?)", (datetime.now().strftime('%Y-%m-%d %H:%M'), self.name, codigo, prod_url, name, tab, situacao, 'avisar'))

        database.commit()
        if(finish == False):
            uri = response.url.split('&p=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&p={}'.format(part, str(page))
            yield scrapy.Request(url=url, callback=self.parse)
        else:
            rows = [[str(row[0]).strip(),str(row[1]).strip()] for row in cursor.execute('SELECT id,status FROM products where spider="'+self.name+'" and tab="'+tab+'"')]
            
            #checa se algum item do banco nao foi encontrado, nesse caso atualiza com o status de remover            
            for row in rows:        
                if len( [data for data in self.encontrados[tab] if row[0] == data['id'] and row[1] == data['situacao']] ) == 0 :                                     
                    cursor.execute('update products set send="remover" where spider="'+self.name+'" and tab="'+tab+'" and status="'+row[1]+'" and id="'+row[0]+'"')
                    database.commit()

       
        