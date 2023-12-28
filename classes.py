from constants import *
from typing import Set, List, Dict
import math
import pygame

class Rope: # Knot가 될 수도 있는 무언가
    def __init__(self, start: int, knot: Knot, length: int, rating: int, input_count: int, key_no: int):
        self.start, self.knot, self.length, self.rating = start, knot, length, rating
        self.n = self.knot.rhythm.n
        self.count = 1
        self.input_counts = [input_count]
        self.key_nos = [key_no]

    def __repr__(self) -> str:
        return f"""**
{self.knot}
COUNTS: {self.input_counts}
RATING: {RATINGS[self.rating]}

"""
        
    def apply(self, input_count: int, key_no):
        self.count += 1
        self.input_counts.append(input_count)
        self.key_nos.append(key_no)

    @property
    def interval(self) -> Tuple[float, float]:
        beats = sum(self.knot.rhythm.ratio[:self.count])
        midpoint = (self.start + beats * self.length)/ RHYTHM_GRID
        distance = self.length * RATING_RULE[self.rating] / RHYTHM_GRID
        return (midpoint - distance, midpoint + distance)
    
    @property
    def available_keys(self) -> List[int]:
        all_keys = list(range(1, KEY_COUNTS + 1))
        match self.knot.key_type:
            case "free":
                return all_keys
            case "one":
                return [self.key_nos[-1]]
            case "slide":
                if self.count == 1:
                    my_keys = {self.key_nos[0] - 1, self.key_nos[0] + 1}
                else:
                    my_keys = {2 * self.key_nos[-1] - self.key_nos[-2]}
                return list(my_keys & set(all_keys))
            case "trill":
                if self.count == 1:
                    return all_keys
                else:
                    return [self.key_nos[-2]]
    
    def is_complete(self) -> bool:
        return self.n == self.count

class Map:
    def __init__(self) -> None:
        self.count = 1
        self.deck = [self.pick() for _ in range(DECK_SIZE)]
        self.nexts = [self.pick() for _ in range(NEXT_SIZE)]
        self.deck_rating = [RATING_COUNTS] * DECK_SIZE
        self.combo_rating = 0
        self.combo_count = 0
        self.timeline: List[Tuple[float, Rope, bool]] = []
        self.alive: List[Rope] = []
        self.open: List[Rope] = []
        self.done: List[Rope] = []
        self.accept: List[Rope|None] = [None] * DECK_SIZE
        self.finish: List[Rope|None] = [None] * DECK_SIZE
        self.ignore_input_counts: List[int] = []
        self.input_count = 0
        self.combo_check: Dict[int, List[int]] = {}
        self.marks = []
        
        self.score = 0
        
    
    def pick(self):
        val = pick_random_at(self.count)
        self.count += 1
        return val
    
    def create_ropes(self, time_input: float, key_no: int, available_pattern: Set[Knot]):
        for rating in range(RATING_COUNTS):
            rating_rule = RATING_RULE[rating]
            for pattern in available_pattern:
                for length in pattern.rhythm.length_available:
                    distance = length / RHYTHM_GRID * rating_rule
                    low = math.ceil(RHYTHM_GRID * (time_input - distance))
                    high = math.trunc(RHYTHM_GRID * (time_input + distance))
                    for start in range(low, high + 1):
                        self.alive.append(
                            Rope(start, pattern, length, rating, self.input_count, key_no)
                        )
                        if self.input_count in self.combo_check:
                            self.combo_check[self.input_count][rating] += 1
                        elif self.input_count not in self.ignore_input_counts:
                            self.combo_check[self.input_count] = [0] * RATING_COUNTS
                            self.combo_check[self.input_count][rating] += 1

    def kill(self, rope: Rope, in_open: bool = True, break_combo: bool = True):
        if in_open:
            self.open.remove(rope)
        try:
            self.alive.remove(rope)
        except ValueError:
            pass
        for input_count in rope.input_counts:
            if input_count in self.combo_check:
                self.combo_check[input_count][rope.rating] -= 1
                if break_combo:
                    if sum(self.combo_check[input_count][:self.combo_rating + 1]) == 0:
                        print(f"{input_count}에서 더 이상 이을 콤보가 없습니다.")
                        self.combo_break()

    def combo_break(self):
        print(f"{RATINGS[self.combo_rating]}으로 {self.combo_count}개 이었습니다.")
        self.combo_rating += 1
        if self.combo_rating == RATING_COUNTS:
            self.combo_count = 0
            self.combo_rating = 0
            self.combo_check = {}
            return
        
        self.write_finish()
        
    def write_timeline(self, time_current: float):
        self.timeline = []
        for rope in self.alive:
            s, e = rope.interval
            if s > time_current:
                self.timeline.append((s, rope, True))
            if e > time_current:
                self.timeline.append((e, rope, False))
        self.timeline.sort(key=lambda x: x[0])

    def update(self, time_current: float):
        erase = 0
        for timing, rope, is_start in self.timeline:
            if timing < time_current:
                erase += 1
                if is_start:
                    self.open.append(rope)
                else:
                    self.kill(rope)
            else:
                break
        self.timeline = self.timeline[erase:]

    def apply(self, key_no: int):
        applied: List[Rope] = []
        for rope in self.open:
            if key_no not in rope.available_keys:
                continue
            applied.append(rope)
            rope.apply(self.input_count, key_no)
            if self.input_count in self.combo_check:
                self.combo_check[self.input_count][rope.rating] += 1
            if rope.is_complete():
                self.done.append(rope)
        for rope in applied:
            self.open.remove(rope)
        self.done.sort(key=lambda x: (x.rating, x.knot.priority))

    def write_accept(self):
        deck = self.deck[:]
        for rope in self.done:
            self.kill(rope, in_open=False, break_combo=False)
            if rope.knot in deck:
                idx = deck.index(rope.knot)
                deck[idx] = 0
                self.accept_rope(rope, idx)
        self.done = []
    
    def write_finish(self):
        for idx, rope in enumerate(self.accept):
            if rope != None and rope.rating <= self.combo_rating:
                self.finish_rope(rope, idx)
    
    def accept_rope(self, rope: Rope, idx: int):
        self.accept[idx] = rope
        self.deck_rating[idx] = rope.rating
    
    def finish_rope(self, rope: Rope, idx: int):
        self.finish[idx] = rope
        self.accept[idx] = None
        for input_count in rope.input_counts:
            if input_count in self.combo_check:
                del self.combo_check[input_count]
            else:
                self.ignore_input_counts.append(input_count)
        self.deck[idx] = self.nexts[0]
        self.deck_rating[idx] = RATING_COUNTS
        self.nexts = [*self.nexts[1:], self.pick()]
        self.combo_count += 1

        print(f"I finished...\n{rope}\n!!!")
        print("♡♡♡")
        
    def kill_ropes_not_in_deck(self):
        to_kill = [rope for rope in self.alive if rope.knot not in self.deck]
        for rope in to_kill:
            self.kill(rope, in_open=False)
    
    def write_alive(self, time_input: float, key_no: int):
        self.kill_ropes_not_in_deck()
        self.create_ropes(time_input, key_no, set(self.deck))

    def on_input_at(self, time_input: float, key_no: int):
        self.input_count += 1
        
        self.apply(key_no) # open의 각 rope에 입력이 들어왔음을 알리고, .done을 작성
        self.write_accept() # .done을 바탕으로 .accept를 작성
        self.write_finish() # .accept를 바탕으로 .finish를 작성

        self.write_alive(time_input, key_no) # 위 작업에 따라 바뀐 덱을 반영해 .alive를 작성
        
        self.write_timeline(time_input)

        print(self.deck)

        print("----------\n\n")
        
    

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = random.randint(2, 5)
        self.velocity = random.uniform(3, 7) * 0.3
        self.angle = random.uniform(0, 2 * math.pi)
        self.acceleration = -0.05  # Deceleration rate
        self.alpha = 255
        self.life = 0.4

    def update(self):
        self.velocity += self.acceleration
        self.x += self.velocity * math.cos(self.angle)
        self.y += self.velocity * math.sin(self.angle)
        self.alpha -= int(255 * (1 / (60 * self.life)))

    def draw(self, screen):
        pygame.draw.circle(screen, (self.color[0], self.color[1], self.color[2], self.alpha), (int(self.x), int(self.y)), self.radius)



class Mark:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.particles = []

    def update_particles(self):
        for particle in self.particles:
            particle.update()
            if particle.alpha <= 0:
                self.particles.remove(particle)

    def draw_particles(self, screen):
        for particle in self.particles:
            particle.draw(screen)

    def create_particles(self):
        for _ in range(20):
            particle = Particle(self.x, self.y, self.color)
            self.particles.append(particle)
            
            
# ComboText class
class ComboText:
    def __init__(self, x, y, combo_text):
        self.x = x
        self.y = y
        self.combo_text = combo_text
        self.font = pygame.font.Font(None, 36)
        self.size = 25
        self.velocity = 2
        self.acceleration = -0.08
        self.timer = 30  # Frames before disappearing

    def update(self):
        self.size += self.velocity
        self.velocity += self.acceleration


        self.timer -= 1

    def draw(self, screen):
        font = pygame.font.Font(None, int(self.size))
        text_surface = font.render(self.combo_text, True, (255, 105, 180)) # neon pink
        text_rect = text_surface.get_rect()
        text_rect.center = (self.x, self.y)
        screen.blit(text_surface, text_rect)