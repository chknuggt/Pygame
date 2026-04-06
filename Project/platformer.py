import pygame
import pickle
from pygame import mixer
import math
import subprocess
import os

# Ensure working directory is the script's folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60

# Game window
screen_width = 800
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Platformer with AI Enemies')

# Define font
font = pygame.font.SysFont('Bauhaus 93', 70)
font_small = pygame.font.SysFont('Bauhaus 93', 30)

# Define game variables
tile_size = 40
game_over = 0
main_menu = True
paused = False
level = 1
max_levels = 5
score = 0

# Define colours
white = (255, 255, 255)
blue = (0, 0, 255)
red = (255, 0, 0)
black = (0, 0, 0)

# Load images
bg_img = pygame.image.load('img/background0.png')
bg_img = pygame.transform.scale(bg_img, (screen_width, screen_height))
restart_img = pygame.image.load('img/button_restart.png')
start_img = pygame.image.load('img/button_start.png')
exit_img = pygame.image.load('img/button_exit.png')
pause_img = pygame.image.load('img/button_pause.png')
resume_img = pygame.image.load('img/button_resume.png')
level_editor_img = pygame.image.load('img/button_level-editor.png')

# Load sounds (if available)
try:
    pygame.mixer.music.load('img/musiccc.wav')
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1, 0.0, 5000)
    coin_fx = pygame.mixer.Sound('img/coin.wav')
    coin_fx.set_volume(0.5)
    jump_fx = pygame.mixer.Sound('img/jump.wav')
    jump_fx.set_volume(0.5)
    game_over_fx = pygame.mixer.Sound('img/game_over.wav')
    game_over_fx.set_volume(0.5)
except:
    coin_fx = None
    jump_fx = None
    game_over_fx = None

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# Function to reset level
def reset_level(level):
    player.reset(100, screen_height - 130)
    blob_group.empty()
    chaser_group.empty()
    platform_group.empty()
    coin_group.empty()
    lava_group.empty()
    exit_group.empty()

    # Load level data and create world
    world_data = []
    if level <= max_levels:
        with open(f'levels/level{level}_data', 'rb') as pickle_in:
            world_data = pickle.load(pickle_in)
    world = World(world_data)

    return world

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        screen.blit(self.image, self.rect)
        return action

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.reset(x, y)

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = 20

        if game_over == 0:
            # Get keypresses
            key = pygame.key.get_pressed()
            if key[pygame.K_UP] and self.jumped == False and self.in_air == False:
                if jump_fx:
                    jump_fx.play()
                self.vel_y = -15
                self.jumped = True
            if key[pygame.K_UP] == False:
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # Handle animation
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # Add gravity
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            # Check for collision
            self.in_air = True
            for tile in world.tile_list:
                # Check for collision in x direction
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # Check for collision in y direction
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # Check if below the ground i.e. jumping
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    # Check if above the ground i.e. falling
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            # Check for collision with enemies
            if pygame.sprite.spritecollide(self, blob_group, False):  # type: ignore[arg-type]
                game_over = -1
                if game_over_fx:
                    game_over_fx.play()
            if pygame.sprite.spritecollide(self, chaser_group, False):  # type: ignore[arg-type]
                game_over = -1
                if game_over_fx:
                    game_over_fx.play()

            # Check for collision with lava
            if pygame.sprite.spritecollide(self, lava_group, False):  # type: ignore[arg-type]
                game_over = -1
                if game_over_fx:
                    game_over_fx.play()

            # Check for collision with exit
            if pygame.sprite.spritecollide(self, exit_group, False):  # type: ignore[arg-type]
                game_over = 1

            # Check for collision with platforms
            for platform in platform_group:
                # Collision in the x direction
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # Collision in the y direction
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # Check if below platform
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    # Check if above platform
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    # Move sideways with the platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction

            # Update player coordinates
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, blue, (screen_width // 2) - 200, screen_height // 2)
            if self.rect.y > 200:
                self.rect.y -= 5

        # Draw player onto screen
        screen.blit(self.image, self.rect)

        return game_over

    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = pygame.image.load(f'img/guy{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('img/ghost.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rect.width = 30
        self.rect.x += 5  # Center the narrower hitbox
        self.width = self.rect.width
        self.height = self.rect.height
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True

class World():
    def __init__(self, data):
        self.tile_list = []

        # Load images
        dirt_img = pygame.image.load('img/dirt.png')
        grass_img = pygame.image.load('img/grass.png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    blob = Enemy(col_count * tile_size, row_count * tile_size + 15)
                    blob_group.add(blob)
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                if tile == 9:
                    chaser = ChaserEnemy(col_count * tile_size, row_count * tile_size + 15)
                    chaser_group.add(chaser)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        base_img = pygame.image.load('img/blob.png')
        self.base_image = pygame.transform.scale(base_img, (tile_size, int(tile_size * 0.75)))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0
        self.patrol_distance = 50
        self.chase_distance = 150
        self.chase_speed = 3
        self.patrol_speed = 2
        self.vel_y = 0

    def update(self):
        dx = 0
        dy = 0

        distance_to_player = math.sqrt((self.rect.centerx - player.rect.centerx)**2 +
                                      (self.rect.centery - player.rect.centery)**2)

        if distance_to_player < self.chase_distance and game_over == 0:
            if player.rect.centerx < self.rect.centerx:
                dx = -self.chase_speed
                self.move_direction = -1
            elif player.rect.centerx > self.rect.centerx:
                dx = self.chase_speed
                self.move_direction = 1
        else:
            dx = self.move_direction * self.patrol_speed
            self.move_counter += self.patrol_speed
            if abs(self.move_counter) > self.patrol_distance:
                self.move_direction *= -1
                self.move_counter = 0

        # Apply gravity
        self.vel_y += 1
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        # Check for collision with world tiles
        for tile in world.tile_list:
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                dx = 0
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                if self.vel_y >= 0:
                    dy = tile[1].top - self.rect.bottom
                    self.vel_y = 0
                else:
                    dy = tile[1].bottom - self.rect.top
                    self.vel_y = 0

        self.rect.x += dx
        self.rect.y += dy

        # Flip image based on direction
        if self.move_direction == -1:
            self.image = pygame.transform.flip(self.base_image, True, False)
        else:
            self.image = self.base_image.copy()

class ChaserEnemy(pygame.sprite.Sprite):
    """AI enemy that chases the player horizontally when in range, with gravity."""
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        # Load and tint the blob image red
        base_img = pygame.image.load('img/blob.png')
        base_img = pygame.transform.scale(base_img, (tile_size, int(tile_size * 0.75)))
        self.base_image = base_img.copy()
        red_overlay = pygame.Surface(self.base_image.get_size(), pygame.SRCALPHA)
        red_overlay.fill((255, 0, 0, 80))
        self.base_image.blit(red_overlay, (0, 0))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.start_x = x
        self.move_direction = 1
        self.move_counter = 0
        self.patrol_speed = 1
        self.chase_speed = 2
        self.detect_range = 200  # Euclidean distance to start chasing
        self.vel_y = 0

    def update(self):
        dx = 0
        dy = 0

        # Calculate Euclidean distance to player (sqrt formula)
        dist = math.sqrt((self.rect.centerx - player.rect.centerx) ** 2 +
                         (self.rect.centery - player.rect.centery) ** 2)

        if dist < self.detect_range and game_over == 0:
            # Chase horizontally only - move toward player's x position
            if player.rect.centerx < self.rect.centerx:
                dx = -self.chase_speed
                self.move_direction = -1
            elif player.rect.centerx > self.rect.centerx:
                dx = self.chase_speed
                self.move_direction = 1
        else:
            # Patrol behavior - move back and forth
            dx = self.move_direction * self.patrol_speed
            self.move_counter += self.patrol_speed
            if abs(self.move_counter) > 50:
                self.move_direction *= -1
                self.move_counter = 0

        # Apply gravity
        self.vel_y += 1
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        # Check for collision with world tiles
        for tile in world.tile_list:
            # Collision in x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                dx = 0
            # Collision in y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                if self.vel_y >= 0:
                    dy = tile[1].top - self.rect.bottom
                    self.vel_y = 0
                else:
                    dy = tile[1].bottom - self.rect.top
                    self.vel_y = 0

        # Apply movement
        self.rect.x += dx
        self.rect.y += dy

        # Flip image based on direction
        if self.move_direction == -1:
            self.image = pygame.transform.flip(self.base_image, True, False)
        else:
            self.image = self.base_image.copy()


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/platform.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        # Create a red rectangle for lava since we don't have the image
        self.image = pygame.Surface((tile_size, tile_size // 2))
        self.image.fill((255, 100, 0))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/coin.png')
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/exit.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Create sprite groups
blob_group = pygame.sprite.Group()
chaser_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# Create player
player = Player(100, screen_height - 130)

# Load initial world
world_data = []
if level <= max_levels:
    with open(f'levels/level{level}_data', 'rb') as pickle_in:
        world_data = pickle.load(pickle_in)
world = World(world_data)

# Create buttons
restart_button = Button(screen_width // 2 - 102, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 - 102, screen_height // 2 - 80, start_img)
exit_button = Button(screen_width // 2 - 102, screen_height // 2 + 160, exit_img)
level_editor_button = Button(screen_width // 2 - 102, screen_height // 2 + 40, level_editor_img)
pause_button = Button(10, 10, pause_img)
resume_button = Button(screen_width // 2 - 102, screen_height // 2 - 70, resume_img)
pause_restart_button = Button(screen_width // 2 - 102, screen_height // 2, restart_img)
pause_main_menu_button = Button(screen_width // 2 - 102, screen_height // 2 + 70, pygame.image.load('img/button_main-menu.png'))

run = True
while run:

    clock.tick(fps)

    screen.blit(bg_img, (0, 0))

    if main_menu == True:
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
        if level_editor_button.draw():
            pygame.quit()
            subprocess.run(['/usr/bin/python', '/home/marioselef/School/Pygame/Project/levels/level_editor.py'])
            exit()
    else:
        world.draw()

        if paused:
            pause_text = font.render('PAUSED', True, blue)
            screen.blit(pause_text, (screen_width // 2 - pause_text.get_width() // 2, screen_height // 2 - 150))
            if resume_button.draw():
                paused = False
            if pause_restart_button.draw():
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = 0
                paused = False
            if pause_main_menu_button.draw():
                main_menu = True
                paused = False
                level = 1
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = 0
                # Prevent the held click from immediately triggering a main menu button
                start_button.clicked = True
                exit_button.clicked = True
                level_editor_button.clicked = True
        else:
            if game_over == 0:
                blob_group.update()
                chaser_group.update()
                platform_group.update()
                # Check if player has collected a coin
                if pygame.sprite.spritecollide(player, coin_group, True):  # type: ignore[arg-type]
                    score += 1
                    if coin_fx:
                        coin_fx.play()
                draw_text('X ' + str(score), font_small, white, tile_size - 10, 10)
                # Draw pause button during gameplay
                if pause_button.draw():
                    paused = True

            blob_group.draw(screen)
            chaser_group.draw(screen)
            platform_group.draw(screen)
            lava_group.draw(screen)
            coin_group.draw(screen)
            exit_group.draw(screen)

            game_over = player.update(game_over)

            # If player has died
            if game_over == -1:
                if restart_button.draw():
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0

            # If player has completed the level
            if game_over == 1:
                # Reset game and go to next level
                level += 1
                if level <= max_levels:
                    # Reset level
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                else:
                    draw_text('YOU WIN!', font, blue, (screen_width // 2) - 140, screen_height // 2)
                    if restart_button.draw():
                        level = 1
                        # Reset level
                        world_data = []
                        world = reset_level(level)
                        game_over = 0
                        score = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()
