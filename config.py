import os
from dotenv import load_dotenv

load_dotenv()

# Configurações do Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Configurações do Mercado Pago
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
MP_PUBLIC_KEY = os.getenv("MP_PUBLIC_KEY")

# Configurações do Grupo
GROUP_ID = os.getenv("GROUP_ID")
GROUP_INVITE_LINK = os.getenv("GROUP_INVITE_LINK")

# Configurações do Webhook
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"

# Configurações do Banco de Dados
DATABASE_PATH = "subscriptions.db"

# Configurações de Planos
PLANS = {
    "monthly": {
        "name": "Plano Mensal",
        "price": 29.90,
        "days": 30
    },
    "yearly": {
        "name": "Plano Anual",
        "price": 299.90,
        "days": 365
    }
}

# Configurações de Notificações
RENEWAL_WARNING_DAYS = [7, 3, 1]  # Dias antes do vencimento para enviar avisos 