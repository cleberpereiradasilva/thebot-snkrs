import discord
import multiprocessing
import json
import os
import time
import sys
from multiprocessing import Process, Queue
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from crawler.data.database import Database
from discord.ext import tasks
from datetime import datetime
from crawler.crawler.spiders.maze_snkrs_spider import MazeSnkrsSpider
from crawler.crawler.spiders.artwalk_calendario_spider import ArtwalkCalendarioSpider
from crawler.crawler.spiders.artwalk_novidades_spider import ArtwalkNovidadesSpider
from crawler.crawler.spiders.artwalk_restock_spider import ArtwalkRestockSpider
from crawler.crawler.spiders.gdlp_novidades_spider import GdlpNovidadesSpider
from crawler.crawler.spiders.gdlp_restock_spider import GdlpRestockSpider
from crawler.crawler.spiders.magicfeet_novidades_spider import MagicfeetNovidadesSpider
from crawler.crawler.spiders.magicfeet_snkrs_spider import MagicfeetSnkrsSpider
from crawler.crawler.spiders.maze_novidades_spider import MazeNovidadesSpider
from crawler.crawler.spiders.maze_restock_spider import MazeRestockSpider
from crawler.crawler.spiders.maze_snkrs_spider import MazeSnkrsSpider
from crawler.crawler.spiders.nike_calendario_spider import NikeCalendarioSpider
from crawler.crawler.spiders.nike_novidades_spider import NikeNovidadesSpider
from crawler.crawler.spiders.nike_restock_spider import NikeRestockSpider

from crawler.crawler import normal_settings as normal_settings 
from crawler.crawler import nike_settings as nike_settings 
from discord.ext import tasks
from scrapy.settings import Settings


def run_spider(spider, database):
    def f(q):
        try:
            my_settings = nike_settings if 'nike' in str(spider) else normal_settings
            crawler_settings = Settings()
            configure_logging()
            crawler_settings.setmodule(my_settings)                       
            runner = CrawlerRunner(settings=crawler_settings)
            runner.crawl(spider, database=database)            
            deferred = runner.join()
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            q.put(None)
        except Exception as e:
            q.put(e)

    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()
    result = q.get()
    p.join()

    if result is not None:
        raise result

def r_spiders():
    database = Database()
    spiders = [            
            ArtwalkCalendarioSpider,
            NikeRestockSpider,         
            ArtwalkNovidadesSpider,
            ArtwalkRestockSpider,            
            GdlpNovidadesSpider,
            NikeCalendarioSpider,
            GdlpRestockSpider,            
            MazeSnkrsSpider,
            MazeNovidadesSpider,
            MazeRestockSpider,
            MagicfeetNovidadesSpider,
            MagicfeetSnkrsSpider,            
            #NikeNovidadesSpider,            
    ]

    for spider in spiders:  
        run_spider(spider, database)

def r_forever():
    database = Database()
    n = 30
    while True:
        try:
            r_spiders()
        except:
            pass
        results = database.get_ultimos()
        get_all = database.get_all()
        rows = [str(row[0]).strip() for row in get_all]            
        for row in rows:                    
            if len( [id for id in results if str(id) == str(row)]) == 0 :                  
                database.delete(row)
        database.delete_ultimos()

        print('Aguardando {}s'.format(n))
        time.sleep(n)



class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        # start the task to run in the background                     
        self.database = Database()
        self.database.avisar_todos()
        self.first_time = self.database.isEmpty()
        try:
            self.channels = json.loads(self.database.get_config().replace("'",'"'))
        except:
            self.channels = {}
        self.my_background_task.start()

    async def show_help(self, adm_channel):
        send_to = self.get_channel(int(adm_channel))
        helper = '''
lista de comandos:
>delete \{url\}
>buscar \{palavra\}
>canais
>configurar 
{  
    "artwalk_calendario":{
        "canal": 0000000000000
    },
    "artwalk_restock": {
        "canal": 0000000000000    
    },
    "artwalk_snkrs": {
        "canal": 0000000000000    
    },
    "artwalk_lancamentos": {
        "canal": 0000000000000    
    },    
    "gdlp_lancamentos": {
        "canal": 0000000000000    
    },
    "gdlp_restock": {
        "canal": 0000000000000    
    },    
    "magicfeet_lancamentos": {
        "canal": 0000000000000    
    },
    "maze_lancamentos": {
        "canal": 0000000000000    
    },
    "maze_restock": {
        "canal": 0000000000000    
    },
    "maze_snkrs": {
        "canal": 0000000000000    
    },
    "nike_lancamentos": {
        "canal": 0000000000000    
    },
    "nike_restock": {
        "canal": 0000000000000    
    },
    "nike_snkrs": {
        "canal": 0000000000000    
    }
}
'''                    
        await send_to.send(helper)
        return 


    async def show_channels(self, adm_channel):
        send_to = self.get_channel(int(adm_channel))
        pretty_dict_str = json.dumps(self.channels, indent=2, sort_keys=True)                        
        await send_to.send(pretty_dict_str)
        return 

    async def delete_by_url(self, url, adm_channel):
        send_to = self.get_channel(int(adm_channel))        
        try:
            url = url.replace('>delete','').strip()
            self.database.delete_by_url(url)            
            await send_to.send("Dados removidos com sucesso!")            
        except Exception as e:                        
            await send_to.send("Erro ao remover os dados! Nada foi perdido.")
        return 

    async def search(self, url, adm_channel):
        send_to = self.get_channel(int(adm_channel))        
        try:
            word = url.replace('>buscar','').strip()            
            results = self.database.search_name(word)
            if len(results) == 0 :
                await send_to.send("Não foram encontrados registros!")
            elif len(results) > 10:
                await send_to.send("Foram encontrados muitos registros!\nPor favor seja um pouco mais específico.")
            else:
                result_list = '\n'.join([name[0] for name in results])
                await send_to.send('Segue resultados da pesquisa:\n{}'.format(result_list))
                
        except Exception as e:                        
            await send_to.send("Erro ao buscar registros!")
        return 

    async def delete_all(self, adm_channel):
        send_to = self.get_channel(int(adm_channel))        
        try:            
            self.database.delete_all()            
            await send_to.send("Dados removidos com sucesso!")            
        except Exception as e:                        
            await send_to.send("Erro ao remover os dados! Nada foi perdido.")
        return 
    
    async def set_channels(self, channels, adm_channel):
        send_to = self.get_channel(int(adm_channel))
        bk_channels = self.channels
        try:
            config = channels.replace('>configurar','')            
            channels_temp = json.loads(config)
            self.channels = json.loads(self.database.set_config(channels_temp).replace("'",'"'))                        
            await send_to.send("Dados atualizados com sucesso!")            
        except:
            self.channels = json.loads(self.database.set_config(bk_channels).replace("'",'"'))
            await send_to.send("Erro ao atualizar os dados! Nada foi perdido.")
        return 

    async def on_message(self, message):             
        adm_channel = os.environ.get('ADMIN_CHANNEL')
        if adm_channel == None:
            return

        if int(message.channel.id) != int(adm_channel):           
            return  #leave

        if message.content.startswith('>help'):
            await self.show_help(int(adm_channel))


        if message.content.startswith('>canais'):
            await self.show_channels(int(adm_channel))

        if message.content.startswith('>buscar'):
           await self.search(message.content, int(adm_channel))    
        
        if message.content.startswith('>configurar'):
           await self.set_channels(message.content, int(adm_channel))

        if message.content.startswith('>delete'):
           await self.delete_by_url(message.content, int(adm_channel))

        if message.content.startswith('>truncate'):
           await self.delete_all(int(adm_channel))

        return

        
    async def on_ready(self):
        print('Logado...')  
        adm_channel = os.environ.get('ADMIN_CHANNEL')    
        send_to = self.get_channel(int(adm_channel))  
        await send_to.send("Im ready and waiting for new products...")
        


    def create_link(self, data, last):
        if 'tamanho' in data.keys():
            if 'url' in data.keys():
                return '**{}** [**comprar**]({})| '.format(data['tamanho'], data['url']['href'])
            else:
                return '**{}**{} '.format(data['tamanho'], ' e' if last else ',')

        if 'aguardando' in data.keys():
            return '**{}**  '.format(data['aguardando'])
    
    @tasks.loop(seconds=15) # task runs every 15 seconds
    async def my_background_task(self): 
        print(' ============ DISCORD ===============')
        for channel in self.channels:                      
            channel_id = int(self.channels[channel]['canal'])            
            send_to = self.get_channel(channel_id)                                       
            rows = self.database.avisos(channel)                                
            for row in rows:               
                tamanhos = json.loads(row['tamanhos']) 
                tamanho_desc = ''.join([self.create_link(k, (idt+1) == (len(tamanhos)-1)) for idt, k in enumerate(tamanhos)])[:-2].replace('|','\n')

                message = '{}'.format(row['name'])
                if 'aguardando' in row['tamanhos']:
                    embed = discord.Embed(title=message, url=row['url'], 
                        description=tamanho_desc, color=3066993) #,color=Hex code
                    embed.set_thumbnail(url=row['imagens'][0])                                               
                    await send_to.send(embed=embed)
                else:
                    description_text='**Código de estilos: ** {}\n**Preço: ** {}\n\n'.format(row['codigo'],row['price'])
                    tamanho_text='**Tamanhos**\n{}'.format(tamanho_desc)
                    links_text='**Links Alternativos**\n' if len(row['outros'][1:3])>0 else ''

                    embed = discord.Embed(title=message, url=row['url'], 
                        description='{}{}{}'.format(description_text,tamanho_text,links_text ), color=3066993) #,color=Hex code        
                    embed.set_thumbnail(url=row['imagens'][0])                

                    for idx, outros in enumerate(row['outros'][1:3]):                    
                        embed.add_field(name='Link {}'.format(idx+1), value='[**aqui**]({})'.format(outros), inline=True)                    

                    await send_to.send(embed=embed)
                self.database.avisado(row['id'])  


    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready() # wait until the bot logs in

def r_discord():
    try:
        key = os.environ.get('DISCORD_SERVER_KEY')           
        client = MyClient()
        client.run(key)
        
    except:
        print(' ')
        print(' ')
        print(' ')
        print(' ********* ERROR NO DISCORD ********** ')
        print(' ********* ERROR NO DISCORD ********** ')
        print(' ********* ERROR NO DISCORD ********** ')
        print(' ********* ERROR NO DISCORD ********** ')
        print(' ********* ERROR NO DISCORD ********** ')
        print(' ********* ERROR NO DISCORD ********** ')
        print(' ********* ERROR NO DISCORD ********** ')
        print(' ')
        print(' ')
        print(' ')


if __name__ == '__main__':
    database = Database()       
    first_time = database.isEmpty()  
    inicio = datetime.now().strftime('%Y-%m-%d %H:%M')   
    if first_time:
        for i in range(0,2):
            r_spiders()            
            print('Rodada {}'.format(i))
            time.sleep(2)
        database.avisar_todos()

    p2 = multiprocessing.Process(name='p2', target=r_discord)
    p2.start()
    time.sleep(5)
    p1 = multiprocessing.Process(name='p1', target=r_forever)    
    p1.start()

    
