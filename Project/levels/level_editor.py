import pygame
import pickle # helps easily save files and get the data out
from os import path
import subprocess
import os

# Ensure working directory is the script's folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

pygame.init()

clock = pygame.time.Clock()
fps = 60

# Game window
tile_size = 40
cols = 20
margin = 80  
screen_width = (tile_size * cols)  
screen_height = ((tile_size * cols) + margin)

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Level Editor')

# Load images
bg_img = pygame.image.load('../img/background0.png')
bg_img = pygame.transform.scale(bg_img, (screen_width, screen_height - margin))
dirt_img = pygame.image.load('../img/dirt.png')
grass_img = pygame.image.load('../img/grass.png')
blob_img = pygame.image.load('../img/blob.png')
platform_x_img = pygame.image.load('../img/platform_x.png')
platform_y_img = pygame.image.load('../img/platform_y.png')
lava_img = pygame.image.load('../img/lava.png')
coin_img = pygame.image.load('../img/coin.png')
door_img = pygame.image.load('../img/exit.png')
save_img = pygame.image.load('../img/button_save.png')
reset_img = pygame.image.load('../img/button_reset.png')
main_menu_img = pygame.image.load('../img/button_main-menu.png')

# Define game variables
clicked = False
level = 1

# Define colours
white = (255, 255, 255)
green = (144, 201, 120)
black = (0, 0, 0)

font = pygame.font.SysFont('Futura', 24)

# Load level 1 data if it exists, otherwise create empty tile list
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)
    pickle_in.close()
else:
    world_data = []
    for row in range(20):
        r = [0] * 20
        world_data.append(r)
    for tile in range(0, 20):
        world_data[19][tile] = 2

# Function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_grid():
    for c in range(21):
        # Vertical lines
        pygame.draw.line(screen, white, (c * tile_size, 0), (c * tile_size, screen_height - margin))
        # Horizontal lines
        pygame.draw.line(screen, white, (0, c * tile_size), (screen_width, c * tile_size))

def draw_world():
    for row in range(20):
        for col in range(20):
            if world_data[row][col] > 0:
                if world_data[row][col] == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    screen.blit(img, (col * tile_size, row * tile_size))
                if world_data[row][col] == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    screen.blit(img, (col * tile_size, row * tile_size))
                if world_data[row][col] == 3:
                    img = pygame.transform.scale(blob_img, (tile_size, int(tile_size * 0.75)))
                    screen.blit(img, (col * tile_size, row * tile_size + (tile_size * 0.25)))
                if world_data[row][col] == 4:
                    img = pygame.transform.scale(platform_x_img, (tile_size, tile_size // 2))
                    screen.blit(img, (col * tile_size, row * tile_size))
                if world_data[row][col] == 5:
                    img = pygame.transform.scale(platform_y_img, (tile_size, tile_size // 2))
                    screen.blit(img, (col * tile_size, row * tile_size))
                if world_data[row][col] == 6:
                    img = pygame.transform.scale(lava_img, (tile_size, tile_size // 2))
                    screen.blit(img, (col * tile_size, row * tile_size + (tile_size // 2)))
                if world_data[row][col] == 7:
                    img = pygame.transform.scale(coin_img, (tile_size // 2, tile_size // 2))
                    screen.blit(img, (col * tile_size + (tile_size // 4), row * tile_size + (tile_size // 4)))
                if world_data[row][col] == 8:
                    img = pygame.transform.scale(door_img, (tile_size, int(tile_size * 1.5)))
                    screen.blit(img, (col * tile_size, row * tile_size - (tile_size // 2)))
                if world_data[row][col] == 9:
                    # AI Chaser enemy - blob with red tint indicator
                    img = pygame.transform.scale(blob_img, (tile_size, int(tile_size * 0.75)))
                    img = img.copy()
                    red_overlay = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 80))
                    img.blit(red_overlay, (0, 0))
                    screen.blit(img, (col * tile_size, row * tile_size + (tile_size * 0.25)))
                    # Draw "AI" label above the enemy
                    ai_label = pygame.font.SysFont('Arial', 12).render('AI', True, (255, 0, 0))
                    screen.blit(ai_label, (col * tile_size + tile_size // 4, row * tile_size))

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self):
        action = False
        pos = pygame.mouse.get_pos()

        # Check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        # Draw button
        screen.blit(self.image, (self.rect.x, self.rect.y))

        return action

# Create load and save buttons and exit too
save_button = Button(47, screen_height - margin + 13, save_img)
reset_button = Button(298, screen_height - margin + 13, reset_img)
main_menu_button = Button(549, screen_height - margin + 13, main_menu_img)


# Save indicator
save_timer = 0
save_message = ''

# Main game loop
run = True
while run:

    clock.tick(fps)

    # Draw background
    screen.fill(green)
    screen.blit(bg_img, (0, 0))

    # Load and save level
    if save_button.draw():
        pickle_out = open(f'level{level}_data', 'wb')
        pickle.dump(world_data, pickle_out)
        pickle_out.close()
        save_timer = fps  # Show message for 1 second
        save_message = 'Saved!'
    if reset_button.draw():
        if path.exists(f'level{level}_data'):
            pickle_in = open(f'level{level}_data', 'rb')
            world_data = pickle.load(pickle_in)
            save_timer = fps
            save_message = 'Reset!'
    if main_menu_button.draw():
        pygame.quit()
        subprocess.run(['/usr/bin/python', '/home/marioselef/School/Pygame/Project/platformer.py'])
        exit()

    # Show the grid and draw the level tiles
    draw_grid()
    draw_world()

    # Text showing current level
    level_text = f'Level: {level}'
    instruction_text = 'Press UP or DOWN to change level'


    # Get text width using the font's size method
    level_text_width = font.size(level_text)[0]
    instruction_text_width = font.size(instruction_text)[0]

    # Position the text
    draw_text(level_text, font, black, screen_width - level_text_width - 10, 10)  # Top-right corner
    draw_text(instruction_text, font, black, screen_width - instruction_text_width - 10, 40)  # Below the first text


    # Event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN and not clicked:
            clicked = True
            pos = pygame.mouse.get_pos()
            x = pos[0] // tile_size
            y = pos[1] // tile_size
            if x < 20 and y < 20:
                if pygame.mouse.get_pressed()[0] == 1:
                    world_data[y][x] += 1
                    if world_data[y][x] > 9:
                        world_data[y][x] = 0
                elif pygame.mouse.get_pressed()[2] == 1:
                    world_data[y][x] -= 1
                    if world_data[y][x] < 0:
                        world_data[y][x] = 9
        if event.type == pygame.MOUSEBUTTONUP:
            clicked = False
        if event.type == pygame.KEYDOWN:
            max_level = 1
            while path.exists(f'level{max_level}_data'):
                max_level += 1
            if event.key == pygame.K_UP and level < max_level:
                level += 1
            elif event.key == pygame.K_DOWN and level > 1:
                level -= 1
            if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                if path.exists(f'level{level}_data'):
                    pickle_in = open(f'level{level}_data', 'rb')
                    world_data = pickle.load(pickle_in)
                    pickle_in.close()
                else:
                    world_data = []
                    for row in range(20):
                        r = [0] * 20
                        world_data.append(r)
                    for tile in range(0, 20):
                        world_data[19][tile] = 2

    # Draw save/reset indicator
    if save_timer > 0:
        save_font = pygame.font.SysFont('Bauhaus 93', 50)
        msg = save_font.render(save_message, True, (0, 180, 0))
        msg_rect = msg.get_rect(center=(screen_width // 2, (screen_height - margin) // 2))
        screen.blit(msg, msg_rect)
        save_timer -= 1

    pygame.display.update()

pygame.quit()
