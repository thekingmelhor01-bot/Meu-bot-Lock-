import discord
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive
import datetime

# ==========================================================
# 🛠️ CONFIGURAÇÃO DE INTENTS E INICIALIZAÇÃO
# ==========================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ==========================================================
# 🛡️ GRUPO DE COMANDOS DE MODERAÇÃO (/mod ...)
# ==========================================================
class ModGroup(app_commands.Group, name="mod", description="Comandos de moderação do servidor"):
    
    # Subcomando: /mod ban
    @app_commands.command(name="ban", description="Bane um membro")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo especificado"):
        try:
            await membro.ban(reason=motivo)
            embed = discord.Embed(
                title="🔨 Usuário Banido",
                description=f"O membro {membro.mention} foi banido com sucesso.",
                color=discord.Color.red()
            )
            embed.add_field(name="Motivo:", value=motivo, inline=False)
            embed.set_footer(text=f"Moderador: {interaction.user}")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao banir: {e}", ephemeral=True)

    # Subcomando: /mod kick
    @app_commands.command(name="kick", description="Expulsa um membro")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo especificado"):
        try:
            await membro.kick(reason=motivo)
            embed = discord.Embed(
                title="👢 Usuário Expulso",
                description=f"O membro {membro.mention} foi expulso do servidor.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Motivo:", value=motivo, inline=False)
            embed.set_footer(text=f"Moderador: {interaction.user}")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao expulsar: {e}", ephemeral=True)

    # Subcomando: /mod mute
    @app_commands.command(name="mute", description="Silencia um membro")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, membro: discord.Member, tempo_minutos: int, motivo: str = "Sem motivo"):
        try:
            duracao = datetime.timedelta(minutes=tempo_minutos)
            await membro.timeout(duracao, reason=motivo)
            embed = discord.Embed(
                title="🔇 Usuário Silenciado",
                description=f"{membro.mention} foi silenciado com sucesso.",
                color=discord.Color.gold()
            )
            embed.add_field(name="Duração:", value=f"{tempo_minutos} minutos", inline=True)
            embed.add_field(name="Motivo:", value=motivo, inline=True)
            embed.set_footer(text=f"Moderador: {interaction.user}")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao silenciar: {e}", ephemeral=True)

# Adiciona o grupo /mod ao bot
bot.tree.add_command(ModGroup())


# ==========================================================
# 💳 COMANDO DE COMPRA E ESTILO LOCK SYSTEM (/comprar)
# ==========================================================

@bot.tree.command(name="comprar", description="Gera um link de pagamento Pix/Cartão")
async def comprar(interaction: discord.Interaction):
    # Banner e estilo do embed de compra
    embed = discord.Embed(
        title="⚡ COMPRAR NITRO LINK",
        description="Clique no botão abaixo para gerar o seu pagamento e receber o produto automaticamente.",
        color=0x2f3136
    )
    embed.set_image(url="https://i.imgur.com/your_banner_here.png") # Coloque o link do seu banner de ativação aqui se quiser
    
    # Botão de compra interativo
    view = discord.ui.View()
    botao_comprar = discord.ui.Button(
        label="Comprar", 
        style=discord.ButtonStyle.green, 
        emoji="🛒",
        custom_id="btn_comprar_fluxo"
    )
    
    # Callback quando clicar em "Comprar"
    async def comprar_callback(inter: discord.Interaction):
        # Aqui geramos o fluxo do Lock System (Modal, Pix ou carrinho temporário)
        await inter.response.send_message("⚙️ Gerando sua chave/PIX de pagamento... Aguarde!", ephemeral=True)
        
    botao_comprar.callback = comprar_callback
    view.add_item(botao_comprar)
    
    await interaction.response.send_message(embed=embed, view=view)


# ==========================================================
# 📦 OUTROS PAINÉIS DO LOCK SYSTEM (PAINEL DE ADMIN)
# ==========================================================

# Comando Slash para o painel administrativo de controle interno
@bot.tree.command(name="painel", description="Acesse o Painel de Controle interno da sua loja")
@app_commands.checks.has_permissions(administrator=True)
async def painel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔒 Lock System - Painel de Controle",
        description=f"Olá, {interaction.user.mention}! Painel administrativo.",
        color=0x2f3136
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================================
# 🚀 INICIALIZAÇÃO DO BOT
# ==========================================================
@bot.event
async def on_ready():
    print(f"🤖 Lock System online como {bot.user}!")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Sincronizados {len(synced)} comandos slash.")
    except Exception as e:
        print(f"Erro de sincronização: {e}")

# Liga o keep_alive e o bot
keep_alive()
bot.run("MTUyNjc3MjQwNTg4NjkxMDQ3NA.GzWeZT.DuORxzaAnl9z9A4QD5QviiWgxfny611LN6fcIc") # <--- Lembre de colar seu token aqui!
            
