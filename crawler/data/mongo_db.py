import pymongo
import os
import logging
import re
import json

MONGO_USER=os.environ.get('MONGO_USER')
MONGO_PASSWORD=os.environ.get('MONGO_PASSWORD')
MONGO_URL=os.environ.get('MONGO_URL')

class MongoDatabase(): 
    def __init__(self):        
        logging.log(logging.DEBUG, "Connecting Database ...")    
        try:
            connection_string = "mongodb+srv://{}:{}@{}/?retryWrites=true&w=majority".format(MONGO_USER, MONGO_PASSWORD, MONGO_URL)
            client = pymongo.MongoClient(connection_string)
            mydb = client["snkrs"]
            self.registros = mydb["registros"]
            self.canais = mydb["canais"] 
            self.ultimos = mydb["ultimos"]
            logging.log(logging.INFO, "Database connected!")
        except Exception as e:
            print(e)            
            raise Exception("\n\n\nErro ao conectar no banco de dados\n\n")
  
    def configure(self, item):        
        self.canais.delete_many({})
        self.canais.insert_one(dict(item))

    def get_canais(self):
        return [[row[k] for k in row.keys()] for row in self.canais.find({},{'_id':0})] 

    def insert_ultimos(self, item):         
        self.ultimos.insert_one(dict(item))

    def delete_ultimos(self):
        self.ultimos.delete_many({})  

    def get_ultimos(self):
        cursor = self.ultimos.find({})
        return [row['id'] for row in cursor]
        

    def insert(self, item):        
        produto = dict(item)
        produto['url']=produto['prod_url']
        self.registros.insert_one(dict(produto))
        
   
    def delete(self, id):
        self.registros.delete_many({"id" : id})
        logging.log(logging.INFO, "Removendo...!")

    def delete_by_url(self, url):        
        self.registros.delete_many({"prod_url" : url})

    def delete_all(self):        
        self.registros.delete_many({}) 

    def count(self, query):
        return [[len([row['_id'] for row in self.registros.find(query)])]]
        

    
    def search(self, fields, query):
        fields = dict(zip(fields, [1]))        
        return [[row['id']] for row in self.registros.find(query, fields)]

    def get_all(self):                
        return [[row[k] for k in row.keys()] for row in self.registros.find({},{'_id':0})] 

    def totais(self):
        return [[row['_id'],row['total']] for row in self.registros.aggregate([{ "$group": { '_id': "$categoria", "total": { "$sum": 1 } } }])]
    
    def search_name(self, word):
        rgx = re.compile(word, re.IGNORECASE)  # compile the regex
        return [[row['prod_url']] for row in self.registros.find({"$or" : [{'name': rgx}, {'prod_url': rgx}]},{'prod_url' : 1, '_id' : 0})]   

    def avisos(self, categoria): 
        return [row for row in self.registros.find({"send": "avisar", "categoria" : categoria},{'_id':0})] 

    def isEmpty(self):  

        return len([row for row in self.registros.find({})]) == 0        
    
    def avisar_todos(self):
        self.registros.update_many({}, {"$set": {'send':'avisado'}})
    
    def avisado(self, id):
        self.registros.update_many({'id': id}, {"$set": {'send':'avisado'}})       
