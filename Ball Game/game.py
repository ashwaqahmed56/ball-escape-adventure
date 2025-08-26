import pygame
import math
import random
import sys
import json
import os

pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
SAVE_FILE = "ball_escape_save.json"
BEST_SCORE_FILE = "best_score.json"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 100, 255)
GREEN = (50, 200, 50)
BROWN = (139, 69, 19)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)
DARK_GREEN = (0, 100, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)
ORANGE = (255, 165, 0)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 0, 139)
PINK = (255, 192, 203)
LAVA_RED = (255, 69, 0)
CYAN = (0, 255, 255)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 149, 237)
BORDER_COLOR = (60, 0, 80)
BORDER_THICKNESS = 15
PLATFORM_COLOR = (100, 100, 100)  # Gray platform for spawning

# Darker background colors for better visibility
WORLDS = {
    "Surface": {
        "bg_color": (135, 206, 235),  # Darker sky blue
        "wall_color": DARK_GREEN,
        "portal_color": BLUE,
        "time_limit": 30,
        "enemy_speed": 2.0,
        "enemy_count": 2,
        "bg_elements": ["tree", "cloud", "mountain"],
        "obstacle_count": 5,
        "portal_visible_time": 10,
        "portal_hidden_time": 5
    },
    "Underground": {
        "bg_color": (101, 67, 33),  # Kept as is
        "wall_color": (101, 67, 33),
        "portal_color": PURPLE,
        "time_limit": 40,
        "enemy_speed": 2.5,
        "enemy_count": 3,
        "bg_elements": ["crystal", "rock", "tunnel"],
        "obstacle_count": 8,
        "portal_visible_time": 8,
        "portal_hidden_time": 6
    },
    "Cave": {
        "bg_color": (50, 50, 50),  # Darker gray
        "wall_color": GRAY,
        "portal_color": YELLOW,
        "time_limit": 50,
        "enemy_speed": 3.0,
        "enemy_count": 4,
        "bg_elements": ["stalactite", "bat", "water_drop"],
        "obstacle_count": 12,
        "portal_visible_time": 7,
        "portal_hidden_time": 7
    },
    "Volcano": {
        "bg_color": (139, 0, 0),  # Darker red
        "wall_color": ORANGE,
        "portal_color": WHITE,
        "time_limit": 60,
        "enemy_speed": 3.5,
        "enemy_count": 5,
        "bg_elements": ["lava_bubble", "smoke", "rock"],
        "obstacle_count": 15,
        "portal_visible_time": 6,
        "portal_hidden_time": 8
    }
}

# Utility: check overlap between rect and list of rects
def rects_overlap(rect, rects, pad=0):
    test = rect.inflate(pad, pad)
    for r in rects:
        if test.colliderect(r):
            return True
    return False

# Utility: check if circle overlaps with rectangle
def circle_rect_overlap(cx, cy, radius, rect):
    # Find the closest point on the rectangle to the circle center
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    
    # Calculate distance between circle center and closest point
    dx = cx - closest_x
    dy = cy - closest_y
    
    # Check if distance is less than radius
    return (dx*dx + dy*dy) < (radius*radius)

# Utility: check if two circles overlap
def circles_overlap(x1, y1, r1, x2, y2, r2):
    dx = x1 - x2
    dy = y1 - y2
    distance_squared = dx*dx + dy*dy
    min_distance = r1 + r2
    return distance_squared < (min_distance * min_distance)

class Button:
    def __init__(self, x, y, width, height, text, font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont('Arial', font_size)
        self.hovered = False
        
    def draw(self, screen):
        color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class SpawnPlatform:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = PLATFORM_COLOR
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height), 2)
        
        # Draw "SPAWN" text
        font = pygame.font.SysFont('Arial', 16)
        text = font.render("SPAWN", True, WHITE)
        text_rect = text.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text, text_rect)
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)

class Obstacle:
    def __init__(self, x, y, width, height, obstacle_type="rectangle"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = obstacle_type
        self.color = DARK_GRAY if obstacle_type in ("rock", "rectangle", "circle", "triangle") else BROWN
        
    def draw(self, screen):
        if self.type == "rectangle" or self.type == "rock":
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, GRAY, (self.x+5, self.y+5, self.width-10, self.height-10), 2)
        elif self.type == "circle":
            pygame.draw.circle(screen, GRAY, (self.x+self.width//2, self.y+self.height//2), min(self.width, self.height)//2)
            pygame.draw.circle(screen, DARK_GRAY, (self.x+self.width//2, self.y+self.height//2), min(self.width, self.height)//2-8, 2)
        elif self.type == "triangle":
            points = [
                (self.x + self.width // 2, self.y),
                (self.x, self.y + self.height),
                (self.x + self.width, self.y + self.height),
            ]
            pygame.draw.polygon(screen, BROWN, points)
            pygame.draw.polygon(screen, DARK_GRAY, points, 2)
        elif self.type == "brick":
            pygame.draw.rect(screen, ORANGE, (self.x, self.y, self.width, self.height))
            brick_h = 12
            for y in range(self.y, self.y + self.height, brick_h):
                pygame.draw.line(screen, BLACK, (self.x, y), (self.x+self.width, y), 1)
                for x in range(self.x, self.x + self.width, 30):
                    pygame.draw.line(screen, BLACK, (x, y), (x, y+brick_h), 1)
                    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "type": self.type
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data["x"], data["y"], data["width"], data["height"], data["type"])

class BackgroundElement:
    def __init__(self, x, y, element_type):
        self.x = x
        self.y = y
        self.type = element_type
        self.speed = random.uniform(0.5, 2.0)
        self.size = random.randint(20, 60)
        self.angle = random.uniform(0, 360)
        self.pulse = 0
        
    def update(self):
        self.pulse += 0.05
        
        if self.type == "cloud":
            self.x += self.speed
            if self.x > SCREEN_WIDTH + 100:
                self.x = -100
                self.y = random.randint(50, 200)
                
        elif self.type == "bat":
            self.x += self.speed * 2
            self.y += math.sin(self.pulse) * 2
            if self.x > SCREEN_WIDTH + 50:
                self.x = -50
                self.y = random.randint(100, SCREEN_HEIGHT - 100)
                
        elif self.type == "water_drop":
            self.y += self.speed * 3
            if self.y > SCREEN_HEIGHT:
                self.y = -20
                self.x = random.randint(0, SCREEN_WIDTH)
                
        elif self.type == "smoke":
            self.y -= self.speed
            self.x += math.sin(self.pulse) * 0.5
            self.size += 0.2
            if self.y < -50:
                self.y = SCREEN_HEIGHT + 20
                self.x = random.randint(0, SCREEN_WIDTH)
                self.size = random.randint(20, 40)
                
        elif self.type == "lava_bubble":
            self.y -= self.speed * 2
            if self.y < 0:
                self.y = SCREEN_HEIGHT + 20
                self.x = random.randint(0, SCREEN_WIDTH)
                
    def draw(self, screen):
        if self.type == "tree":
            pygame.draw.rect(screen, BROWN, (self.x - 10, self.y, 20, 40))
            pygame.draw.circle(screen, DARK_GREEN, (self.x, self.y - 10), 30)
            pygame.draw.circle(screen, GREEN, (self.x, self.y - 10), 25)
            
        elif self.type == "cloud":
            for i in range(3):
                offset_x = i * 25 - 25
                pygame.draw.circle(screen, WHITE, (int(self.x + offset_x), int(self.y)), 20)
            pygame.draw.circle(screen, WHITE, (int(self.x - 10), int(self.y - 10)), 15)
            pygame.draw.circle(screen, WHITE, (int(self.x + 10), int(self.y - 10)), 15)
            
        elif self.type == "mountain":
            points = [(self.x, self.y + 100), (self.x - 80, self.y + 100), (self.x, self.y - 50)]
            pygame.draw.polygon(screen, GRAY, points)
            points = [(self.x, self.y - 50), (self.x - 30, self.y - 20), (self.x + 30, self.y - 20)]
            pygame.draw.polygon(screen, WHITE, points)
            
        elif self.type == "crystal":
            self.angle += 1
            points = []
            for i in range(6):
                angle = self.angle + i * 60
                x = self.x + math.cos(math.radians(angle)) * self.size
                y = self.y + math.sin(math.radians(angle)) * self.size
                points.append((x, y))
            pygame.draw.polygon(screen, PURPLE, points)
            pygame.draw.polygon(screen, PINK, points, 2)
            
        elif self.type == "rock":
            pygame.draw.circle(screen, DARK_GRAY, (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(screen, GRAY, (int(self.x - 5), int(self.y - 5)), self.size - 10)
            
        elif self.type == "tunnel":
            pygame.draw.ellipse(screen, BLACK, (self.x - 40, self.y - 30, 80, 60))
            pygame.draw.ellipse(screen, DARK_GRAY, (self.x - 40, self.y - 30, 80, 60), 3)
            
        elif self.type == "stalactite":
            points = [(self.x, self.y), (self.x - 15, self.y + 40), (self.x + 15, self.y + 40)]
            pygame.draw.polygon(screen, GRAY, points)
            pygame.draw.polygon(screen, DARK_GRAY, points, 2)
            
        elif self.type == "bat":
            pygame.draw.ellipse(screen, BLACK, (self.x - 15, self.y - 5, 30, 10))
            pygame.draw.polygon(screen, BLACK, [(self.x - 15, self.y), (self.x - 25, self.y - 10), (self.x - 25, self.y + 10)])
            pygame.draw.polygon(screen, BLACK, [(self.x + 15, self.y), (self.x + 25, self.y - 10), (self.x + 25, self.y + 10)])
            
        elif self.type == "water_drop":
            pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), 5)
            pygame.draw.circle(screen, LIGHT_BLUE, (int(self.x - 1), int(self.y - 1)), 3)
            
        elif self.type == "smoke":
            pygame.draw.circle(screen, GRAY, (int(self.x), int(self.y)), int(self.size))
            
        elif self.type == "lava_bubble":
            pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), int(self.size))
            pygame.draw.circle(screen, YELLOW, (int(self.x - 3), int(self.y - 3)), int(self.size - 5))

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.radius = 20
        self.type = power_type
        self.duration = 300
        self.pulse = 0
        self.collected = False
        self.colors = {
            "speed": GREEN,
            "shield": BLUE,
            "freeze": CYAN
        }
        
    def update(self):
        self.pulse += 0.1
        
    def draw(self, screen):
        if not self.collected:
            pulse_radius = self.radius + math.sin(self.pulse) * 3
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(pulse_radius + 3))
            pygame.draw.circle(screen, self.colors[self.type], (int(self.x), int(self.y)), int(pulse_radius))
            
            if self.type == "speed":
                points = [(self.x - 5, self.y - 10), (self.x + 2, self.y - 2), 
                         (self.x - 2, self.y + 2), (self.x + 5, self.y + 10)]
                pygame.draw.lines(screen, WHITE, False, points, 3)
            elif self.type == "shield":
                pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 10, 2)
            elif self.type == "freeze":
                for angle in range(0, 360, 60):
                    end_x = self.x + math.cos(math.radians(angle)) * 10
                    end_y = self.y + math.sin(math.radians(angle)) * 10
                    pygame.draw.line(screen, WHITE, (self.x, self.y), (end_x, end_y), 2)
    
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "type": self.type,
            "collected": self.collected
        }
    
    @classmethod
    def from_dict(cls, data):
        power_up = cls(data["x"], data["y"], data["type"])
        power_up.collected = data["collected"]
        return power_up

class Player:
    def __init__(self, x, y):
        self.radius = 15
        self.x = x
        self.y = y
        self.speed = 5
        self.base_speed = 5
        self.color = BLUE
        self.trail = []
        self.max_trail_length = 20
        self.shield_active = False
        self.shield_timer = 0
        
    def move(self, keys, obstacles):
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)
            
        new_x, new_y = self.x, self.y
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += self.speed
            
        border_off = BORDER_THICKNESS
        new_x = max(self.radius + border_off, min(SCREEN_WIDTH - border_off - self.radius, new_x))
        new_y = max(self.radius + border_off, min(SCREEN_HEIGHT - border_off - self.radius, new_y))
        
        player_rect = pygame.Rect(new_x - self.radius, new_y - self.radius, self.radius * 2, self.radius * 2)
        
        collision = False
        for obs in obstacles:
            if player_rect.colliderect(obs.get_rect()):
                collision = True
                break
                
        if not collision:
            self.x, self.y = new_x, new_y
            
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False
                
    def activate_power(self, power_type):
        if power_type == "speed":
            self.speed = self.base_speed * 1.5
        elif power_type == "shield":
            self.shield_active = True
            self.shield_timer = 300
            
    def deactivate_power(self, power_type):
        if power_type == "speed":
            self.speed = self.base_speed
            
    def draw(self, screen):
        # Draw trail
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))
            radius = int(self.radius * (i / len(self.trail)))
            if radius > 0:
                s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color, alpha), (radius, radius), radius)
                screen.blit(s, (int(pos[0]-radius), int(pos[1]-radius)))
        
        # Thick outline for visibility
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius + 6)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius + 3)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        
        if self.shield_active:
            shield_radius = self.radius + 10 + math.sin(pygame.time.get_ticks() * 0.01) * 3
            pygame.draw.circle(screen, (100, 100, 255, 128), (int(self.x), int(self.y)), int(shield_radius), 3)
            
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "speed": self.speed,
            "base_speed": self.base_speed,
            "shield_active": self.shield_active,
            "shield_timer": self.shield_timer,
            "trail": self.trail[-10:]
        }
    
    def load_from_dict(self, data):
        self.x = data["x"]
        self.y = data["y"]
        self.speed = data["speed"]
        self.base_speed = data["base_speed"]
        self.shield_active = data["shield_active"]
        self.shield_timer = data["shield_timer"]
        self.trail = data.get("trail", [])

class Enemy:
    def __init__(self, x, y, speed, color):
        self.radius = 20
        self.base_radius = 20
        self.x = x
        self.y = y
        self.base_speed = speed
        self.speed = speed
        self.color = color
        self.direction = random.uniform(0, 2 * math.pi)
        self.change_direction_timer = 0
        self.vision_range = 200
        self.base_vision_range = 200
        self.frozen = False
        self.freeze_timer = 0
        self.enraged = False
        
    def update(self, player, obstacles):
        if self.frozen:
            self.freeze_timer -= 1
            if self.freeze_timer <= 0:
                self.frozen = False
                self.speed = self.base_speed * (1.5 if self.enraged else 1)
            return
            
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < self.vision_range:
            self.direction = math.atan2(dy, dx)
        else:
            self.change_direction_timer -= 1
            if self.change_direction_timer <= 0:
                self.direction += random.uniform(-math.pi/4, math.pi/4)
                self.change_direction_timer = random.randint(30, 90)
        
        new_x = self.x + self.speed * math.cos(self.direction)
        new_y = self.y + self.speed * math.sin(self.direction)
        
        enemy_rect = pygame.Rect(new_x - self.radius, new_y - self.radius, self.radius*2, self.radius*2)
        
        collision = False
        for obstacle in obstacles:
            if enemy_rect.colliderect(obstacle.get_rect()):
                collision = True
                self.direction += math.pi / 2
                break
                
        if not collision:
            self.x = new_x
            self.y = new_y
        else:
            self.x += self.speed * math.cos(self.direction)
            self.y += self.speed * math.sin(self.direction)
            
        if self.x <= self.radius + BORDER_THICKNESS or self.x >= SCREEN_WIDTH - self.radius - BORDER_THICKNESS:
            self.direction = math.pi - self.direction
        if self.y <= self.radius + BORDER_THICKNESS or self.y >= SCREEN_HEIGHT - self.radius - BORDER_THICKNESS:
            self.direction = -self.direction
            
        self.x = max(self.radius + BORDER_THICKNESS, min(SCREEN_WIDTH - self.radius - BORDER_THICKNESS, self.x))
        self.y = max(self.radius + BORDER_THICKNESS, min(SCREEN_HEIGHT - self.radius - BORDER_THICKNESS, self.y))
        
    def make_enraged(self):
        self.enraged = True
        self.speed = self.base_speed * 1.5
        self.vision_range = self.base_vision_range * 1.5
        self.radius = self.base_radius * 1.3
        
    def calm_down(self):
        self.enraged = False
        self.speed = self.base_speed
        self.vision_range = self.base_vision_range
        self.radius = self.base_radius
        
    def freeze(self):
        self.frozen = True
        self.freeze_timer = 300
        self.speed = 0
        
    def draw(self, screen):
        color = self.color if not self.frozen else (100, 100, 100)
        if self.enraged:
            pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), int(self.radius + 5))
        
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(self.radius))
        
        eye_offset = int(7 * (self.radius / self.base_radius))
        eye_radius = int(4 * (self.radius / self.base_radius))
        pygame.draw.circle(screen, WHITE, (int(self.x - eye_offset), int(self.y - eye_offset)), eye_radius)
        pygame.draw.circle(screen, WHITE, (int(self.x + eye_offset), int(self.y - eye_offset)), eye_radius)
        pygame.draw.circle(screen, BLACK, (int(self.x - eye_offset), int(self.y - eye_offset)), 2)
        pygame.draw.circle(screen, BLACK, (int(self.x + eye_offset), int(self.y - eye_offset)), 2)
        
        if self.frozen:
            pygame.draw.circle(screen, (200, 200, 255), (int(self.x), int(self.y)), int(self.radius + 5), 3)
        
        if self.enraged and not self.frozen:
            pygame.draw.line(screen, RED, (self.x - eye_offset - 5, self.y - eye_offset - 5), 
                             (self.x - eye_offset + 5, self.y - eye_offset - 10), 2)
            pygame.draw.line(screen, RED, (self.x + eye_offset - 5, self.y - eye_offset - 10), 
                             (self.x + eye_offset + 5, self.y - eye_offset - 5), 2)
            
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "base_speed": self.base_speed,
            "speed": self.speed,
            "color": self.color,
            "direction": self.direction,
            "vision_range": self.vision_range,
            "base_vision_range": self.base_vision_range,
            "frozen": self.frozen,
            "freeze_timer": self.freeze_timer,
            "enraged": self.enraged,
            "radius": self.radius,
            "base_radius": self.base_radius
        }
    
    @classmethod
    def from_dict(cls, data):
        enemy = cls(data["x"], data["y"], data["base_speed"], data["color"])
        enemy.speed = data["speed"]
        enemy.direction = data["direction"]
        enemy.vision_range = data["vision_range"]
        enemy.base_vision_range = data["base_vision_range"]
        enemy.frozen = data["frozen"]
        enemy.freeze_timer = data["freeze_timer"]
        enemy.enraged = data["enraged"]
        enemy.radius = data["radius"]
        enemy.base_radius = data["base_radius"]
        return enemy

class Portal:
    def __init__(self, world_config):
        self.radius = 30
        self.x = random.randint(self.radius + BORDER_THICKNESS, SCREEN_WIDTH - self.radius - BORDER_THICKNESS)
        self.y = random.randint(self.radius + BORDER_THICKNESS, SCREEN_HEIGHT - self.radius - BORDER_THICKNESS)
        self.color = world_config["portal_color"]
        self.pulse = 0
        self.visible = True
        self.visible_time = world_config["portal_visible_time"] * 1000
        self.hidden_time = world_config["portal_hidden_time"] * 1000
        self.last_toggle = pygame.time.get_ticks()
        
    def update(self):
        self.pulse += 0.1
        current_time = pygame.time.get_ticks()
        
        if self.visible:
            if current_time - self.last_toggle > self.visible_time:
                self.visible = False
                self.last_toggle = current_time
                return True
        else:
            if current_time - self.last_toggle > self.hidden_time:
                self.visible = True
                self.last_toggle = current_time
                return False
                
        return None
        
    def draw(self, screen):
        if self.visible:
            pulse_radius = self.radius + math.sin(self.pulse) * 5
            
            for i in range(3):
                alpha = 100 - i * 30
                radius = pulse_radius + i * 10
                pygame.draw.circle(screen, (*self.color, alpha), (int(self.x), int(self.y)), int(radius), 2)
            
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(pulse_radius))
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(pulse_radius - 5))
        
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "color": self.color,
            "visible": self.visible,
            "last_toggle": self.last_toggle,
            "visible_time": self.visible_time,
            "hidden_time": self.hidden_time
        }
    
    def load_from_dict(self, data):
        self.x = data["x"]
        self.y = data["y"]
        self.color = data["color"]
        self.visible = data["visible"]
        self.last_toggle = data["last_toggle"]
        self.visible_time = data["visible_time"]
        self.hidden_time = data["hidden_time"]

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Ball Escape Adventure")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 36)
        self.small_font = pygame.font.SysFont('Arial', 24)
        self.state = "PLAYING"
        self.exit_button = Button(SCREEN_WIDTH - 100, 20, 80, 30, "Exit")
        self.best_score = self.load_best_score()
        
        if os.path.exists(SAVE_FILE):
            if not self.load_game():
                self.reset_game()
        else:
            self.reset_game()
            
    def load_best_score(self):
        if os.path.exists(BEST_SCORE_FILE):
            with open(BEST_SCORE_FILE, "r") as f:
                data = json.load(f)
                return data.get("best_score", 0)
        return 0
        
    def save_best_score(self):
        if self.score > self.best_score:
            self.best_score = self.score
            with open(BEST_SCORE_FILE, "w") as f:
                json.dump({"best_score": self.best_score}, f)
                
    def reset_game(self):
        # Create spawn platform first
        platform_width = 120
        platform_height = 60
        platform_x = SCREEN_WIDTH // 2 - platform_width // 2
        platform_y = SCREEN_HEIGHT // 2 - platform_height // 2
        self.spawn_platform = SpawnPlatform(platform_x, platform_y, platform_width, platform_height)
        
        # Create player at the center of the platform
        player_x, player_y = self.spawn_platform.get_center()
        self.player = Player(player_x, player_y)
        
        self.worlds_list = list(WORLDS.keys())
        self.current_world_index = 0
        self.current_world = self.worlds_list[self.current_world_index]
        self.world_config = WORLDS[self.current_world]
        self.enemies = []
        self.portal = Portal(self.world_config)
        self.time_remaining = self.world_config["time_limit"]
        self.level_start_time = pygame.time.get_ticks()
        self.lives = 3
        self.score = 0
        self.background_elements = []
        self.power_ups = []
        self.active_powers = {}
        self.obstacles = []
        self.portal_cycle_count = 0
        
        # Create obstacles first
        self.create_obstacles()
        
        # Then create enemies
        self.create_enemies()
        
        # Finally create background elements
        self.create_background()
        
        self.power_up_timer = 0
        
    def create_obstacles(self):
        self.obstacles = []
        shapes = ["rectangle", "circle", "triangle", "brick"]
        obstacle_count = self.world_config["obstacle_count"]
        placed_rects = [self.spawn_platform.get_rect()]  # Include spawn platform in collision checks
        
        for _ in range(obstacle_count):
            attempts = 0
            while attempts < 100:  # Prevent infinite loop
                width = random.randint(50, 100)
                height = random.randint(50, 100)
                x = random.randint(BORDER_THICKNESS, SCREEN_WIDTH - BORDER_THICKNESS - width)
                y = random.randint(BORDER_THICKNESS, SCREEN_HEIGHT - BORDER_THICKNESS - height)
                
                rect = pygame.Rect(x, y, width, height)
                
                # Check collision with player (circle)
                if circle_rect_overlap(self.player.x, self.player.y, self.player.radius, rect):
                    attempts += 1
                    continue
                    
                # Check collision with portal (circle)
                if circle_rect_overlap(self.portal.x, self.portal.y, self.portal.radius, rect):
                    attempts += 1
                    continue
                    
                # Check collision with already placed obstacles
                if rects_overlap(rect, placed_rects):
                    attempts += 1
                    continue
                    
                obstacle_type = random.choice(shapes)
                self.obstacles.append(Obstacle(x, y, width, height, obstacle_type))
                placed_rects.append(rect)
                break
                
    def create_enemies(self):
        self.enemies = []
        enemy_colors = [RED, ORANGE, PURPLE, YELLOW, (255, 0, 255)]
        
        for i in range(self.world_config["enemy_count"]):
            attempts = 0
            while attempts < 100:  # Prevent infinite loop
                x = random.randint(BORDER_THICKNESS + 30, SCREEN_WIDTH - BORDER_THICKNESS - 30)
                y = random.randint(BORDER_THICKNESS + 30, SCREEN_HEIGHT - BORDER_THICKNESS - 30)
                
                # Check if too close to player (circle)
                if circles_overlap(x, y, 20, self.player.x, self.player.y, self.player.radius + 20):
                    attempts += 1
                    continue
                    
                # Check if too close to portal (circle)
                if circles_overlap(x, y, 20, self.portal.x, self.portal.y, self.portal.radius + 20):
                    attempts += 1
                    continue
                    
                # Check collision with obstacles
                collision_with_obstacle = False
                for obs in self.obstacles:
                    if circle_rect_overlap(x, y, 20, obs.get_rect()):
                        collision_with_obstacle = True
                        break
                        
                if collision_with_obstacle:
                    attempts += 1
                    continue
                    
                color = enemy_colors[i % len(enemy_colors)]
                self.enemies.append(Enemy(x, y, self.world_config["enemy_speed"], color))
                break
                
    def create_background(self):
        self.background_elements = []
        element_types = self.world_config["bg_elements"]
        
        for element_type in element_types:
            count = 5 if element_type in ["cloud", "bat", "water_drop", "smoke", "lava_bubble"] else 3
            
            for _ in range(count):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                self.background_elements.append(BackgroundElement(x, y, element_type))
                
    def spawn_power_up(self):
        if len(self.power_ups) < 2:
            power_types = ["speed", "shield", "freeze"]
            power_type = random.choice(power_types)
            
            while True:
                x = random.randint(BORDER_THICKNESS, SCREEN_WIDTH - BORDER_THICKNESS)
                y = random.randint(BORDER_THICKNESS, SCREEN_HEIGHT - BORDER_THICKNESS)
                
                player_dist = math.sqrt((x - self.player.x) ** 2 + (y - self.player.y) ** 2)
                portal_dist = math.sqrt((x - self.portal.x) ** 2 + (y - self.portal.y) ** 2)
                
                if player_dist > 100 and portal_dist > 100:
                    self.power_ups.append(PowerUp(x, y, power_type))
                    break
                    
    def spawn_additional_enemies(self):
        enemy_colors = [RED, ORANGE, PURPLE, YELLOW, (255, 0, 255)]
        count = random.randint(1, 2)
        
        for _ in range(count):
            while True:
                x = random.randint(BORDER_THICKNESS + 30, SCREEN_WIDTH - BORDER_THICKNESS - 30)
                y = random.randint(BORDER_THICKNESS + 30, SCREEN_HEIGHT - BORDER_THICKNESS - 30)
                
                player_dist = math.sqrt((x - self.player.x) ** 2 + (y - self.player.y) ** 2)
                
                if player_dist > 200:
                    color = random.choice(enemy_colors)
                    new_enemy = Enemy(x, y, self.world_config["enemy_speed"] * 1.2, color)
                    new_enemy.make_enraged()
                    self.enemies.append(new_enemy)
                    break
                    
    def save_game(self):
        save_data = {
            "current_world_index": self.current_world_index,
            "player": self.player.to_dict(),
            "enemies": [enemy.to_dict() for enemy in self.enemies],
            "portal": self.portal.to_dict(),
            "lives": self.lives,
            "score": self.score,
            "time_remaining": self.time_remaining,
            "level_start_time": self.level_start_time,
            "obstacles": [obs.to_dict() for obs in self.obstacles],
            "power_ups": [pu.to_dict() for pu in self.power_ups],
            "active_powers": self.active_powers,
            "portal_cycle_count": self.portal_cycle_count
        }
        
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(save_data, f)
            return True
        except:
            return False
            
    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            return False
            
        try:
            with open(SAVE_FILE, 'r') as f:
                save_data = json.load(f)
            
            self.current_world_index = save_data["current_world_index"]
            self.current_world = self.worlds_list[self.current_world_index]
            self.world_config = WORLDS[self.current_world]
            
            self.player.load_from_dict(save_data["player"])
            
            self.enemies = []
            for enemy_data in save_data["enemies"]:
                self.enemies.append(Enemy.from_dict(enemy_data))
            
            self.portal = Portal(self.world_config)
            self.portal.load_from_dict(save_data["portal"])
            
            self.lives = save_data["lives"]
            self.score = save_data["score"]
            self.time_remaining = save_data["time_remaining"]
            self.level_start_time = save_data["level_start_time"]
            
            self.obstacles = []
            for obs_data in save_data["obstacles"]:
                self.obstacles.append(Obstacle.from_dict(obs_data))
            
            self.power_ups = []
            for pu_data in save_data["power_ups"]:
                self.power_ups.append(PowerUp.from_dict(pu_data))
            
            self.active_powers = save_data["active_powers"]
            self.portal_cycle_count = save_data["portal_cycle_count"]
            
            # Create spawn platform when loading game
            platform_width = 120
            platform_height = 60
            platform_x = SCREEN_WIDTH // 2 - platform_width // 2
            platform_y = SCREEN_HEIGHT // 2 - platform_height // 2
            self.spawn_platform = SpawnPlatform(platform_x, platform_y, platform_width, platform_height)
            
            self.create_background()
            return True
        except:
            return False
            
    def next_level(self):
        self.current_world_index += 1
        if self.current_world_index >= len(self.worlds_list):
            self.current_world_index = 0
            
        self.current_world = self.worlds_list[self.current_world_index]
        self.world_config = WORLDS[self.current_world]
        self.portal = Portal(self.world_config)
        self.time_remaining = self.world_config["time_limit"]
        self.level_start_time = pygame.time.get_ticks()
        
        # Create spawn platform for the new level
        platform_width = 120
        platform_height = 60
        platform_x = SCREEN_WIDTH // 2 - platform_width // 2
        platform_y = SCREEN_HEIGHT // 2 - platform_height // 2
        self.spawn_platform = SpawnPlatform(platform_x, platform_y, platform_width, platform_height)
        
        # Position player at the center of the platform
        self.player.x, self.player.y = self.spawn_platform.get_center()
        self.player.trail = []
        
        self.create_obstacles()
        self.create_enemies()
        self.create_background()
        
        self.power_ups = []
        self.active_powers = {}
        self.portal_cycle_count = 0
        
        self.score += 100
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if self.exit_button.handle_event(event):
                self.save_game()
                return False
                    
            if self.state == "PLAYING":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.save_game()
                    return False
                    
            if self.state == "GAME_OVER":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.reset_game()
                    self.state = "PLAYING"
                    
            elif self.state == "LEVEL_COMPLETE":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.next_level()
                    self.state = "PLAYING"
                    
        return True
        
    def update(self):
        if self.state != "PLAYING":
            return
            
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.obstacles)
        
        for element in self.background_elements:
            element.update()
        
        for enemy in self.enemies:
            enemy.update(self.player, self.obstacles)
            
        portal_result = self.portal.update()
        if portal_result is not None:
            if portal_result:
                for enemy in self.enemies:
                    enemy.make_enraged()
                self.spawn_additional_enemies()
                self.portal_cycle_count += 1
            else:
                for enemy in self.enemies:
                    enemy.calm_down()
        
        for power_up in self.power_ups[:]:
            power_up.update()
            
        for power_type, timer in list(self.active_powers.items()):
            timer -= 1
            if timer <= 0:
                if power_type == "speed":
                    self.player.deactivate_power("speed")
                elif power_type == "freeze":
                    for enemy in self.enemies:
                        enemy.frozen = False
                        enemy.speed = enemy.base_speed * (1.5 if enemy.enraged else 1)
                del self.active_powers[power_type]
            else:
                self.active_powers[power_type] = timer
        
        self.power_up_timer += 1
        if self.power_up_timer > 300:
            self.spawn_power_up()
            self.power_up_timer = 0
        
        elapsed = (pygame.time.get_ticks() - self.level_start_time) / 1000
        self.time_remaining = max(0, self.world_config["time_limit"] - elapsed)
        
        player_rect = self.player.get_rect()
        
        for enemy in self.enemies:
            if player_rect.colliderect(enemy.get_rect()):
                if not self.player.shield_active:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.state = "GAME_OVER"
                        self.save_best_score()
                    else:
                        # Respawn player on platform
                        self.player.x, self.player.y = self.spawn_platform.get_center()
                        self.player.trail = []
                        self.player.shield_active = True
                        self.player.shield_timer = 120
                break
                
        if self.portal.visible and player_rect.colliderect(self.portal.get_rect()):
            self.state = "LEVEL_COMPLETE"
            
        for power_up in self.power_ups[:]:
            if player_rect.colliderect(power_up.get_rect()):
                if power_up.type == "speed":
                    self.player.activate_power("speed")
                elif power_up.type == "shield":
                    self.player.activate_power("shield")
                elif power_up.type == "freeze":
                    for enemy in self.enemies:
                        enemy.freeze()
                
                self.active_powers[power_up.type] = power_up.duration
                self.power_ups.remove(power_up)
                self.score += 50
            
        if self.time_remaining <= 0:
            self.lives -= 1
            if self.lives <= 0:
                self.state = "GAME_OVER"
                self.save_best_score()
            else:
                self.level_start_time = pygame.time.get_ticks()
                self.time_remaining = self.world_config["time_limit"]
                # Respawn player on platform
                self.player.x, self.player.y = self.spawn_platform.get_center()
                self.player.trail = []
    
    def draw(self):
        self.screen.fill(self.world_config["bg_color"])
        pygame.draw.rect(self.screen, BORDER_COLOR, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), BORDER_THICKNESS)
        
        # Draw spawn platform
        self.spawn_platform.draw(self.screen)
        
        for element in self.background_elements:
            element.draw(self.screen)
        
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
        
        world_text = self.font.render(f"World: {self.current_world}", True, WHITE)
        self.screen.blit(world_text, (20, 20))
        
        for i in range(self.lives):
            heart_x = 20 + i * 40
            heart_y = 70
            pygame.draw.circle(self.screen, RED, (heart_x, heart_y), 15)
            pygame.draw.circle(self.screen, (200, 0, 0), (heart_x, heart_y), 15, 2)
            # Draw heart shape
            pygame.draw.polygon(self.screen, RED, [
                (heart_x, heart_y + 5),
                (heart_x - 10, heart_y - 5),
                (heart_x - 5, heart_y - 10),
                (heart_x, heart_y - 5),
                (heart_x + 5, heart_y - 10),
                (heart_x + 10, heart_y - 5)
            ])
        
        time_text = self.font.render(f"Time: {int(self.time_remaining)}s", True, WHITE)
        self.screen.blit(time_text, (SCREEN_WIDTH - 200, 20))
        
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - 100, 20))
        
        best_text = self.small_font.render(f"Best: {self.best_score}", True, YELLOW)
        self.screen.blit(best_text, (SCREEN_WIDTH // 2 - 50, 60))
        
        for power_up in self.power_ups:
            power_up.draw(self.screen)
        
        self.portal.draw(self.screen)
        
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        self.player.draw(self.screen)
        
        self.exit_button.draw(self.screen)
        
        if self.state == "GAME_OVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.font.render("GAME OVER", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(game_over_text, text_rect)
            
            score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(score_text, score_rect)
            
            if self.score >= self.best_score:
                new_record_text = self.font.render("NEW RECORD!", True, YELLOW)
                record_rect = new_record_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                self.screen.blit(new_record_text, record_rect)
            
            restart_text = self.small_font.render("Press R to Restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
            self.screen.blit(restart_text, restart_rect)
            
        elif self.state == "LEVEL_COMPLETE":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            complete_text = self.font.render("LEVEL COMPLETE!", True, GREEN)
            text_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(complete_text, text_rect)
            
            score_text = self.font.render(f"Score: {self.score}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(score_text, score_rect)
            
            next_text = self.small_font.render("Press SPACE to Continue", True, WHITE)
            next_rect = next_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(next_text, next_rect)
            
            # Show next world preview
            next_world_index = (self.current_world_index + 1) % len(self.worlds_list)
            next_world = self.worlds_list[next_world_index]
            preview_text = self.small_font.render(f"Next: {next_world}", True, YELLOW)
            preview_rect = preview_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
            self.screen.blit(preview_text, preview_rect)
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

# Main execution
if __name__ == "__main__":
    game = Game()
    game.run()