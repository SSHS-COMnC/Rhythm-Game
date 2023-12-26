import pygame
import time
from constants import *
from classes import Map

# Initialize Pygame
pygame.init()

# Set up display (not necessary for playing music, but Pygame initialization is required)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Music Player")

# Initialize mixer
pygame.mixer.init()

map_p1 = Map()

# Load music file
music_file = "tracks/DEAF KEV - Invincible [NCS Release].mp3"
pygame.mixer.music.load(music_file)
bpm = 100

# loading images
image_paths = [f"./images/{knot.name}.png" for knot in KNOTS]
image_dict = {knot.name: pygame.image.load(image_path).convert_alpha() for knot, image_path in zip(KNOTS, image_paths)}

font = pygame.font.Font(None, 36)

TIMER_EVENT = pygame.USEREVENT + 1

beat_interval = 60 / bpm

# Play the music
pygame.mixer.music.play()

clock = pygame.time.Clock()
fps = 60

latency = 0 # 레이턴시, ms 단위

time_initial = time.time() + latency / 1000


print(map_p1.deck)

def key_to_no(key):
    if key == pygame.K_a:
        return 1
    elif key == pygame.K_s:
        return 2
    elif key == pygame.K_d:
        return 3
    elif key == pygame.K_f:
        return 4

# Main loop (to keep the program running while the music plays)
while True:
    time_current = (time.time() - time_initial)/beat_interval
    map_p1.update(time_current)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f]:
                print(time_current)
                map_p1.on_input_at(time_current, key_to_no(event.key))


    # draw background
    screen.fill((255, 255, 255))
    
    # Render text surface
    text_surface = font.render("DECK", True, (0, 0, 0))
    
    # Blit text onto the screen
    screen.blit(text_surface, (850, 20))
    
    # draw deck images
    pygame.draw.rect(screen, (0, 0 ,0), (800, 50, 175, 420), 3)
    for idx, knot in enumerate(map_p1.deck):
        screen.blit(image_dict[knot.name], (830, 70+idx * 130))
            
    # draw next images
    for idx, knot in enumerate(map_p1.nexts):
        screen.blit(image_dict[knot.name], (idx * 200, 0))
        
        
    # draw the moving line
    pygame.draw.rect(screen, (0, 0, 0), (40, 120, 680, 270), 3)
    
    # Update the display
    pygame.display.flip()

    # Control the frame rate
    clock.tick(fps)