import pygame
import random
import sys
import math
from collections import deque

# Initialize Pygame
pygame.init()

# Constants {
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
GRID_SIZE = 4
BOX_SIZE = SCREEN_WIDTH // GRID_SIZE
FPS = 60

# Enhanced Color Palette {
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
DARKER_GRAY = (64, 64, 64)
ROAD_COLOR = (45, 45, 45)  # Darker asphalt color
CURB_COLOR = (180, 180, 180)  # Light gray for curbs
GRASS_COLOR = (100, 160, 50)  # Green for roadside
POLE_COLOR = (70, 70, 70)  # Dark gray for signal poles
# }

# Game settings {
TRANSITION_TIME = 5 * FPS  # 5 seconds
SIGNAL_TIME = 10 * FPS    # 10 seconds
MAX_CARS = 20  # Slightly increased car count
SAFE_DISTANCE = 15
INTERSECTION_MARGIN = 25
# }
# }

# Setup display {
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Enhanced Realistic Traffic Simulation")
clock = pygame.time.Clock()
# }

class Car:
    def __init__(self, x, y, direction, speed, image):
        # Position and movement {
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        # }
        
        # Image handling {
        self.original_image = image
        self.image = pygame.transform.rotate(self.original_image, self.get_rotation_angle())
        self.rect = self.image.get_rect(topleft=(x, y))
        # }
        
        # State flags {
        self.braking = False
        self.in_intersection = False
        # }
        
        # Lane positioning {
        self.lane = None
        if direction in ['N', 'S']:
            self.lane = self.x + (self.rect.width // 2)
        else:
            self.lane = self.y + (self.rect.width // 2)
        # }

    def get_rotation_angle(self):
        rotation_map = {
            'N': 90,
            'S': 0,
            'E': 0,
            'W': 180
        }
        return rotation_map.get(self.direction, 0)

    def is_in_intersection(self):
        intersection_zone = (BOX_SIZE, BOX_SIZE, BOX_SIZE * 2, BOX_SIZE * 2)
        return self.rect.colliderect(pygame.Rect(intersection_zone))

    def will_collide_with_others(self, new_x, new_y, cars):
        future_rect = self.rect.copy()
        future_rect.x = new_x
        future_rect.y = new_y

        for car in cars:
            if car != self:
                # Direct collision check
                if future_rect.colliderect(car.rect):
                    return True

                # Safe distance check {
                if car.direction == self.direction and abs(car.lane - self.lane) < self.rect.width:
                    if self.direction == 'N' and car.y < self.y and self.y - (car.y + car.rect.height) < SAFE_DISTANCE:
                        return True
                    elif self.direction == 'S' and car.y > self.y and car.y - (self.y + self.rect.height) < SAFE_DISTANCE:
                        return True
                    elif self.direction == 'E' and car.x > self.x and car.x - (self.x + self.rect.height) < SAFE_DISTANCE:
                        return True
                    elif self.direction == 'W' and car.x < self.x and self.x - (car.x + car.rect.height) < SAFE_DISTANCE:
                        return True
                # }
        return False

    def move(self, stop_signals, cars, transitioning):
        global active_ns_cars, active_ew_cars
        
        # State update {
        self.braking = False
        was_in_intersection = self.in_intersection
        self.in_intersection = self.is_in_intersection()
        # }

        # Intersection tracking {
        if not was_in_intersection and self.in_intersection:
            if self.direction in ['N', 'S']:
                active_ns_cars.append(self)
            else:
                active_ew_cars.append(self)
        # }

        # Movement calculation {
        new_x, new_y = self.x, self.y
        current_direction = self.direction
        
        if current_direction == 'N':
            new_y = self.y - self.speed
        elif current_direction == 'S':
            new_y = self.y + self.speed
        elif current_direction == 'E':
            new_x = self.x + self.speed
        elif current_direction == 'W':
            new_x = self.x - self.speed
        # }

        # Movement execution {
        should_stop = (self.should_stop_at_intersection(stop_signals, transitioning, current_direction) or 
                      self.will_collide_with_others(new_x, new_y, cars))
        
        if not should_stop:
            self.x, self.y = new_x, new_y
            self.rect.x, self.rect.y = self.x, self.y
        else:
            self.braking = True
        # }

    def should_stop_at_intersection(self, stop_signals, transitioning, current_direction):
        if self.in_intersection:
            return False

        # Intersection boundaries
        intersection_zone = BOX_SIZE, BOX_SIZE * 3

        # Transition handling
        if transitioning:
            if current_direction in ['N', 'S'] and self not in active_ns_cars:
                return True
            if current_direction in ['E', 'W'] and self not in active_ew_cars:
                return True

        # Signal checks
        if current_direction in ['N', 'S'] and stop_signals['NS']:
            return True
        elif current_direction in ['E', 'W'] and stop_signals['EW']:
            return True
        
        return False

    def draw(self, screen):
        # Draw car {
        screen.blit(self.image, (self.x, self.y))
        # }

        # Draw brake lights {
        if self.braking:
            brake_color = RED
            brake_size = 10
            
            if self.direction in ['N', 'S']:
                brake_pos = (int(self.x + self.rect.width/2), int(self.y + self.rect.height))
            else:
                brake_pos = (int(self.x), int(self.y + self.rect.height/2))
                
            pygame.draw.circle(screen, brake_color, brake_pos, brake_size)
        # }

def generate_car(cars, car_images):
    if len(cars) < MAX_CARS:
        # Car properties {
        direction = random.choice(['N', 'S', 'E', 'W'])
        speed = random.randint(3, 5)
        # }
        
        # Position calculation {
        if direction == 'N':
            x = BOX_SIZE * 1.5 - car_images[direction].get_width() // 2
            y = SCREEN_HEIGHT + car_images[direction].get_height()
        elif direction == 'S':
            x = BOX_SIZE * 2.5 - car_images[direction].get_width() // 2
            y = -car_images[direction].get_height()
        elif direction == 'E':
            x = -car_images[direction].get_height()
            y = BOX_SIZE * 1.5 - car_images[direction].get_width() // 2
        else:  # W
            x = SCREEN_WIDTH + car_images[direction].get_height()
            y = BOX_SIZE * 2.5 - car_images[direction].get_width() // 2
        # }

        # Create and add car {
        new_car = Car(x, y, direction, speed, car_images[direction])
        if not any(new_car.rect.colliderect(car.rect) for car in cars):
            cars.append(new_car)
        # }

def draw_road_texture():
    # More detailed background
    screen.fill(GRASS_COLOR)
    
    # Add noise/texture to grass
    for _ in range(1000):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        color_variation = random.randint(-20, 20)
        grass_var = tuple(max(0, min(255, GRASS_COLOR[i] + color_variation)) for i in range(3))
        pygame.draw.circle(screen, grass_var, (x, y), 1)
    
    # More realistic road rendering
    road_rect = pygame.Surface((BOX_SIZE * 2, SCREEN_HEIGHT), pygame.SRCALPHA)
    road_rect.fill((45, 45, 45, 230))  # Slightly transparent
    screen.blit(road_rect, (BOX_SIZE, 0))
    
    road_rect = pygame.Surface((SCREEN_WIDTH, BOX_SIZE * 2), pygame.SRCALPHA)
    road_rect.fill((45, 45, 45, 230))
    screen.blit(road_rect, (0, BOX_SIZE))
    
    # Add subtle road texture
    for _ in range(500):
        x = random.randint(BOX_SIZE, BOX_SIZE * 3)
        y = random.randint(0, SCREEN_HEIGHT)
        pygame.draw.line(screen, (50, 50, 50), (x, y), (x, y+1), 1)

    # Retain original lane markings
    dash_length = 30
    gap_length = 30
    stripe_width = 3
    total_length = dash_length + gap_length

    # Center lines (double yellow)
    # Vertical
    pygame.draw.rect(screen, YELLOW, (BOX_SIZE * 2 - stripe_width - 2, 0, stripe_width, SCREEN_HEIGHT))
    pygame.draw.rect(screen, YELLOW, (BOX_SIZE * 2 + 2, 0, stripe_width, SCREEN_HEIGHT))
    # Horizontal
    pygame.draw.rect(screen, YELLOW, (0, BOX_SIZE * 2 - stripe_width - 2, SCREEN_WIDTH, stripe_width))
    pygame.draw.rect(screen, YELLOW, (0, BOX_SIZE * 2 + 2, SCREEN_WIDTH, stripe_width))

    # White dashed lines
    # Draw vertical dashed lines
    for i in range(0, SCREEN_HEIGHT, total_length):
        if i < BOX_SIZE or i > BOX_SIZE * 3:  # Don't draw in intersection
            pygame.draw.rect(screen, WHITE, (BOX_SIZE * 1.5 - stripe_width//2, i, stripe_width, dash_length))
            pygame.draw.rect(screen, WHITE, (BOX_SIZE * 2.5 - stripe_width//2, i, stripe_width, dash_length))

    # Draw horizontal dashed lines
    for i in range(0, SCREEN_WIDTH, total_length):
        if i < BOX_SIZE or i > BOX_SIZE * 3:  # Don't draw in intersection
            pygame.draw.rect(screen, WHITE, (i, BOX_SIZE * 1.5 - stripe_width//2, dash_length, stripe_width))
            pygame.draw.rect(screen, WHITE, (i, BOX_SIZE * 2.5 - stripe_width//2, dash_length, stripe_width))

def draw_traffic_light_housing(x, y, orientation):
    housing_width = 40
    housing_height = 90
    housing_depth = 15
    
    if orientation == 'vertical':
        # Main housing
        pygame.draw.rect(screen, BLACK, (x - housing_width//2, y - housing_height//2, 
                                       housing_width, housing_height))
        # 3D effect
        pygame.draw.polygon(screen, DARKER_GRAY, [
            (x + housing_width//2, y - housing_height//2),
            (x + housing_width//2 + housing_depth, y - housing_height//2 + housing_depth),
            (x + housing_width//2 + housing_depth, y + housing_height//2 + housing_depth),
            (x + housing_width//2, y + housing_height//2)
        ])
    else:
        # Main housing
        pygame.draw.rect(screen, BLACK, (x - housing_height//2, y - housing_width//2,
                                       housing_height, housing_width))
        # 3D effect
        pygame.draw.polygon(screen, DARKER_GRAY, [
            (x - housing_height//2, y - housing_width//2),
            (x + housing_height//2, y - housing_width//2),
            (x + housing_height//2, y - housing_width//2 - housing_depth),
            (x - housing_height//2, y - housing_width//2 - housing_depth)
        ])

def draw_traffic_lights(signals, transitioning):
    # Light properties
    light_radius = 15
    
    # Draw lights for each direction
    positions = {
        'N': (BOX_SIZE * 3.2, BOX_SIZE),
        'S': (BOX_SIZE * 0.8, BOX_SIZE * 3),
        'E': (BOX_SIZE, BOX_SIZE * 0.8),
        'W': (BOX_SIZE * 3, BOX_SIZE * 3.2)
    }

    for pos, (x, y) in positions.items():
        # Draw traditional housing
        draw_traffic_light_housing(x, y, 'vertical')

        # Determine signal color
        is_ns = pos in ['N', 'S']
        signal_color = YELLOW if transitioning else (GREEN if not signals['NS' if is_ns else 'EW'] else RED)
        
        # Draw light
        pygame.draw.circle(screen, signal_color, (x, y), light_radius)

def load_car_images():
    try:
        # Load PNG images for cars
        car_images = {
            'N': pygame.transform.scale(pygame.image.load('car_north.png'), (60, 40)),
            'S': pygame.transform.scale(pygame.image.load('car_south.png'), (60, 40)),
            'E': pygame.transform.scale(pygame.image.load('car_east.png'), (60, 40)),
            'W': pygame.transform.scale(pygame.image.load('car_west.png'), (60, 40))
        }
        return car_images
    except pygame.error as e:
        print(f"Error loading car images: {e}")
        print("Please ensure car PNG files (car_north.png, car_south.png, car_east.png, car_west.png) are in the same directory.")
        return None

def main():
    global active_ns_cars, active_ew_cars
    
    # Initialize game state {
    active_ns_cars = []
    active_ew_cars = []
    cars = []
    signal_timer = 0
    transition_timer = 0
    signals = {'NS': True, 'EW': False}
    transitioning = False
    # }

    # Load car images
    car_images = load_car_images()
    if car_images is None:
        return

    # Game loop {
    running = True
    while running:
        # Event handling {
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        # }

        # Signal timing {
        if transitioning:
            transition_timer += 1
            if transition_timer >= TRANSITION_TIME:
                transitioning = False
                transition_timer = 0
                signals['NS'] = not signals['NS']
                signals['EW'] = not signals['EW']
                active_ns_cars.clear()
                active_ew_cars.clear()
        else:
            signal_timer += 1
            if signal_timer >= SIGNAL_TIME:
                transitioning = True
                signal_timer = 0
        # }

        # Car generation {
        if random.randint(1, 15) == 1:
            generate_car(cars, car_images)
        # }

        # Drawing {
        draw_road_texture()
        draw_traffic_lights(signals, transitioning)
        # }

        # Car updates {
        for car in cars[:]:
            car.move(signals, cars, transitioning)
            car.draw(screen)
        # }

        # Cleanup off-screen cars {
        for car in cars[:]:
            if ((car.direction == 'N' and car.y < -car.rect.height) or
                (car.direction == 'S' and car.y > SCREEN_HEIGHT + car.rect.height) or
                (car.direction == 'E' and car.x > SCREEN_WIDTH + car.rect.height) or
                (car.direction == 'W' and car.x < -car.rect.height)):
                
                if car in active_ns_cars:
                    active_ns_cars.remove(car)
                if car in active_ew_cars:
                    active_ew_cars.remove(car)
                cars.remove(car)
        # }

        pygame.display.flip()
        clock.tick(FPS)
    # }

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
