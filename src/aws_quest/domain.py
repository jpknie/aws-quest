from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class DisjointSet:
    def __init__(self, size):
        self.parent = list(range(size))

    def find(self, x):
        while x != self.parent[x]:
            x = self.parent[x]
        return x

    def union(self, a, b):
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return False
        
        self.parent[root_b] = root_a
        return True

class Player():
    pos_x: int
    pos_y: int

    def __init__(self, pos_x=0, pos_y=0):
        self.pos_x = pos_x
        self.pos_y = pos_y

    def get_x(self):
        return self.pos_x
    
    def get_y(self):
        return self.pos_y
    
    def move_up(self):
        self.pos_y -= 1
    
    def move_down(self):
        self.pos_y += 1
    
    def move_left(self):
        self.pos_x -= 1
    
    def move_right(self):
        self.pos_x += 1


@dataclass
class Choice:
    id: str
    text: str

@dataclass
class Question:
    prompt: str
    choices: list[Choice]
    correct_choice_ids: set[str]
    difficulty: str

    def is_correct(self, selected_choise_ids: set[str]) -> bool:
        return selected_choise_ids == self.correct_choice_ids

@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

@dataclass
class Node:
    rect: Rect
    left: Node | None = None
    right: Node | None = None

class Direction(Enum):
    EAST = 0
    WEST = 1
    SOUTH = 2
    NORTH = 3

@dataclass
class Edge:
    a: int
    b: int
    direction: Direction
    distance: float

