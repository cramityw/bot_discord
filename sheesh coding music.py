import asyncio
import discord
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl
from random import choice

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


client = commands.Bot(command_prefix='!')
client.remove_command('help')

status = ['я сплю', 'отдыхаю', 'танцую']
que = [] 
loop = False 

#проверка бота
@client.event 
async def on_ready():
    change_status.start()
    print('Бот онлайн!')

#выдает задержку
@client.command()
async def ping(ctx):
    await ctx.send(f'**Pong!** Задержка: {round(client.latency * 1000)}мс')

#команда для общения
@client.command()
async def hello(ctx):
    responses = ['я сплю', 'привет', 'пока', 'спокойной ночи']
    await ctx.send(choice(responses))

#команда для очистки последних сообщений
@client.command()
async def clear(ctx, amount = 200):
    await ctx.channel.purge(limit = amount)

#при использовании этой команды выводит несколько фраз
@client.command()
async def credits(ctx):
    await ctx.send('`Сделано для курсовой`')
    await ctx.send('`Поставьте 5, пожалуйста`')

#функция для присоединения бота к голосовому каналу
@client.command()
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("Ты не подключен к голосову каналу")
        return
    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

#функция для того, чтобы бот вышел из голосовго канала
@client.command()
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()

#фунция зацикливания
@client.command()
async def loopmode(ctx):
    global loop

    if loop:
        await ctx.send('Мод зацикливания сейчас `Выключен`')
        loop = False;

    else:
        await ctx.send('Мод зацикливания сейчас `Включен`')
        loop = True

#функция для воспроизведения музыки
@client.command()
async def play(ctx):
    global que

    if not ctx.message.author.voice:
        await ctx.send("Ты не подключен к голосовому каналу")
        return

    elif len(que) == 0:
        await ctx.send('В очереди пусто! Используй `!queue`, чтобы добавить песню!')

    else:
        try:
            channel = ctx.message.author.voice.channel 
            await channel.connect()
        except: pass

    server = ctx.message.guild
    voice_channel = server.voice_client

    while queue:
        try:
            while voice_channel.is_playing() or voice_channel.is_paused():
                await asyncio.sleep(2)
                pass

        except AttributeError:
            pass

        try:
            async with ctx.typing():
                player = await YTDLSource.from_url(que[0], loop=client.loop)
                voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

                if loop:
                    que.append(que[0])

                del(que[0])

            await ctx.send('**Сейчас играет:** {}'.format(player.title))
        except: break    

#команда которая прекращает играть эту песню
@client.command()
async def stop(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.stop()

#для остановки музыки в голосом канале
@client.command()
async def pause(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.pause()

#для продолжения воспроизведения музыки
@client.command()
async def resume(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.resume()

#создаем очередь
@client.command()
async def queue(ctx, *, url):
    global que

    que.append(url)
    await ctx.send(f'`{url}` добавлена в очередь!')

#для удаления песни из списка очереди
@client.command()
async def remove(ctx, number):
    global que

    try:
        del(que[int(number)])
        await ctx.send(f'Сейчас ваша очередь `{que}!`')
    
    except:
        await ctx.send('Ваша очередь пуста или такого номера нет в очереди :(')

#для просмотра списка очереди
@client.command(pass_context = True)
async def view(ctx):
    await ctx.send(f'Сейчас очередь состоит состоит из `{que}` !')




#функция для вывода нового окна help
@client.command(pass_context = True)
async def help(ctx):
    prefix = '!'
    emb = discord.Embed(title = '**Навигация по командам**')

    emb.add_field (name = '{}join'.format(prefix), value = 'Команда, чтобы бот зашел в ваш голосовой канал')#добавляем команды и описание, которые будут высвечиваться при вызове этого окна
    emb.add_field (name = '{}leave'.format(prefix), value = 'Команда, чтобы бот покинул ваш голосовой канал')

    emb.add_field (name = '{}play'.format(prefix), value = 'Эта команда воспроизводит музыку')
    emb.add_field (name = '{}stop'.format(prefix), value = 'Эта команда пропускает песню, которую ты сейчас слушаешь')
    emb.add_field (name = '{}pause'.format(prefix), value = 'Команда для остановки воспроизведния песни')
    emb.add_field (name = '{}resume'.format(prefix), value = 'Команда для продолжения воспроизводения песни')
    emb.add_field (name = '{}queue'.format(prefix), value = 'Команда для добавлении песни в очередь')
    emb.add_field (name = '{}loopmode'.format(prefix), value = 'Команда зацикливает песни в очереди')
    emb.add_field (name = '{}view'.format(prefix), value = 'Команда для просмотра списка очереди')
    emb.add_field (name = '{}remove'.format(prefix), value = 'Эта команда удаляет песню из очереди')

    emb.add_field (name = '{}hello'.format(prefix), value = 'Команда для общения')
    emb.add_field (name = '{}clear'.format(prefix), value = 'Убирает нужное количество сообщений')
    emb.add_field (name = '{}ping'.format(prefix), value = 'Эта команда показывает задержку')
    emb.add_field (name = '{}credits'.format(prefix), value = 'Эта команда показывает информацию о разработчике')

    await ctx.send (embed = emb)

@tasks.loop(seconds=180)
async def change_status():
    await client.change_presence(activity=discord.Game(choice(status)))

client.run('')