import discord, asyncio, subprocess, re, psutil, mcrcon
from discord.ext import commands
from discord import Embed
from pyngrok import ngrok
from config import TOKEN, MC_DIR, ADMIN_ID

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='!help'))
    print(f'logged as {bot.user.name}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f'Sorry {ctx.author.name}, the command you want to use doesnt exist, type !help to see the avaible commands')
    if isinstance(error, commands.CheckFailure):
        await ctx.send(f'Sorry {ctx.author.name}, you have to be ADMIN to use this command.')

admin = ADMIN_ID
def admin_auth(ctx):
    return ctx.author.id in admin

minecraft = None
def minecraft_start():
    global minecraft
    global server
    if minecraft_active():
        return False
    minecraft = subprocess.Popen(['java', '-Xmx4096M', '-Xms4096M', '-jar', 'server.jar', 'nogui'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=MC_DIR, start_new_session=True)
    print(f"PID del servidor: {minecraft.pid}")
    return True

def minecraft_stop():
    global minecraft
    if minecraft_active() == False:
        return False
    minecraft.stdin.write('stop\n')
    minecraft.stdin.flush()
    minecraft.wait()
    minecraft.stdin.close()
    minecraft = None
    return True

def minecraft_active():
    global minecraft
    for proc in psutil.process_iter():
        try:
            if "java" in proc.name() and "-jar" in proc.cmdline() and "server.jar" in proc.cmdline():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


ngrok_tunnel = None
def start_ngrok():
    global ngrok_tunnel
    ngrok_tunnel = ngrok.connect(25565, 'tcp')

def stop_ngrok():
    global ngrok_tunnel
    if ngrok_tunnel is not None:
        ngrok.kill()
        ngrok_tunnel = None

def get_ngrok_url():
    global ngrok_tunnel
    if ngrok_tunnel is not None:
        return ngrok_tunnel.public_url
    return None


@bot.command()
async def start_sv(ctx):
    if minecraft_active():
        await ctx.send("Server is already up")
        return
    await ctx.send(f'The start process begins...')
    minecraft_start()
    start_ngrok()
    print('process started')
    await asyncio.sleep(1)
    url = get_ngrok_url()
    url = url.replace('tcp://', '')
    print(url)
    embed = discord.Embed(title='Minecraft Server', description='Server was initializated succesfully', color=0x00ff00)
    embed.add_field(name='Server IP:', value=f'```{url}```', inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.check(admin_auth)
async def stop_sv(ctx):
    if not minecraft_active():
        await ctx.send(f'The server is already shutdown')
        return
    await ctx.send(f'The server is going to shutdown')
    minecraft_stop()
    stop_ngrok()
    embed = discord.Embed(title='Minecraft Server', description='Server shutdown succesfully', color=0x00ff00)
    await ctx.send(embed=embed)

@bot.command()
async def check_status(ctx):
    if not minecraft_active():
        embed = discord.Embed(title='Server is inactive', description='use "!start_sv" to start it', color=0x00ff00)
        await ctx.send(embed=embed)
        return

    url = get_ngrok_url()
    url = url.replace('tcp://', '')
    embed = discord.Embed(title='El servidor se encuentra activo', color=0x00ff00)
    embed.add_field(name='IP del servidor.', value=f'```{url}```', inline=False)
    await ctx.send(embed=embed)


@bot.command()
@commands.check(admin_auth)
async def comando(ctx, arg):
    if not minecraft_active():
        ctx.send('Sorry, the server is inactive.')
        return
    server = mcrcon.MCRcon("localhost", "1234")
    server.connect()
    response = server.command(f'{arg}')
    embed = discord.Embed(title='Server response', color=0x00ff00)
    embed.add_field(name='Server says: ', value=f'```{response}```', inline=False)
    server.disconnect()
    await ctx.send(embed=embed)


@bot.command()
async def ayuda(ctx):
    embed = discord.Embed(title='Comandos del bot', color=0x00ff00)
    embed.add_field(name='!start_sv', value=f'Start the server', inline=False)
    embed.add_field(name='!check_status', value=f'Check the server status', inline=False)
    embed.add_field(name='(admin only) !stop_sv', value=f'Stop the server', inline=False)
    embed.add_field(name='(admin only) !comando', value=f'Execute a server command', inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)
