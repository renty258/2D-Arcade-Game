import pygame
import random
import sys
import os

pygame.init()

# Параметры экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Аркада")

# Загрузка изображений
background = pygame.image.load("background.jpg")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

player_image = pygame.image.load("player.png")
player_image = pygame.transform.scale(player_image, (50, 50))

obstacle_image = pygame.image.load("obstacle.png")
obstacle_image = pygame.transform.scale(obstacle_image, (50, 50))

explosion_image = pygame.image.load("explosion.png")
explosion_image = pygame.transform.scale(explosion_image, (WIDTH, HEIGHT))

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)

# Шрифты
font_large = pygame.font.SysFont(None, 72)
font_small = pygame.font.SysFont(None, 36)

# Файл рекордов
SCORES_FILE = "scores.txt"

# Функция для текста с обводкой
def draw_text_outline(text, font, color, outline_color, surface, x, y):
    base = font.render(text, True, color)
    outline = font.render(text, True, outline_color)
    rect = base.get_rect(center=(x, y))
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, -2), (-2, 2), (2, 2)]:
        surface.blit(outline, (rect.x + dx, rect.y + dy))
    surface.blit(base, rect)

# Кнопки
def draw_button(text, x, y, w, h):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    rect = pygame.Rect(x, y, w, h)

    if rect.collidepoint(mouse):
        pygame.draw.rect(screen, GRAY, rect)
        if click[0] == 1:
            pygame.time.delay(200)
            return True
    else:
        pygame.draw.rect(screen, DARK_GRAY, rect)

    draw_text_outline(text, font_small, BLACK, WHITE, screen, x + w // 2, y + h // 2)
    return False

# Работа с рекордами
def save_score(score):
    with open(SCORES_FILE, "a") as f:
        f.write(str(score) + "\n")

def load_scores():
    if not os.path.exists(SCORES_FILE):
        return []
    with open(SCORES_FILE, "r") as f:
        return [int(line.strip()) for line in f if line.strip().isdigit()]

# Таблица рекордов
def show_high_scores():
    running = True
    while running:
        screen.blit(background, (0, 0))
        draw_text_outline("Таблица рекордов", font_large, BLACK, WHITE, screen, WIDTH // 2, 50)

        scores = load_scores()
        scores.sort(reverse=True)

        if scores:
            draw_text_outline(f"Лучший результат: {scores[0]}", font_small, BLACK, WHITE, screen, WIDTH // 2, 120)
        else:
            draw_text_outline("Нет результатов", font_small, BLACK, WHITE, screen, WIDTH // 2, 120)

        for i, score in enumerate(scores[:10]):
            draw_text_outline(f"{i+1}) {score}", font_small, BLACK, WHITE, screen, WIDTH // 2, 170 + i * 30)

        if draw_button("Назад", WIDTH // 2 - 75, HEIGHT - 80, 150, 50):
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()

# Классы для объектов игры
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("player.png")
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT - 60)
        self.speed = 7

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed

class Obstacle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("obstacle.png")
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - 50)
        self.rect.y = -50
        self.speed = 5

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()  # Удаляет препятствие из группы

# Оптимизация с пулом объектов для препятствий
class ObstaclePool:
    def __init__(self, size=10):
        self.pool = [Obstacle() for _ in range(size)]
        self.available = self.pool.copy()

    def get_obstacle(self):
        if self.available:
            return self.available.pop()
        return Obstacle()  # Создаём новый, если нет доступных объектов

    def return_obstacle(self, obstacle):
        obstacle.rect.y = -50  # Возвращаем препятствие в начальную позицию
        self.available.append(obstacle)

# Игровой цикл
def game_loop():
    global score
    score = 0
    spawn_timer = 0
    clock = pygame.time.Clock()
    running = True

    # Создание групп спрайтов
    all_sprites = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()

    # Создание игрока и добавление его в группу
    player = Player()
    all_sprites.add(player)

    # Пул препятствий
    obstacle_pool = ObstaclePool()

    last_spawn_time = pygame.time.get_ticks()

    # Основной игровой цикл
    while running:
        clock.tick(60)

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Обновление всех спрайтов
        all_sprites.update()

        # Управление временем появления препятствий
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time >= 1000:  # Каждые 1 секунду
            obstacle = obstacle_pool.get_obstacle()
            all_sprites.add(obstacle)
            obstacles.add(obstacle)
            last_spawn_time = current_time

        # Проверка на столкновение игрока с препятствием
        if pygame.sprite.spritecollide(player, obstacles, True):
            screen.blit(explosion_image, (0, 0))
            pygame.display.flip()
            pygame.time.delay(1000)
            save_score(score)
            break

        # Удаляем препятствия, которые ушли за экран
        for obstacle in obstacles:
            if obstacle.rect.top > HEIGHT:
                obstacle_pool.return_obstacle(obstacle)
                obstacle.kill()

        # Отображение
        screen.blit(background, (0, 0))
        all_sprites.draw(screen)
        draw_text_outline(f"Счёт: {score}", font_small, BLACK, WHITE, screen, WIDTH // 2, 30)

        pygame.display.flip()

# Главное меню
def main_menu():
    while True:
        screen.blit(background, (0, 0))
        draw_text_outline("2D Аркада", font_large, BLACK, WHITE, screen, WIDTH // 2, 150)

        if draw_button("Играть", WIDTH // 2 - 100, 250, 200, 50):
            game_loop()
        if draw_button("Таблица рекордов", WIDTH // 2 - 100, 320, 200, 50):
            show_high_scores()
        if draw_button("Выйти", WIDTH // 2 - 100, 390, 200, 50):
            pygame.quit()
            sys.exit()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()

# Запуск игры
main_menu()
