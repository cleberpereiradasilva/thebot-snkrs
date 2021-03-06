from scrapy.exceptions import DropItem
import logging
try:
    from crawler.crawler.items import Inserter, Updater, Deleter
    from crawler.data.database import Database
except:
    from crawler.items import Inserter, Updater, Deleter
    from data.database import Database
class CrawlerPipeline:
    def __init__(self):        
        self.connection = Database()

    def inserir(self, item):       
        self.connection.insert(item)
        result = self.connection.search(['id'], {'id': item['id']})[0]        
        logging.log(logging.WARNING, "Item inserido no database {}".format(len(result) == 1)) 
        
    def atualizar(self, item):             
        self.connection.update(item)
        logging.log(logging.WARNING, "Item atualizado no database") 

    def add_delete(self, item):             
        self.connection.insert_ultimos(item)
        

    def process_item(self, item, spider):
        valid = True       
        for data in item:
            if not data:
                valid = False              
                raise DropItem("Missing {0}!".format(data))                
        if valid:  
            if isinstance(item, Inserter):  
                self.inserir(item)                  
            if isinstance(item, Updater):    
                self.atualizar(item)     
            if isinstance(item, Deleter):    
                self.add_delete(item)               
        return item

   
