"""
Модуль для работы с базой данных пользователей.
"""

import sqlite3
import logging
import os

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с SQLite базой данных."""
    
    def __init__(self, db_path='bot.db'):
        """Инициализация подключения к базе данных."""
        # Используем директорию data, если установлена переменная DOCKER_ENV или DATA_DIR
        data_dir = os.getenv('DATA_DIR', 'data')
        docker_env = os.getenv('DOCKER_ENV', '').lower() in ('true', '1', 'yes')
        
        if docker_env or os.getenv('DATA_DIR'):
            # В Docker или если указана DATA_DIR - используем её
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, db_path)
        elif os.path.exists('data'):
            # Если директория data существует локально - используем её
            os.makedirs('data', exist_ok=True)
            self.db_path = os.path.join('data', db_path)
        else:
            # Иначе используем текущую директорию
            self.db_path = db_path
        self.conn = None
    
    def get_connection(self):
        """Получить соединение с базой данных."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_database(self):
        """Инициализация структуры базы данных."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                notion_token TEXT,
                page_id TEXT,
                page_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logger.info("База данных инициализирована")
    
    def get_user_config(self, user_id: int) -> dict:
        """Получить конфигурацию пользователя."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT notion_token, page_id, page_name FROM users WHERE user_id = ?',
            (user_id,)
        )
        
        row = cursor.fetchone()
        if row:
            return {
                'notion_token': row['notion_token'],
                'page_id': row['page_id'],
                'page_name': row['page_name']
            }
        return {}
    
    def save_notion_token(self, user_id: int, token: str):
        """Сохранить токен Notion для пользователя."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (user_id, notion_token, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                notion_token = ?,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, token, token))
        
        conn.commit()
        logger.info(f"Токен сохранен для пользователя {user_id}")
    
    def save_page_config(self, user_id: int, page_id: str, page_name: str):
        """Сохранить конфигурацию страницы для пользователя."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET page_id = ?, page_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (page_id, page_name, user_id))
        
        conn.commit()
        logger.info(f"Конфигурация страницы сохранена для пользователя {user_id}")
    
    def reset_user_config(self, user_id: int):
        """Сбросить конфигурацию пользователя."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        
        conn.commit()
        logger.info(f"Конфигурация сброшена для пользователя {user_id}")
    
    def close(self):
        """Закрыть соединение с базой данных."""
        if self.conn:
            self.conn.close()
            self.conn = None
