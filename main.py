import sqlite3
import pygame
import sys
import time

# Инициализация Pygame
pygame.init()
lever_timers = {}
current_level = 1
# Размеры экрана
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Огонь и Вода')

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (100, 200, 255)
GREY = (58, 58,  58)
FONT = pygame.font.SysFont("Arial", 32)
# FPS
FPS = 60
clock = pygame.time.Clock()

# Загрузка изображений
background = pygame.image.load('assets/background.png')
fire_sprite = pygame.image.load('assets/fire_sprite.png')
water_sprite = pygame.image.load('assets/water_sprite.png')

# Изменим размеры спрайтов
fire_sprite = pygame.transform.scale(fire_sprite, (50, 50))
water_sprite = pygame.transform.scale(water_sprite, (50, 50))

# Загрузка музыки
music_files = ['assets/music1.mp3', 'assets/music2.mp3', 'assets/music3.mp3']
current_music = 0  # Индекс текущей музыки
pygame.mixer.music.load(music_files[current_music])
pygame.mixer.music.set_volume(0.5)  # Начальная громкость

class DatabaseManager:
    @staticmethod
    def create_db():
        conn = sqlite3.connect("game_results.db")
        c = conn.cursor()
        
        # Создаем таблицу, если она не существует
        c.execute('''CREATE TABLE IF NOT EXISTS results
                     (name TEXT, time REAL)''')
        
        # Добавляем столбец level, если его нет
        c.execute("PRAGMA table_info(results)")
        columns = c.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'level' not in column_names:
            c.execute("ALTER TABLE results ADD COLUMN level INTEGER")
        
        conn.commit()
        conn.close()

    @staticmethod
    def insert_result(name, time, level):
        conn = sqlite3.connect("game_results.db")
        c = conn.cursor()
        c.execute("INSERT INTO results (name, time, level) VALUES (?, ?, ?)", (name, time, level))
        conn.commit()
        conn.close()

    @staticmethod
    def get_results_by_level(level):
        conn = sqlite3.connect("game_results.db")
        c = conn.cursor()
        c.execute("SELECT * FROM results WHERE level = ? ORDER BY time ASC", (level,))
        results = c.fetchall()
        conn.close()
        return results

    @staticmethod
    def get_all_results():
        conn = sqlite3.connect("game_results.db")
        c = conn.cursor()
        c.execute("SELECT * FROM results ORDER BY time ASC")  # Результаты отсортированы по времени
        results = c.fetchall()
        conn.close()
        return results

class LevelManager:
    def check_water_obstacle_collision(player, level_data):
        """Проверяет, сталкивается ли вода с препятствием 'O'."""
        player_rect = pygame.Rect(player.x, player.y, 50, 50)
        for y, row in enumerate(level_data):
            for x, tile in enumerate(row):
                if tile == 'O' and player_rect.colliderect(pygame.Rect(x * 50, y * 50, 50, 50)):
                    return True
        return False
        
    @staticmethod
    def check_fire_obstacle_collision(player, level_data):
        """Проверяет, сталкивается ли огненный игрок с препятствием для огня (X)."""
        player_rect = pygame.Rect(player.x, player.y, 50, 50)
        for y, row in enumerate(level_data):
            for x, tile in enumerate(row):
                if tile == 'X' and player_rect.colliderect(pygame.Rect(x * 50, y * 50, 50, 50)):
                    return True
        return False
    
    @staticmethod
    def load_level(file_path):
        level_data = []
        spawn_fire = None
        spawn_water = None
        with open(file_path, 'r') as file:
            for y, line in enumerate(file):
                row = []
                for x, tile in enumerate(line.strip()):
                    if tile == 'F':  # Заменили S_F на F для огня
                        spawn_fire = (x * 50, y * 50)  # Запоминаем координаты для огня
                        row.append(' ')  # Пустое место для огня
                    elif tile == 'W':  # Заменили S_W на W для воды
                        spawn_water = (x * 50, y * 50)  # Запоминаем координаты для воды
                        row.append(' ')  # Пустое место для воды
                    elif tile == ' ':
                        row.append(' ')  # Пустое место
                    else:
                        row.append(tile)  # Стены или другие объекты
                level_data.append(row)
        
        if spawn_fire is None or spawn_water is None:
            print("Error: Spawn points for fire or water not found!")
            return None, None, None

        return level_data, spawn_fire, spawn_water

    @staticmethod
    def render_level(level_data):
        for y, row in enumerate(level_data):
            for x, tile in enumerate(row):
                if tile == '#':  # Стена
                    pygame.draw.rect(screen, (0, 0, 0), (x * 50, y * 50, 50, 50))  # Черная стена
                elif tile == 'O':  # Препятствие для воды (огонь)
                    pygame.draw.rect(screen, (255, 165, 0), (x * 50, y * 50, 50, 50))  # Оранжевое препятствие
                elif tile == 'X':  # Препятствие для огня (вода)
                    pygame.draw.rect(screen, (0, 255, 255), (x * 50, y * 50, 50, 50))  # Голубое препятствие
                elif tile == 'P':  # Портал
                    pygame.draw.rect(screen, (255, 255, 0), (x * 50, y * 50, 50, 50))  # Желтый портал
                elif tile == 'L':  # Рычаг
                    pygame.draw.rect(screen, (169, 169, 169), (x * 50, y * 50, 50, 50))  # Серый рычаг
                elif tile == 'D':  # Дверь
                    pygame.draw.rect(screen, (255, 0, 0), (x * 50, y * 50, 50, 50))  # Красная дверь
                elif tile == 'S':  # Лава
                    pygame.draw.rect(screen, (255, 0, 0), (x * 50, y * 50, 50, 50))  # Красная лава
                elif tile == 'I':  # Платформа
                    pygame.draw.rect(screen, (0, 255, 0), (x * 50, y * 50, 50, 50))  # Зеленая платформа

    @staticmethod
    def check_collision(rect, level_data):
        # Проверка всех пикселей в прямоугольнике
        for y in range(rect.top // 50, (rect.bottom // 50) + 1):
            for x in range(rect.left // 50, (rect.right // 50) + 1):
                if level_data[y][x] == '#':  # Если в этой клетке стена
                    return True
        return False

    @staticmethod
    def check_portal_collision(player, level_data):
        player_rect = pygame.Rect(player.x, player.y, 50, 50)
        for y, row in enumerate(level_data):
            for x, tile in enumerate(row):
                if tile == 'P' and player_rect.colliderect(pygame.Rect(x * 50, y * 50, 50, 50)):
                    return True
        return False

    @staticmethod
    def check_lava_collision(player, level_data):
        player_rect = pygame.Rect(player.x, player.y, 50, 50)
        for y, row in enumerate(level_data):
            for x, tile in enumerate(row):
                if tile == 's' and player_rect.colliderect(pygame.Rect(x * 50, y * 50, 50, 50)):
                    return True
        return False

    @staticmethod
    def check_lever_collision(player, level_data):
        player_rect = pygame.Rect(player.x, player.y, 50, 50)
        for y, row in enumerate(level_data):
            for x, tile in enumerate(row):
                if tile == 'L' and player_rect.colliderect(pygame.Rect(x * 50, y * 50, 50, 50)):
                    level_data[y][x] = ' '  # Убираем рычаг, если его активировали
                    # Открываем дверь, меняем на пустое место
                    for row in level_data:
                        for i, col in enumerate(row):
                            if col == 'D':
                                row[i] = ' '  # Открытие двери
                    return True
        return False

    @staticmethod
    def get_level_objects(level_data):
        """Находит координаты всех рычагов и дверей"""
        levers = set()
        doors = set()

        for y, row in enumerate(level_data):
            for x, tile in enumerate(row):
                if tile == 'L':  # Рычаг
                    levers.add((x, y))
                elif tile == 'D':  # Дверь
                    doors.add((x, y))

        return levers, doors

    @staticmethod
    def toggle_door(level_data, doors):
        """Переключает двери между закрытым и открытым состоянием"""
        for x, y in doors:
            if level_data[y][x] == 'D':
                level_data[y][x] = ' '  # Открываем дверь
            else:
                level_data[y][x] = 'D'  # Закрываем дверь обратно

    @staticmethod
    def check_lever_interaction(player, level_data, levers, doors):
        """Проверяет, стоит ли игрок рядом с рычагом и нажимает ли клавишу 'E'"""
        player_rect = pygame.Rect(player.x, player.y, 50, 50)

        for x, y in levers:
            lever_rect = pygame.Rect(x * 50, y * 50, 50, 50)
            if player_rect.colliderect(lever_rect):
                keys = pygame.key.get_pressed()
                if keys[pygame.K_e]:  # Игрок нажал "E"
                    current_time = time.time()
                    last_used = lever_timers.get((x, y), 0)

                    if current_time - last_used >= 2:  # Прошло 2 секунды?
                        LevelManager.toggle_door(level_data, doors)
                        lever_timers[(x, y)] = current_time  # Обновляем таймер
                        return True

        return False

    @staticmethod
    def check_collision_with_doors(player, level_data, is_fire):
        """Запрещает движение игрока через закрытые двери"""
        player_rect = pygame.Rect(player.x, player.y, 50, 50)
        
        for y, row in enumerate(level_data):
            for x, tile in enumerate(row):
                if tile == 'D':  # Дверь
                    door_rect = pygame.Rect(x * 50, y * 50, 50, 50)
                    # Если игрок сталкивается с дверью, проверяем, можно ли пройти
                    if player_rect.colliderect(door_rect):
                        if level_data[y][x] == 'D':  # Если дверь закрыта
                            # Огненный персонаж не может пройти через дверь
                            if is_fire:
                                return True  # Огненный персонаж не может пройти через дверь
                            # Водяной персонаж не может пройти через дверь
                            if not is_fire:
                                return True  # Водяной персонаж не может пройти через дверь
        return False

    @staticmethod
    def check_on_ground(rect, level_data):
        for y in range(rect.bottom // 50, (rect.bottom // 50) + 1):
            for x in range(rect.left // 50, (rect.right // 50) + 1):
                if level_data[y][x] == '.':  # Пол
                    return True
        return False

class UIManager:
    @staticmethod
    def draw_button(text, x, y, width, height, color):
        font = pygame.font.Font(None, 36)
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, color, button_rect)
        text_surface = font.render(text, True, BLACK)
        screen.blit(text_surface, (x + 10, y + 10))
        return button_rect

    @staticmethod
    def level_complete_screen(level_time):
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        screen.fill(WHITE)

        # Заголовок экрана
        title_text = FONT.render("УРОВЕНЬ ПРОЙДЕН", True, BLACK)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(title_text, title_rect)

        # Время прохождения уровня
        time_text = FONT.render(f"Время: {level_time:.2f} секунд", True, BLACK)
        time_rect = time_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(time_text, time_rect)

        # Кнопка для ввода имени игрока
        input_prompt = FONT.render("Введите ваше имя:", True, BLACK)
        input_prompt_rect = input_prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(input_prompt, input_prompt_rect)

        # Отображение поля для ввода имени
        name_input_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 100, 300, 40)
        pygame.draw.rect(screen, BLACK, name_input_rect, 2)

        # Отображение введенного имени
        player_name = ""
        name_text = FONT.render(player_name, True, BLACK)
        screen.blit(name_text, (WIDTH // 2 - 140, HEIGHT // 2 + 110))

        pygame.display.flip()

        # Ожидание ввода имени
        typing = True
        while typing:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:  # Если нажата клавиша Enter
                        typing = False
                    elif event.key == pygame.K_BACKSPACE:  # Если нажата клавиша Backspace
                        player_name = player_name[:-1]
                    else:  # Добавляем символы в имя
                        player_name += event.unicode

            # Обновляем текст с именем
            name_text = FONT.render(player_name, True, BLACK)
            screen.fill(WHITE)  # Очистить экран перед обновлением
            screen.blit(title_text, title_rect)
            screen.blit(time_text, time_rect)
            screen.blit(input_prompt, input_prompt_rect)
            pygame.draw.rect(screen, BLACK, name_input_rect, 2)
            screen.blit(name_text, (WIDTH // 2 - 140, HEIGHT // 2 + 110))

            pygame.display.flip()

        return player_name

    @staticmethod
    def level_complete_buttons():
        screen = pygame.display.get_surface()

        # Кнопки
        next_level_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 150, 300, 50)
        pygame.draw.rect(screen, BLACK, next_level_button)
        next_level_text = FONT.render("Следующий уровень", True, WHITE)
        screen.blit(next_level_text, (WIDTH // 2 - next_level_text.get_width() // 2, HEIGHT // 2 + 160))

        main_menu_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 220, 300, 50)
        pygame.draw.rect(screen, BLACK, main_menu_button)
        main_menu_text = FONT.render("Главное меню", True, WHITE)
        screen.blit(main_menu_text, (WIDTH // 2 - main_menu_text.get_width() // 2, HEIGHT // 2 + 230))

        pygame.display.flip()

        # Ожидание нажатия кнопки
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if next_level_button.collidepoint(mouse_pos):
                        return "next_level"
                    elif main_menu_button.collidepoint(mouse_pos):
                        return "main_menu"

    @staticmethod
    def start_screen():
        running = True
        while running:
            screen.fill(WHITE)  # Очистка экрана
            screen.blit(background, (0, 0))  # Отображение фона

            # Кнопки
            level_button = UIManager.draw_button("Выбрать уровень", 800, 400, 280, 60, BUTTON_COLOR)
            volume_button = UIManager.draw_button("Настройки громкости", 800, 500, 280, 60, BUTTON_COLOR)
            quit_button = UIManager.draw_button("Выход", 800, 600, 280, 60, BUTTON_COLOR)

            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if level_button.collidepoint(mouse_pos):
                        return "level"
                    if volume_button.collidepoint(mouse_pos):
                        return "volume"
                    if quit_button.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()

            pygame.display.update()
            clock.tick(FPS)

    @staticmethod
    def level_selection():
        running = True
        while running:
            screen.fill(WHITE)
            screen.blit(background, (0, 0))

            # Кнопки для выбора уровня
            level_buttons = []
            for i in range(5):
                level_buttons.append(UIManager.draw_button(f"Уровень {i + 1}", 800, 200 + i * 100, 280, 60, BUTTON_COLOR))

            # Кнопка для выхода в главное меню
            back_button = UIManager.draw_button("Назад", 800, 800, 280, 60, BUTTON_COLOR)

            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    for i, button in enumerate(level_buttons):
                        if button.collidepoint(mouse_pos):
                            return i  # Возвращаем номер выбранного уровня 
                    if back_button.collidepoint(mouse_pos):
                        return "back"  # Возвращаемся в главное меню

            pygame.display.update()
            clock.tick(FPS)

    @staticmethod
    def volume_settings():
        global current_music
        running = True
        volume = pygame.mixer.music.get_volume()
        while running:
            screen.fill(WHITE)
            screen.blit(background, (0, 0))

            # Кнопки для изменения громкости
            UIManager.draw_button("Громкость: {:.1f}".format(volume), 800, 400, 280, 60, BUTTON_COLOR)
            decrease_button = UIManager.draw_button("Уменьшить", 800, 500, 280, 60, BUTTON_COLOR)
            increase_button = UIManager.draw_button("Увеличить", 800, 600, 280, 60, BUTTON_COLOR)

            # Кнопки для изменения музыки
            music_button = UIManager.draw_button("Сменить музыку: {}".format(current_music + 1), 800, 700, 280, 60, BUTTON_COLOR)

            # Кнопка для выхода
            back_button = UIManager.draw_button("Назад", 800, 800, 280, 60, BUTTON_COLOR)

            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if decrease_button.collidepoint(mouse_pos) and volume > 0:
                        volume -= 0.1
                        pygame.mixer.music.set_volume(volume)
                    if increase_button.collidepoint(mouse_pos) and volume < 1:
                        volume += 0.1
                        pygame.mixer.music.set_volume(volume)
                    if music_button.collidepoint(mouse_pos):
                        current_music = (current_music + 1) % len(music_files)
                        pygame.mixer.music.load(music_files[current_music])
                        pygame.mixer.music.play(-1, 0.0)  # Запуск выбранной музыки в цикле
                    if back_button.collidepoint(mouse_pos):
                        return "back"  # Возвращаемся в главное меню

            pygame.display.update()
            clock.tick(FPS)

    @staticmethod
    def main_menu():
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        screen.fill(WHITE)

        # Заголовок
        title_text = FONT.render("ГЛАВНОЕ МЕНЮ", True, BLACK)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(title_text, title_rect)

        # Кнопки
        play_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 50)
        pygame.draw.rect(screen, BLACK, play_button)
        play_text = FONT.render("Начать игру", True, WHITE)
        screen.blit(play_text, (WIDTH // 2 - play_text.get_width() // 2, HEIGHT // 2 - 40))

        results_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 20, 300, 50)
        pygame.draw.rect(screen, BLACK, results_button)
        results_text = FONT.render("Просмотр результатов", True, WHITE)
        screen.blit(results_text, (WIDTH // 2 - results_text.get_width() // 2, HEIGHT // 2 + 30))

        quit_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 90, 300, 50)
        pygame.draw.rect(screen, BLACK, quit_button)
        quit_text = FONT.render("Выход", True, WHITE)
        screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 100))

        pygame.display.flip()

        # Ожидание нажатия кнопки
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if play_button.collidepoint(mouse_pos):
                        return "play"
                    elif results_button.collidepoint(mouse_pos):
                        return "results"
                    elif quit_button.collidepoint(mouse_pos):
                        pygame.quit()
                        return "quit"

    @staticmethod
    def display_results():
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        screen.fill(WHITE)

        # Заголовок
        title_text = FONT.render("РЕЗУЛЬТАТЫ", True, BLACK)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(title_text, title_rect)

        # Список уровней (для примера, от 1 до 3)
        level_buttons = []
        for level in range(1, 6):
            level_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 4 + 50 + (level - 1) * 60, 300, 50)
            pygame.draw.rect(screen, BLACK, level_button)
            level_text = FONT.render(f"Уровень {level}", True, WHITE)
            screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, HEIGHT // 4 + 60 + (level - 1) * 60))
            level_buttons.append((level_button, level))

        # Кнопка возврата в главное меню
        back_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 100, 300, 50)
        pygame.draw.rect(screen, BLACK, back_button)
        back_text = FONT.render("Назад", True, WHITE)
        screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 90))

        pygame.display.flip()

        # Ожидание нажатия кнопки
        waiting = True
        selected_level = None
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    for button, level in level_buttons:
                        if button.collidepoint(mouse_pos):
                            selected_level = level
                            waiting = False
                            break
                    if back_button.collidepoint(mouse_pos):
                        return "back"

        # Получаем результаты для выбранного уровня
        results = DatabaseManager.get_results_by_level(selected_level)

        # Отображаем результаты
        screen.fill(WHITE)  # Очищаем экран для результатов
        y_offset = HEIGHT // 4 + 50
        for result in results:
            name_text = FONT.render(f"Игрок: {result[0]}, Время: {result[1]:.2f}", True, BLACK)
            screen.blit(name_text, (WIDTH // 2 - name_text.get_width() // 2, y_offset))
            y_offset += 40

        # Кнопка возврата в главное меню
        pygame.draw.rect(screen, BLACK, back_button)
        screen.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 90))

        pygame.display.flip()

        # Ожидание нажатия кнопки
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if back_button.collidepoint(mouse_pos):
                        return "back"

class GameManager:
    @staticmethod
    def main(level):
        # Сохраняем текущую музыку перед запуском уровня
        global current_music
        pygame.mixer.music.load(music_files[current_music])
        pygame.mixer.music.play(-1, 0.0)  # Запуск музыки в цикле для уровня

        while True:
            result = UIManager.main_menu()

            if result == "play":
                # Запуск игры (вместо этого можно вызвать функцию начала уровня)
                print("Начало игры")
                break  # Эмулируем начало игры
            elif result == "results":
                # Показать результаты
                UIManager.display_results()
            elif result == "quit":
                pygame.quit()
                break

        DatabaseManager.create_db()

        start_ticks = pygame.time.get_ticks()

        # Загрузка уровня и точек спавна
        level_data, spawn_fire, spawn_water = LevelManager.load_level(f'levels/level{level + 1}.txt')
        
        if level_data is None:
            return  # Если уровня не удалось загрузить, выходим из функции
        
        # Начальные позиции для игроков
        player1 = pygame.Rect(spawn_fire[0], spawn_fire[1], 50, 50) if spawn_fire else None
        player2 = pygame.Rect(spawn_water[0], spawn_water[1], 50, 50) if spawn_water else None

        fire_rect = pygame.Rect(player1.x, player1.y, 50, 50)
        water_rect = pygame.Rect(player2.x, player2.y, 50, 50)

        if player1 is None or player2 is None:
            print("Error: Failed to create player rects!")
            return

        # Переменные для физики
        gravity = 0.5  # Гравитация
        jump_strength = -12  # Сила прыжка
        player1_vel_y = 0  # Вертикальная скорость игрока 1
        player2_vel_y = 0  # Вертикальная скорость игрока 2
        on_ground1 = False  # Переменная для проверки, на земле ли игрок 1
        on_ground2 = False  # Переменная для проверки, на земле ли игрок 2
        levers, doors = LevelManager.get_level_objects(level_data)

        # Основной игровой цикл
        while True:
            screen.fill(WHITE)  # Очистка экрана
            if LevelManager.check_lever_interaction(player1, level_data, levers, doors) or LevelManager.check_lever_interaction(player2, level_data, levers, doors):
                print("Рычаг активирован!")

            # Отображение фона и уровня
            screen.fill((46, 139, 87))
            LevelManager.render_level(level_data)  # Отображение уровня

            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        print("Рестарт уровня!")
                        GameManager.main(level)  # Рестарт уровня

            # Проверка на землю для игрока 1
            if not LevelManager.check_collision(player1, level_data):
                player1_vel_y += gravity  # Гравитация
                on_ground1 = False
            else:
                player1_vel_y = 0
                on_ground1 = True

            # Проверка столкновений с препятствиями и респавн
            if LevelManager.check_fire_obstacle_collision(player1, level_data):  # Огонь сталкивается с 'X'
                print("Огонь столкнулся с препятствием 'X'! Респавн...")
                player1.x, player1.y = spawn_fire  # Возврат на стартовую позицию

            if LevelManager.check_water_obstacle_collision(player2, level_data):  # Вода сталкивается с 'O'
                print("Вода столкнулась с препятствием 'O'! Респавн...")
                player2.x, player2.y = spawn_water  # Возврат на стартовую позицию

            if LevelManager.check_collision_with_doors(player1, level_data, is_fire=True):
                print("Огонь не может пройти через дверь.")
            if LevelManager.check_collision_with_doors(player2, level_data, is_fire=False):
                print("Вода не может пройти через дверь.")

            # Проверка на землю для игрока 2
            if not LevelManager.check_collision(player2, level_data):
                player2_vel_y += gravity  # Гравитация
                on_ground2 = False
            else:
                player2_vel_y = 0
                on_ground2 = True

            # Управление для игрока 1 (Огонь)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:
                player1.x -= 5
                if LevelManager.check_collision(player1, level_data) or LevelManager.check_collision_with_doors(player1, level_data, is_fire=True):
                    player1.x += 5  # Возврат назад, если столкновение с стеной или закрытой дверью
            if keys[pygame.K_d]:
                player1.x += 5
                if LevelManager.check_collision(player1, level_data) or LevelManager.check_collision_with_doors(player1, level_data, is_fire=True):
                    player1.x -= 5  # Возврат назад, если столкновение с стеной или закрытой дверью
            if keys[pygame.K_w] and on_ground1:  # Прыжок, если на земле
                player1_vel_y = jump_strength
            player1.y += player1_vel_y  # Применяем вертикальную скорость

            # Управление для игрока 2 (Вода)
            if keys[pygame.K_LEFT]:
                player2.x -= 5
                if LevelManager.check_collision(player2, level_data) or LevelManager.check_collision_with_doors(player2, level_data, is_fire=False):
                    player2.x += 5  # Возврат назад, если столкновение с стеной или закрытой дверью
            if keys[pygame.K_RIGHT]:
                player2.x += 5
                if LevelManager.check_collision(player2, level_data) or LevelManager.check_collision_with_doors(player2, level_data, is_fire=False):
                    player2.x -= 5  # Возврат назад, если столкновение с стеной или закрытой дверью
            if keys[pygame.K_UP] and on_ground2:  # Прыжок, если на земле
                player2_vel_y = jump_strength

            player2.y += player2_vel_y  # Применяем вертикальную скорость

            # Список рычагов
            lever_rects = []
            for y, row in enumerate(level_data):
                for x, tile in enumerate(row):
                    if tile == 'L':  # Если на уровне есть рычаг
                        lever_rect = pygame.Rect(x * 50, y * 50, 50, 50)
                        lever_rects.append(lever_rect)
            # Проверка на взаимодействие с порталом (P)
            portal_rects = []
            for y, row in enumerate(level_data):
                for x, tile in enumerate(row):
                    if tile == 'P':  # Если на уровне есть портал
                        portal_rect = pygame.Rect(x * 50, y * 50, 50, 50)
                        portal_rects.append(portal_rect)
            door_rects = []
            for y, row in enumerate(level_data):
                for x, tile in enumerate(row):
                    if tile == 'D':  # Если на уровне есть дверь
                        door_rect = pygame.Rect(x * 50, y * 50, 50, 50)
                        door_rects.append(door_rect)
                
            for portal_rect in portal_rects:
                if player1.colliderect(portal_rect) and player2.colliderect(portal_rect):
                    # Если игроки касаются портала, переход на следующий уровень
                    level_time = (pygame.time.get_ticks() - start_ticks) / 1000  # Время в секундах
                    current_level = level + 1
                    # Показать экран завершения уровня
                    player_name = UIManager.level_complete_screen(level_time)

                    # Вставляем результаты в БД
                    DatabaseManager.insert_result(player_name, level_time, current_level)

                    # Показать кнопки для продолжения
                    result = UIManager.level_complete_buttons()

                    if result == "next_level":
                        print(f"Игрок {player_name} перешел на следующий уровень.")
                    elif result == "main_menu":
                        print(f"Игрок {player_name} вернулся в главное меню.")
                    elif result == "quit":
                        pygame.quit()
                    print("Переход на следующий уровень!")
                    return  # Можем здесь перейти на новый уровень
                
            for lever_rect in lever_rects:
                if player1.colliderect(lever_rect) or player2.colliderect(lever_rect):
                    # Логика активации рычага (например, открытие дверей)
                    for door_rect in door_rects:
                        if door_rect.colliderect(lever_rect):
                            door_rect.width = 0  # Закрытие двери
                        else:
                            door_rect.width = 50  # Открытие двери

            for lever_rect in lever_rects:
                pygame.draw.rect(screen, GREY, lever_rect)  # Рычаг

            for door_rect in door_rects:
                pygame.draw.rect(screen, (0, 255, 0), door_rect)  # Дверь

            # Отображение спрайтов игроков
            screen.blit(fire_sprite, player1)  # Огонь
            screen.blit(water_sprite, player2)  # Вода

            # Обновление экрана
            pygame.display.update()

            # Установка FPS
            clock.tick(FPS)

    if __name__ == '__main__':
        pygame.mixer.music.play(-1, 0.0)  # Запуск музыки в цикле

        # Основной цикл
        while True:
            result = UIManager.start_screen()

            if result == "level":
                level = UIManager.level_selection()  # Переход к выбору уровня
                if level != "back":
                    main(level)  # Переход к выбранному уровню
            elif result == "volume":
                result = UIManager.volume_settings()  # Настройки громкости
                if result == "back":
                    continue  # Возвращаемся в главное меню