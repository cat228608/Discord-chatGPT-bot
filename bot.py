import openai
import discord
from discord.ext import commands
import os
import requests
import asyncio
import gtts 
import urllib.request
from playsound import playsound 
import dc_db

bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())

headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://freetts.ru',
    'Referer': 'https://freetts.ru/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36 OPR/48.0.2685.52',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Opera";v="95", "Chromium";v="109", "Not;A=Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

@bot.command()
async def chat(ctx, *, message):
    if ctx.guild is None:
        await ctx.send("Бот предназначен для использования только на серверах!")
        return
        
    id_server = ctx.message.guild.id
        
    while True:
        print(f"[LOG] - {id_server} использует команду chat.")
        result = dc_db.get_key(id_server)
        if result == 'no key':
            print(f"[LOG] - {id_server} получил ответ 'no key'")
            await ctx.send(f'На вашем сервере нет добавленых api ключей!\nИспользуйте команду /token <key> что бы добавить токен')
            break
        keys = result[0]
        try:
            print(f"[LOG] - {id_server} генерирует текст по ключу '{keys}'.")
            openai.api_key = keys
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"User: {message}",
                max_tokens=2048,
                n=1,
                stop=None,
                temperature=0.7,
            )
            text_respons = response.choices[0].text
            await ctx.send(f'ChatGPT: {text_respons}')
            
            get_status_tts = dc_db.get_tts_status(id_server)
            
            if get_status_tts == 'on':
                print(f"[LOG] - {id_server} начинаю озвучивание текста.")
                voice_channel = ctx.message.author.voice.channel
                if not voice_channel:
                    print(f"[LOG] - {id_server} озвучивание провалилось.")
                    await ctx.send(f'Вы должны находиться в голосовом канале, что бы озвучивание работало корректно!')
                    pass
                data = {
                    'code': '5',
                    'pitch': '0',
                    'rate': '0',
                    'format': 'mp3',
                    'text': f'{text_respons}',
                }
                responses = requests.post('https://freetts.ru/syn.php', headers=headers, data=data)
                site = f"https://freetts.ru/{responses.json()['file']}"
                urllib.request.urlretrieve(site, f"{id_server}.mp3")
                vc = await voice_channel.connect()
                vc.play(discord.FFmpegPCMAudio(f'{id_server}.mp3'))
                while True:
                    await asyncio.sleep(5)

                    if vc.is_playing() == False:
                        await vc.disconnect()
                        break
                break
            if get_status_tts == 'off':
                break
            if get_status_tts == 'error':
                await ctx.send(f'Ошибка получения статуса tts!')
                break
            
        except Exception as er:
            print(f"[ERROR] - {id_server} вызвана ошибка: {er}")
            if str(er) == "You exceeded your current quota, please check your plan and billing details.":
                dc_db.del_key(keys)
            elif "Incorrect API key provided" in str(er):
                dc_db.del_key(keys)
            else:
                break
                       
@bot.command()
async def set_tts(ctx, *, message):
    if ctx.guild is None:
        await ctx.send("Бот предназначен для использования только на серверах!")
        return
        
    id_server = ctx.message.guild.id
    if message != 'on' and message != 'off':
        print(f"[LOG] - {id_server} ввел некоректное значение /set_tts.")
        await ctx.send("Не допустимое значение!\nПример команды: /set_tts <on/off>")
        pass
    else:
        result = dc_db.set_status(id_server, message)
        print(f"[LOG] - {id_server} изменили статус tts на {message}")
        if result == 'not required':
            if message == 'on':
                await ctx.send("Озвучивание текста уже было активно!")
            if message == 'off':
                await ctx.send("Озвучивание текста уже было отключено!")
        elif result == 'good': #Аня ты лучик солнышка в моем мире)
            if message == 'on':
                await ctx.send("Озвучивание текста было успешно включено!")
            if message == 'off':
                await ctx.send("Озвучивание текста успешно отключено!")
        else:
            await ctx.send("Была вызвана ошибка!")
            print(f"[ERROR] - {id_server} была вызвана ошибка: {result}")
        pass
    
@bot.command()
async def token(ctx, *, message):
    if ctx.guild is None:
        await ctx.send("Бот предназначен для использования только на серверах!")
        return
        
    id_server = ctx.message.guild.id
    if message != '' or message != ' ':
        print(f"[LOG] - {id_server} добавляют токен: {message}")
        try:
            openai.api_key = f'{message}'
            openai.Completion.create(engine="text-davinci-002", prompt="What is the capital of France?")
            result = dc_db.add_key(id_server, message)
            if result == 'good':
                await ctx.send(f'Ваш токен успешно добавлен!')
            else:
                await ctx.send(f'Была вызвана ошибка!')
                print(f"[ERROR] - {id_server} была вызвана ошибка: {result}")
        except Exception as er:
            print(f"[ERROR] - {id_server} была вызвана ошибка: {er}")
            await ctx.send("Токен невалидный!")
    else:
        await ctx.send("Токен не может быть пустой!")

bot.run('Тут токен')