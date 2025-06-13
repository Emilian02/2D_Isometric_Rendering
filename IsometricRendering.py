import pygame
import sys
from collections import defaultdict, deque

# Initialize Pygame
pygame.init()

# Screen dimensions
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Isometric Rendering")

# Colors
WHITE = (255, 255, 255)
GRAY = (169, 169, 169)
LIGHT_BLUE = (173, 216, 230)

# Tile sizes
TILE_WIDTH = 64
TILE_HEIGHT = 64
TILE_WIDTH_HALF = TILE_WIDTH // 2
TILE_HEIGHT_HALF = TILE_HEIGHT // 4

# Grid sizes
GRID_WIDTH, GRID_HEIGHT = 8, 8

# List of elevated positions with z-coordinates
ELEVATED_POSITIONS = [(0, -1, 1), (0, -2, 1), (1, -2, 1), (1, -1, 1)]

# Conversion of grid to isometric screen coordinates
def grid_to_iso(x: int, y: int):
    screen_x = (x - y) * TILE_WIDTH_HALF + WINDOW_WIDTH // 2
    screen_y = (x + y) * TILE_HEIGHT_HALF + WINDOW_HEIGHT // 2
    return screen_x, screen_y

class Renderer:
    def __init__(self, window):
        self.window = window
        self.load_tiles()

    def load_tiles(self):
        try:
            # Load tile images
            self.floor_tile = pygame.image.load("Isometric_Tiles_Pixel_Art\\Blocks\\blocks_1.png")
            self.floor_ice_tile = pygame.image.load("Isometric_Tiles_Pixel_Art\\Blocks\\blocks_9.png")
            self.right_ramp_tile = pygame.image.load("Isometric_Tiles_Pixel_Art\\Blocks\\blocks_10.png")
        except pygame.error as e:
            print(f"Error loading tiles: {e}")
            sys.exit()

    def is_near_elevated(self, x, y, z):
        # Check if the given position is near an elevated position
        for ex, ey, ez in ELEVATED_POSITIONS:
            if (abs(x - ex) == 1 and y == ey and z == ez) or (abs(y - ey) == 1 and x == ex and z == ez):
                return True
        return False

    def draw_tiles(self, player):
        tiles = []

        # Iterate over the grid to add floor tiles
        for x in range(-GRID_WIDTH, GRID_WIDTH + 1):
            for y in range(-GRID_HEIGHT, GRID_HEIGHT + 1):
                screen_x, screen_y = grid_to_iso(x, y)
                tile_x = screen_x - TILE_WIDTH_HALF
                tile_y = screen_y

                if (x, y, 0) not in ELEVATED_POSITIONS:
                    tiles.append((tile_y, 0, self.floor_tile, (tile_x, tile_y), 0, (x, y, 0)))

        # Add elevated tiles
        for x, y, z in ELEVATED_POSITIONS:
            screen_x, screen_y = grid_to_iso(x, y)
            tile_x = screen_x - TILE_WIDTH_HALF
            tile_y = screen_y - TILE_HEIGHT_HALF

            if (x, y, z) == (0, -1, 1):
                tiles.append((tile_y + TILE_HEIGHT_HALF, 0, self.floor_tile, (tile_x, tile_y + TILE_HEIGHT_HALF), 0, (x, y, z)))
                tiles.append((tile_y + TILE_HEIGHT_HALF, 2, self.right_ramp_tile, (tile_x, tile_y), z, (x, y, z)))
            else:
                tiles.append((tile_y + TILE_HEIGHT_HALF, 2, self.floor_ice_tile, (tile_x, tile_y), z, (x, y, z)))

        # Add player to the list of tiles
        player_screen_x, player_screen_y = grid_to_iso(player.x, player.y)
        player_frame = player.frames[player.direction]
        player_tile_y = player_screen_y - player_frame.get_height() // 2

        # Adjust player y-coordinate if near elevated tiles
        if self.is_near_elevated(player.x, player.y, player.z):
            player_tile_y -= TILE_HEIGHT_HALF

        # Determine player z-index based on their z coordinate and position
        player_z = 1 if (player.x, player.y, player.z) in ELEVATED_POSITIONS else 0
        tiles.append((player_tile_y + TILE_HEIGHT_HALF, 0, player_frame, (player_screen_x - player_frame.get_width() // 2, player_screen_y - player_frame.get_height() // 2), player_z, (player.x, player.y, player.z)))

        # Create a graph for topological sorting
        graph = defaultdict(list) # Keeps track of which tiles depend on which
        in_degree = defaultdict(int) # Keeps track of how many dependencies each tile has

        # Add edges based on dependencies
        for i, (_, _, _, _, _, (x1, y1, z1)) in enumerate(tiles):
            for j, (_, _, _, _, _, (x2, y2, z2)) in enumerate(tiles):
                if i != j and (x1, y1, z1) != (x2, y2, z2):
                    if (x1, y1, z1) < (x2, y2, z2):
                        graph[i].append(j) # Tile i should be drawn before Tile j
                        in_degree[j] += 1 # Tile j has one more dependency

        # Perform topological sorting
         # Initialize a queue with all tiles that have no dependencies
        zero_in_degree_queue = deque([i for i in range(len(tiles)) if in_degree[i] == 0])

        # Create an empty list to store tiles in the correct order
        sorted_tiles = []

        # Continue processing tiles while there are tiles in the queue
        while zero_in_degree_queue:
            # Take the next tile from the queue (the tile with no remaining dependencies)
            node = zero_in_degree_queue.popleft()
            
            # Add this tile to the sorted list
            sorted_tiles.append(node)
            
            # Check all tiles that depend on this tile
            for neighbor in graph[node]:
                # Decrease the count of dependencies for this neighboring tile
                in_degree[neighbor] -= 1
                
                # If this neighboring tile now has no remaining dependencies, add it to the queue
                if in_degree[neighbor] == 0:
                    zero_in_degree_queue.append(neighbor)

        # Draw tiles in topologically sorted order
        for index in sorted_tiles:
            _, _, tile, pos, _, _ = tiles[index]
            self.window.blit(tile, pos)

    def draw_grid_lines(self):
        # Draw grid lines for visual reference
        for x in range(-GRID_WIDTH, GRID_WIDTH + 1):
            for y in range(-GRID_HEIGHT, GRID_HEIGHT + 1):
                # Get the 4 corners of the tile
                top = grid_to_iso(x, y)
                right = grid_to_iso(x + 1, y)
                bottom = grid_to_iso(x + 1, y + 1)
                left = grid_to_iso(x, y + 1)

                # Draw the lines connecting the 4 corners
                pygame.draw.line(self.window, WHITE, top, right, 1)
                pygame.draw.line(self.window, WHITE, right, bottom, 1)
                pygame.draw.line(self.window, WHITE, bottom, left, 1)
                pygame.draw.line(self.window, WHITE, left, top, 1)

class Player:
    def __init__(self):
        # Initialize player position, direction, and other attributes
        self.x, self.y, self.z = -2, -2, 0
        self.direction = 'down'
        self.frame_index = 0
        self.move_speed = 0.05
        self.last_update = pygame.time.get_ticks()
        self.load_sprites()

    def load_sprites(self):
        try:
            # Load player sprite sheets for different directions
            self.sprite_sheets = {
                'up': pygame.image.load("PlayerAnim\\UpAnim\\Up_Anim.png").convert_alpha(),
                'down': pygame.image.load("PlayerAnim\\DownAnim\\Down_Anim.png").convert_alpha(),
                'left': pygame.image.load("PlayerAnim\\LeftAnim\\Left_Anim.png").convert_alpha(),
                'right': pygame.image.load("PlayerAnim\\RightAnim\\Right_Anim.png").convert_alpha()
            }
        except pygame.error as e:
            print(f"Error loading player sprites: {e}")
            sys.exit()

        # Extract the first frame from each sprite sheet
        self.frames = {direction: self.extract_first_frame(sheet) for direction, sheet in self.sprite_sheets.items()}

    def extract_first_frame(self, sheet):
        # Extract the first frame from the sprite sheet
        frame_width = sheet.get_width()
        frame_height = 22
        frame = sheet.subsurface(pygame.Rect(0, 0, frame_width, frame_height))
        return frame

    def update(self):
        # Update player position based on key presses
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.x -= self.move_speed
            self.direction = 'left'
        elif keys[pygame.K_RIGHT]:
            self.x += self.move_speed
            self.direction = 'right'
        elif keys[pygame.K_UP]:
            self.y -= self.move_speed
            self.direction = 'up'
        elif keys[pygame.K_DOWN]:
            self.y += self.move_speed
            self.direction = 'down'

        # Update z-coordinate based on position
        self.z = 1 if (self.x, self.y, 1) in ELEVATED_POSITIONS else 0

    def draw(self, window):
        # Draw the player on the screen
        screen_x, screen_y = grid_to_iso(self.x, self.y)
        frame = self.frames[self.direction]
        window.blit(frame, (screen_x - frame.get_width() // 2, screen_y - frame.get_height() // 2))

def main():
    # Main game loop
    clock = pygame.time.Clock()
    player = Player()
    renderer = Renderer(WINDOW)
    running = True
    renderGrid = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_RETURN:
                    renderGrid = not renderGrid

        # Fill the window with a light blue color
        WINDOW.fill(LIGHT_BLUE)

        # Update player position and draw tiles and grid lines
        player.update()
        renderer.draw_tiles(player)

        if renderGrid:
            renderer.draw_grid_lines()

        # Update the display
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()