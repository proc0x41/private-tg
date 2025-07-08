import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, ADMIN_ID, GROUP_INVITE_LINK, RENEWAL_WARNING_DAYS
from database import Database
from payments import PaymentManager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização do bot
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Instâncias dos módulos
db = Database("subscriptions.db")
payment_manager = PaymentManager()

# Estados para o FSM
class SubscriptionStates(StatesGroup):
    choosing_plan = State()
    processing_payment = State()

# Função para criar teclado de planos
def create_plans_keyboard():
    """Cria teclado inline com os planos disponíveis"""
    builder = InlineKeyboardBuilder()
    
    plans = payment_manager.get_all_plans()
    for plan_id, plan_info in plans.items():
        builder.add(InlineKeyboardButton(
            text=f"{plan_info['name']} - R$ {plan_info['price']:.2f}",
            callback_data=f"plan_{plan_id}"
        ))
    
    builder.adjust(1)
    return builder.as_markup()

# Função para criar teclado de pagamento
def create_payment_keyboard(payment_id: str):
    """Cria teclado para o pagamento"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✅ Pagamento Confirmado",
        callback_data=f"confirm_payment_{payment_id}"
    ))
    
    builder.add(InlineKeyboardButton(
        text="❌ Cancelar",
        callback_data="cancel_payment"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Comando inicial do bot"""
    user_id = message.from_user.id
    
    # Verifica se o usuário já tem uma assinatura ativa
    subscription = await db.get_subscription(user_id)
    
    if subscription:
        # Usuário já tem assinatura ativa
        days_left = (subscription["expiration_date"] - datetime.now()).days
        
        await message.answer(
            f"🎉 Olá! Você já possui uma assinatura ativa!\n\n"
            f"📅 Plano: {subscription['plan_type']}\n"
            f"⏰ Dias restantes: {days_left}\n"
            f"📅 Expira em: {subscription['expiration_date'].strftime('%d/%m/%Y')}\n\n"
            f"🔗 Link do grupo: {GROUP_INVITE_LINK}\n\n"
            f"Use /status para ver mais detalhes da sua assinatura."
        )
    else:
        # Usuário não tem assinatura, mostra planos
        await message.answer(
            "🚀 Bem-vindo ao Grupo Privado!\n\n"
            "Para acessar nosso conteúdo exclusivo, escolha um dos planos abaixo:\n\n"
            "💎 Acesso a conteúdo premium\n"
            "📱 Suporte exclusivo\n"
            "🎯 Estratégias avançadas\n"
            "📊 Análises detalhadas\n\n"
            "Escolha seu plano:",
            reply_markup=create_plans_keyboard()
        )

@dp.callback_query(F.data.startswith("plan_"))
async def process_plan_selection(callback: types.CallbackQuery, state: FSMContext):
    """Processa a seleção de plano"""
    plan_id = callback.data.split("_")[1]
    
    # Armazena o plano selecionado
    await state.update_data(selected_plan=plan_id)
    
    plan_info = payment_manager.get_plan_info(plan_id)
    if not plan_info:
        await callback.answer("Plano não encontrado!")
        return
    
    await callback.message.edit_text(
        f"📋 Resumo do Plano Selecionado:\n\n"
        f"📦 Plano: {plan_info['name']}\n"
        f"💰 Valor: R$ {plan_info['price']:.2f}\n"
        f"⏰ Duração: {plan_info['days']} dias\n\n"
        f"Para continuar, clique em 'Gerar PIX' para receber o código de pagamento.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Gerar PIX", callback_data="generate_pix")],
            [InlineKeyboardButton(text="🔙 Voltar", callback_data="back_to_plans")]
        ])
    )

@dp.callback_query(F.data == "generate_pix")
async def generate_pix_payment(callback: types.CallbackQuery, state: FSMContext):
    """Gera o pagamento PIX"""
    user_data = await state.get_data()
    plan_id = user_data.get("selected_plan")
    
    if not plan_id:
        await callback.answer("Erro: Plano não selecionado!")
        return
    
    user_info = {
        "first_name": callback.from_user.first_name or "Usuário",
        "last_name": callback.from_user.last_name or "Telegram"
    }
    
    # Gera o pagamento PIX
    payment_result = payment_manager.generate_pix_payment(
        callback.from_user.id, plan_id, user_info
    )
    
    if not payment_result["success"]:
        await callback.message.edit_text(
            f"❌ Erro ao gerar pagamento: {payment_result['error']}\n\n"
            "Tente novamente ou entre em contato com o suporte."
        )
        return
    
    # Salva o pagamento no banco
    await db.add_payment(
        user_id=callback.from_user.id,
        payment_id=payment_result["payment_id"],
        plan_type=plan_id,
        amount=payment_result["amount"],
        pix_code=payment_result["pix_code"]
    )
    
    # Armazena o ID do pagamento
    await state.update_data(payment_id=payment_result["payment_id"])
    
    # Envia o código PIX
    pix_message = (
        f"💳 Pagamento PIX Gerado!\n\n"
        f"📦 Plano: {payment_result['plan_name']}\n"
        f"💰 Valor: R$ {payment_result['amount']:.2f}\n"
        f"🆔 ID do Pagamento: {payment_result['payment_id']}\n\n"
        f"📋 Código PIX (Copie e Cole):\n"
        f"`{payment_result['pix_code']}`\n\n"
        f"⚠️ IMPORTANTE:\n"
        f"• Copie o código acima\n"
        f"• Abra seu app bancário\n"
        f"• Cole o código no PIX\n"
        f"• Confirme o pagamento\n\n"
        f"Após o pagamento, clique em 'Confirmar Pagamento' abaixo."
    )
    
    await callback.message.edit_text(
        pix_message,
        parse_mode="Markdown",
        reply_markup=create_payment_keyboard(payment_result["payment_id"])
    )

@dp.callback_query(F.data.startswith("confirm_payment_"))
async def confirm_payment(callback: types.CallbackQuery, state: FSMContext):
    """Confirma o pagamento manualmente"""
    payment_id = callback.data.split("_")[2]
    
    # Verifica o status do pagamento no Mercado Pago
    payment_info = await db.get_payment_by_id(payment_id)
    if not payment_info:
        await callback.answer("Pagamento não encontrado!")
        return
    
    # Verifica se o pagamento foi aprovado
    mp_result = payment_manager.verify_payment(payment_info["payment_id"])
    
    if mp_result["success"] and mp_result["status"] == "approved":
        # Pagamento aprovado, cria a assinatura
        plan_info = payment_manager.get_plan_info(payment_info["plan_type"])
        payment_date = datetime.now()
        expiration_date = payment_date + timedelta(days=plan_info["days"])
        
        success = await db.add_subscription(
            user_id=callback.from_user.id,
            username=callback.from_user.username or f"user_{callback.from_user.id}",
            first_name=callback.from_user.first_name or "Usuário",
            last_name=callback.from_user.last_name or "Telegram",
            plan_type=payment_info["plan_type"],
            payment_date=payment_date,
            expiration_date=expiration_date,
            payment_id=payment_id
        )
        
        if success:
            await callback.message.edit_text(
                f"🎉 Pagamento Confirmado!\n\n"
                f"✅ Sua assinatura foi ativada com sucesso!\n"
                f"📅 Expira em: {expiration_date.strftime('%d/%m/%Y')}\n\n"
                f"🔗 Link do Grupo Privado:\n{GROUP_INVITE_LINK}\n\n"
                f"Bem-vindo ao grupo! Use /status para ver detalhes da sua assinatura."
            )
        else:
            await callback.message.edit_text(
                "❌ Erro ao ativar assinatura. Entre em contato com o suporte."
            )
    else:
        await callback.message.edit_text(
            "❌ Pagamento não confirmado!\n\n"
            "O pagamento ainda não foi processado. Aguarde alguns minutos e tente novamente, "
            "ou entre em contato com o suporte se já realizou o pagamento."
        )

@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    """Cancela o pagamento"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Pagamento cancelado!\n\n"
        "Use /start para escolher um plano novamente."
    )

@dp.callback_query(F.data == "back_to_plans")
async def back_to_plans(callback: types.CallbackQuery, state: FSMContext):
    """Volta para a seleção de planos"""
    await state.clear()
    
    await callback.message.edit_text(
        "🚀 Escolha seu plano:\n\n"
        "💎 Acesso a conteúdo premium\n"
        "📱 Suporte exclusivo\n"
        "🎯 Estratégias avançadas\n"
        "📊 Análises detalhadas\n\n"
        "Escolha seu plano:",
        reply_markup=create_plans_keyboard()
    )

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """Comando para verificar status da assinatura"""
    user_id = message.from_user.id
    
    subscription = await db.get_subscription(user_id)
    
    if not subscription:
        await message.answer(
            "❌ Você não possui uma assinatura ativa.\n\n"
            "Use /start para escolher um plano."
        )
        return
    
    days_left = (subscription["expiration_date"] - datetime.now()).days
    
    if days_left <= 0:
        await message.answer(
            "⚠️ Sua assinatura expirou!\n\n"
            "Use /start para renovar sua assinatura."
        )
    else:
        await message.answer(
            f"📊 Status da Sua Assinatura:\n\n"
            f"✅ Status: Ativa\n"
            f"📦 Plano: {subscription['plan_type']}\n"
            f"📅 Data de início: {subscription['payment_date'].strftime('%d/%m/%Y')}\n"
            f"📅 Data de expiração: {subscription['expiration_date'].strftime('%d/%m/%Y')}\n"
            f"⏰ Dias restantes: {days_left}\n\n"
            f"🔗 Link do grupo: {GROUP_INVITE_LINK}"
        )

@dp.message(Command("vendas"))
async def cmd_sales(message: types.Message):
    """Comando para admin ver vendas"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Acesso negado!")
        return
    
    sales_summary = await db.get_sales_summary()
    
    if not sales_summary:
        await message.answer("❌ Erro ao obter dados de vendas!")
        return
    
    summary_text = (
        f"📊 Resumo de Vendas\n\n"
        f"✅ Assinaturas Ativas: {sales_summary['active_subscriptions']}\n"
        f"❌ Assinaturas Expiradas: {sales_summary['expired_subscriptions']}\n"
        f"💰 Total de Vendas: {sales_summary['total_sales']}\n"
        f"💵 Receita Total: R$ {sales_summary['total_revenue']:.2f}\n\n"
        f"📈 Vendas por Plano:\n"
    )
    
    for plan_type, count, revenue in sales_summary['sales_by_plan']:
        summary_text += f"• {plan_type}: {count} vendas - R$ {revenue:.2f}\n"
    
    await message.answer(summary_text)

async def check_expired_subscriptions():
    """Verifica assinaturas expiradas e remove usuários do grupo"""
    while True:
        try:
            expired_subscriptions = await db.get_expired_subscriptions()
            
            for subscription in expired_subscriptions:
                user_id = subscription["user_id"]
                
                # Atualiza status da assinatura
                await db.update_subscription_status(user_id, "expired")
                
                # Tenta remover do grupo (se o bot for admin)
                try:
                    await bot.ban_chat_member(GROUP_ID, user_id)
                    logger.info(f"Usuário {user_id} removido do grupo por assinatura expirada")
                except Exception as e:
                    logger.error(f"Erro ao remover usuário {user_id} do grupo: {e}")
                
                # Envia mensagem de aviso
                try:
                    await bot.send_message(
                        user_id,
                        "⚠️ Sua assinatura expirou!\n\n"
                        "Você foi removido do grupo privado. "
                        "Use /start para renovar sua assinatura."
                    )
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem para usuário {user_id}: {e}")
            
            # Aguarda 1 hora antes da próxima verificação
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Erro na verificação de assinaturas expiradas: {e}")
            await asyncio.sleep(3600)

async def send_renewal_warnings():
    """Envia avisos de renovação"""
    while True:
        try:
            for days in RENEWAL_WARNING_DAYS:
                expiring_subscriptions = await db.get_subscriptions_expiring_soon(days)
                
                for subscription in expiring_subscriptions:
                    user_id = subscription["user_id"]
                    
                    # Verifica se já enviou notificação recente
                    notification_sent = await db.has_recent_notification(
                        user_id, f"renewal_warning_{days}d"
                    )
                    
                    if not notification_sent:
                        try:
                            await bot.send_message(
                                user_id,
                                f"⚠️ Aviso de Renovação!\n\n"
                                f"Sua assinatura expira em {days} dia(s).\n"
                                f"Para continuar acessando o grupo privado, "
                                f"renove sua assinatura usando /start"
                            )
                            
                            # Registra a notificação
                            await db.add_notification(
                                user_id, f"renewal_warning_{days}d"
                            )
                            
                        except Exception as e:
                            logger.error(f"Erro ao enviar aviso para usuário {user_id}: {e}")
            
            # Aguarda 12 horas antes da próxima verificação
            await asyncio.sleep(43200)
            
        except Exception as e:
            logger.error(f"Erro no envio de avisos de renovação: {e}")
            await asyncio.sleep(43200)

async def main():
    """Função principal"""
    # Inicia as tarefas em background
    asyncio.create_task(check_expired_subscriptions())
    asyncio.create_task(send_renewal_warnings())
    
    # Inicia o bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 