import discord
import os
import json
from discord.ext import tasks
try:
    from crawler.data.database import Database
except:
    from data.database import Database

class DiscordClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        # start the task to run in the background                             
        self.database = Database() 
        self.database.avisar_todos()
        self.first_time = self.database.isEmpty()
        try:
            self.channels = json.loads(self.database.get_canais()[0][0].replace("'",'"'))
        except:
            self.channels = {}
        self.my_background_task.start()

    


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
            print(e)                    
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

    async def totais(self, adm_channel):
        send_to = self.get_channel(int(adm_channel))        
        try:            
            results = self.database.totais()   
            result_list = '\n'.join(["{}: {}".format(data[0], data[1]) for data in results])         
            await send_to.send('Segue consolidado:\n{}'.format(result_list))
        except Exception as e:                        
            await send_to.send("Erro ao buscar os dados!")
        return 
    
    async def set_channels(self, channels, adm_channel):
        send_to = self.get_channel(int(adm_channel))
        bk_channels = self.channels
        try:
            config = channels.replace('>configurar','') 
            self.database.configure({"canais" : config})            
            self.channels = json.loads(self.database.get_canais()[0][0].replace("'",'"'))
            await send_to.send("Dados atualizados com sucesso!")            
        except:
            self.database.configure({"canais" : bk_channels})  
            print(self.database.get_canais())
            self.channels = json.loads(self.database.get_canais()[0][0].replace("'",'"'))
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

        if message.content.startswith('>totais'):
           await self.totais(int(adm_channel))

        return

        
    async def on_ready(self):
        print('Logado...')  
        adm_channel = os.environ.get('ADMIN_CHANNEL')    
        send_to = self.get_channel(int(adm_channel))  
        await send_to.send("Tudo pronto e monitorando novos produtos!")
        


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
                    embed.set_thumbnail(url=row['imagens'].split('|')[0])                                               
                    await send_to.send(embed=embed)
                else:
                    description_text='**Código de estilos: ** {}\n**Preço: ** {}\n\n'.format(row['codigo'],row['price'])
                    tamanho_text='**Tamanhos**\n{}'.format(tamanho_desc)
                    links_text='\n**Links Alternativos**\n' if len(row['outros'][1:3])>0 else ''

                    embed = discord.Embed(title=message, url=row['url'], 
                        description='{}{}{}'.format(description_text,tamanho_text,links_text ), color=3066993) #,color=Hex code        
                    embed.set_thumbnail(url=row['imagens'].split('|')[0])                

                    for idx, outros in enumerate(row['outros'][1:3]):                    
                        embed.add_field(name='Link {}'.format(idx+1), value='[**aqui**]({})'.format(outros), inline=True)                    

                    await send_to.send(embed=embed)
                self.database.avisado(row['id'])  


    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready() # wait until the bot logs in



    async def show_help(self, adm_channel):
        send_to = self.get_channel(int(adm_channel))
        helper = '''
lista de comandos:
>delete \{url\}
>buscar \{palavra\}
>canais
>configurar 
{    
  "artwalk_restock": {
    "canal": 0000000000
  }, 
  "artwalk_lancamentos": {
    "canal": 0000000000
  },   
  "artwalk_calendario": {
    "canal": 0000000000
  },
  "gdlp_lancamentos": {
    "canal": 0000000000
  },
  "gdlp_restock": {
    "canal": 0000000000
  }, 
  "magicfeet_lancamentos": {
    "canal": 0000000000
  },
  "magicfeet_snkrs": {
    "canal": 0000000000
  },
  "maze_lancamentos": {
    "canal": 0000000000
  },
  "maze_restock": {
    "canal": 0000000000
  },
  "maze_snkrs": {
    "canal": 0000000000
  },
  "nike_lancamentos": {
    "canal": 0000000000
  },
  "nike_restock": {
    "canal": 0000000000
  },
  "nike_snkrs": {
    "canal": 0000000000
  }
}
'''                    
        await send_to.send(helper)
        return 