import sqlite3
import os
import logging

class Sqlite(): 
    def __init__(self):        
        logging.log(logging.DEBUG, "Connecting Database ...")           
        db_path = '{}/snikers_database.db'.format(os.path.dirname(__file__))
        database = sqlite3.connect(db_path)
        cursor = database.cursor()
        try:
            cursor.execute('''CREATE TABLE products
                    (created_at text, spider text, id text, url text, name text, price text, categoria text, tab text, imagens text, tamanhos text, send text)''')            
        except:
            pass

        try:
            cursor.execute('''CREATE TABLE config (channels text)''')
            database.commit()
        except:
            pass            
        
        self.cursor = cursor
        self.database = database
        logging.log(logging.INFO, "Database connected!")

    def get_config(self):
        query = 'SELECT channels FROM config'
        return [row[0] for row in self.cursor.execute(query)][0]

    def set_config(self, config):
        self.cursor.execute('delete from config')        
        self.cursor.execute('insert into config values("{}")'.format(config))
        self.database.commit()
        return self.get_config()

    def insert(self, item):        
        self.cursor.execute("insert into products(created_at ,spider ,id ,url ,name ,categoria ,tab ,send, imagens, tamanhos, price ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            (
                item['created_at'],
                item['spider'],
                item['codigo'], 
                item['prod_url'], 
                item['name'], 
                item['categoria'], 
                item['tab'], 
                item['send'],
                item['imagens'], 
                item['tamanhos'],
                item['price']
            ))
        self.database.commit()             
    
    def update(self, item):
        self.cursor.execute("update products set imagens = ?, tamanhos = ? where url = ? ", 
            (
                item['imagens'],
                item['tamanhos'],            
                item['prod_url'], 
            ))
        self.database.commit()
    def delete(self, item):
        self.cursor.execute("delete from products where id = ? ", 
            (                
                item['id'], 
            ))
        self.database.commit()

    def delete_by_url(self, url):        
        self.cursor.execute("delete from products where url = '{}' ".format(url))
        self.database.commit()

    def search(self, fields, item):
        query = 'SELECT {} FROM products where {}'.format(','.join(fields), ' and '.join(['{}="{}"'.format(k, item[k]) for k in item.keys()]) )
        return [row for row in self.cursor.execute(query)]

    def avisos(self, spider):
        query = 'SELECT id, name, url, imagens, tamanhos FROM products where send="avisar" and spider="{}"'.format(spider)        
        return [{'id': row[0], 'name': row[1], 'url': row[2], 'imagens': row[3].split('|'), 'tamanhos': row[4].split('|') } for row in self.cursor.execute(query)]

    def isEmpty(self):
        rows = [row[0] for row in self.cursor.execute('SELECT count(id) FROM products')][0]           
        return int(rows) == 0
    
    def avisar_todos(self):
        self.cursor.execute("update products set send='avisado'")
        self.database.commit()  
    
    def avisado(self, id):
        self.cursor.execute("update products set send='avisado' where id = '{}'".format(id))
        self.database.commit()  
       
        

    
