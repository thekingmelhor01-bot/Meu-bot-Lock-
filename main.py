import discord
from discord import app_commands
import json
import os
import datetime
from typing import Optional
import asyncio
from fastapi import FastAPI, Request, HTTPException
import uvicorn
import requests

# Inicialização do Servidor Web (FastAPI) para o Webhook da AbacatePay
app = FastAPI()

class LockStoreBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = LockStoreBot()
DATA_FILE = "store_data.json"

# --- CONFIGURAÇÕES DE API ---
# Pega o token da AbacatePay que você configurará no Render
ABACATEPAY_KEY = os.getenv("ABACATEPAY_KEY") 

# --- FUNÇÕES DE BANCO DE DADOS LOCAL (JSON) ---
def carregar_dados():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return resetar_dados()
    return resetar_dados()

def resetar_dados():
    default = {
        "usuarios": {},
        "catalogo": {},
        "cupons": {},
    }
    salvar_dados(default)
    return default

def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- WEBHOOK DA ABACATEPAY (ENTREGA AUTOMÁTICA) ---
@app.post("/webhook")
async def receber_pagamento(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido")
    
    # 1. Verifica se o evento recebido é de pagamento concluído
    if payload.get("event") == "checkout.completed":
        data = payload.get("data", {})
        metadata = data.get("metadata", {})
        
        # Recuperamos o ID do Discord do comprador e o produto que passamos na criação
        user_id = metadata.get("user_id")
        nome_produto = metadata.get("product_name")
        
        if user_id and nome_produto:
            user_id = int(user_id)
            dados = carregar_dados()
            catalogo = dados["catalogo"]
            produto_formatado = nome_produto.title()
            
            if produto_formatado in catalogo:
                produto = catalogo[produto_formatado]
                estoque = produto.get("estoque", [])
                
                # Se tiver estoque disponível
                if len(estoque) > 0:
                    entrega = estoque.pop(0)  # Pega e remove o primeiro item do estoque (linha)
                    dados["catalogo"][produto_formatado]["estoque"] = estoque
                    salvar_dados(dados)
                    
                    # Tenta enviar o produto diretamente na DM do usuário no Discord
                    try:
                        user = await bot.fetch_user(user_id)
                        embed_dm = discord.Embed(
                            title="📦 Pagamento Confirmado - Entrega Automática!",
                            description=f"Seu pagamento via **AbacatePay** foi aprovado com sucesso!\n\nAqui está o seu produto:\n\n```\n{entrega}\n```",
                            color=0x2ecc71
                        )
                        embed_dm.set_footer(text="Obrigado por comprar conosco!")
                        await user.send(embed=embed_dm)
                        print(f"Produto {produto_formatado} entregue com sucesso para o usuário {user_id}.")
                    except Exception as e:
                        print(f"Não consegui enviar a DM para o usuário {user_id}: {e}")
                else:
                    # Caso o estoque acabe na fração de segundo do pagamento
                    try:
                        user = await bot.fetch_user(user_id)
                        await user.send(f"⚠️ Seu pagamento para **{produto_formatado}** foi aprovado, mas o estoque esgotou nesse meio tempo! Entre em contato com o suporte para receber manualmente.")
                    except Exception:
                        pass
                    print(f"Estoque esgotado para {produto_formatado} comprado por {user_id}")
                    
    return {"status": "success"}

@app.get("/")
def home():
    return {"status": "Bot e Webhook da AbacatePay Rodando!"}

# --- COMANDO PRINCIPAL: GERAR COBRANÇA (COMPRAR) ---
@bot.tree.command(name="comprar", description="Gera um link de pagamento Pix/Cartão para comprar um produto")
async def comprar(interaction: discord.Interaction, item: str):
    dados = carregar_dados()
    catalogo = dados["catalogo"]
    
    item_formatado = item.title()
    if item_formatado not in catalogo:
        await interaction.response.send_message(f"❌ O produto **{item}** não existe no catálogo!", ephemeral=True)
        return
        
    produto = catalogo[item_formatado]
    estoque = produto.get("estoque", [])
    
    # Verifica se há estoque antes de criar a cobrança
    if len(estoque) == 0:
        await interaction.response.send_message(f"❌ O produto **{item_formatado}** está sem estoque no momento!", ephemeral=True)
        return

    # Evita erros caso você não tenha colocado a Chave de API no Render ainda
    if not ABACATEPAY_KEY:
        await interaction.response.send_message("❌ Erro no sistema: A chave da API da AbacatePay não foi configurada pelo administrador.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True) # Dá tempo para o bot carregar a API da AbacatePay

    # Converte o preço do seu catálogo para centavos (A AbacatePay trabalha em centavos: R$ 10,00 = 1000)
    preco_centavos = int(produto["preco"] * 100)

    # Criação do checkout na API da AbacatePay
    url = "https://api.abacatepay.com/v1/checkout/create"
    headers = {
        "Authorization": f"Bearer {ABACATEPAY_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "frequency": "ONE_TIME",
        "methods": ["PIX"], # focado em PIX
        "products": [
            {
                "externalId": item_formatado.lower().replace(" ", "-"),
                "name": item_formatado,
                "quantity": 1,
                "price": preco_centavos
            }
        ],
        "returnUrl": "https://discord.com", # Para onde o cliente vai após pagar
        # O segredo está aqui: salvamos quem está comprando e o que está comprando
        "metadata": {
            "user_id": str(interaction.user.id),
            "product_name": item_formatado
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        
        # Se a criação deu certo, pegamos o link de pagamento
        if response.status_code == 200 or response.status_code == 201:
            checkout_url = res_data["data"]["url"]
            
            embed = discord.Embed(
                title="💳 Quase lá! Complete seu pagamento",
                description=f"Você está adquirindo: **{item_formatado}**\nValor: **R$ {produto['preco']:.2f}**\n\nClique no botão abaixo para pagar via Pix na AbacatePay. Assim que pagar, seu produto será enviado automaticamente aqui na sua DM!",
                color=0x3498db
            )
            
            # Botão clicável bonito no Discord para ir ao pagamento
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Pagar Agora (PIX)", url=checkout_url, style=discord.ButtonStyle.link))
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            erro_msg = res_data.get("error", "Erro desconhecido")
            await interaction.followup.send(f"❌ Erro ao gerar pagamento na AbacatePay: {erro_msg}", ephemeral=True)
            
    except Exception as e:
        await interaction.followup.send(f"❌ Erro de conexão com o gateway de pagamento: {e}", ephemeral=True)

# --- COMANDOS DE MODERAÇÃO ---
class ModeracaoGrupo(app_commands.Group):
    def __init__(self):
        super().__init__(name="mod", description="Comandos de moderação")

    @app_commands.command(name="kick", description="Expulsa um membro")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membro: discord.Member, motivo: Optional[str] = "Não especificado"):
        await membro.kick(reason=motivo)
        await interaction.response.send_message(f"👞 {membro.mention} foi expulso! Motivo: {motivo}")

    @app_commands.command(name="ban", description="Bane um membro")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membro: discord.Member, motivo: Optional[str] = "Não especificado"):
        await membro.ban(reason=motivo)
        await interaction.response.send_message(f"🔨 {membro.mention} foi banido! Motivo: {motivo}")

    @app_commands.command(name="mute", description="Silencia um membro")
    @app_commands.default_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: Optional[str] = "Não especificado"):
        duracao = datetime.timedelta(minutes=minutos)
        await membro.timeout(duracao, reason=motivo)
        await interaction.response.send_message(f"🔇 {membro.mention} silenciado por {minutos}m! Motivo: {motivo}")

# --- COMANDOS DO PRODUTO E ESTOQUE ---
class CatalogoGrupo(app_commands.Group):
    def __init__(self):
        super().__init__(name="catalogo", description="Gerenciar produtos")

    @app_commands.command(name="criar", description="Cadastra um produto")
    @app_commands.default_permissions(administrator=True)
    async def criar(self, interaction: discord.Interaction, nome: str, preco_reais: float, descricao: str):
        dados = carregar_dados()
        dados["catalogo"][nome.title()] = {"preco": preco_reais, "descricao": descricao, "estoque": []}
        salvar_dados(dados)
        await interaction.response.send_message(f"📦 Produto **{nome.title()}** cadastrado por **R$ {preco_reais:.2f}**!")

    @app_commands.command(name="estoque", description="Adiciona estoque por linhas")
    @app_commands.default_permissions(administrator=True)
    async def estoque(self, interaction: discord.Interaction, produto: str, itens: str):
        dados = carregar_dados()
        prod = produto.title()
        if prod not in dados["catalogo"]:
            await interaction.response.send_message("❌ Produto inexistente!", ephemeral=True)
            return
        novas_linhas = [l.strip() for l in itens.split("\n") if l.strip()]
        dados["catalogo"][prod]["estoque"].extend(novas_linhas)
        salvar_dados(dados)
        await interaction.response.send_message(f"✅ Adicionado {len(novas_linhas)} itens ao estoque de **{prod}**!")

# Registro dos Grupos no Bot
bot.tree.add_command(ModeracaoGrupo())
bot.tree.add_command(CatalogoGrupo())

# --- EXECUÇÃO EM SEGUNDO PLANO ---
async def rodar_webserver():
    config = uvicorn.Config(app, host="0.0.0.0", port=10000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("ERRO: Variável de ambiente 'DISCORD_TOKEN' não configurada!")
        return
    
    await asyncio.gather(
        bot.start(token),
        rodar_webserver()
    )

if __name__ == "__main__":
    asyncio.run(main())
          
