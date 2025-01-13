database.py 
import sqlite3

# Создаем или подключаемся к базе данных
def init_db():
    conn = sqlite3.connect('game_results.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            level INTEGER,
            score INTEGER,
            time INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Сохранение результата
def save_result(player_name, level, score, time):
    conn = sqlite3.connect('game_results.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO results (player_name, level, score, time)
        VALUES (?, ?, ?, ?)
    ''', (player_name, level, score, time))
    conn.commit()
    conn.close()

# Получение лучшего результата
def get_best_result():
    conn = sqlite3.connect('game_results.db')
    cursor = conn.cursor()
    cursor.execute('SELECT player_name, level, score, time FROM results ORDER BY score DESC LIMIT 1')
    best_result = cursor.fetchone()
    conn.close()
    return best_result
