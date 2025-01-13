#enemy.py
import pygame

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load('assets/images/enemy.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
    
    def update(self):
        # Простое движение врага (например, из стороны в сторону)
        self.rect.x += self.speed
        if self.rect.x > 750 or self.rect.x < 0:
            self.speed = -self.speed
