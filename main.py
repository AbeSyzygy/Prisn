import pygame
import sys
import os

from pygame.locals import *
from pygame import mixer

# SETTINGS #
#//////////////////////////////////////////////////////////////////////////////
GRID_SQUARE_SIZE = 20
FPS = 60
MOVE_DELAY = 100
#//////////////////////////////////////////////////////////////////////////////

# Very nice colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
COL_WALL = (128, 128, 128)

colour_mappings = {
    'R': RED,
    'G': GREEN,
    'B': BLUE,
    ('R', 'G'): YELLOW,
    ('G', 'B'): CYAN,
    ('R', 'B'): MAGENTA,
}

symbol_col_map = {
    't': 'R', 'T': 'R',
    'h': 'G', 'H': 'G',
    'n': 'B', 'N': 'B',
    'y': ('R', 'G'), 'Y': ('R', 'G'),
    'c': ('G', 'B'), 'C': ('G', 'B'),
    'm': ('R', 'B'), 'M': ('R', 'B'),
}

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

pygame.init()

class Snake:
    def __init__(self, col, start_pos, col_key):
        self.col = col
        self.positions = [start_pos]
        self.direction = None
        self.last_move_time = 0
        self.colour_key = col_key
        self.length = 1

    def move(self):
        if self.direction:
            head_x, head_y = self.positions[0]
            dir_x, dir_y = self.direction
            new_head = (head_x + dir_x, head_y + dir_y)
            self.positions = [new_head] + self.positions[:self.length - 1]

    def grow(self):
        self.length += 1

    def set_direction(self, new_direction):
        if self.direction:
            if (self.direction[0] + new_direction[0] == 0) and (self.direction[1] + new_direction[1] == 0):
                return
        self.direction = new_direction

def load_level_from_file(symbol_file_path, id_file_path):
    if not os.path.isfile(symbol_file_path):
        print(f"'{symbol_file_path}' missing")
        pygame.quit()
        sys.exit()
    if not os.path.isfile(id_file_path):
        print(f"'{id_file_path}' missing")
        pygame.quit()
        sys.exit()
    with open(symbol_file_path, 'r') as file:
        symbol_data = [line.rstrip('\n') for line in file]
    with open(id_file_path, 'r') as file:
        id_data = [line.rstrip('\n') for line in file]
    return symbol_data, id_data

def parse_level(symbol_data, id_data):
    walls = []
    snake_positions = {}
    switches = {}
    blocks = {}
    goal_positions = []

    # Check level file for character-block mappings
    for y, (symbol_row, id_row) in enumerate(zip(symbol_data, id_data)):
        for x, (symbol_cell, id_cell) in enumerate(zip(symbol_row, id_row)):
            symbol = symbol_cell
            # deal with id_char whitespace
            id_char = id_cell.strip()

            if symbol == 'W':
                walls.append((x, y))
            elif symbol in ('R', 'G', 'B'):
                snake_positions[symbol] = (x, y)
            elif symbol == 'O':
                goal_positions.append((x, y))
            elif symbol.islower() or symbol.isupper():
                col_key = symbol_col_map.get(symbol)
                if col_key:
                    if symbol.islower():
                        # switch
                        switches.setdefault(col_key, {}).setdefault(id_char, []).append((x, y))
                    else:
                        # ...block
                        blocks.setdefault(col_key, {}).setdefault(id_char, []).append((x, y))
                else:
                    # Invalid symbol
                    pass
    return walls, snake_positions, switches, blocks, goal_positions

def check_collision(head_x, head_y, snake, walls, blocks, snake_segments):
    new_head = (head_x, head_y)
    if new_head in snake.positions[1:]:
        return 'stop'

    if new_head in walls:
        return 'stop'

    snake_col = snake.colour_key

    for col_key, ids in blocks.items():
        for id_num, positions in ids.items():
            if new_head in positions:
                if isinstance(col_key, tuple):
                    if snake_col in col_key:
                        return 'stop'
                    else:
                        return 'stop'
                elif col_key == snake_col:
                    return 'stop'
                else:
                    return 'stop'

    return 'no_collision'

def darken_col(col, factor=0.4):
    return tuple(int(c * factor) for c in col)

def col_key_to_str(col_key):
    if isinstance(col_key, tuple):
        combination_map = {
            ('R', 'G'): 'Y',
            ('G', 'B'): 'C',
            ('R', 'B'): 'M'
        }
        return combination_map.get(col_key, ''.join(col_key))
    else:
        return col_key

def draw_snake_segments(snake_segments, snakes):
    for pos, colour_tuples in snake_segments.items():
        rect = pygame.Rect(pos[0] * GRID_SQUARE_SIZE, pos[1] * GRID_SQUARE_SIZE,
                           GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
        if len(colour_tuples) == 1:
            col, col_key = colour_tuples[0]
            # Identify if this position is head
            head_snake = None

            for snake in snakes:
                if snake.positions[0] == pos and snake.colour_key == col_key:
                    head_snake = snake
                    break

            if head_snake:
                pygame.draw.rect(screen, col, rect)

            else:
                pygame.draw.rect(screen, col, rect.inflate(-4, -4))

        else:
            # Multiple snakes, same position
            unique_col_keys = set(col_key for _, col_key in colour_tuples)
            if len(unique_col_keys) == 2:
                combo = tuple(sorted(unique_col_keys))
                combined_key_str = col_key_to_str(combo)
            elif len(unique_col_keys) > 2:
                # If >2 overlapping character colours, combine colours
                combined_key_str = None
            else:
                # one colour, multiple characters
                combined_key_str = col_key_to_str(next(iter(unique_col_keys)))

            if combined_key_str and isinstance(combined_key_str, str):
                # Default to mixed colour-combined square
                mixed_col = mix_cols([col for col, _ in colour_tuples])

                head_found = False

                for snake in snakes:
                    if snake.positions[0] == pos:
                        print("FOUND MIXED HEAD COLOUR!")
                        head_found = True
                        break
                if head_found:
                    pygame.draw.rect(screen, mixed_col, rect)
                else:
                    pygame.draw.rect(screen, mixed_col, rect.inflate(-4, -4))
            else:
                # Default to colour-combined square
                mixed_col = mix_cols([col for col, _ in colour_tuples])
                pygame.draw.rect(screen, mixed_col, rect.inflate(-4, -4))

def mix_cols(cols):
    r = min(sum(colour[0] for colour in cols), 255)
    g = min(sum(colour[1] for colour in cols), 255)
    b = min(sum(colour[2] for colour in cols), 255)
    return (r, g, b)

def draw_character_selection(current_snake, snake_colours, screen_width):
    indicator_size = 23
    padding = 0
    num_snakes = len(snake_colours)
    start_x = screen_width - (indicator_size + padding) * num_snakes

    for i, col in enumerate(snake_colours):
        rect = pygame.Rect(start_x + i * (indicator_size + padding), padding,
                           indicator_size, indicator_size)
        pygame.draw.rect(screen, col, rect)
        if i == current_snake:
            inner_rect = rect.inflate(-10, -10)
            pygame.draw.rect(screen, BLACK, inner_rect)

def get_next_level_filename(current_level):
    # Generate next level's filename, given active level's filename
    level_num = int(current_level.split('_')[-1].split('.')[0])
    next_level = f"levels/lvl_{level_num + 1}.txt"
    return next_level if os.path.isfile(next_level) else None

def game(level_active):
    global screen, image_assets
    clock = pygame.time.Clock()

    symbol_file_path = level_active
    id_file_path = level_active.replace('.txt', '_map.txt')

    symbol_data, id_data = load_level_from_file(symbol_file_path, id_file_path)

    GRID_HEIGHT = len(symbol_data)
    GRID_WIDTH = max(len(row) for row in symbol_data)
    SCREEN_WIDTH = GRID_WIDTH * GRID_SQUARE_SIZE
    SCREEN_HEIGHT = GRID_HEIGHT * GRID_SQUARE_SIZE

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PRISN")

    walls, snake_positions, switches, blocks, goal_positions = parse_level(symbol_data, id_data)

    snakes = []
    for colour_key, pos in snake_positions.items():
        colour = colour_mappings[colour_key]
        snake = Snake(colour, pos, colour_key)
        snakes.append(snake)

    current_snake = 0

    # Image dict init
    image_assets = {}

    # Image - walls
    wall_image = None
    try:
        wall_image = pygame.image.load('assets/wall.png').convert_alpha()
        print("Loaded 'wall.png'")
    except Exception as e:
        print(f"no 'wall.png': {e}")
    image_assets['wall'] = wall_image

    # Image - win
    goal_image = None
    try:
        goal_image = pygame.image.load('assets/goal.png').convert_alpha()
        print("Loaded 'goal.png'")
    except Exception as e:
        print(f"no 'goal.png': {e}")
    image_assets['goal'] = goal_image

    # Image - snake
    for snake in snakes:
        col_key = snake.colour_key
        image_key = f'snake_{col_key}'
        image = None
        try:
            image_filename = f'assets/snake_{col_key}.png'
            image = pygame.image.load(image_filename).convert_alpha()
            print(f"Loaded '{image_filename}'")
        except Exception as e:
            print(f"no snake image '{image_filename}': {e}")
        image_assets[image_key] = image

    # Load combined snake images (e.g., snake_Y.png, snake_C.png, snake_M.png)
    # WHY doesn't this wooooork?
    combined_colours = [key for key in colour_mappings.keys() if isinstance(key, tuple)]
    for combo in combined_colours:
        combined_key_str = col_key_to_str(combo)
        image_key = f'snake_{combined_key_str}'
        image = None
        try:
            combined_image_filename = f'assets/snake_{combined_key_str}.png'
            image = pygame.image.load(combined_image_filename).convert_alpha()
            print(f"Loaded combined character image '{combined_image_filename}'")
        except Exception as e:
            print(f"no combined character image '{combined_image_filename}': {e}")
        image_assets[image_key] = image

    # Load images - blocks, switches
    used_col_keys = set()

    for col_key in blocks.keys():
        used_col_keys.add(col_key)
    for col_key in switches.keys():
        used_col_keys.add(col_key)

    for col_key in used_col_keys:
        # Load block image
        block_key = f'block_{col_key_to_str(col_key)}'
        block_image = None
        try:
            col_key_str = col_key_to_str(col_key)
            image_filename = f'assets/block_{col_key_str}.png'
            block_image = pygame.image.load(image_filename).convert_alpha()
            print(f"Loaded block image '{image_filename}'")
        except Exception as e:
            print(f"no block image '{image_filename}': {e}")
        image_assets[f'block_{col_key}'] = block_image

        # Load switch image
        switch_key = f'switch_{col_key_to_str(col_key)}'
        switch_image = None
        try:
            image_filename = f'assets/switch_{col_key_str}.png'
            switch_image = pygame.image.load(image_filename).convert_alpha()
            print(f"Loaded switch image '{image_filename}'")
        except Exception as e:
            print(f"no switch image '{image_filename}': {e}")
        image_assets[f'switch_{col_key}'] = switch_image


    # ////////////////// MAIN LOOP (wow look at it go!) ////////////////// #

    while True:
        screen.fill(BLACK)
        current_time = pygame.time.get_ticks()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                # Handle reset
                if event.key == pygame.K_r:
                    print("Level reset")
                    game(level_active)
                # Character select
                if event.key == pygame.K_1 and len(snakes) >= 1:
                    current_snake = 0
                    print("Selected R")
                elif event.key == pygame.K_2 and len(snakes) >= 2:
                    current_snake = 1
                    print("Selected G")
                elif event.key == pygame.K_3 and len(snakes) >= 3:
                    current_snake = 2
                    print("Selected B")
                # Movement keys
                elif event.key in (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d):
                    if event.key == pygame.K_w:
                        snakes[current_snake].set_direction(UP)
                        print(f"Snake {current_snake + 1} set direction UP.")
                    elif event.key == pygame.K_s:
                        snakes[current_snake].set_direction(DOWN)
                        print(f"Snake {current_snake + 1} set direction DOWN.")
                    elif event.key == pygame.K_a:
                        snakes[current_snake].set_direction(LEFT)
                        print(f"Snake {current_snake + 1} set direction LEFT.")
                    elif event.key == pygame.K_d:
                        snakes[current_snake].set_direction(RIGHT)
                        print(f"Snake {current_snake + 1} set direction RIGHT.")

                    snake = snakes[current_snake]

                    original_positions = list(snake.positions)
                    snake.move()
                    head_x, head_y = snake.positions[0]

                    collision_type = check_collision(head_x, head_y, snake, walls, blocks, snake_segments={})

                    if collision_type == 'stop':
                        snake.positions = original_positions
                        print(f"Snake {current_snake + 1} collided with wall or itself. Movement stopped.")
                    elif collision_type == 'death':
                        print("fuked it m8")
                        pygame.quit()
                        sys.exit()
                    else:
                        snake.last_move_time = current_time
                        print(f"Snake {current_snake + 1} moved")

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d):
                    snakes[current_snake].direction = None
                    print(f"Snake {current_snake + 1} stopped")

        # Movement (based on direction and MOVE_DELAY)
        if snakes[current_snake].direction:
            if current_time - snakes[current_snake].last_move_time >= MOVE_DELAY:
                snake = snakes[current_snake]

                original_positions = list(snake.positions)
                snake.move()
                head_x, head_y = snake.positions[0]

                collision_type = check_collision(head_x, head_y, snake, walls, blocks, snake_segments={})

                if collision_type == 'stop':
                    snake.positions = original_positions
                    print(f"Snake {current_snake + 1} collision -> stop")
                elif collision_type == 'death':
                    print("fuked it m8.")
                    pygame.quit()
                    sys.exit()
                else:
                    snake.last_move_time = current_time
                    print(f"Snake {current_snake + 1} moved")

        # Get snake head positions
        head_positions = {}
        for snake in snakes:
            head_pos = snake.positions[0]
            snake_col = snake.colour_key
            if head_pos in head_positions:
                head_positions[head_pos].append(snake_col)
            else:
                head_positions[head_pos] = [snake_col]


        # //////// Check switch activation ////////

        # Single-colour switches
        for snake in snakes:
            head_pos = snake.positions[0]
            snake_col = snake.colour_key

            if snake_col in switches:
                for id_num, positions in list(switches[snake_col].items()):
                    if head_pos in positions:
                        # Remove matching-ID blocks
                        if snake_col in blocks and id_num in blocks[snake_col]:
                            del blocks[snake_col][id_num]
                            print(f"Snake '{snake_col}' activated switch '{id_num}' -> block removed")
                        switches[snake_col][id_num].remove(head_pos)
                        if not switches[snake_col][id_num]:
                            del switches[snake_col][id_num]
                        snake.grow()
                        print(f"Snake '{snake_col}' --> new length: {snake.length}")

        # Check colour combination switches
        for pos, cols_at_pos in head_positions.items():
            if len(cols_at_pos) >= 2:
                colour_keys_set = set(cols_at_pos)
                for combo_colour in [key for key in switches.keys() if isinstance(key, tuple)]:
                    if set(combo_colour) == colour_keys_set:
                        for id_num, positions in list(switches[combo_colour].items()):
                            if pos in positions:
                                # Remove blocks with matching ID
                                if combo_colour in blocks and id_num in blocks[combo_colour]:
                                    del blocks[combo_colour][id_num]
                                    print(f"Combined snakes {combo_colour} activated switch '{id_num}'. Removed block.")
                                switches[combo_colour][id_num].remove(pos)
                                if not switches[combo_colour][id_num]:
                                    del switches[combo_colour][id_num]
                                # Add to trail for all involved snakes
                                for snake in snakes:
                                    if snake.colour_key in combo_colour:
                                        snake.grow()
                                        print(f"Snake '{snake.colour_key}' --> length: {snake.length}")

        # Collect snake segments *after* movement + switch activation
        snake_segments = {}
        for snake in snakes:
            for pos in snake.positions:
                if pos in snake_segments:
                    snake_segments[pos].append((snake.col, snake.colour_key))
                else:
                    snake_segments[pos] = [(snake.col, snake.colour_key)]

        # Check for win
        if all(snake.positions[0] in goal_positions for snake in snakes):
            print("$$$ CASH PRIZES YOU ARE WINNER $$$")
            next_level = get_next_level_filename(level_active)
            if next_level:
                print(f"loading next level: {next_level}")
                game(next_level)
            else:
                print("That'll do now get to bed.")
                level_active = first_level
                next_level = first_level
                show_title_screen()
                game(first_level)


        # Draw walls
        for wall in walls:
            rect = pygame.Rect(wall[0] * GRID_SQUARE_SIZE, wall[1] * GRID_SQUARE_SIZE,
                               GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
            if image_assets['wall']:
                screen.blit(image_assets['wall'], rect)
            else:
                pygame.draw.rect(screen, COL_WALL, rect)

        # Draw blocks
        for col_key, ids in blocks.items():
            col_key_str = col_key_to_str(col_key)
            image_key = f'block_{col_key}'
            image = image_assets.get(image_key)
            for id_num, positions in ids.items():
                for pos in positions:
                    rect = pygame.Rect(pos[0] * GRID_SQUARE_SIZE, pos[1] * GRID_SQUARE_SIZE,
                                       GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
                    if image:
                        screen.blit(image, rect)
                    else:
                        col = colour_mappings.get(col_key, WHITE)
                        darker_col = darken_col(col)
                        pygame.draw.rect(screen, darker_col, rect)
        

        # Draw - characters with flipped + combined assets
        draw_snake_segments(snake_segments, snakes)

        # Draw - switches
        for col_key, ids in switches.items():
            col_key_str = col_key_to_str(col_key)
            image_key = f'switch_{col_key}'
            image = image_assets.get(image_key)
            for id_num, positions in ids.items():
                for pos in positions:
                    rect = pygame.Rect(pos[0] * GRID_SQUARE_SIZE, pos[1] * GRID_SQUARE_SIZE,
                                       GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
                    if image:
                        screen.blit(image, rect)
                    else:
                        col = colour_mappings.get(col_key, WHITE)
                        # smaller rect
                        small_rect = rect.inflate(-GRID_SQUARE_SIZE * 0.2, -GRID_SQUARE_SIZE * 0.2)
                        pygame.draw.rect(screen, col, small_rect)

        # Draw - win blocks
        for pos in goal_positions:
            rect = pygame.Rect(pos[0] * GRID_SQUARE_SIZE, pos[1] * GRID_SQUARE_SIZE,
                               GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
            if image_assets['goal']:
                screen.blit(image_assets['goal'], rect)
            else:
                pygame.draw.rect(screen, WHITE, rect)

        # Draw - character selection indicator
        snake_colours = [snake.col for snake in snakes]
        draw_character_selection(current_snake, snake_colours, SCREEN_WIDTH)

        pygame.display.flip()
        clock.tick(FPS)

def show_title_screen():
    # TITLE SCREEN
    # TODO should have instructions and backstory and stuff

    mixer.init()
    mixer.music.load('assets/audio/music/music.ogg')
    mixer.music.play(-1)
    mixer.music.set_volume(0.2)

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("PRISN")

    # Title screen assets
    title_image = pygame.image.load("assets/title_screen/title_screen.png").convert()
    begin_button = pygame.image.load("assets/title_screen/begin_button.png").convert_alpha()

    title_rect = title_image.get_rect(center = (400, 250))
    button_rect = begin_button.get_rect(center = (400, 450))

    while True:
        screen.fill((0, 0, 0))

        screen.blit(title_image, title_rect)
        screen.blit(begin_button, button_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    return
        pygame.display.flip()
        pygame.time.Clock().tick(30)


if __name__ == "__main__":
    show_title_screen()
    first_level = "levels/lvl_1.txt"
    level_active = first_level
    game(level_active)
