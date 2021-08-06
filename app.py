import discord
import scrapy
import os
import scrapy.crawler as crawler
import sqlite3
from multiprocessing import Process, Queue
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from crawler.crawler.spiders.nike_snkrs_spider import NikeSnkrsSpider
from crawler.crawler.spiders.nike_novidades_spider import NikeNovidadesSpider
from discord.ext import tasks

print("app.py")
print(os.path.abspath(os.path.dirname(__file__)))
db_path = '{}/data/nike_database.db'.format(os.path.abspath(os.path.dirname(__file__)).split('crawler/crawler')[0])
print(db_path)

database = sqlite3.connect(db_path)
cursor = database.cursor()




async def run_spider():
    def f(q):
        try:
            configure_logging()
            runner = crawler.CrawlerRunner()
            runner.crawl(NikeSnkrsSpider)
            runner.crawl(NikeNovidadesSpider)
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


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        # start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        print('Logado...')


    @tasks.loop(seconds=180) # task runs every 15 seconds
    async def my_background_task(self):        
        channels = [{
            'spider': 'nike_snkrs',
            'id': 872973958444626041,
            'tab':'Calendario',
            'status': 'aviseme',
            'mensagem' : {
                'inserido': 'Novo produto inserido no calendário[Avise-me]',
                'removido': 'Produto removido do calendário[Avise-me]'
                }
            },
            {
            'spider': 'nike_snkrs',
            'id': 872973958444626041,
            'tab':'Calendario',
            'status': 'comprar',
            'mensagem' : {
                'inserido': 'Novo produto inserido no calendário[Comprar]',
                'removido': 'Produto removido do calendário[Comprar]'
                }
            },
            {
            'spider': 'nike_snkrs',
            'id': 872973958444626041,
            'tab':'Calendario',
            'status': 'esgotado',
            'mensagem' : {
                'inserido': 'Novo produto inserido no calendário[Esgotado]',
                'removido': 'Produto removido do calendário[Esgotado]'
                }
            },
            {
            'spider': 'nike_snkrs',
            'id': 872725671858827304,                  
            'tab':'Feed',
            'status': 'aviseme',
            'mensagem' : {
                'inserido': 'Novo produto inserido no reestoque[Avise-me]',
                'removido': 'Produto removido do reestoque[Avise-me]'
                }
            },
            {
            'spider': 'nike_snkrs',
            'id': 872725671858827304,
            'tab':'Feed',
            'status': 'comprar',
            'mensagem' : {
                'inserido': 'Novo produto inserido no reestoque[Comprar]',
                'removido': 'Produto removido do reestoque[Comprar]'
                }
            },
            {
            'spider': 'nike_snkrs',
            'id': 872725671858827304,
            'tab':'Feed',
            'status': 'esgotado',
            'mensagem' : {
                'inserido': 'Novo produto inserido no reestoque[Esgotado]',
                'removido': 'Produto removido do reestoque[Esgotado]'
                }
            },
            {
            'spider': 'nike_snkrs',
            'id': 872973807671996476,
            'tab':'Feed',
            'status': 'aviseme',
            'mensagem' : {
                'inserido': 'Novo produto inserido no estoque[Avise-me]',
                'removido': 'Produto removido do estoque[Avise-me]'
                }
            },
            {
            'spider': 'nike_snkrs',
            'id': 872973807671996476,
            'tab':'Feed',
            'status': 'comprar',
            'mensagem' : {
                'inserido': 'Novo produto inserido no estoque[Comprar]',
                'removido': 'Produto removido do estoque[Comprar]'
                }
            },
            {
            'spider': 'nike_snkrs',
            'id': 872973807671996476,
            'tab':'Feed',
            'status': 'esgotado',
            'mensagem' : {
                'inserido': 'Novo produto inserido no estoque[Esgotado]',
                'removido': 'Produto removido do estoque[Esgotado]'
                }
            },
            {
            'spider': 'nike_novidades',
            'id': 872971373859983390,
            'tab': 'Feminino',
            'status': 'Em breve',
            'mensagem' : {
                'inserido': '"Em breve" produto inserido na página[Feminino]',
                'removido': 'Produto removido de "Em breve"[Feminino]'
                }
            },
            {
            'spider': 'nike_novidades',
            'id': 872971373859983390,
            'tab': 'Feminino',
            'status': 'Comprar',
            'mensagem' : {
                'inserido': 'Novo produto disponível para comprar inserido na página[Feminino]',
                'removido': 'Produto removido de "Comprar"[Feminino]'
                }
            },
            {
            'spider': 'nike_novidades',
            'id': 872971373859983390,
            'tab': 'Masculino',
            'status': 'Em breve',
            'mensagem' : {
                'inserido': '"Em breve" produto inserido na página[Masculino]',
                'removido': 'Produto removido de "Em breve"[Masculino]'
                }
            },
            {
            'spider': 'nike_novidades',
            'id': 872971373859983390,
            'tab': 'Masculino',
            'status': 'Comprar',
            'mensagem' : {
                'inserido': 'Novo produto disponível para comprar inserido na página[Masculino]',
                'removido': 'Produto removido de "Comprar"[Masculino]'
                }
            }
        ]
        await run_spider()
        # for channel in channels:
        #     send_to = self.get_channel(channel['id'])
        #     query = 'SELECT name, url, id FROM products where send="avisar" and status="{}"  and spider="{}" and tab="{}"'.format(channel['status'],channel['spider'],channel['tab'])
            

        #     rows = [[str(row[0]).strip(),str(row[1]).strip(), str(row[2]).strip()]  for row in cursor.execute(query)]            
        #     for row in rows:
        #         print('Enviando mensagem para channel {}'.format(channel['id']))
        #         #await send_to.send("{}:\n {}\n{}".format(channel['mensagem']['inserido'], row[0], row[1]))
        #         print("update products set send='avisado' where id='"+row[2]+"'")
        #         cursor.execute("update products set send='avisado' where id='"+row[2]+"'")
        #         database.commit()

        
        

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready() # wait until the bot logs in

client = MyClient()

client.run('ODcyMTMxNjcwMTcyNjQzMzkw.YQlZ6Q.jFepmzwgmN4iFy-nh5p0qX_gQJU')
