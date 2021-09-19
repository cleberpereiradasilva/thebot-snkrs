
import multiprocessing
import json
from multiprocessing import process
import os
import time
import hashlib
import sys
from multiprocessing import Process, Queue
from twisted.internet import reactor

from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from crawler.data.database import Database


from crawler.discord.discord_client import DiscordClient




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
from crawler.crawler import nike_settings as slow_settings 
from scrapy.settings import Settings

from twisted.python import log
import logging
# from logging.handlers import RotatingFileHandler
# from scrapy.utils.log import configure_logging
# configure_logging(install_root_handler=False)
# log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# log_level = logging.WARNING  # Or better yet get `LOG_LEVEL` from settings.
# log_file = 'scrapy_log.log'  # Or better yet get `LOG_FILE` from settings.

# logging.basicConfig(
#     format=log_format,
#     level=log_level
# )

# rotating_file_log = RotatingFileHandler(log_file, maxBytes=(1024*10000), backupCount=1)
# rotating_file_log.setFormatter(logging.Formatter(log_format))

# root_logger = logging.getLogger()
# #root_logger.addHandler(rotating_file_log)

# logging.basicConfig(filemode='a', filename='scrapy_log.txt')
# observer = log.PythonLoggingObserver()
# observer.start()


database = Database()     
results = database.search(['id', 'spider'],{})  

proxy_env = os.environ.get('PROXY_LIST')
proxy_list = None

if proxy_env:    
    proxy_list = ['{}:{}@{}:{}'.format(p.split(':')[2],p.split(':')[3],p.split(':')[0],p.split(':')[1]) for p in proxy_env.split('|')] 


def run_spider(spider=None, url=None, proxy=None):
    def f(q):
        try:
            #my_settings = slow_settings if 'nike' in str(spider) or 'maze' in str(spider) else normal_settings
            my_settings = normal_settings
            crawler_settings = Settings()
            configure_logging()
            crawler_settings.setmodule(my_settings)                       
            runner = CrawlerRunner(settings=crawler_settings)
            if url: 
                if proxy:               
                    runner.crawl(spider, results=results, url=url, proxy_list=proxy)
                else:
                    runner.crawl(spider, results=results, url=url)
            else:
                if proxy:
                    runner.crawl(spider, results=results, proxy_list=proxy )
                else:
                    runner.crawl(spider, results=results )
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


def r_spiders(n=1):    

    if n == 1:
        run_spider(ArtwalkCalendarioSpider)
        run_spider(ArtwalkRestockSpider) 
        run_spider(ArtwalkNovidadesSpider)

    if n == 2:
        run_spider(MagicfeetSnkrsSpider)
        run_spider(MagicfeetNovidadesSpider)

    if n == 3:
        run_spider(MazeRestockSpider)
        run_spider(MazeSnkrsSpider)

    if n == 4:
        run_spider(spider=NikeRestockSpider, proxy=proxy_list)    
        run_spider(spider=NikeCalendarioSpider, proxy=proxy_list)    

    if n == 5:
        run_spider(spider=GdlpRestockSpider, proxy=proxy_list)
        run_spider(spider=GdlpNovidadesSpider, proxy=proxy_list)
        
    if n == 6:      
        run_spider(spider=NikeNovidadesSpider, url='https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3ACalcados&demanda=true&p=1',proxy=proxy_list)
        run_spider(spider=NikeNovidadesSpider, url='https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3ACalcados&demanda=true&p=1',proxy=proxy_list)
        run_spider(spider=NikeNovidadesSpider, url='https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3AAcess%F3rios&demanda=true&p=1',proxy=proxy_list)
        run_spider(spider=NikeNovidadesSpider, url='https://www.nike.com.br/lancamento-fem-26?Filtros=Tipo%20de%20Produto%3ARoupas&demanda=true&p=1',proxy=proxy_list)
        run_spider(spider=NikeNovidadesSpider, url='https://www.nike.com.br/lancamento-masc-28?Filtros=Tipo%20de%20Produto%3ARoupas&demanda=true&p=1',proxy=proxy_list)
            
  
    if n == 7:
        spiders = [
                {'spider': MazeNovidadesSpider, 'url': 'https://www.maze.com.br/categoria/roupas/camisetas'},            
                {'spider': MazeNovidadesSpider, 'url': 'https://www.maze.com.br/categoria/acessorios/meias'},
                {'spider': MazeNovidadesSpider, 'url': 'https://www.maze.com.br/categoria/roupas/saia'},
                {'spider': MazeNovidadesSpider, 'url': 'https://www.maze.com.br/categoria/roupas/calcas'},
                {'spider': MazeNovidadesSpider, 'url': 'https://www.maze.com.br/categoria/acessorios/gorros'},
                {'spider': MazeNovidadesSpider, 'url': 'https://www.maze.com.br/categoria/acessorios/bones'},
            ]
        for spider in spiders:
            run_spider(spider=spider['spider'], url=spider['url'])
            time.sleep(5)

def r_forever(blc):
    n = 15
    times = 0
    while True:
        try:
            r_spiders(blc)
        except:
            pass

        # times = times + 1

        # if times > 50: 
        #     results = database.get_ultimos()
        #     get_all = database.get_all()
        #     rows = [str(row[0]).strip() for row in get_all]            
        #     for row in rows:                    
        #         if len( [id for id in results if str(id) == str(row)]) == 0 :                  
        #             print('Removendo {}'.format(row))               
        #             time.sleep(1)
        #             database.delete(row)
        #     database.delete_ultimos()
        #     times = 0
        #database.delete_ultimos()
        print('Aguardando {}s p{}'.format(n, blc))
        time.sleep(n)




def r_discord():  
    key = os.environ.get('DISCORD_SERVER_KEY')           
    client = DiscordClient()
    client.run(key)
        
  

        
    


if __name__ == '__main__':  
    #database.delete_all()   
    #print('Removendo...')
    #time.sleep(1)
    #r_spiders()

    first_time = database.isEmpty() 
    if first_time:
        for i in range(0,3):
            processos = []
            for blc in range(1,8):    
               r_spiders(i)
            print('Rodada {}'.format(i))
            time.sleep(1)
        database.avisar_todos()

    p2 = multiprocessing.Process(name='p2', target=r_discord)
    p2.start()
    # time.sleep(5)
    processos = []
    for i in range(1,8):        
        processos.append(multiprocessing.Process(name='p'+str(i), target=r_forever, args=(i,)))

    for p in processos:
        p.start()


