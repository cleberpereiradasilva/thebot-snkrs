import sqlite3
import os

print("===== START DATABASE =====")
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

class Sqlite(): 
    pass
