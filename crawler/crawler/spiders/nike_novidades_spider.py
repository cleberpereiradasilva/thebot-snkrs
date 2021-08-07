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
               (date text, spider text, id text, url text, name text, categoria text, tab text, send text)''')
    database.commit()
except:
    pass

class NikeNovidadesSpider(scrapy.Spider):
    name = "nike_novidades"    
    encontrados = {}


    def start_requests(self):
        urls = [
            'https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3ACalcados&demanda=true&p=1',
            'https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3ACalcados&demanda=true&p=1',

            'https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3AAcess%F3rios&demanda=true&p=1',
            'https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3AAcess%F3rios&demanda=true&p=1',

            'https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3ARoupas&demanda=true&p=1',
            'https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3ARoupas&demanda=true&p=1',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def add_name(self, tab, id):
        if tab in  self.encontrados:
            self.encontrados[tab].append(id)
        else:
            self.encontrados[tab] = [id]

    def parse(self, response):
        items = response.xpath('//div[@data-codigo]')  
        finish  = True
        tab = 'Feminino' if 'fem' in response.url else 'Masculino'
        categoria = 'nov-calcados' if 'Calcados' in response.url else 'nov-roupas' if 'Roupas' in response.url else 'nov-acessorios'
        if(len(items) > 0 ):
            finish = False           

        for item in items:                      
            codigo = 'ID{}$'.format(item.xpath('./@data-codigo').get().strip())            
            name = item.xpath('.//a[@class="produto__nome"]/text()').get()
            prod_url = item.xpath('.//a/@href').get()           
            comprar = False if item.xpath('.//a//div[contains(@style,"display:none")]/text()').get() == None else True
            self.add_name(tab, str(codigo))

            if comprar == True:
                #pega todos os nomes da tabela, apenas os nomes    
                rows = [str(row[0]).strip() for row in cursor.execute('SELECT id FROM products where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'"')]

                #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar                            
                if len( [id for id in rows if str(id) == str(codigo)]) == 0:                
                    cursor.execute("insert into products values (?, ?, ?, ?, ?, ?, ?, ?)", (datetime.now().strftime('%Y-%m-%d %H:%M'), self.name, codigo, prod_url, name, categoria, tab, 'avisar'))                

        database.commit()                       
        if(finish == False):
            uri = response.url.split('&p=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&p={}'.format(part, str(page))
            yield scrapy.Request(url=url, callback=self.parse)
        else:
           #checa se algum item do banco nao foi encontrado, nesse caso atualiza com o status de remover            
            rows = [str(row[0]).strip() for row in cursor.execute('SELECT id FROM products where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'"')]                        
            try:
                v = self.encontrados[tab]
            except:
                print("========== Err ============")                
                print(response.url)
                print('Total items ', len(items))
                for k in self.encontrados.keys():
                    print('{} Total={}'.format(k,len(self.encontrados[k])))
                print("===========================")
            
            for row in rows:
                if len( [id for id in self.encontrados[tab] if str(id) == str(row)]) == 0 :                                       
                    cursor.execute('update products set send="remover" where spider="'+self.name+'" and categoria="'+categoria+'" and tab="'+tab+'" and id="'+row+'"')
                    database.commit()
                
           

       
        