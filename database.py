# database.py
import sqlite3
from datetime import datetime

DB_NAME = 'patients_visits.db' # Новое имя БД для чистоты

# Класс Patient больше не нужен для хранения всех данных,
# но может быть полезен для передачи ID и имени.
# Оставим его простым или уберем совсем. Пока уберем.

class DatabaseManager:
    """Класс для управления базой данных пациентов и их визитов."""
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self):
        """Возвращает соединение с базой данных."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Включаем поддержку внешних ключей для SQLite
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize_db(self):
        """Создает таблицы пациентов и визитов, если они не существуют."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Таблица Пациентов (только ID и уникальное имя)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS patients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE
                    )
                ''')
                # Таблица Визитов (с внешним ключом на пациента)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS visits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        visit_date TEXT NOT NULL,
                        chest_pain INTEGER,      -- 0 for False, 1 for True
                        ecg_abnormal INTEGER,    -- 0 for False, 1 for True
                        troponin_high INTEGER,   -- 0 for False, 1 for True
                        heart_rate REAL,       -- Allows NULL
                        systolic_bp REAL,      -- Allows NULL
                        FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                    )
                ''')
                # Индекс для быстрого поиска визитов по пациенту
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_visit_patient_id ON visits (patient_id)
                ''')
                conn.commit()
            print(f"База данных '{self.db_path}' инициализирована с таблицами patients и visits.")
        except sqlite3.Error as e:
            print(f"Ошибка при инициализации БД: {e}")

    def get_or_create_patient_id(self, name):
        """Находит пациента по имени или создает нового. Возвращает ID пациента."""
        find_sql = "SELECT id FROM patients WHERE name = ?"
        insert_sql = "INSERT INTO patients (name) VALUES (?)"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(find_sql, (name,))
                row = cursor.fetchone()
                if row:
                    print(f"Найден пациент '{name}' с ID: {row['id']}")
                    return row['id']
                else:
                    cursor.execute(insert_sql, (name,))
                    conn.commit()
                    new_id = cursor.lastrowid
                    print(f"Создан новый пациент '{name}' с ID: {new_id}")
                    return new_id
        except sqlite3.IntegrityError:
             # Это может случиться, если два запроса пытаются создать одновременно
             # Попробуем найти еще раз
             with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(find_sql, (name,))
                row = cursor.fetchone()
                if row: return row['id']
                else: raise # Если все равно не нашли, пробрасываем ошибку
        except sqlite3.Error as e:
            print(f"Ошибка при поиске/создании пациента '{name}': {e}")
            return None

    def save_visit_data(self, patient_id, visit_date, chest_pain, ecg_abnormal,
                        troponin_high, heart_rate, systolic_bp):
        """Сохраняет данные нового визита для пациента."""
        sql = '''
            INSERT INTO visits (patient_id, visit_date, chest_pain, ecg_abnormal, troponin_high, heart_rate, systolic_bp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            patient_id, visit_date,
            1 if chest_pain else 0, 1 if ecg_abnormal else 0, 1 if troponin_high else 0,
            heart_rate, systolic_bp
        )
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                visit_id = cursor.lastrowid
                print(f"Сохранен визит ID: {visit_id} для пациента ID: {patient_id} от {visit_date}")
                return visit_id
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении визита для пациента ID {patient_id}: {e}")
            return None

    def get_all_patients_list(self):
        """Возвращает список всех пациентов (id, name)."""
        patients = []
        sql = "SELECT id, name FROM patients ORDER BY name"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                patients = [dict(row) for row in cursor.fetchall()]
            return patients
        except sqlite3.Error as e:
            print(f"Ошибка при получении списка пациентов: {e}")
            return []

    def get_patient_visits(self, patient_id):
        """Возвращает список визитов (id, visit_date) для пациента, отсортированный по дате."""
        visits = []
        sql = "SELECT id, visit_date FROM visits WHERE patient_id = ? ORDER BY visit_date DESC"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (patient_id,))
                visits = [dict(row) for row in cursor.fetchall()]
            return visits
        except sqlite3.Error as e:
            print(f"Ошибка при получении визитов для пациента ID {patient_id}: {e}")
            return []

    def get_visit_data_by_id(self, visit_id):
        """Получает полные данные визита по ID визита, включая имя пациента."""
        # Используем JOIN для получения имени пациента
        sql = """
            SELECT
                v.id as visit_id, v.visit_date, v.chest_pain, v.ecg_abnormal,
                v.troponin_high, v.heart_rate, v.systolic_bp,
                p.id as patient_id, p.name as patient_name
            FROM visits v
            JOIN patients p ON v.patient_id = p.id
            WHERE v.id = ?
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (visit_id,))
                row = cursor.fetchone()
                if row:
                    # Возвращаем результат как словарь
                    return dict(row)
                else:
                    return None
        except sqlite3.Error as e:
            print(f"Ошибка при получении данных визита ID {visit_id}: {e}")
            return None