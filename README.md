# Bot do Telegram - Grupo Privado Pago

Bot completo para gerenciar acesso a grupo privado pago com integração Mercado Pago PIX.

## Funcionalidades

- Funil de vendas com planos mensal/anual
- Pagamento PIX automático via Mercado Pago
- Webhook para confirmação de pagamentos
- Gestão automática de assinaturas
- Expulsão automática de usuários expirados
- Notificações de renovação
- Comandos admin para relatórios

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente:
```bash
cp env.example .env
# Edite o arquivo .env com suas configurações
```

3. Execute o bot:
```bash
python main.py
```

## Configuração

### Variáveis de Ambiente (.env)

```env
BOT_TOKEN=seu_token_do_bot
ADMIN_ID=seu_id_do_telegram
MP_ACCESS_TOKEN=seu_access_token_mp
MP_PUBLIC_KEY=seu_public_key_mp
GROUP_ID=id_do_grupo
GROUP_INVITE_LINK=link_do_grupo
WEBHOOK_URL=https://seu-dominio.com
```

### Passos de Configuração

1. **Criar bot no Telegram** via @BotFather
2. **Configurar Mercado Pago** com webhook
3. **Criar grupo privado** e adicionar bot como admin
4. **Configurar servidor público** para webhook

## Comandos

- `/start` - Iniciar bot e escolher plano
- `/status` - Ver status da assinatura
- `/vendas` - Relatório de vendas (admin)

## Estrutura

- `bot.py` - Bot principal
- `payments.py` - Integração Mercado Pago
- `webhook.py` - Servidor webhook
- `database.py` - Banco de dados SQLite
- `config.py` - Configurações
- `main.py` - Execução principal 