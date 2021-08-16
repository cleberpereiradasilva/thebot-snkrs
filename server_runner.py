import os, time
from crawler.data.database import Database
import subprocess



if __name__ == '__main__':
    database = Database()   
    first_time = database.isEmpty()   
    discord_on = False  

    while True:
        if first_time:            
            for i in range(1,10):
                os.system("python server_spiders.py")
            first_time = False
        if first_time == False and discord_on == False:
            subprocess.Popen(['python','server_discord.py'])
            discord_on = True
            time.sleep(20)

        os.system("python server_spiders.py")
        print('Aguardando...')
        time.sleep(15)
