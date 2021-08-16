import os, subprocess, time

subprocess.Popen(['python','server_discord.py'])


while True:
    os.system("python server_spider.py")
    print('Aguardando...')
    time.sleep(15)
