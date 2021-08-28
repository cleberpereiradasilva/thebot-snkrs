
from .sqlite_db import Sqlite
from .mongo_db import MongoDatabase

class Database(MongoDatabase): 
    def __init__(self): 
        super().__init__()
    
