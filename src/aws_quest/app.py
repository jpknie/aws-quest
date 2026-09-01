from __future__ import annotations

from math import sqrt
from pathlib import Path
import json
import random

import pygame

from .domain import (
    Choice,
    Direction,
    DisjointSet,
    Edge,
    Node,
    Player,
    Question,
    Rect,
)
from .lights import LightLayer

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
QUESTION = 3

STARTING_HEALTH = 100
QUESTIONS_PER_RUN = 10


def normalize_answer(answer: str) -> str:
    return answer.strip().lower()


def is_correct_answer(user_answer: str, correct_answer: str) -> bool:
    return normalize_answer(user_answer) == normalize_answer(correct_answer)


def calculate_damage(difficulty: str) -> int:
    if difficulty == "easy":
        return 30
    if difficulty == "medium":
        return 20
    if difficulty == "hard":
        return 10
    raise ValueError(f"Unknown difficulty: {difficulty}")


def load_questions(path: str | Path) -> list[Question]:
    with open(path, "r", encoding="utf-8") as file:
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


def distance_between(room_a, room_b):
    ax, ay, aw, ah = room_a
    bx, by, bw, bh = room_b
    dx = (bx + bw / 2) - (ax + aw / 2)
    dy = (by + bh / 2) - (ay + ah / 2)
    return sqrt(dx * dx + dy * dy)


def direction_between(room_a, room_b):
    ra_x, ra_y, ra_w, ra_h = room_a
    rb_x, rb_y, rb_w, rb_h = room_b

    center_a = (ra_x + ra_w / 2, ra_y + ra_h / 2)
    center_b = (rb_x + rb_w / 2, rb_y + rb_h / 2)

    dx = center_b[0] - center_a[0]
    dy = center_b[1] - center_a[1]

    if abs(dx) > abs(dy):
        return Direction.EAST if dx > 0 else Direction.WEST
    return Direction.SOUTH if dy > 0 else Direction.NORTH


def main():
    RogueQuest()
    print("Exiting AWS Quest...")


class RogueQuest:
    def __init__(self):
        print("Starting Rogue Quest...")
        pygame.init()
        pygame.display.set_caption("AWS Quest")

        self.screen = pygame.display.set_mode((VIEWPORT_WIDTH, VIEWPORT_HEIGHT))
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 64)

        self.light_layer = LightLayer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
        self.cam_x = 0
        self.cam_y = 0
        self.health = STARTING_HEALTH
        self.correct_answers = 0
        self.answered_questions = 0
        self.total_questions = 0
        self.active_question: Question | None = None
        self.active_question_position: tuple[int, int] | None = None
        self.last_feedback = "Find the yellow AWS question tiles. WASD moves."
        self.game_over = False
        self.quest_complete = False

        self.world_grid = [
            [WALL for _ in range(WORLD_WIDTH_TILES)]
            for _ in range(WORLD_HEIGHT_TILES)
        ]

        self.root = Node(Rect(0, 0, WORLD_WIDTH_TILES, WORLD_HEIGHT_TILES))
        self.leaves: list[Node] = []
        self.rooms: list[tuple[int, int, int, int]] = []

        self.generate_world(self.root)
        self.collect_leaves(self.root)
        self.generate_rooms()
        self.edges = self.generate_edges()
        self.init_world()

        start_room = self.rooms[1] if len(self.rooms) > 1 else self.rooms[0]
        self.start_room = start_room
        self.player = self.init_player(start_room)

        questions_path = Path(__file__).with_name("questions.json")
        self.questions = load_questions(questions_path)
        self.question_tiles: dict[tuple[int, int], Question] = {}
        self.place_questions()

        self.running = True
        self.game_loop(self.screen)

    def init_player(self, room):
        rx, ry, rw, rh = room
        # Rooms are already expressed in tile coordinates. Do not divide by tile size here.
        return Player(rx + rw // 2, ry + rh // 2)

    def restart(self):
        self.health = STARTING_HEALTH
        self.correct_answers = 0
        self.answered_questions = 0
        self.active_question = None
        self.active_question_position = None
        self.game_over = False
        self.quest_complete = False
        self.last_feedback = "Quest restarted."
        self.cam_x = 0
        self.cam_y = 0
        self.player = self.init_player(self.start_room)
        self.place_questions()

    def init_world(self):
        for y in range(WORLD_HEIGHT_TILES):
            for x in range(WORLD_WIDTH_TILES):
                self.world_grid[y][x] = FLOOR

        for room in self.rooms:
            rx, ry, rw, rh = room
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    if y in (ry, ry + rh - 1) or x in (rx, rx + rw - 1):
                        self.world_grid[y][x] = WALL
                    else:
                        self.world_grid[y][x] = FLOOR

            door_x, door_y = self.get_door_coord(
                random.choice(["top", "left", "right", "bottom"]),
                rx,
                ry,
                rw,
                rh,
            )
            self.world_grid[door_y][door_x] = DOOR

    def place_questions(self):
        # Remove old markers before placing a new run.
        for position in getattr(self, "question_tiles", {}):
            x, y = position
            if self.world_grid[y][x] == QUESTION:
                self.world_grid[y][x] = FLOOR

        self.question_tiles = {}
        if not self.questions:
            self.total_questions = 0
            return

        candidates: list[tuple[int, int]] = []
        player_pos = (self.player.get_x(), self.player.get_y())

        for room in self.rooms:
            rx, ry, rw, rh = room
            interior = [
                (x, y)
                for y in range(ry + 1, ry + rh - 1)
                for x in range(rx + 1, rx + rw - 1)
                if self.world_grid[y][x] == FLOOR and (x, y) != player_pos
            ]
            if interior:
                candidates.append(random.choice(interior))

        random.shuffle(candidates)
        selected_questions = random.sample(
            self.questions,
            k=min(QUESTIONS_PER_RUN, len(self.questions)),
        )

        for position, question in zip(candidates, selected_questions):
            self.question_tiles[position] = question
            x, y = position
            self.world_grid[y][x] = QUESTION

        self.total_questions = len(self.question_tiles)

    def get_door_coord(self, side, tx, ty, tw, th):
        if side == "top":
            return random.randint(tx + 1, tx + tw - 2), ty
        if side == "left":
            return tx, random.randint(ty + 1, ty + th - 2)
        if side == "right":
            return tx + tw - 1, random.randint(ty + 1, ty + th - 2)
        return random.randint(tx + 1, tx + tw - 2), ty + th - 1

    def can_move_to(self, x: int, y: int) -> bool:
        if x < 0 or y < 0 or x >= WORLD_WIDTH_TILES or y >= WORLD_HEIGHT_TILES:
            return False
        return self.world_grid[y][x] != WALL

    def try_move_player(self, dx: int, dy: int):
        if self.game_over or self.active_question is not None:
            return

        new_x = self.player.get_x() + dx
        new_y = self.player.get_y() + dy
        if not self.can_move_to(new_x, new_y):
            self.last_feedback = "Wall. Find another route."
            return

        self.player.pos_x = new_x
        self.player.pos_y = new_y
        self.move_camera_based_player()
        self.check_question_tile()

    def check_question_tile(self):
        position = (self.player.get_x(), self.player.get_y())
        question = self.question_tiles.get(position)
        if question is not None:
            self.active_question = question
            self.active_question_position = position
            self.last_feedback = "AWS encounter! Choose A-D."

    def answer_question(self, choice_id: str):
        if self.active_question is None:
            return

        question = self.active_question
        selected = {choice_id.upper()}
        correct = question.is_correct(selected)

        if correct:
            self.correct_answers += 1
            self.last_feedback = "Correct!"
        else:
            damage = calculate_damage(question.difficulty)
            self.health = max(0, self.health - damage)
            correct_ids = ", ".join(sorted(question.correct_choice_ids))
            self.last_feedback = f"Wrong. -{damage} HP. Correct answer: {correct_ids}."

        self.answered_questions += 1

        if self.active_question_position is not None:
            x, y = self.active_question_position
            self.question_tiles.pop(self.active_question_position, None)
            if self.world_grid[y][x] == QUESTION:
                self.world_grid[y][x] = FLOOR

        self.active_question = None
        self.active_question_position = None

        if self.health <= 0:
            self.game_over = True
            self.last_feedback = "Game over. Press R to restart."
        elif self.answered_questions >= self.total_questions and self.total_questions > 0:
            self.quest_complete = True
            self.last_feedback = "AWS Quest complete! Press R for another run."

    def move_camera_based_player(self):
        px = self.player.get_x() * TILE_WIDTH_PIXELS
        py = self.player.get_y() * TILE_HEIGHT_PIXELS
        screen_px = px - self.cam_x * TILE_WIDTH_PIXELS
        screen_py = py - self.cam_y * TILE_HEIGHT_PIXELS

        margin_x = 2 * TILE_WIDTH_PIXELS
        margin_y = 2 * TILE_HEIGHT_PIXELS
        max_cam_x = max(0, WORLD_WIDTH_TILES - VIEWPORT_WIDTH // TILE_WIDTH_PIXELS)
        max_cam_y = max(0, WORLD_HEIGHT_TILES - VIEWPORT_HEIGHT // TILE_HEIGHT_PIXELS)

        if screen_px >= VIEWPORT_WIDTH - margin_x:
            self.cam_x = min(self.cam_x + 1, max_cam_x)
        elif screen_px <= margin_x:
            self.cam_x = max(self.cam_x - 1, 0)

        if screen_py >= VIEWPORT_HEIGHT - margin_y:
            self.cam_y = min(self.cam_y + 1, max_cam_y)
        elif screen_py <= margin_y:
            self.cam_y = max(self.cam_y - 1, 0)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    continue

                if event.key == pygame.K_r and (self.game_over or self.quest_complete):
                    self.restart()
                    continue

                if self.active_question is not None:
                    key_to_choice = {
                        pygame.K_a: "A",
                        pygame.K_b: "B",
                        pygame.K_c: "C",
                        pygame.K_d: "D",
                        pygame.K_1: "A",
                        pygame.K_2: "B",
                        pygame.K_3: "C",
                        pygame.K_4: "D",
                    }
                    choice_id = key_to_choice.get(event.key)
                    if choice_id is not None:
                        self.answer_question(choice_id)
                    continue

                match event.key:
                    case pygame.K_a:
                        self.try_move_player(-1, 0)
                    case pygame.K_d:
                        self.try_move_player(1, 0)
                    case pygame.K_s:
                        self.try_move_player(0, 1)
                    case pygame.K_w:
                        self.try_move_player(0, -1)

    def render_tiles(self, screen):
        max_y = min(WORLD_HEIGHT_TILES, self.cam_y + VIEWPORT_HEIGHT // TILE_HEIGHT_PIXELS + 1)
        max_x = min(WORLD_WIDTH_TILES, self.cam_x + VIEWPORT_WIDTH // TILE_WIDTH_PIXELS + 1)

        for y in range(self.cam_y, max_y):
            for x in range(self.cam_x, max_x):
                tile = self.world_grid[y][x]
                if tile == FLOOR:
                    color = pygame.Color(50, 50, 50)
                elif tile == WALL:
                    color = pygame.Color(70, 70, 70)
                elif tile == DOOR:
                    color = pygame.Color(0, 180, 0)
                else:
                    color = pygame.Color(210, 180, 0)

                tile_rect = (
                    (x - self.cam_x) * TILE_WIDTH_PIXELS,
                    (y - self.cam_y) * TILE_HEIGHT_PIXELS,
                    TILE_WIDTH_PIXELS,
                    TILE_HEIGHT_PIXELS,
                )
                pygame.draw.rect(screen, color, tile_rect)
                pygame.draw.rect(screen, pygame.Color(40, 40, 40), tile_rect, 1)

    def draw_hud(self):
        health_text = self.font.render(f"HP {self.health}/{STARTING_HEALTH}", True, "white")
        score_text = self.font.render(
            f"AWS {self.correct_answers}/{self.total_questions}", True, "white"
        )
        feedback_text = self.small_font.render(self.last_feedback, True, "white")

        self.screen.blit(health_text, (20, 16))
        self.screen.blit(score_text, (20, 48))
        self.screen.blit(feedback_text, (20, VIEWPORT_HEIGHT - 30))

    def draw_wrapped_text(self, text: str, rect: pygame.Rect, font: pygame.font.Font, line_gap=6):
        words = text.split()
        lines: list[str] = []
        current = ""

        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= rect.width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        y = rect.top
        for line in lines:
            rendered = font.render(line, True, "white")
            self.screen.blit(rendered, (rect.left, y))
            y += font.get_linesize() + line_gap
        return y

    def draw_question_overlay(self):
        if self.active_question is None:
            return

        overlay = pygame.Surface((VIEWPORT_WIDTH, VIEWPORT_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 205))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(140, 95, VIEWPORT_WIDTH - 280, VIEWPORT_HEIGHT - 190)
        pygame.draw.rect(self.screen, pygame.Color(35, 35, 35), panel)
        pygame.draw.rect(self.screen, pygame.Color(180, 180, 180), panel, 2)

        title = self.font.render(
            f"AWS question ({self.active_question.difficulty})", True, "white"
        )
        self.screen.blit(title, (panel.left + 30, panel.top + 25))

        y = self.draw_wrapped_text(
            self.active_question.prompt,
            pygame.Rect(panel.left + 30, panel.top + 70, panel.width - 60, 120),
            self.font,
        )
        y += 24

        for choice in self.active_question.choices:
            y = self.draw_wrapped_text(
                f"{choice.id}. {choice.text}",
                pygame.Rect(panel.left + 45, y, panel.width - 90, 80),
                self.small_font,
                3,
            )
            y += 10

        hint = self.small_font.render("Press A-D (or 1-4)", True, "white")
        self.screen.blit(hint, (panel.left + 30, panel.bottom - 45))

    def draw_end_state(self):
        if not self.game_over and not self.quest_complete:
            return

        text = "GAME OVER" if self.game_over else "AWS QUEST COMPLETE"
        rendered = self.large_font.render(text, True, "white")
        restart = self.font.render("Press R to restart", True, "white")
        self.screen.blit(rendered, rendered.get_rect(center=(VIEWPORT_WIDTH // 2, VIEWPORT_HEIGHT // 2 - 20)))
        self.screen.blit(restart, restart.get_rect(center=(VIEWPORT_WIDTH // 2, VIEWPORT_HEIGHT // 2 + 40)))

    def game_loop(self, screen):
        clock = pygame.time.Clock()
        print("Entering game loop..")

        while self.running:
            self.handle_events()
            screen.fill("black")
            self.render_tiles(screen)

            px = self.player.get_x()
            py = self.player.get_y()
            layer = self.light_layer.draw_player_light(
                (
                    (px - self.cam_x) * TILE_WIDTH_PIXELS,
                    (py - self.cam_y) * TILE_HEIGHT_PIXELS,
                )
            )
            self.screen.blit(layer, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            pygame.draw.rect(
                self.screen,
                pygame.Color(150, 0, 0),
                (
                    (px - self.cam_x) * TILE_WIDTH_PIXELS,
                    (py - self.cam_y) * TILE_HEIGHT_PIXELS,
                    TILE_WIDTH_PIXELS,
                    TILE_HEIGHT_PIXELS,
                ),
            )

            self.draw_hud()
            self.draw_question_overlay()
            self.draw_end_state()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def generate_rooms(self):
        for leaf in self.leaves:
            self.rooms.append(
                (
                    leaf.rect.x + ROOM_MARGIN,
                    leaf.rect.y + ROOM_MARGIN,
                    leaf.rect.w - 2 * ROOM_MARGIN,
                    leaf.rect.h - 2 * ROOM_MARGIN,
                )
            )

    def generate_doors(self, rooms, edges):
        dsu = DisjointSet(len(rooms))
        shuffled = edges.copy()
        random.shuffle(shuffled)
        doors = []
        for edge in shuffled:
            if dsu.union(edge.a, edge.b):
                doors.append(edge)
        return doors

    def generate_world(self, node: Node):
        can_split_vertical = node.rect.w >= 2 * MIN_LEAF_SIZE
        can_split_horizontal = node.rect.h >= 2 * MIN_LEAF_SIZE

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
