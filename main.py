import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View, Button, Modal, TextInput
from keep_alive import keep_alive
import datetime

# ==========================================================
# 🛠️ CONFIGURAÇÃO DE INTENTS E INICIALIZAÇÃO
# ==========================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Banco de dados simulado (em memória) para produtos
PRODUTOS_MOCK = [
    {"titulo": "* N1trada *", "ref": "8-9", "preco": 9.99},
    {"titulo": "N1trada", "ref": "7-99", "preco": 14.99},
    {"titulo": "* Ativação n1trada", "ref": "2-02", "preco": 19.99},
    {"titulo": "Sem título configurado ainda", "ref": "nitro", "preco": 0.00},
    {"titulo": "Dados", "ref": "PUXAR--DADOS", "preco": 4.60}
]

# ==========================================================
# 📋 MODAL NATIVO: CRIANDO PRODUTO (Imagem 2)
# ==========================================================
class CriarProdutoModal(Modal, title="Criando Produto"):
    referencia = TextInput(label="Referencia *", placeholder="EX: gemas-roblox", required=True)
    titulo = TextInput(label="Titulo", placeholder="Insira o título do produto", required=False)
    descricao = TextInput(label="Descrição", style=discord.TextStyle.long, placeholder="Descreva seu produto aqui...", required=False, max_length=2000)
    valor = TextInput(label="Valor", placeholder="Ex: 15.00", required=True)
    canais = TextInput(label="Canais (Opcional)", placeholder="ID do canal para envio", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        # Transforma o valor digitado em float com segurança
        try:
            preco_float = float(self.valor.value.replace(',', '.'))
        except ValueError:
            preco_float = 0.00

        novo_prod = {
            "titulo": self.titulo.value or "Sem título configurado ainda",
            "ref": self.referencia.value,
            "preco": preco_float
        }
        PRODUTOS_MOCK.append(novo_prod)

        embed = discord.Embed(
            title="✅ Produto Criado",
            description=f"O produto **{novo_prod['titulo']}** (Ref: `{novo_prod['ref']}`) foi adicionado com sucesso!",
            color=0x2f3136
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ==========================================================
# 🎛️ VIEWS E MENUS DE SELEÇÃO (INTERFACES EXCLUSIVAS)
# ==========================================================

# Seletor de Gerenciamento do Painel Principal (Imagem 5)
class PainelPrincipalSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Gerenciamento de Produtos", description="Configure ou crie novos produtos da loja.", emoji="📦"),
            discord.SelectOption(label="Configurações de Vendas", description="Ajuste termos, cargos e notificações.", emoji="⚙️"),
            discord.SelectOption(label="Estatísticas Financeiras", description="Veja o rendimento da sua loja.", emoji="📊")
        ]
        super().__init__(placeholder="Selecione uma área para gerenciar...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Gerenciamento de Produtos":
            await enviar_painel_produtos(interaction)
        elif self.values[0] == "Configuracoes de Vendas":
            await enviar_configuracoes_vendas(interaction)
        else:
            await interaction.response.send_message(f"Área '{self.values[0]}' selecionada!", ephemeral=True)

# Seletor de Produtos Cadastrados (Imagem 3)
class ProdutoSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for prod in PRODUTOS_MOCK[:5]: # Exibe até os 5 primeiros
            options.append(discord.SelectOption(
                label=prod["titulo"],
                description=f"Referência: {prod['ref']}",
                emoji="📦"
            ))
        super().__init__(placeholder="Selecione um produto para gerenciar...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        produto_selecionado = self.values[0]
        await interaction.response.send_message(f"⚙️ Abrindo configurações do produto: **{produto_selecionado}**", ephemeral=True)

# ==========================================================
# 🖼️ FUNÇÕES GERADORAS DE TELAS (REPRODUZINDO OS PRINTS)
# ==========================================================

# Tela: Gerenciamento de Produtos (Imagem 4)
async def enviar_painel_produtos(interaction: discord.Interaction):
    total = len(PRODUTOS_MOCK)
    embed = discord.Embed(
        title="⚙️ Gerenciamento de Produtos",
        description="Gerencie ou crie os seus produtos abaixo\n\n📈 **Estatísticas:**\n"
                    f" └ Total de Produtos: **{total}**\n"
                    f" └ Produtos Ativos: **{total}**\n"
                    f" └ Produtos Inativos: **0**\n\n"
                    "Página **1/1**",
        color=0x2f3136
    )
    
    view = View()
    
    # Seletor de Produtos (Imagem 3)
    view.add_item(ProdutoSelect())
    
    # Linha de botões de controle
    btn_anterior = Button(label="Anterior", style=discord.ButtonStyle.green, disabled=True, row=1)
    btn_inicio = Button(label="Início", style=discord.ButtonStyle.grey, disabled=True, row=1)
    btn_proxima = Button(label="Próxima", style=discord.ButtonStyle.green, disabled=True, row=1)
    
    btn_criar = Button(label="Criar Produto", style=discord.ButtonStyle.grey, emoji="➕", row=2)
    btn_buscar = Button(label="Buscar", style=discord.ButtonStyle.grey, emoji="🔍", row=2)
    btn_atualizar = Button(label="Atualizar", style=discord.ButtonStyle.green, emoji="🔄", row=3)
    btn_voltar = Button(label="Voltar", style=discord.ButtonStyle.red, emoji="↩️", row=3)

    # Callback para abrir o modal de criação nativo ao clicar em "Criar Produto"
    async def criar_callback(inter: discord.Interaction):
        await inter.response.send_modal(CriarProdutoModal())
    btn_criar.callback = criar_callback

    # Callback para voltar ao painel de controle principal
    async def voltar_callback(inter: discord.Interaction):
        await enviar_painel_controle(inter)
    btn_voltar.callback = voltar_callback

    view.add_item(btn_anterior)
    view.add_item(btn_inicio)
    view.add_item(btn_proxima)
    view.add_item(btn_criar)
    view.add_item(btn_buscar)
    view.add_item(btn_atualizar)
    view.add_item(btn_voltar)

    await interaction.response.edit_message(embed=embed, view=view)

# Tela: Configurações de Vendas (Imagem 1)
async def enviar_configuracoes_vendas(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 Configurações de Vendas",
        description="Ajuste termos, cargo de clientes e notificações de vendas.\n\n"
                    "👥 **Cargo Clientes:**\n`Clique para selecionar um cargo`\n\n"
                    "📝 **Termos de Compra**\n*Sem termos definidos ainda...*\n\n"
                    "🔔 **Formato da Notificação Pública de Venda:**\n`Notificação normal`\n\n"
                    "*Lembre-se de salvar as alterações, elas ficam disponíveis por até 24 horas.*",
        color=0x2f3136
    )
    view = View()
    view.add_item(Button(label="Alterar Termos", style=discord.ButtonStyle.grey, row=0))
    view.add_item(Button(label="Notificação de Vendas", style=discord.ButtonStyle.grey, emoji="💰", row=0))
    view.add_item(Button(label="Menu Principal", style=discord.ButtonStyle.grey, row=1))
    view.add_item(Button(label="Salvar Alterações", style=discord.ButtonStyle.green, row=1))
    
    await interaction.response.edit_message(embed=embed, view=view)

# Tela: Painel de Controle Principal (Imagem 5)
async def enviar_painel_controle(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏠 Painel de Controle",
        description=f"**Luck System #Forn**\nOlá, {interaction.user.mention}! Aqui está o resumo da sua loja.\n\n"
                    "✨ **Visão Geral**\n"
                    " └ Notificações não lidas: **2**\n"
                    " └ Configurações atualizadas **há 2 meses**\n\n"
                    "❓ **O que deseja gerenciar?**\n"
                    "Selecione uma área no menu abaixo para começar.\n"
                    "*Todas as ações são aplicadas em tempo real.*",
        color=0x2f3136
    )
    embed.set_thumbnail(url="https://i.imgur.com/8Nf9v9e.png") # Ilustração do robozinho azul se quiser usar
    
    view = View()
    view.add_item(PainelPrincipalSelect())
    view.add_item(Button(label="Fechar Loja", style=discord.ButtonStyle.red, emoji="🔒", row=1))
    view.add_item(Button(label="Notificações (2)", style=discord.ButtonStyle.green, emoji="🔔", row=1))
    view.add_item(Button(label="Documentação", style=discord.ButtonStyle.link, url="https://shopeasy.com.br", row=1))
    
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ==========================================================
# ⚡ COMANDOS SLASH ATIVOS
# ==========================================================
@bot.tree.command(name="painel", description="Abre o painel de controle administrativo da sua loja ShopEasy.")
@app_commands.checks.has_permissions(administrator=True)
async def painel_cmd(interaction: discord.Interaction):
    await enviar_painel_controle(interaction)

@bot.tree.command(name="configuracoes", description="Ajustes rápidos de vendas, termos e cargos.")
@app_commands.checks.has_permissions(administrator=True)
async def configuracoes_cmd(interaction: discord.Interaction):
    # Envia a tela de configurações de vendas diretamente
    embed = discord.Embed(
        title="🛒 Configurações de Vendas",
        description="Ajuste termos, cargo de clientes e notificações de vendas.",
        color=0x2f3136
    )
    view = View()
    view.add_item(Button(label="Alterar Termos", style=discord.ButtonStyle.grey, row=0))
    view.add_item(Button(label="Salvar Alterações", style=discord.ButtonStyle.green, row=1))
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ==========================================================
# 🚀 MONITORAMENTO E STARTUP
# ==========================================================
@bot.event
async def on_ready():
    print(f"🤖 ShopEasy / Luck System carregado como {bot.user}!")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Sincronizados {len(synced)} comandos slash com sucesso.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

keep_alive()
bot.run("MTUyNjc3MjQwNTg4NjkxMDQ3NA.GzWeZT.DuORxzaAnl9z9A4QD5QviiWgxfny611LN6fcIc")
    
