import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive # Certifique-se que seu keep_alive.py está na mesma pasta

# Configuração de Intenções (Obrigatório para os comandos funcionarem)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    try:
        # ISSO É O QUE FAZ OS COMANDOS APARECEREM!
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

# Comando de Painel
@bot.tree.command(name="painel", description="Mostra o painel de configurações")
async def painel(interaction: discord.Interaction):
    await interaction.response.send_message("Aqui está o seu painel de controle!", ephemeral=True)

# Comando de Exemplo (Kick)
@bot.tree.command(name="kick", description="Expulsa um membro")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member):
    await member.kick()
    await interaction.response.send_message(f"{member.name} foi expulso.")

# Inicia o servidor web do keep_alive e o bot
keep_alive()
bot.run(os.environ['DISCORD_TOKEN'])
