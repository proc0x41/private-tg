import asyncio
import uvicorn
from bot import main as bot_main
from webhook import app as webhook_app
import threading
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_webhook():
    """Executa o servidor webhook em uma thread separada"""
    uvicorn.run(webhook_app, host="0.0.0.0", port=8000, log_level="info")

def run_bot():
    """Executa o bot do Telegram"""
    asyncio.run(bot_main())

if __name__ == "__main__":
    logger.info("Iniciando bot do Telegram e servidor webhook...")
    
    # Inicia o servidor webhook em uma thread separada
    webhook_thread = threading.Thread(target=run_webhook, daemon=True)
    webhook_thread.start()
    
    logger.info("Servidor webhook iniciado na porta 8000")
    
    # Inicia o bot do Telegram
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao executar o bot: {e}") 