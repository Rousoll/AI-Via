import pygame
import sys
import os
import json
import random

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 800
CENTER = WIDTH // 2, HEIGHT // 2
ROAD_WIDTH = 140
INTERSECTION_SIZE = 180
STOP_LINE_DIST = INTERSECTION_SIZE // 2 + 10
CAR_SIZE = (22, 38)
EMERGENCY_SIZE = (28, 48)
GAP = 16

LANE_POSITIONS = [
    (CENTER[0], CENTER[1] - 200),  # Top
    (CENTER[0] + 200, CENTER[1]),  # Right
    (CENTER[0], CENTER[1] + 200),  # Bottom
    (CENTER[0] - 200, CENTER[1])   # Left
]
LANE_DIRECTIONS = [
    (0, 1),   # Down
    (-1, 0),  # Left
    (0, -1),  # Up
    (1, 0)    # Right
]
LANE_LABELS = ['A', 'B', 'C', 'D']
CAR_COLORS = [(100, 200, 255), (255, 200, 100), (200, 255, 100), (200, 100, 255), (255, 100, 200)]
AMBULANCE_COLOR = (255, 0, 0)
POLICE_COLOR = (0, 0, 0)
FIRETRUCK_COLOR = (0, 200, 0)
VEHICLE_TYPE_COLOR = {
    'ambulance': AMBULANCE_COLOR,
    'police': POLICE_COLOR,
    'fire': FIRETRUCK_COLOR
}

def load_signals_for_intersection(folder_path='class_counts'):
    files = sorted(os.listdir(folder_path))[:4]
    emergency_types = ['ambulance', 'fire', 'police']
    signals = []
    for file in files:
        with open(os.path.join(folder_path, file), 'r') as f:
            data = json.load(f)
            vehicles = []
            for etype in emergency_types:
                vehicles += [etype] * data.get(etype, 0)
            vehicles += ['car'] * sum(data.get(k, 0) for k in data if k not in emergency_types)
            random.shuffle(vehicles)
            signals.append({
                'file_name': file,
                'vehicles': vehicles
            })
    return signals

class Vehicle:
    def __init__(self, vtype, lane_idx, pos_idx):
        self.vtype = vtype
        self.lane_idx = lane_idx
        self.pos_idx = pos_idx
        self.size = EMERGENCY_SIZE if vtype != 'car' else CAR_SIZE
        self.color = VEHICLE_TYPE_COLOR.get(vtype, CAR_COLORS[pos_idx % len(CAR_COLORS)])
        self.reset_position()

    def reset_position(self):
        x, y = LANE_POSITIONS[self.lane_idx]
        dx, dy = LANE_DIRECTIONS[self.lane_idx]
        offset = STOP_LINE_DIST + (self.pos_idx) * (self.size[1] + GAP)
        self.x = x - dx * offset - self.size[0] // 2
        self.y = y - dy * offset - self.size[1] // 2

    def move(self, speed=5):
        dx, dy = LANE_DIRECTIONS[self.lane_idx]
        self.x += dx * speed
        self.y += dy * speed

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size[0], self.size[1]), border_radius=10)

def load_signals_for_intersection(folder_path='class_counts'):
    files = sorted(os.listdir(folder_path))[:4]
    emergency_types = ['ambulance', 'fire', 'police']
    signals = []
    for file in files:
        with open(os.path.join(folder_path, file), 'r') as f:
            data = json.load(f)
            vehicles = []
            for etype in emergency_types:
                vehicles += [etype] * data.get(etype, 0)
            vehicles += ['car'] * sum(data.get(k, 0) for k in data if k not in emergency_types)
            random.shuffle(vehicles)
            signals.append({
                'file_name': file,
                'vehicles': vehicles
            })
    return signals

def create_lane_vehicles(signals):
    lanes = []
    for idx, signal in enumerate(signals):
        lane = []
        for pos_idx, vtype in enumerate(signal['vehicles']):
            lane.append(Vehicle(vtype, idx, pos_idx))
        lanes.append(lane)
    return lanes

def get_next_active_idx(signals, current_idx):
    # Priority: ambulance > fire > police > most cars
    for priority in ['ambulance', 'fire', 'police']:
        for idx, signal in enumerate(signals):
            if priority in signal['vehicles']:
                return idx
    max_cars = max((s['vehicles'].count('car'), idx) for idx, s in enumerate(signals))
    if max_cars[0] > 0:
        return max_cars[1]
    return (current_idx + 1) % len(signals)

def draw_intersection(screen, lanes, active_idx, font, big_font):
    screen.fill((230,230,230))
    # Draw roads
    pygame.draw.rect(screen, (180,180,180), (CENTER[0]-ROAD_WIDTH//2, 0, ROAD_WIDTH, HEIGHT))
    pygame.draw.rect(screen, (180,180,180), (0, CENTER[1]-ROAD_WIDTH//2, WIDTH, ROAD_WIDTH))
    # Draw intersection
    pygame.draw.rect(screen, (90,90,90), (CENTER[0]-INTERSECTION_SIZE//2, CENTER[1]-INTERSECTION_SIZE//2, INTERSECTION_SIZE, INTERSECTION_SIZE), border_radius=40)
    # Draw stop lines
    for idx in range(4):
        x, y = CENTER
        dx, dy = LANE_DIRECTIONS[idx]
        lx = x + dx * STOP_LINE_DIST
        ly = y + dy * STOP_LINE_DIST
        if dx == 0:
            pygame.draw.line(screen, (255,255,255), (lx-40, ly), (lx+40, ly), 8)
        else:
            pygame.draw.line(screen, (255,255,255), (lx, ly-40), (lx, ly+40), 8)
    # Draw traffic lights at lane entrance
    for idx in range(4):
        x, y = LANE_POSITIONS[idx]
        dx, dy = LANE_DIRECTIONS[idx]
        light_x = x - dx * 60 - dy * 40
        light_y = y - dy * 60 - dx * 40
        for i, color in enumerate([(255,0,0), (255,255,0), (0,255,0)]):
            is_on = (i == 2 and idx == active_idx)
            pygame.draw.circle(screen, color if is_on else (180,180,180), (int(light_x), int(light_y + i*28)), 15)
    # Draw vehicles
    for lane in lanes:
        for v in lane:
            v.draw(screen)
    # Draw lane labels
    for idx in range(4):
        x, y = LANE_POSITIONS[idx]
        dx, dy = LANE_DIRECTIONS[idx]
        label = big_font.render(LANE_LABELS[idx], True, (50,50,50))
        screen.blit(label, (x-18, y-60 if dy==0 else y-18))

def simulate_intersection(signals):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Intersection Simulation")
    font = pygame.font.SysFont(None, 26)
    big_font = pygame.font.SysFont(None, 40)
    clock = pygame.time.Clock()

    active_idx = get_next_active_idx(signals, -1)
    lanes = create_lane_vehicles(signals)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        lane = lanes[active_idx]
        if lane:
            v = lane[0]
            dx, dy = LANE_DIRECTIONS[active_idx]
            # Check if vehicle has crossed the intersection
            crossed = (
                (dx != 0 and ((dx > 0 and v.x > CENTER[0]+INTERSECTION_SIZE//2) or (dx < 0 and v.x < CENTER[0]-INTERSECTION_SIZE//2 - v.size[0])))
                or
                (dy != 0 and ((dy > 0 and v.y > CENTER[1]+INTERSECTION_SIZE//2) or (dy < 0 and v.y < CENTER[1]-INTERSECTION_SIZE//2 - v.size[1])))
            )
            if crossed:
                lane.pop(0)
                for idx2, v2 in enumerate(lane):
                    v2.pos_idx = idx2
                    v2.reset_position()
            else:
                v.move(speed=8 if v.vtype == 'car' else 5)

            # If the first vehicle is an emergency and has passed the intersection, switch lane
            if not lane or (not any(v.vtype in ['ambulance', 'fire', 'police'] for v in lane)):
                active_idx = get_next_active_idx(
                    [{'vehicles': [v.vtype for v in lane]} for lane in lanes], active_idx)
        else:
            # No vehicles left in this lane, go to next
            active_idx = get_next_active_idx(
                [{'vehicles': [v.vtype for v in lane]} for lane in lanes], active_idx)

        draw_intersection(screen, lanes, active_idx, font, big_font)
        pygame.display.flip()
        clock.tick(75)

        # End simulation if all lanes are empty
        if all(len(lane) == 0 for lane in lanes):
            pygame.time.wait(800)
            running = False

    # End screen
    screen.fill((255,255,255))
    end_text = big_font.render("Simulation Complete!", True, (0, 180, 0))
    screen.blit(end_text, (WIDTH//2-180, HEIGHT//2-20))
    pygame.display.flip()
    pygame.time.wait(2000)
    pygame.quit()

if __name__ == "__main__":
    signals = load_signals_for_intersection()
    simulate_intersection(signals)