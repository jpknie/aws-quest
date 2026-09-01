import pygame


class LightLayer:
    def __init__(self, viewport_width, viewport_height):
        self.circle_radius = 200
        self.circle2_radius = 100
        self.circle3_radius = 50
        self.falloff1 = (50, 50, 50)
        self.falloff2 = (100, 100, 100)
        self.falloff3 = (255, 255, 255)

        self.lights = []
        self.layer = pygame.Surface((viewport_width, viewport_height))
        self.layer.fill((0, 0, 0))

    def add_light(self, coords: tuple[int, int]):
        self.lights.append(coords)

    def get_lights(self):
        return self.lights

    def draw_player_light(self, player_coord):
        # Clear every frame so the player's old positions do not remain illuminated.
        self.layer.fill((0, 0, 0))
        px, py = player_coord
        sx = px + 16
        sy = py + 16
        pygame.draw.circle(self.layer, self.falloff1, (sx, sy), self.circle_radius)
        pygame.draw.circle(self.layer, self.falloff2, (sx, sy), self.circle2_radius)
        pygame.draw.circle(self.layer, self.falloff3, (sx, sy), self.circle3_radius)
        return self.layer

    def render_lights(self):
        for light_coord in self.lights:
            pygame.draw.circle(self.layer, self.falloff1, light_coord, self.circle_radius)
            pygame.draw.circle(self.layer, self.falloff2, light_coord, self.circle2_radius)
            pygame.draw.circle(self.layer, self.falloff3, light_coord, self.circle3_radius)
        return self.layer
