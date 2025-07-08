from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import json
from typing import Dict, Any
from payments import PaymentManager
from database import Database
from config import DATABASE_PATH, GROUP_INVITE_LINK
from datetime import datetime
import asyncio

app = FastAPI()
payment_manager = PaymentManager()
db = Database(DATABASE_PATH)

@app.post("/webhook")
async def mercadopago_webhook(request: Request):
    """Endpoint para receber webhooks do Mercado Pago"""
    try:
        # Lê o corpo da requisição
        body = await request.body()
        webhook_data = json.loads(body)
        
        print(f"Webhook recebido: {webhook_data}")
        
        # Processa o webhook
        result = payment_manager.process_webhook(webhook_data)
        
        if not result["success"]:
            return JSONResponse(
                status_code=400,
                content={"error": result["error"]}
            )
        
        # Se o pagamento foi aprovado
        if result["status"] == "approved":
            await process_approved_payment(result)
        
        # Atualiza o status do pagamento no banco
        await db.update_payment_status(
            result["external_reference"], 
            result["status"]
        )
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Webhook processado"}
        )
        
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Erro interno do servidor"}
        )

async def process_approved_payment(payment_result: Dict[str, Any]):
    """Processa um pagamento aprovado"""
    try:
        # Obtém o pagamento do banco
        payment = await db.get_payment_by_id(payment_result["external_reference"])
        
        if not payment:
            print(f"Pagamento não encontrado: {payment_result['external_reference']}")
            return
        
        user_id = payment["user_id"]
        plan_type = payment["plan_type"]
        
        # Calcula a data de expiração
        plan_info = payment_manager.get_plan_info(plan_type)
        if not plan_info:
            print(f"Plano não encontrado: {plan_type}")
            return
        
        payment_date = datetime.now()
        expiration_date = payment_date.replace(
            day=payment_date.day + plan_info["days"]
        )
        
        # Obtém informações do usuário (você precisará implementar isso)
        # Por enquanto, vamos usar dados básicos
        user_info = {
            "username": f"user_{user_id}",
            "first_name": "Usuário",
            "last_name": "Telegram"
        }
        
        # Adiciona a assinatura ao banco
        success = await db.add_subscription(
            user_id=user_id,
            username=user_info["username"],
            first_name=user_info["first_name"],
            last_name=user_info["last_name"],
            plan_type=plan_type,
            payment_date=payment_date,
            expiration_date=expiration_date,
            payment_id=payment_result["external_reference"]
        )
        
        if success:
            print(f"Assinatura criada para usuário {user_id}")
            # Aqui você pode adicionar lógica para enviar o link do grupo
            # via bot do Telegram (implementar no bot.py)
        else:
            print(f"Erro ao criar assinatura para usuário {user_id}")
            
    except Exception as e:
        print(f"Erro ao processar pagamento aprovado: {e}")

@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 