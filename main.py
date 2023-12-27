import pygame
import pygame.midi
import time
from constants import *
from classes import *
from midi import _print_device_info

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
bpm = 50

# loading images
image_paths = [f"./images/{knot.name}.png" for knot in KNOTS]
image_dict = {knot.name: pygame.image.load(image_path).convert_alpha() for knot, image_path in zip(KNOTS, image_paths)}

font = pygame.font.Font(None, 36)


# Rectangle parameters
rectangle_width = 680
rectangle_height = 270
rectangle_x = 40
rectangle_y = 120
border_thickness = 2

line_x = 100  
line_length = rectangle_height

# Shiny effect parameters
shiny_effect_duration = 0.2  # Duration of the shiny effect in seconds
shiny_effect_start_time = 0
shiny_effect_active = False


TIMER_EVENT = pygame.USEREVENT + 1

beat_interval = 60 / bpm


# Play the music
pygame.mixer.music.play()

clock = pygame.time.Clock()
fps = 60

latency = 0 # 레이턴시, ms 단위

time_initial = time.time() + latency / 1000


print(map_p1.deck)

def key_to_no(event):
    if IS_INPUT_DEVICE_MIDI:
        if event.status == 145:
            keys = [41, 43, 45, 47]
            if event.data1 not in keys:
                return False, None
            else:
                return True, 1 + keys.index(event.data1)
        else:
            return False, None
    else:
        key = event.key
        if key == pygame.K_a:
            return True, 1
        elif key == pygame.K_s:
            return True, 2
        elif key == pygame.K_d:
            return True, 3
        elif key == pygame.K_f:
            return True, 4
        else:
            return False, None

if IS_INPUT_DEVICE_MIDI:
    pygame.fastevent.init()
    event_get = pygame.fastevent.get
    event_post = pygame.fastevent.post
    pygame.midi.init()
    _print_device_info()

    input_id = pygame.midi.get_default_input_id()

    print("using input_id :%s:" % input_id)
    midi_input = pygame.midi.Input(input_id)
input_event_type = pygame.midi.MIDIIN if IS_INPUT_DEVICE_MIDI else pygame.KEYDOWN

temp_combo_count = 0
combo_texts = []

# Main loop (to keep the program running while the music plays)
while True:
    time_current = (time.time() - time_initial)/beat_interval
    map_p1.update(time_current)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        if event.type == input_event_type:
            appropriate, key_no = key_to_no(event)
            if appropriate:
                print(time_current)
                map_p1.on_input_at(time_current, key_no)
                mark = Mark(line_x, rectangle_y + line_length // 2, (0, 255, 0))
                mark.create_particles()
                shiny_effect_active = True
                shiny_effect_start_time = time.time()
                map_p1.marks.append(mark)


    # draw background
    screen.fill((255, 255, 255))
    
    # Draw bordered rectangle
    pygame.draw.rect(screen, (0, 0, 0), (rectangle_x, rectangle_y, rectangle_width, rectangle_height), border_thickness)
    # draw a vertical line in side the bordered rectangle, at positions of 1/8, 3/8, 5/8, 7/8
    for i in range(1, 8, 2):
        pygame.draw.line(screen, (0, 0, 0), (rectangle_x + rectangle_width * i // 8, rectangle_y), (rectangle_x + rectangle_width * i // 8, rectangle_y + rectangle_height), 1)
    
    # Calculate line position within the rectangle
    line_progress = time_current - int(time_current)
    line_x = rectangle_x + line_progress * rectangle_width
    
    # Draw the line
    pygame.draw.line(screen, (0, 0, 0), (line_x, rectangle_y), (line_x, rectangle_y + line_length), 2)  # Draw a line within the rectangle

    
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
        
    # draw combo text
    if map_p1.combo_count  != temp_combo_count:
        if map_p1.combo_count > 0:
            combo_texts.append(ComboText(320,420, f"{RATINGS[map_p1.combo_rating]}  X {map_p1.combo_count}"))
    for combo_text in combo_texts:
        combo_text.update()
        combo_text.draw(screen)

        if combo_text.timer <= 0:
            combo_texts.remove(combo_text)
    temp_combo_count = map_p1.combo_count
    
    # Shiny effect
    if shiny_effect_active:
        shiny_elapsed_time = time.time() - shiny_effect_start_time
        
        if shiny_elapsed_time < shiny_effect_duration:
            pygame.draw.line(screen, (0, 255, 0), (line_x, rectangle_y), (line_x , rectangle_y + line_length), 5)  # Flashing effect
            shiny_progress = shiny_elapsed_time / shiny_effect_duration
            for i in range(10):
                shiny_alpha = int((1 - shiny_progress) * 255 * (10 - i) * 0.1)
                vertical_line = pygame.Surface((5, line_length), pygame.SRCALPHA)
                vertical_line.fill((0, 255, 0, shiny_alpha))
                screen.blit(vertical_line, (line_x + i * 3, rectangle_y))
                vertical_line2 = pygame.Surface((5, line_length), pygame.SRCALPHA)
                vertical_line2.fill((0, 255, 0, shiny_alpha))
                screen.blit(vertical_line2, (line_x - i * 3, rectangle_y))
        else:
            shiny_effect_active = False
            
    # Update and draw marks with particles
    for mark in map_p1.marks:
        mark.update_particles()
        mark.draw_particles(screen)
    
    # Update the display
    pygame.display.flip()

    # Control the frame rate
    clock.tick(fps)
    
    if IS_INPUT_DEVICE_MIDI:
        if midi_input.poll():
            midi_events = midi_input.read(10)
            # convert them into pygame events.
            midi_evs = pygame.midi.midis2events(midi_events, midi_input.device_id)

            for m_e in midi_evs:
                event_post(m_e)

del midi_input
pygame.midi.quit()