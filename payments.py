import mercadopago
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from config import MP_ACCESS_TOKEN, PLANS

class PaymentManager:
    def __init__(self):
        self.mp = mercadopago.SDK(MP_ACCESS_TOKEN)
    
    def generate_pix_payment(self, user_id: int, plan_type: str, 
                           user_info: Dict[str, str]) -> Dict[str, Any]:
        """Gera um pagamento PIX para o plano escolhido"""
        try:
            plan = PLANS.get(plan_type)
            if not plan:
                raise ValueError(f"Plano inválido: {plan_type}")
            
            # Gera um ID único para o pagamento
            payment_id = str(uuid.uuid4())
            
            # Cria o pagamento no Mercado Pago
            payment_data = {
                "transaction_amount": plan["price"],
                "description": f"Assinatura {plan['name']} - Grupo Privado",
                "payment_method_id": "pix",
                "payer": {
                    "email": f"user_{user_id}@telegram.com",
                    "first_name": user_info.get("first_name", "Usuário"),
                    "last_name": user_info.get("last_name", "Telegram")
                },
                "external_reference": payment_id,
                "notification_url": "https://seu-dominio.com/webhook"
            }
            
            payment_response = self.mp.payment().create(payment_data)
            
            if payment_response["status"] == 201:
                payment_info = payment_response["response"]
                
                # Extrai o código PIX
                pix_code = None
                if "point_of_interaction" in payment_info:
                    pix_data = payment_info["point_of_interaction"]["transaction_data"]
                    if "qr_code" in pix_data:
                        pix_code = pix_data["qr_code"]
                    elif "qr_code_base64" in pix_data:
                        pix_code = pix_data["qr_code_base64"]
                
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "mp_payment_id": payment_info["id"],
                    "pix_code": pix_code,
                    "amount": plan["price"],
                    "plan_type": plan_type,
                    "plan_name": plan["name"],
                    "expiration_date": datetime.now() + timedelta(days=plan["days"])
                }
            else:
                return {
                    "success": False,
                    "error": "Erro ao criar pagamento no Mercado Pago"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verifica o status de um pagamento no Mercado Pago"""
        try:
            payment_response = self.mp.payment().get(payment_id)
            
            if payment_response["status"] == 200:
                payment_info = payment_response["response"]
                
                return {
                    "success": True,
                    "status": payment_info["status"],
                    "status_detail": payment_info["status_detail"],
                    "external_reference": payment_info.get("external_reference"),
                    "transaction_amount": payment_info["transaction_amount"]
                }
            else:
                return {
                    "success": False,
                    "error": "Erro ao verificar pagamento"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa webhook do Mercado Pago"""
        try:
            if webhook_data.get("type") == "payment":
                payment_id = webhook_data["data"]["id"]
                payment_info = self.verify_payment(payment_id)
                
                if payment_info["success"]:
                    return {
                        "success": True,
                        "payment_id": payment_id,
                        "status": payment_info["status"],
                        "external_reference": payment_info["external_reference"],
                        "amount": payment_info["transaction_amount"]
                    }
            
            return {
                "success": False,
                "error": "Webhook inválido ou não processado"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao processar webhook: {str(e)}"
            }
    
    def get_plan_info(self, plan_type: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de um plano"""
        return PLANS.get(plan_type)
    
    def get_all_plans(self) -> Dict[str, Any]:
        """Obtém todos os planos disponíveis"""
        return PLANS 