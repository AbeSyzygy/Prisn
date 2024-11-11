import pygame
import sys
import os

# SETTINGS #
#//////////////////////////////////////////////////////////////////////////////
GRID_SQUARE_SIZE = 20
FPS = 60
MOVE_DELAY = 100
#//////////////////////////////////////////////////////////////////////////////

# very beautiful colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
COL_WALL = (128, 128, 128)

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

    def move(self):
        if self.direction:
            head_x, head_y = self.positions[0]
            dir_x, dir_y = self.direction
            new_head = (head_x + dir_x, head_y + dir_y)
            self.positions = [new_head] + self.positions[:-1]

    def grow(self):
        self.positions.append(self.positions[-1])

    def draw(self, surface):
        for pos in self.positions:
            rect = pygame.Rect(pos[0] * GRID_SQUARE_SIZE, pos[1] * GRID_SQUARE_SIZE,
                               GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
            pygame.draw.rect(surface, self.col, rect)

def load_level_from_file(file_path):
    if not os.path.isfile(file_path):
        print(f"'{file_path}' missing")
        pygame.quit()
        sys.exit()
    with open(file_path, 'r') as file:
        level_data = [line.rstrip('\n') for line in file]
    return level_data

def parse_level(level_data):
    walls = []
    snake_positions = {}
    switches = {'R': [], 'G': [], 'B': []}
    blocks = {'R': [], 'G': [], 'B': []}
    goal_positions = []

    for y, row in enumerate(level_data):
        for x, cell in enumerate(row):
            if cell == 'W':
                walls.append((x, y))
            elif cell in ('R', 'G', 'B'):
                snake_positions[cell] = (x, y)
            elif cell == 't':
                switches['R'].append((x, y))
            elif cell == 'T':
                blocks['R'].append((x, y))
            elif cell == 'h':
                switches['G'].append((x, y))
            elif cell == 'H':
                blocks['G'].append((x, y))
            elif cell == 'n':
                switches['B'].append((x, y))
            elif cell == 'N':
                blocks['B'].append((x, y))
            elif cell == 'O':
                goal_positions.append((x, y))
    return walls, snake_positions, switches, blocks, goal_positions

# Character select indicator
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

def check_collision(new_head, snake, walls, blocks):
    # ...with own body
    if new_head in snake.positions[1:]:
        return 'death'

    if new_head in walls:
        return 'stop'

    for colour_key, block_positions in blocks.items():
        if new_head in block_positions:
            if colour_key == snake.colour_key:
                # Block of own colour --> stop movement
                return 'stop'
            else:
                return 'death'

    return 'no_collision'

def game(level_active):
    global screen
    clock = pygame.time.Clock()

    level_data = load_level_from_file(level_active)

    # lvl data --> screen / grid dimensions
    GRID_HEIGHT = len(level_data)
    GRID_WIDTH = max(len(row) for row in level_data)
    SCREEN_WIDTH = GRID_WIDTH * GRID_SQUARE_SIZE
    SCREEN_HEIGHT = GRID_HEIGHT * GRID_SQUARE_SIZE

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ayylmao: Mega-Snake In Technicolour")

    walls, snake_positions, switches, blocks, goal_positions = parse_level(level_data)

    # Snakes init
    snakes = []
    snake_colour_map = {'R': RED, 'G': GREEN, 'B': BLUE}
    snake_keys = []
    for colour_key in snake_positions:
        colour = snake_colour_map[colour_key]
        pos = snake_positions[colour_key]
        snake = Snake(colour, pos, colour_key)
        snakes.append(snake)
        snake_keys.append(colour_key)

    current_snake = 0

    while True:
        screen.fill(BLACK)
        current_time = pygame.time.get_ticks()

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
                elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    if event.key == pygame.K_UP:
                        snakes[current_snake].direction = UP
                    elif event.key == pygame.K_DOWN:
                        snakes[current_snake].direction = DOWN
                    elif event.key == pygame.K_LEFT:
                        snakes[current_snake].direction = LEFT
                    elif event.key == pygame.K_RIGHT:
                        snakes[current_snake].direction = RIGHT

                    snake = snakes[current_snake]
                    head_x, head_y = snake.positions[0]
                    dir_x, dir_y = snake.direction
                    new_head = (head_x + dir_x, head_y + dir_y)

                    collision_type = check_collision(new_head, snake, walls, blocks)

                    if collision_type == 'stop':
                        # ignore movement commands
                        pass
                    elif collision_type == 'death':
                        print("fuked it m8")
                        pygame.quit()
                        sys.exit()
                    else:
                        # vs don't
                        snake.positions = [new_head] + snake.positions[:-1]
                        snake.last_move_time = current_time

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    snakes[current_snake].direction = None

        # Movement
        if snakes[current_snake].direction:
            if current_time - snakes[current_snake].last_move_time >= MOVE_DELAY:
                snake = snakes[current_snake]
                head_x, head_y = snake.positions[0]
                dir_x, dir_y = snake.direction
                new_head = (head_x + dir_x, head_y + dir_y)

                collision_type = check_collision(new_head, snake, walls, blocks)

                if collision_type == 'stop':
                    pass  # movement logic ignored, path blocked
                elif collision_type == 'death':
                    print("fuked it m8")
                    pygame.quit()
                    sys.exit()
                else:
                    snake.positions = [new_head] + snake.positions[:-1]
                    snake.last_move_time = current_time

        # Check switch activation
        for i, snake in enumerate(snakes):
            head_pos = snake.positions[0]
            colour_key = snake_keys[i]

            if head_pos in switches[colour_key]:
                # Opens door (remove block)
                blocks[colour_key] = []
                switches[colour_key].remove(head_pos)

        # Check for win
        if all(snake.positions[0] in goal_positions for snake in snakes):
            print("$$$ yeah winner $$$")
            pygame.quit()
            sys.exit()

        for wall in walls:
            rect = pygame.Rect(wall[0] * GRID_SQUARE_SIZE, wall[1] * GRID_SQUARE_SIZE,
                               GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
            pygame.draw.rect(screen, COL_WALL, rect)

        block_colours = {'R': (139, 0, 0), 'G': (0, 100, 0), 'B': (0, 0, 139)}
        for colour_key, positions in blocks.items():
            for pos in positions:
                rect = pygame.Rect(pos[0] * GRID_SQUARE_SIZE, pos[1] * GRID_SQUARE_SIZE,
                                   GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
                pygame.draw.rect(screen, block_colours[colour_key], rect)

        switch_colours = {'R': (255, 69, 0), 'G': (50, 205, 50), 'B': (65, 105, 225)}
        for colour_key, positions in switches.items():
            for pos in positions:
                rect = pygame.Rect(pos[0] * GRID_SQUARE_SIZE, pos[1] * GRID_SQUARE_SIZE,
                                   GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
                pygame.draw.rect(screen, switch_colours[colour_key], rect)

        for pos in goal_positions:
            rect = pygame.Rect(pos[0] * GRID_SQUARE_SIZE, pos[1] * GRID_SQUARE_SIZE,
                               GRID_SQUARE_SIZE, GRID_SQUARE_SIZE)
            pygame.draw.rect(screen, WHITE, rect)

        for snake in snakes:
            snake.draw(screen)

        snake_colours = [snake.col for snake in snakes]
        draw_character_selection(current_snake, snake_colours, SCREEN_WIDTH)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    default_level = "levels/lvl_1.txt"
    level_active = default_level
    if not level_active:
        level_active = default_level
    game(level_active)
