import os, time
from crawler.data.database import Database
import subprocess

from datetime import datetime

inicio = datetime.now().strftime('%Y-%m-%d %H:%M') 






if __name__ == '__main__':
    database = Database()   
    first_time = database.isEmpty()   
    discord_on = False  
    while True:
        if first_time:            
            for i in range(1,10):
                os.system("python server_spiders.py")
                os.system("python server_spiders_nike.py")
            first_time = False
        if first_time == False and discord_on == False:
            print(['python','server_discord.py', '', inicio])
            subprocess.Popen(['python','server_discord.py', '', inicio])
            discord_on = True
            time.sleep(20)

        os.system("python server_spiders.py")
        os.system("python server_spiders_nike.py")
        print('Aguardando...')
        time.sleep(15)
