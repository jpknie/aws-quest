
from math import floor, sqrt

from .domain import (
    DisjointSet,
    Player,
    Choice,
    Question,
    Rect,
    Node,
    Direction,
    Edge
)

from .lights import LightLayer

import random
import json
import pygame

player = None

MIN_LEAF_SIZE = 10

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720

WORLD_WIDTH_TILES = 50
WORLD_HEIGHT_TILES = 50
ROOM_MARGIN = 1

TILE_WIDTH_PIXELS = 32
TILE_HEIGHT_PIXELS = 32

WALL = 0
FLOOR = 1
DOOR = 2

def distance_between(room_a, room_b):
    ax, ay, aw, ah = room_a
    bx, by, bw, bh = room_b
    dx = (bx + bw / 2) - (ax + aw / 2)
    dy = (by + bh / 2) - (ay + ah / 2)
    return sqrt(dx * dx + dy * dy)    

def direction_between(room_a, room_b):
    (ra_x, ra_y, ra_w, ra_h) = room_a
    (rb_x, rb_y, rb_w, rb_h) = room_b

    center_a = (ra_x + ra_w/2, ra_y + ra_h/2)
    center_b = (rb_x + rb_w/2, rb_y + rb_h/2)
    
    dx = center_b[0] - center_a[0]
    dy = center_b[1] - center_a[1]

    if abs(dx) > abs(dy):
        direction = Direction.EAST if dx > 0 else Direction.WEST
    else:
        direction = Direction.SOUTH if dy > 0 else Direction.NORTH

    return direction

def main():
    quest = RogueQuest()
    print("Exiting AWS Quest...")

class RogueQuest:
    player: Player
    world_grid: list[list[int]]
    edges: list[Edge]
    rooms: list[tuple[int, int, int, int]]
    root: Node
    screen: pygame.Surface
    leaves: list[Node]
    light_layer: LightLayer
    cam_y: int
    cam_x: int
    
    def __init__(self):
        self.player = None
        self.light_layer = LightLayer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
        self.cam_x = 0
        self.cam_y = 0
        self.world_grid = [
            [WALL for x in range(WORLD_WIDTH_TILES)]
            for y in range(WORLD_HEIGHT_TILES)
        ]
        print("Starting Rogue Quest...")
        pygame.init()
        self.screen = pygame.display.set_mode((VIEWPORT_WIDTH, VIEWPORT_HEIGHT))
        self.root = Node(Rect(0, 0, WORLD_WIDTH_TILES, WORLD_HEIGHT_TILES))
        self.leaves = []
        self.rooms = []
        self.generate_world(self.root)
        self.collect_leaves(self.root)
        self.generate_rooms()
        self.edges = self.generate_edges()
        self.init_world()
        self.player = self.init_player(self.rooms[1])
        self.game_loop(self.screen)
        self.running = False

    def init_player(self, room):
        rx,ry,rw,rh = room
        return Player((rx + rw//2) // TILE_WIDTH_PIXELS, (ry + rh//2) // TILE_HEIGHT_PIXELS)

    def init_world(self):
        self.light_layer.add_light((50, 50))
        self.light_layer.add_light((40, 40))
        print(f"Lights: {self.light_layer.get_lights()}")

        for i in range(WORLD_WIDTH_TILES):
            for j in range(WORLD_HEIGHT_TILES):
                self.world_grid[j][i] = FLOOR
        
        for room in self.rooms:
            rx, ry, rw, rh = room
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    if y == ry:
                        self.world_grid[y][x] = WALL
                    elif x == rx:
                        self.world_grid[y][x] = WALL
                    elif x == (rx + rw) - 1:
                        self.world_grid[y][x] = WALL
                    elif y == (ry + rh) - 1:
                        self.world_grid[y][x] = WALL
                    else:
                        self.world_grid[y][x] = FLOOR
            (door_x, door_y) = self.get_door_coord(random.choice(["top","left","right","bottom"]), rx, ry, rw, rh)
            self.world_grid[door_y][door_x] = DOOR
        
    def draw_edges(self):
        c = pygame.Color(0,101,0)
        for edge in self.edges:
            pygame.draw.rect(self.screen, c, edge)

    def get_door_coord(self, side, tx, ty, tw, th):
        door_y = None
        door_x = None
        if side == "top":
            door_y = ty
            door_x = random.randint(tx + 1, tx + tw - 2)
        elif side == "left":
            door_x = tx
            door_y = random.randint(ty + 1, ty + th - 2)
        elif side == "right":
            door_x = tx + tw - 1
            door_y = random.randint(ty + 1, ty + th - 2)
        else: # Bottom
            door_y = ty + th - 1
            door_x = random.randint(tx + 1, tx + tw - 2)
        return (door_x, door_y)

    # cam_rect: (x, y, width, height)
    def move_camera_based_player(self, cam_rect:(int, int, int, int)):
        should_move_cam_left=False
        should_move_cam_right=False
        should_move_cam_up=False
        should_move_cam_down=False
        (camx,camy,camw,camh) = cam_rect
        (px, py) = (self.player.get_x() * TILE_WIDTH_PIXELS, self.player.get_y() * TILE_HEIGHT_PIXELS)
        print(f"player {px},{py}, cam_rect: {camx}, {camy}, {camh}, {camw}")
        # CASE 1: player is 2 tiles from the left edge - cam should move left
        # CASE 2: player is 2 tiles from the right edge - cam should move right
        # CASE 3: player is 2 tiles from top of the edge - cam should move up
        # CASE 4: player is 2 tiles from bottom of the edge - cam should move down

        # CORNER CASES: don't move camera if player is at the corners: topleft, topright, bottomleft, bottomright

        world_width_px=WORLD_WIDTH_TILES * TILE_WIDTH_PIXELS
        world_height_px=WORLD_HEIGHT_TILES * TILE_HEIGHT_PIXELS

        topleft_rect = (0, 0, TILE_WIDTH_PIXELS, TILE_HEIGHT_PIXELS)
        bottomleft_rect = (0, world_height_px - TILE_HEIGHT_PIXELS, TILE_WIDTH_PIXELS, TILE_HEIGHT_PIXELS)
        bottomright_rect = (world_width_px - TILE_WIDTH_PIXELS, world_height_px - TILE_HEIGHT_PIXELS, TILE_WIDTH_PIXELS, TILE_HEIGHT_PIXELS)
        topright_rect = (world_width_px - TILE_WIDTH_PIXELS, 0, TILE_WIDTH_PIXELS, TILE_HEIGHT_PIXELS)

        cx = px + (TILE_WIDTH_PIXELS // 2)
        cy = py + (TILE_HEIGHT_PIXELS // 2)

        topleft = self.within_rectangle((cx, cy), topleft_rect)
        bottomleft = self.within_rectangle((cx, cy), bottomleft_rect)
        bottomright = self.within_rectangle((cx, cy), bottomright_rect)
        topright = self.within_rectangle((cx, cy), topright_rect)

        if topleft or bottomleft or bottomright or topright:
            return # we do not move camera in the corners

        screen_px = px - self.cam_x * TILE_WIDTH_PIXELS
        screen_py = py - self.cam_y * TILE_HEIGHT_PIXELS

        margin_x = 2 * TILE_WIDTH_PIXELS
        margin_y = 2 * TILE_HEIGHT_PIXELS

        max_cam_x = WORLD_WIDTH_TILES - VIEWPORT_WIDTH // TILE_WIDTH_PIXELS
        max_cam_y = WORLD_HEIGHT_TILES - VIEWPORT_HEIGHT // TILE_HEIGHT_PIXELS

        # Player approaches right edge
        if screen_px >= VIEWPORT_WIDTH - margin_x:
            self.cam_x = min(self.cam_x + 1, max_cam_x)

        # Player approaches left edge
        elif screen_px <= margin_x:
            self.cam_x = max(self.cam_x - 1, 0)

        # Player approaches bottom edge
        if screen_py >= VIEWPORT_HEIGHT - margin_y:
            self.cam_y = min(self.cam_y + 1, max_cam_y)

        # Player approaches top edge
        elif screen_py <= margin_y:
            self.cam_y = max(self.cam_y - 1, 0)

    # returns true if within rectangle
    def within_rectangle(self, point, rect):
        (px, py) = point
        (x, y, width, height) = rect
        return px >= x and px <= x + width and py >= y and py <= y + height

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_a:
                        self.player.move_left()
                    case pygame.K_d:
                        self.player.move_right()
                    case pygame.K_s:
                        self.player.move_down()
                    case pygame.K_w:
                        self.player.move_up()
                    case pygame.K_DOWN:
                        self.cam_y += 1 if self.cam_y <= WORLD_HEIGHT_TILES else WORLD_HEIGHT_TILES
                    case pygame.K_UP:
                        self.cam_y -= 1 if self.cam_y >= 0 else 0
                    case pygame.K_LEFT:
                        self.cam_x -= 1 if self.cam_x >= 0 else 0
                    case pygame.K_RIGHT:
                        self.cam_x += 1 if self.cam_x <= WORLD_WIDTH_TILES else WORLD_WIDTH_TILES
                self.move_camera_based_player((self.cam_x * TILE_WIDTH_PIXELS, self.cam_y * TILE_HEIGHT_PIXELS, VIEWPORT_WIDTH, VIEWPORT_HEIGHT)) 
                
    def render_tiles(self, screen):
        c = pygame.Color(105,100,50)
        for y in range(self.cam_y, WORLD_HEIGHT_TILES):
            for x in range(self.cam_x, WORLD_WIDTH_TILES):
                tile = self.world_grid[y][x]
                if tile == FLOOR:
                    c = pygame.Color(50,50,50)
                if tile == WALL:
                    c = pygame.Color(70,70,70)
                if tile == DOOR:
                    c = pygame.Color(0,255,0)
                tile_rect = ((x - self.cam_x) * TILE_WIDTH_PIXELS, (y - self.cam_y) * TILE_HEIGHT_PIXELS, TILE_WIDTH_PIXELS, TILE_HEIGHT_PIXELS) 
                pygame.draw.rect(screen, c, tile_rect)

    def game_loop(self, screen):
        clock = pygame.time.Clock()
        self.running = True
        print("Entering game loop..")
        while self.running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            self.handle_events()
            # fill the screen with a color to wipe away anything from last frame
            screen.fill("black")
            self.render_tiles(screen)
            
            pw = TILE_WIDTH_PIXELS
            ph = TILE_HEIGHT_PIXELS
            px = self.player.get_x()
            py = self.player.get_y()
            layer=self.light_layer.draw_player_light(((px - self.cam_x) * TILE_WIDTH_PIXELS, (py - self.cam_y) * TILE_HEIGHT_PIXELS))
            self.screen.blit(layer, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
         
            pygame.draw.rect(self.screen, pygame.Color(150, 0, 0), ((px - self.cam_x) * TILE_WIDTH_PIXELS, (py - self.cam_y) * TILE_HEIGHT_PIXELS, pw, ph))
            pygame.display.flip()
            clock.tick(60)  # limits FPS to 60

        pygame.quit()

    def generate_rooms(self):
        for leaf in self.leaves:
            self.rooms.append((leaf.rect.x + ROOM_MARGIN, leaf.rect.y + ROOM_MARGIN, leaf.rect.w - 2*ROOM_MARGIN, leaf.rect.h - 2*ROOM_MARGIN))        

    def normalize_answer(self,answer: str) -> str:
        return answer.strip().lower()

    def is_correct_answer(self, user_answer: str, correct_answer: str) -> bool:
        return self.normalize_answer(user_answer) == self.normalize_answer(correct_answer)

    def calculate_damage(self, difficulty: str) -> int:
        if difficulty == "easy":
            return 30
        if difficulty == "medium":
            return 20
        if difficulty == "hard":
            return 10
        raise ValueError(f"Unknown difficulty: {difficulty}")

    def load_questions(path: str) -> list[Question]:
        with open(path, 'r', encoding='utf-8') as file:
            question_data = json.load(file)

        return [
            Question(
                prompt=item["prompt"],
                difficulty=item["difficulty"],
                choices=[Choice(**choice) for choice in item["choices"]],
                correct_choice_ids=set(item["correct_choice_ids"]),
            )
            for item in question_data
        ]

    def generate_doors(rooms, edges):
        dsu = DisjointSet(len(rooms))
        shuffled = edges.copy()
        random.shuffle(shuffled)
        doors = []
        for edge in shuffled:
            if dsu.union(edge.a, edge.b):
                doors.append(edge)
        return doors

    def generate_world(self,node: Node):
        can_split_vertical = node.rect.w >= 2 * MIN_LEAF_SIZE
        can_split_horizontal = node.rect.h >= 2 * MIN_LEAF_SIZE
        vertical_split = False

        if can_split_vertical and can_split_horizontal:
            vertical_split = random.choice([True, False])
        elif can_split_vertical:
            vertical_split = True
        elif can_split_horizontal:
            vertical_split = False
        else:
            return node

        if vertical_split:
            split_offset = random.randint(MIN_LEAF_SIZE, node.rect.w - MIN_LEAF_SIZE)
            split_x = node.rect.x + split_offset
            node.left = Node(Rect(node.rect.x, node.rect.y, split_x - node.rect.x, node.rect.h))
            node.right = Node(Rect(split_x, node.rect.y, node.rect.w + node.rect.x - split_x, node.rect.h))

        # horizontal split
        else:
            split_offset = random.randint(MIN_LEAF_SIZE, node.rect.h - MIN_LEAF_SIZE)
            split_y = node.rect.y + split_offset
            node.left = Node(Rect(node.rect.x, node.rect.y, node.rect.w, split_y - node.rect.y))
            node.right = Node(Rect(node.rect.x, split_y, node.rect.w, node.rect.h + node.rect.y - split_y))
        
        self.generate_world(node.left)
        self.generate_world(node.right)

    def collect_leaves(self, node: Node):
        if node.left is None and node.right is None:
            self.leaves.append(node)
        if node.left:
            self.collect_leaves(node.left)
        if node.right:
            self.collect_leaves(node.right)

    def generate_edges(self):
        edges = []
        for i in range(len(self.rooms)):
            for j in range(i + 1, len(self.rooms)):
                direction = direction_between(self.rooms[i], self.rooms[j])
                distance = distance_between(self.rooms[i], self.rooms[j])
                edges.append(Edge(i, j, direction, distance))
        return edges

if __name__ == "__main__":
    main()