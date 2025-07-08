import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de assinaturas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                plan_type TEXT NOT NULL,
                payment_date DATETIME NOT NULL,
                expiration_date DATETIME NOT NULL,
                payment_id TEXT,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de pagamentos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                payment_id TEXT NOT NULL,
                plan_type TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                pix_code TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de notificações enviadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def add_subscription(self, user_id: int, username: str, first_name: str, 
                             last_name: str, plan_type: str, payment_date: datetime, 
                             expiration_date: datetime, payment_id: str) -> bool:
        """Adiciona uma nova assinatura"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO subscriptions 
                (user_id, username, first_name, last_name, plan_type, payment_date, 
                 expiration_date, payment_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
            ''', (user_id, username, first_name, last_name, plan_type, 
                  payment_date, expiration_date, payment_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao adicionar assinatura: {e}")
            return False
    
    async def get_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtém a assinatura ativa de um usuário"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND status = 'active'
                ORDER BY expiration_date DESC
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Erro ao obter assinatura: {e}")
            return None
    
    async def update_subscription_status(self, user_id: int, status: str) -> bool:
        """Atualiza o status de uma assinatura"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE subscriptions 
                SET status = ? 
                WHERE user_id = ? AND status = 'active'
            ''', (status, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar status da assinatura: {e}")
            return False
    
    async def get_expired_subscriptions(self) -> List[Dict[str, Any]]:
        """Obtém todas as assinaturas expiradas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM subscriptions 
                WHERE expiration_date < ? AND status = 'active'
            ''', (datetime.now(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        except Exception as e:
            print(f"Erro ao obter assinaturas expiradas: {e}")
            return []
    
    async def get_subscriptions_expiring_soon(self, days: int) -> List[Dict[str, Any]]:
        """Obtém assinaturas que expiram em X dias"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            target_date = datetime.now() + timedelta(days=days)
            
            cursor.execute('''
                SELECT * FROM subscriptions 
                WHERE expiration_date BETWEEN ? AND ? 
                AND status = 'active'
            ''', (datetime.now(), target_date))
            
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        except Exception as e:
            print(f"Erro ao obter assinaturas expirando em breve: {e}")
            return []
    
    async def add_payment(self, user_id: int, payment_id: str, plan_type: str, 
                         amount: float, pix_code: str) -> bool:
        """Adiciona um novo pagamento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO payments 
                (user_id, payment_id, plan_type, amount, pix_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, payment_id, plan_type, amount, pix_code))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao adicionar pagamento: {e}")
            return False
    
    async def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Atualiza o status de um pagamento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE payments 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE payment_id = ?
            ''', (status, payment_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar status do pagamento: {e}")
            return False
    
    async def get_payment_by_id(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Obtém um pagamento pelo ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM payments WHERE payment_id = ?
            ''', (payment_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Erro ao obter pagamento: {e}")
            return None
    
    async def get_sales_summary(self) -> Dict[str, Any]:
        """Obtém resumo de vendas para o admin"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total de assinaturas ativas
            cursor.execute('''
                SELECT COUNT(*) FROM subscriptions WHERE status = 'active'
            ''')
            active_subscriptions = cursor.fetchone()[0]
            
            # Total de assinaturas expiradas
            cursor.execute('''
                SELECT COUNT(*) FROM subscriptions WHERE status = 'expired'
            ''')
            expired_subscriptions = cursor.fetchone()[0]
            
            # Total de vendas (pagamentos aprovados)
            cursor.execute('''
                SELECT COUNT(*), SUM(amount) FROM payments WHERE status = 'approved'
            ''')
            sales_result = cursor.fetchone()
            total_sales = sales_result[0] or 0
            total_revenue = sales_result[1] or 0
            
            # Vendas por plano
            cursor.execute('''
                SELECT plan_type, COUNT(*), SUM(amount) 
                FROM payments 
                WHERE status = 'approved' 
                GROUP BY plan_type
            ''')
            sales_by_plan = cursor.fetchall()
            
            conn.close()
            
            return {
                'active_subscriptions': active_subscriptions,
                'expired_subscriptions': expired_subscriptions,
                'total_sales': total_sales,
                'total_revenue': total_revenue,
                'sales_by_plan': sales_by_plan
            }
        except Exception as e:
            print(f"Erro ao obter resumo de vendas: {e}")
            return {}
    
    async def add_notification(self, user_id: int, notification_type: str) -> bool:
        """Registra uma notificação enviada"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notifications (user_id, notification_type)
                VALUES (?, ?)
            ''', (user_id, notification_type))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao adicionar notificação: {e}")
            return False
    
    async def has_recent_notification(self, user_id: int, notification_type: str, 
                                    hours: int = 24) -> bool:
        """Verifica se uma notificação foi enviada recentemente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM notifications 
                WHERE user_id = ? AND notification_type = ? 
                AND sent_at > datetime('now', '-{} hours')
            '''.format(hours), (user_id, notification_type))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
        except Exception as e:
            print(f"Erro ao verificar notificação recente: {e}")
            return False 