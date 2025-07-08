#!/usr/bin/env python3
"""
Script de inicialização do Bot do Telegram - Grupo Privado Pago
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    try:
        import aiogram
        import fastapi
        import mercadopago
        import uvicorn
        logger.info("Todas as dependências estão instaladas")
        return True
    except ImportError as e:
        logger.error(f"Dependência não encontrada: {e}")
        logger.error("Execute: pip install -r requirements.txt")
        return False

async def main():
    """Função principal"""
    logger.info("Iniciando Bot do Telegram - Grupo Privado Pago")
    
    # Verificações iniciais
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # Importa os módulos principais
        from bot import main as bot_main
        from webhook import app as webhook_app
        import uvicorn
        import threading
        
        logger.info("Módulos carregados com sucesso")
        
        # Inicia o servidor webhook em uma thread separada
        def run_webhook():
            uvicorn.run(webhook_app, host="0.0.0.0", port=8000, log_level="info")
        
        webhook_thread = threading.Thread(target=run_webhook, daemon=True)
        webhook_thread.start()
        
        logger.info("Servidor webhook iniciado na porta 8000")
        logger.info("Bot iniciado com sucesso!")
        logger.info("Pressione Ctrl+C para parar")
        
        # Inicia o bot
        await bot_main()
        
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao executar o bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Verifica se o arquivo .env existe
    if not Path('.env').exists():
        logger.error("Arquivo .env não encontrado!")
        logger.error("Copie env.example para .env e configure as variáveis")
        sys.exit(1)
    
    # Executa o bot
    asyncio.run(main()) 