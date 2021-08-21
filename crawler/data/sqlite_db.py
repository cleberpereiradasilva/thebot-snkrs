import sqlite3
import os
import logging
import sys
class Sqlite(): 
    def __init__(self):        
        logging.log(logging.DEBUG, "Connecting Database ...")           
        db_path = '{}/snikers_database.db'.format(os.path.dirname(__file__))
        database = sqlite3.connect(db_path)
        cursor = database.cursor()
        try:
            cursor.execute('''CREATE TABLE products
                    (created_at text, spider text, id text, codigo text, url text, name text, price text, categoria text, tab text, imagens text, tamanhos text, send text, outros text)''')            
        except:
            pass

        try:
            cursor.execute('''CREATE TABLE config (channels text)''')
            database.commit()
        except:
            pass  

        try:
            cursor.execute('''CREATE TABLE ultimos (id text)''')
            database.commit()
        except:
            pass             
        
        self.cursor = cursor
        self.database = database
        logging.log(logging.INFO, "Database connected!")

    def get_config(self):
        query = 'SELECT channels FROM config'
        try:
            return [row[0] for row in self.cursor.execute(query)][0]
        except:
            return []

    def set_config(self, config):
        self.cursor.execute('delete from config')        
        self.cursor.execute('insert into config values("{}")'.format(config))
        self.database.commit()
        return self.get_config()

    def insert_ultimos(self, item):         
        self.cursor.execute("insert into ultimos(id) values (?)", 
            (                    
                item['id'],                  
            ))
        self.database.commit()  

    def delete_ultimos(self):
        self.cursor.execute("delete from ultimos")
        self.database.commit()

    def get_ultimos(self):
        query = 'SELECT id FROM ultimos'
        return [row for row in self.cursor.execute(query)]
        

    def insert(self, item):          
        try:      
            self.cursor.execute("insert into products(created_at ,spider ,id ,codigo, url ,name ,categoria ,tab ,send, imagens, tamanhos, price, outros ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                (
                    item['created_at'],
                    item['spider'],
                    item['id'], 
                    item['codigo'], 
                    item['prod_url'], 
                    item['name'], 
                    item['categoria'], 
                    item['tab'], 
                    item['send'],
                    item['imagens'], 
                    item['tamanhos'],
                    item['price'],
                    item['outros']                
                ))
            self.database.commit()          


            results = self.search(['id'],{
                'id':item['id']                
            })[0][0] 
            if results == item['id']:
                return True
            if results == item['id'] == False:                  
                logging.log(logging.ERROR, "Erro ao inserir {}".format(item['url']))                              
                print("====== Erro ao inserir =============")
                print(item['url'])                
                print("====== Erro ao inserir =============")
                return False

        except sqlite3.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')       
            return False     
            
    
    def update(self, item):
        self.cursor.execute("update products set imagens = ?, tamanhos = ? where url = ? ", 
            (
                item['imagens'],
                item['tamanhos'],            
                item['prod_url'], 
            ))
        self.database.commit()
    def delete(self, id):
        self.cursor.execute("delete from products where id = ? ", 
            (                
                id, 
            ))
        self.database.commit()       
        logging.log(logging.INFO, "Removendo...!")

    def delete_by_url(self, url):        
        self.cursor.execute("delete from products where url = '{}' ".format(url))
        self.database.commit()

    def delete_all(self):        
        self.cursor.execute("delete from products")
        self.database.commit()

    def search(self, fields, item):
        query = 'SELECT {} FROM products where {}'.format(','.join(fields), ' and '.join(['lower({})="{}"'.format(k, str(item[k]).lower()) for k in item.keys()]) )        
        return [row for row in self.cursor.execute(query)]

    def get_all(self):
        query = 'SELECT id FROM products'        
        return [row for row in self.cursor.execute(query)]
    
    def search_name(self, word):
        query = 'SELECT url FROM products where lower(name) like "%{}%" or lower(url) like "%{}%"'.format(word.lower(), word.lower())
        return [row for row in self.cursor.execute(query)]    

    def avisos(self, categoria):        
        query = 'SELECT id, name, url, imagens, tamanhos, price, codigo, outros FROM products where send="avisar" and categoria="{}"'.format(categoria)        
        return [{'id': row[0], 'name': row[1], 'url': row[2], 'imagens': row[3].split('|'), 'tamanhos': row[4], 'price' : row[5], 'codigo': row[6], 'outros' : row[7].split('|') } for row in self.cursor.execute(query)]

    def isEmpty(self):
        rows = [row[0] for row in self.cursor.execute('SELECT count(id) FROM products')][0]           
        return int(rows) == 0
    
    def avisar_todos(self):
        self.cursor.execute("update products set send='avisado'")
        self.database.commit()  
    
    def avisado(self, id):
        self.cursor.execute("update products set send='avisado' where id = '{}'".format(id))
        self.database.commit()  
       
        

    
