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
intents.members = True  # Necessário para os comandos de moderação (ban, kick, mute)
bot = commands.Bot(command_prefix="!", intents=intents)


# ==========================================================
# 🛡️ SISTEMA DE MODERAÇÃO (COMANDOS SLASH)
# ==========================================================

# 1. Comando: Banir Usuário (/ban)
@bot.tree.command(name="ban", description="🛡️ [Moderação] Bane um membro do servidor")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo especificado"):
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
        await interaction.response.send_message(f"❌ Não consegui banir o membro. Erro: {e}", ephemeral=True)


# 2. Comando: Expulsar Usuário (/kick)
@bot.tree.command(name="kick", description="🛡️ [Moderação] Expulsa um membro do servidor")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo especificado"):
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
        await interaction.response.send_message(f"❌ Não consegui expulsar o membro. Erro: {e}", ephemeral=True)


# 3. Comando: Silenciar Usuário (/mute)
@bot.tree.command(name="mute", description="🛡️ [Moderação] Silencia um usuário temporariamente (Timeout)")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, membro: discord.Member, tempo_minutos: int, motivo: str = "Sem motivo"):
    try:
        duracao = datetime.timedelta(minutes=tempo_minutos)
        await membro.timeout(duracao, reason=motivo)
        embed = discord.Embed(
            title="🔇 Usuário Silenciado",
            description=f"{membro.mention} foi colocado de castigo.",
            color=discord.Color.gold()
        )
        embed.add_field(name="Duração:", value=f"{tempo_minutos} minutos", inline=True)
        embed.add_field(name="Motivo:", value=motivo, inline=True)
        embed.set_footer(text=f"Moderador: {interaction.user}")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Não consegui silenciar o usuário. Erro: {e}", ephemeral=True)


# 4. Comando: Limpar Chat (/clear)
@bot.tree.command(name="clear", description="🧹 [Moderação] Limpa mensagens do chat atual")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, quantidade: int):
    if quantidade < 1 or quantidade > 100:
        return await interaction.response.send_message("❌ Escolha um número entre 1 e 100.", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True) # Evita timeout da API do Discord
    deleted = await interaction.channel.purge(limit=quantidade)
    await interaction.followup.send(f"🧹 Chat limpo! Removi `{len(deleted)}` mensagens.", ephemeral=True)


# ==========================================================
# 📦 SISTEMA DE VENDAS (LOCK SYSTEM) - INTERFACES & MODAL
# ==========================================================

# Modal de Criação de Produto (O formulário interativo)
class CriarProdutoModal(discord.ui.Modal, title="📦 Criando Produto"):
    referencia = discord.ui.TextInput(
        label="Referencia *", 
        placeholder="EX: gemas-roblox",
        required=True
    )
    titulo = discord.ui.TextInput(
        label="Titulo", 
        placeholder="Título visível do produto",
        required=False
    )
    descricao = discord.ui.TextInput(
        label="Descrição", 
        style=discord.TextStyle.paragraph,
        placeholder="Escreva detalhes do produto aqui...",
        required=False,
        max_length=2000
    )
    valor = discord.ui.TextInput(
        label="Valor", 
        placeholder="Ex: 4.60",
        required=False
    )
    canais = discord.ui.TextInput(
        label="Canais", 
        placeholder="ID do canal onde o produto será postado",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        ref = self.referencia.value
        tit = self.titulo.value or "Sem título"
        val = self.valor.value or "0.00"
        
        embed = discord.Embed(
            title="✅ Produto Criado no Lock System!",
            description=f"**Referência:** `{ref}`\n**Título:** {tit}\n**Valor:** R$ {val}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# Menu de Gerenciamento de Produtos (Com paginação)
class GerenciadorProdutosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.select(
        placeholder="📦 Selecione um produto para gerenciar",
        options=[
            discord.SelectOption(label="N1trada", description="Referência: 7-99", emoji="⚡"),
            discord.SelectOption(label="Ativação n1trada", description="Referência: 2-02", emoji="💎"),
            discord.SelectOption(label="Dados", description="Referência: PUXAR--DADOS", emoji="🔍")
        ]
    )
    async def select_product(self, interaction: discord.Interaction, select: discord.ui.Select):
        produto_nome = select.values[0]
        
        embed = discord.Embed(
            title=f"📦 Editando: {produto_nome}",
            description="Use as opções abaixo para alterar as configurações do produto.",
            color=0x2f3136
        )
        await interaction.response.edit_message(embed=embed, view=MenuEdicaoProdutoView())

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.grey, disabled=True, row=1)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="Início", style=discord.ButtonStyle.grey, disabled=True, row=1)
    async def home_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="Próxima", style=discord.ButtonStyle.grey, disabled=True, row=1)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="Criar Produto", style=discord.ButtonStyle.green, emoji="➕", row=2)
    async def create_product(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CriarProdutoModal())

    @discord.ui.button(label="Voltar", style=discord.ButtonStyle.red, row=2)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await voltar_painel_principal(interaction)


# Menu de Edição para o Produto Selecionado
class MenuEdicaoProdutoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Voltar ao Gerenciamento", style=discord.ButtonStyle.red)
    async def back_to_management(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚙️ Gerenciamento de Produtos",
            description="Gerencie ou crie os seus produtos abaixo.\n\n**Estatísticas:**\n└ Total de Produtos: **3**\n└ Ativos: **3**",
            color=0x2f3136
        )
        await interaction.response.edit_message(embed=embed, view=GerenciadorProdutosView())


# Painel de Controle Principal (Home)
class PainelPrincipalView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="🏠 Selecione uma área para gerenciar",
        options=[
            discord.SelectOption(label="Gerenciamento de Produtos", description="Crie, edite ou remova produtos", emoji="📦"),
            discord.SelectOption(label="Configurações de Vendas", description="Ajuste termos e cargos", emoji="⚙️")
        ]
    )
    async def main_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        area = select.values[0]
        
        if area == "Gerenciamento de Produtos":
            embed = discord.Embed(
                title="⚙️ Gerenciamento de Produtos",
                description="Gerencie ou crie os seus produtos abaixo.\n\n**Estatísticas:**\n└ Total de Produtos: **3**\n└ Ativos: **3**",
                color=0x2f3136
            )
            await interaction.response.edit_message(embed=embed, view=GerenciadorProdutosView())
            
        elif area == "Configurações de Vendas":
            await interaction.response.send_message("⚙️ Menu de configurações de vendas em breve...", ephemeral=True)

    @discord.ui.button(label="Fechar Loja", style=discord.ButtonStyle.red, emoji="🔒")
    async def close_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 A loja do Lock System foi fechada temporariamente!", ephemeral=True)


# Função Auxiliar de Navegação
async def voltar_painel_principal(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔒 Lock System - Painel de Controle",
        description=f"Olá, {interaction.user.mention}! Aqui está o resumo da sua loja.\n\n**Visão Geral**\n└ Status: 🟢 **Online**\n└ Notificações pendentes: **0**",
        color=0x2f3136
    )
    await interaction.response.edit_message(embed=embed, view=PainelPrincipalView())


# ==========================================================
# 🚀 COMANDOS GERAIS & INICIALIZAÇÃO
# ==========================================================

# Comando Slash principal para abrir a loja
@bot.tree.command(name="painel", description="Acesse o Painel de Controle do seu Lock System")
async def painel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔒 Lock System - Painel de Controle",
        description=f"Olá, {interaction.user.mention}! Aqui está o resumo da sua loja.\n\n**Visão Geral**\n└ Status: 🟢 **Online**\n└ Notificações pendentes: **0**",
        color=0x2f3136
    )
    # Abre apenas para o administrador de forma efêmera (oculta)
    await interaction.response.send_message(embed=embed, view=PainelPrincipalView(), ephemeral=True)


@bot.event
async def on_ready():
    print(f"🤖 Lock System online como {bot.user}!")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Sincronizados {len(synced)} comandos de barra (Slash).")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


# Tratamento de erro caso alguém tente moderar sem permissão
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Você não tem permissões administrativas para executar este comando!", ephemeral=True)

# Liga o Keep Alive do Render e inicia o bot
keep_alive()
bot.run("SEU_TOKEN_AQUI")  # <--- COLOQUE SEU TOKEN DO DISCORD AQUI!
        
