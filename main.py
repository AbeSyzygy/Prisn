import pygame
import sys
import os

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

    for y, (symbol_row, id_row) in enumerate(zip(symbol_data, id_data)):
        for x, (symbol_cell, id_cell) in enumerate(zip(symbol_row, id_row)):
            symbol = symbol_cell
            id_char = id_cell

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
                        # switch,
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
                        return 'death'
                elif col_key == snake_col:
                    return 'stop'
                else:
                    return 'death'

    return 'no_collision'

def darken_color(color, factor=0.7):
    return tuple(int(c * factor) for c in color)

def color_key_to_str(color_key):
    if isinstance(color_key, tuple):
        return ''.join(color_key)
    else:
        return color_key

def draw_snake_segments(snake_segments):
    for pos, color_tuples in snake_segments.items():
        rect = pygame.Rect(pos[0] * GRID_SQUARE_SIZE, pos[1] * GRID_SQUARE_SIZE,
                                    GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
        if len(color_tuples) == 1:
            color, color_key = color_tuples[0]
            image_key = f'snake_{color_key}'
            image = image_assets.get(image_key)
            if image:
                screen.blit(image, rect)
            else:
                pygame.draw.rect(screen, color, rect)
        else:
            # Multiple snakes in the same position
            colors = [col for col, key in color_tuples]
            mixed_col = mix_cols(colors)
            pygame.draw.rect(screen, mixed_col, rect)

def mix_cols(cols):
    r = min(sum(colour[0] for colour in cols), 255)
    g = min(sum(colour[1] for colour in cols), 255)
    b = min(sum(colour[2] for colour in cols), 255)
    return (r, g, b)

def draw_character_selection(current_snake, snake_colours, screen_width):
    indicator_size = 30
    padding = 10
    num_snakes = len(snake_colours)
    start_x = screen_width - (indicator_size + padding) * num_snakes

    for i, col in enumerate(snake_colours):
        rect = pygame.Rect(start_x + i * (indicator_size + padding), padding,
                           indicator_size, indicator_size)
        pygame.draw.rect(screen, col, rect)
        if i == current_snake:
            inner_rect = rect.inflate(-10, -10)
            pygame.draw.rect(screen, BLACK, inner_rect)

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
    pygame.display.set_caption("ayyylmao: Mega-Snake In Technicolour")

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
    except:
        pass
    image_assets['wall'] = wall_image

    # Image - win
    goal_image = None
    try:
        goal_image = pygame.image.load('assets/goal.png').convert_alpha()
    except:
        pass
    image_assets['goal'] = goal_image

    # Image - snake
    for snake in snakes:
        color_key = snake.colour_key
        image = None
        try:
            image_filename = f'assets/snake_{color_key}.png'
            image = pygame.image.load(image_filename).convert_alpha()
        except:
            pass
        image_assets[f'snake_{color_key}'] = image

    # Load images for blocks and switches
    used_color_keys = set()

    for color_key in blocks.keys():
        used_color_keys.add(color_key)
    for color_key in switches.keys():
        used_color_keys.add(color_key)

    for color_key in used_color_keys:
        # Load block image
        block_image = None
        try:
            color_key_str = color_key_to_str(color_key)
            image_filename = f'assets/block_{color_key_str}.png'
            block_image = pygame.image.load(image_filename).convert_alpha()
        except:
            pass
        image_assets[f'block_{color_key}'] = block_image

        # Load switch image
        switch_image = None
        try:
            image_filename = f'assets/switch_{color_key_str}.png'
            switch_image = pygame.image.load(image_filename).convert_alpha()
        except:
            pass
        image_assets[f'switch_{color_key}'] = switch_image

    while True:
        screen.fill(BLACK)
        current_time = pygame.time.get_ticks()

        # Collect snake segments
        snake_segments = {}
        for snake in snakes:
            for pos in snake.positions:
                if pos in snake_segments:
                    snake_segments[pos].append((snake.col, snake.colour_key))
                else:
                    snake_segments[pos] = [(snake.col, snake.colour_key)]

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                # Character select
                if event.key == pygame.K_1 and len(snakes) >= 1:
                    current_snake = 0
                elif event.key == pygame.K_2 and len(snakes) >= 2:
                    current_snake = 1
                elif event.key == pygame.K_3 and len(snakes) >= 3:
                    current_snake = 2
                # Movement keys
                elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    if event.key == pygame.K_UP:
                        snakes[current_snake].set_direction(UP)
                    elif event.key == pygame.K_DOWN:
                        snakes[current_snake].set_direction(DOWN)
                    elif event.key == pygame.K_LEFT:
                        snakes[current_snake].set_direction(LEFT)
                    elif event.key == pygame.K_RIGHT:
                        snakes[current_snake].set_direction(RIGHT)

                    snake = snakes[current_snake]

                    original_positions = list(snake.positions)
                    snake.move()
                    head_x, head_y = snake.positions[0]

                    collision_type = check_collision(head_x, head_y, snake, walls, blocks, snake_segments)

                    if collision_type == 'stop':
                        snake.positions = original_positions
                    elif collision_type == 'death':
                        print("fuked it m8")
                        pygame.quit()
                        sys.exit()
                    else:
                        snake.last_move_time = current_time

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    snakes[current_snake].direction = None

        # Movement
        if snakes[current_snake].direction:
            if current_time - snakes[current_snake].last_move_time >= MOVE_DELAY:
                snake = snakes[current_snake]

                original_positions = list(snake.positions)
                snake.move()
                head_x, head_y = snake.positions[0]

                collision_type = check_collision(head_x, head_y, snake, walls, blocks, snake_segments)

                if collision_type == 'stop':
                    snake.positions = original_positions
                elif collision_type == 'death':
                    print("fuked it m8")
                    pygame.quit()
                    sys.exit()
                else:
                    snake.last_move_time = current_time

        # Check switch activation
        for snake in snakes:
            head_pos = snake.positions[0]
            snake_col = snake.colour_key

            # Single-col switches
            if snake_col in switches:
                for id_num, positions in list(switches[snake_col].items()):
                    if head_pos in positions:
                        # matching-ID blocks removed
                        if snake_col in blocks and id_num in blocks[snake_col]:
                            del blocks[snake_col][id_num]
                        switches[snake_col][id_num].remove(head_pos)
                        if not switches[snake_col][id_num]:
                            del switches[snake_col][id_num]
                        snake.grow()

        # Check colour-combo switches
        for pos, color_tuples in snake_segments.items():
            if len(color_tuples) >= 2:
                col_keys = [snake.colour_key for snake in snakes if snake.positions[0] == pos]
                colour_keys_set = set(col_keys)
                for combo_colour in [key for key in switches.keys() if isinstance(key, tuple)]:
                    if set(combo_colour) == colour_keys_set:
                        for id_num, positions in list(switches[combo_colour].items()):
                            if pos in positions:
                                # Remove blocks with matching ID
                                if combo_colour in blocks and id_num in blocks[combo_colour]:
                                    del blocks[combo_colour][id_num]
                                switches[combo_colour][id_num].remove(pos)
                                if not switches[combo_colour][id_num]:
                                    del switches[combo_colour][id_num]
                                # Add snake segments
                                for snake in snakes:
                                    if snake.colour_key in combo_colour:
                                        snake.grow()

        # Check for win
        if all(snake.positions[0] in goal_positions for snake in snakes):
            print("$$$ CASH PRIZES YOU ARE WINNER $$$")
            pygame.quit()
            sys.exit()

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
            color_key_str = color_key_to_str(col_key)
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
                        darker_col = darken_color(col)
                        pygame.draw.rect(screen, darker_col, rect)

        # Draw switches
        for col_key, ids in switches.items():
            color_key_str = color_key_to_str(col_key)
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
                        # Adjust rect size to be slightly smaller
                        small_rect = rect.inflate(-GRID_SQUARE_SIZE * 0.2, -GRID_SQUARE_SIZE * 0.2)
                        pygame.draw.rect(screen, col, small_rect)

        # Draw win blocks
        for pos in goal_positions:
            rect = pygame.Rect(pos[0] * GRID_SQUARE_SIZE, pos[1] * GRID_SQUARE_SIZE,
                               GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
            if image_assets['goal']:
                screen.blit(image_assets['goal'], rect)
            else:
                pygame.draw.rect(screen, WHITE, rect)

        # Draw snakes
        draw_snake_segments(snake_segments)

        snake_colours = [snake.col for snake in snakes]
        draw_character_selection(current_snake, snake_colours, SCREEN_WIDTH)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    default_level = "levels/lvl_1.txt"
    level_active = default_level
    game(level_active)
