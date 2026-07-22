
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

import random
import json
import pygame

player = None

MIN_LEAF_SIZE = 10

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720

WORLD_WIDTH_TILES = 400
WORLD_HEIGHT_TILES = 400
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
    scroll_y: int
    scroll_x: int
    
    def __init__(self):
        self.player = None
        self.scroll_x = 0
        self.scroll_y = 0
        self.world_grid = [
            [WALL for x in range(WORLD_WIDTH_TILES)]
            for y in range(WORLD_HEIGHT_TILES)
        ]
        print("Starting AWS Quest...")
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
        self.enter_loop(self.screen)

    def init_player(self, room):
        rx,ry,rw,rh = room
        return Player((rx + rw//2) // TILE_WIDTH_PIXELS, (ry + rh//2) // TILE_HEIGHT_PIXELS)

    def init_world(self):
        for i in range(WORLD_WIDTH_TILES):
            for j in range(WORLD_HEIGHT_TILES):
                self.world_grid[j][i] = FLOOR
        
        for room in self.rooms:
            door_gen = False
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
            if door_gen == False:
                (door_x, door_y) = self.get_door_coord(random.choice(["top","left","right","bottom"]), rx, ry, rw, rh)
                self.world_grid[door_y][door_x] = DOOR
                door_gen = True
        
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

    def enter_loop(self, screen):
        layer = pygame.Surface((VIEWPORT_WIDTH, VIEWPORT_HEIGHT))
        layer.fill((0, 255, 255))
        circle = (10,10)
        circle_radius = 10
        pygame.draw.circle(layer, (255, 255, 255), circle, circle_radius)
        clock = pygame.time.Clock()
        running = True
        c = pygame.Color(105,100,50)
            
        while running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
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
                            self.scroll_y += 1 if self.scroll_y <= WORLD_HEIGHT_TILES else WORLD_HEIGHT_TILES
                        case pygame.K_UP:
                            self.scroll_y -= 1 if self.scroll_y >= 0 else 0
                        case pygame.K_LEFT:
                            self.scroll_x -= 1 if self.scroll_x >= 0 else 0
                        case pygame.K_RIGHT:
                            self.scroll_x += 1 if self.scroll_x <= WORLD_WIDTH_TILES else WORLD_WIDTH_TILES

            # fill the screen with a color to wipe away anything from last frame
            screen.fill("black")
            
            for y in range(self.scroll_y, WORLD_HEIGHT_TILES):
                for x in range(self.scroll_x, WORLD_WIDTH_TILES):
                    tile = self.world_grid[y][x]
                    if tile == FLOOR:
                        c = pygame.Color(50,50,50)
                    if tile == WALL:
                        c = pygame.Color(70,70,70)
                    if tile == DOOR:
                        c = pygame.Color(0,255,0)
                    tile_rect = ((x - self.scroll_x) * TILE_WIDTH_PIXELS, (y - self.scroll_y) * TILE_HEIGHT_PIXELS, TILE_WIDTH_PIXELS, TILE_HEIGHT_PIXELS) 
                    pygame.draw.rect(screen, c, tile_rect)

            self.screen.blit(layer, (10, 10), special_flags=pygame.BLEND_RGBA_MULT)
            # RENDER YOUR GAME HERE
            pw = TILE_WIDTH_PIXELS
            ph = TILE_HEIGHT_PIXELS
            px = self.player.get_x()
            py = self.player.get_y()
            pygame.draw.rect(self.screen, pygame.Color(150, 0, 0), (px * TILE_WIDTH_PIXELS, py * TILE_HEIGHT_PIXELS, pw, ph))
            # flip() the display to put your work on screen
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