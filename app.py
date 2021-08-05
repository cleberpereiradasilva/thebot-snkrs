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




def run_spider():
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

        # an attribute we can access from our task
        self.counter = 0

        # start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        channel = self.get_channel(872725671858827304)
        await channel.send("Logado...")


    @tasks.loop(seconds=15) # task runs every 15 seconds
    async def my_background_task(self):
        channel = self.get_channel(872725671858827304) # channel ID goes here
        self.counter += 1                
        run_spider()
        rows = [[str(row[0]).strip(),str(row[1]).strip()]  for row in cursor.execute('SELECT name, send FROM products where send<>"avisado" and status="aviseme"')]
        for row in rows:
            await channel.send("Novo item adicionado em 'avise-me' : {} - {}".format(row[0]))
            cursor.execute("update products set send='avisado' where name='"+row[0]+"'")
            database.commit()

        
        

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready() # wait until the bot logs in

client = MyClient()

client.run('ODcyMTMxNjcwMTcyNjQzMzkw.YQlZ6Q.ct63ztrBdFVJeknttl1cuQAvu1Q')
