#main.py
import pygame
import time
from player import Player
from world import World
from database import save_result, get_best_result

# Инициализация Pygame
pygame.init()

# Установим размеры окна
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("SCRAA")

# Шрифты и цвета
font = pygame.font.Font(None, 36)
WHITE = (255, 255, 255)

# Загрузим музыку
pygame.mixer.music.load('assets/sounds/background_music.mp3')
pygame.mixer.music.play(-1)  # Зацикливаем музыку

# Главная игра
def main_game():
    player = Player()
    world = World(screen)
    all_sprites = pygame.sprite.Group(player)
    clock = pygame.time.Clock()

    running = True
    level = 1
    score = 0
    start_time = time.time()
    
    while running:
        screen.fill((0, 0, 0))  # Черный фон
        world.update(level)  # Обновляем мир
        all_sprites.update()  # Обновляем все спрайты
        all_sprites.draw(screen)  # Отображаем спрайты
        
        # Показываем статистику
        elapsed_time = int(time.time() - start_time)
        time_text = font.render(f"Time: {elapsed_time}s", True, WHITE)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(time_text, (10, 10))
        screen.blit(score_text, (10, 50))
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Столкновения
        if player.rect.colliderect(world.portal.rect):
            # Переход на следующий уровень
            level += 1
            score += 100  # Бонус за уровень
            start_time = time.time()  # Сбрасываем таймер
        
        # Обновляем экран
        pygame.display.flip()
        clock.tick(60)

    # Завершаем игру, сохраняя результаты
    save_result("Player1", level, score, elapsed_time)

# Запуск игры
main_game()
pygame.quit()
