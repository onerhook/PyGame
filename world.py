#world.py
import pygame
from enemy import Enemy

class World:
    def __init__(self, screen):
        self.screen = screen
        self.portal = pygame.sprite.Sprite()
        self.portal.image = pygame.Surface((50, 50))
        self.portal.image.fill((0, 255, 0))  # Зеленый портал
        self.portal.rect = self.portal.image.get_rect()
        self.portal.rect.center = (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100)
        self.enemies = pygame.sprite.Group()
        
        # Добавляем врагов
        self.enemies.add(Enemy(100, 100))
        self.enemies.add(Enemy(300, 300))

    def update(self, level):
        # Механики для разных уровней
        if level == 1:
            self.portal.rect.center = (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100)
        elif level == 2:
            self.portal.rect.center = (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 200)
        
        # Обновляем врагов
        self.enemies.update()
        
        # Отображаем портал и врагов
        self.screen.blit(self.portal.image, self.portal.rect)
        self.enemies.draw(self.screen)
