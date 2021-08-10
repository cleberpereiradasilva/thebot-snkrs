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
                    (created_at text, spider text, id text, url text, name text, categoria text, tab text, send text, imagens text, tamanhos text)''')
            database.commit()
        except:
            pass
        self.cursor = cursor
        self.database = database
        logging.log(logging.INFO, "Database connected!")

    def insert(self, item):        
        self.cursor.execute("insert into products(created_at ,spider ,id ,url ,name ,categoria ,tab ,send, imagens, tamanhos ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
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
                item['tamanhos']
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

    def search(self, fields, item):
        query = 'SELECT {} FROM products where {}'.format(','.join(fields), ' and '.join(['{}="{}"'.format(k, item[k]) for k in item.keys()]) )
        return [row for row in self.cursor.execute(query)]
        

    
