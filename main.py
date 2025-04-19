from board import boards
from collections import deque
import time
import pygame
import math
import random
import heapq
import tracemalloc
import time
pygame.init()
pygame.mixer.init()  # Khởi tạo mixer cho âm thanh
move_sound = pygame.mixer.Sound("sound/tick.mp3")

WIDTH = 1100
HEIGHT = 900
TILE_WIDTH = WIDTH // 30
TILE_HEIGHT = (HEIGHT - 50) // 32

screen = pygame.display.set_mode([WIDTH, HEIGHT])
timer = pygame.time.Clock()
pygame.display.set_caption("Pacman")
fps = 60
color = "blue"
PI = math.pi
font = pygame.font.Font("freesansbold.ttf", 20)
level = boards
counter = 0
count = 0
flicker = False

# Tải nhạc nền
try:
    background_music = pygame.mixer.music.load("sound/background.mp3")
    pygame.mixer.music.set_volume(0.5)  # 50% âm lượng
except:
    print("Không thể tải file nhạc nền. Đảm bảo file MP3 đã được thêm vào thư mục 'sound'.")

player_images_right = []
for i in range(1, 5):
    player_images_right.append(
        pygame.transform.scale(pygame.image.load(f"player_images/{i}.png"), (45, 45))
    )

player_images_left = []
for i in range(1, 5):
    img = pygame.transform.scale(pygame.image.load(f"player_images/{i}.png"), (45, 45))
    player_images_left.append(pygame.transform.rotate(img, 180))


player_images_up = []
for i in range(1, 5):
    img = pygame.transform.scale(pygame.image.load(f"player_images/{i}.png"), (45, 45))
    player_images_up.append(pygame.transform.rotate(img, 90))

player_images_down = []
for i in range(1, 5):
    img = pygame.transform.scale(pygame.image.load(f"player_images/{i}.png"), (45, 45))
    player_images_down.append(pygame.transform.rotate(img, 270))


def calculate_game_duration(start_time):
    return time.time() - start_time


# ====== DOT CLASS ======
class Dot:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 2, y - 2, 4, 4)
        self.eaten = False

    def draw(self):
        if not self.eaten:
            pygame.draw.circle(screen, (255, 255, 0), self.rect.center, 3)

dots = []

def create_dots():
    for y in range(len(level)):
        for x in range(len(level[0])):
            if level[y][x] in [1, 2]:
                pos_x = x * TILE_WIDTH + TILE_WIDTH // 2
                pos_y = y * TILE_HEIGHT + TILE_HEIGHT // 2
                dots.append(Dot(pos_x, pos_y))

class Ghost:
    def __init__(self, image_path, speed):
        self.num1 = (HEIGHT - 50) // 32  # Cell height
        self.num2 = WIDTH // 30  # Cell width
        self.image = pygame.transform.scale(pygame.image.load(image_path), (45, 45))
        self.speed = 3
        self.path = []
        self.move_delay = 30
        self.count = 8
        self.target_x = 0
        self.target_y = 0
        self.move_counter = 0
        self.set_initial_position()

    def move(self):
        if not self.path:
            self.calculate_path_to_player()
            if self.count == 8:
                # If no path, calculate a new path to the player
                self.calculate_path_to_player()

            if self.count > 0:
                dx = self.target_x - self.x
                dy = self.target_y - self.y
                distance = math.hypot(dx, dy)
                if self.count == 1:
                    self.x = self.target_x
                    self.y = self.target_y
                    self.count = 0
                else:
                    self.x += (dx / distance) * self.speed
                    self.y += (dy / distance) * self.speed
                    self.count -= 1

            if self.path:
                next_cell = self.path.pop(0)
                self.target_x = next_cell[0] * self.num2 + (0.5 * self.num2) - 22
                self.target_y = next_cell[1] * self.num1 + (0.5 * self.num1) - 22
        else:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.hypot(dx, dy)

            if distance < self.speed:
                self.x = self.target_x
                self.y = self.target_y

                if self.path:
                    if len(self.path) == 1:
                        self.count -= 1
                    next_cell = self.path.pop(0)
                    self.target_x = next_cell[0] * self.num2 + (0.5 * self.num2) - 22
                    self.target_y = next_cell[1] * self.num1 + (0.5 * self.num1) - 22
            else:
                # Di chuyển từng bước nhỏ hướng về target
                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed

    def teleport(self):
        # Tìm một vị trí hợp lệ ngẫu nhiên trên bản đồ
        valid_positions = []
        for y in range(len(level)):
            for x in range(len(level[0])):
                # Chỉ thêm các ô đường đi hợp lệ
                if level[y][x] in [1, 2, 9]:
                    valid_positions.append((x, y))

        if valid_positions:
            # Chọn ngẫu nhiên một vị trí
            new_x, new_y = random.choice(valid_positions)
            # Cập nhật vị trí
            self.x = new_x * self.num2 + (0.5 * self.num2) - 22
            self.y = new_y * self.num1 + (0.5 * self.num1) - 22
            # Đặt lại đường đi
            self.path = []
            self.count = 8
            # Hiển thị hiệu ứng dịch chuyển (tuỳ chọn)
            self.show_teleport_effect()

    def show_teleport_effect(self):
        # Hiệu ứng đơn giản khi dịch chuyển, vẽ một vòng tròn ở vị trí mới
        pygame.draw.circle(screen, "white", (self.x + 22, self.y + 22), 20, 2)
        pygame.display.update()
        pygame.time.delay(100)  # Dừng 100ms để hiệu ứng hiển thị rõ hơn

    def draw_ghost(self):
        screen.blit(self.image, (self.x, self.y))


def display_statistics():
    stat_font = pygame.font.Font("freesansbold.ttf", 24)
    ghosts_names = ["Pink (DFS)", "Blue (BFS)", "Orange (UCS)", "Red (A*)"]
    start_y = HEIGHT // 2 + 150

    for i, ghost in enumerate(ghosts):
        try:
            text = (f"{ghosts_names[i]} | "
                    f"Total Time: {round(ghost.total_search_time, 4)}s | "
                    f"Total Memory: {round(ghost.total_memory_usage, 2)}KB | "
                    f"Total Expanded: {ghost.total_expanded_nodes}")
        except AttributeError:
            text = f"{ghosts_names[i]} | No Data"
        
        stat_text = stat_font.render(text, True, "white")
        screen.blit(stat_text, (WIDTH//2 - 400, start_y + i*30))



class Pink_ghost(Ghost):
    def __init__(self):
        super().__init__("ghost_images/pink.png", 4)
        self.total_search_time = 0
        self.total_memory_usage = 0
        self.total_expanded_nodes = 0


    def set_initial_position(self):
        x = len(level[0]) // 2 + 2
        y = len(level) // 2 - 2
        self.x = x * self.num2 + (0.5 * self.num2) - 22
        self.y = y * self.num1 + (0.5 * self.num1) - 22

    def calculate_path_to_player(self):
        ghost_grid_x = int((self.x + 22) // self.num2)
        ghost_grid_y = int((self.y + 22) // self.num1)
        player_grid_x = int((player.x + 22) // self.num2)
        player_grid_y = int((player.y + 22) // self.num1)

        self.path = self.find_path(
            (ghost_grid_x, ghost_grid_y), (player_grid_x, player_grid_y)
        )

    def find_path(self, start, goal):
        tracemalloc.start()
        start_time = time.time()

        path, expanded = self.dfs(start, goal)

        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.search_time = end_time - start_time
        self.memory_usage = peak / 1024  # in KB
        self.expanded_nodes = expanded
         # Cộng dồn vô tổng
        self.total_search_time += self.search_time
        self.total_memory_usage += self.memory_usage
        self.total_expanded_nodes += expanded

        return path
    
    def dfs(self, start, goal):
        stack = [(start, [])]
        visited = set()
        expanded = 0

        while stack:
            (x, y), path = stack.pop()
            expanded += 1

            if (x, y) == goal:
                return path + [(x, y)], expanded

            if (x, y) in visited:
                continue
            visited.add((x, y))

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < len(level[0]) and 0 <= ny < len(level):
                    if level[ny][nx] in [1, 2, 9, 10]:
                        stack.append(((nx, ny), path + [(x, y)]))

        return [], expanded


class Blue_ghost(Ghost):
    def __init__(self):
        super().__init__("ghost_images/blue.png", 3)
        self.total_search_time = 0
        self.total_memory_usage = 0
        self.total_expanded_nodes = 0


    def set_initial_position(self):
        x = len(level[0]) // 2 - 3
        y = len(level) // 2 - 2
        self.x = x * self.num2 + (0.5 * self.num2) - 22
        self.y = y * self.num1 + (0.5 * self.num1) - 22

    def calculate_path_to_player(self):
        ghost_grid_x = int((self.x + 22) // self.num2)
        ghost_grid_y = int((self.y + 22) // self.num1)
        player_grid_x = int((player.x + 22) // self.num2)
        player_grid_y = int((player.y + 22) // self.num1)

        self.path = self.find_path(
            (ghost_grid_x, ghost_grid_y), (player_grid_x, player_grid_y)
        )

    def find_path(self, start, goal):
        tracemalloc.start()
        start_time = time.time()

        path, expanded = self.bfs(start, goal)

        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.search_time = end_time - start_time
        self.memory_usage = peak / 1024  # in KB
        self.expanded_nodes = expanded
         # Cộng dồn vô tổng
        self.total_search_time += self.search_time
        self.total_memory_usage += self.memory_usage
        self.total_expanded_nodes += expanded
        return path

    
    def bfs(self, start, goal):
            queue = deque([(start, [])])
            visited = set()
            expanded = 0

            while queue:
                (x, y), path = queue.popleft()
                expanded += 1

                if (x, y) == goal:
                    return path + [(x, y)], expanded

                if (x, y) in visited:
                    continue
                visited.add((x, y))

                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < len(level[0]) and 0 <= ny < len(level):
                        if level[ny][nx] in [1, 2, 9, 10]:
                            queue.append(((nx, ny), path + [(x, y)]))

            return [], expanded 


class Orange_ghost(Ghost):
    def __init__(self):
        super().__init__("ghost_images/orange.png", 3)
        self.total_search_time = 0
        self.total_memory_usage = 0
        self.total_expanded_nodes = 0

    def set_initial_position(self):
        x = len(level[0]) // 2 - 3
        y = len(level) // 2
        self.x = x * self.num2 + (0.5 * self.num2) - 22
        self.y = y * self.num1 + (0.5 * self.num1) - 22

    def calculate_path_to_player(self):
        ghost_grid_x = int((self.x + 22) // self.num2)
        ghost_grid_y = int((self.y + 22) // self.num1)
        player_grid_x = int((player.x + 22) // self.num2)
        player_grid_y = int((player.y + 22) // self.num1)

        self.path = self.find_path(
            (ghost_grid_x, ghost_grid_y), (player_grid_x, player_grid_y)
        )

    def find_path(self, start, goal):
        tracemalloc.start()
        start_time = time.time()

        path, expanded = self.ucs(start, goal)

        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.search_time = end_time - start_time
        self.memory_usage = peak / 1024  # KB
        self.expanded_nodes = expanded

         # Cộng dồn vô tổng
        self.total_search_time += self.search_time
        self.total_memory_usage += self.memory_usage
        self.total_expanded_nodes += expanded

        return path

    def ucs(self, start, goal):
        queue = [(0, start, [])]
        visited = set()
        expanded = 0

        while queue:
            cost, (x, y), path = heapq.heappop(queue)
            expanded += 1

            if (x, y) == goal:
                return path + [(x, y)], expanded

            if (x, y) in visited:
                continue
            visited.add((x, y))

            move = [
                (0, -1, 3),  # up
                (0, 1, 1),   # down
                (-1, 0, 2),  # left
                (1, 0, 2),   # right
            ]

            for dx, dy, move_cost in move:
                nx, ny = x + dx, y + dy
                if 0 <= nx < len(level[0]) and 0 <= ny < len(level):
                    if level[ny][nx] in [1, 2, 9, 10]:
                        heapq.heappush(
                            queue, (cost + move_cost, (nx, ny), path + [(x, y)])
                        )

        return [], expanded


class RedGhost(Ghost):
    def __init__(self):
        super().__init__("ghost_images/red.png", 3)
        self.total_search_time = 0
        self.total_memory_usage = 0
        self.total_expanded_nodes = 0

    def set_initial_position(self):
        x = len(level[0]) // 2 + 2
        y = len(level) // 2
        self.x = x * self.num2 + (0.5 * self.num2) - 22
        self.y = y * self.num1 + (0.5 * self.num1) - 22

    def calculate_path_to_player(self):
        ghost_grid_x = int((self.x + 22) // self.num2)
        ghost_grid_y = int((self.y + 22) // self.num1)
        player_grid_x = int((player.x + 22) // self.num2)
        player_grid_y = int((player.y + 22) // self.num1)

        self.path = self.find_path(
            (ghost_grid_x, ghost_grid_y), (player_grid_x, player_grid_y)
        )

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_path(self, start, goal):
        tracemalloc.start()
        start_time = time.time()

        path, expanded = self.astar(start, goal)

        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.search_time = end_time - start_time
        self.memory_usage = peak / 1024
        self.expanded_nodes = expanded

         # Cộng dồn vô tổng
        self.total_search_time += self.search_time
        self.total_memory_usage += self.memory_usage
        self.total_expanded_nodes += expanded

        return path

    def astar(self, start, goal):
        open_set = [(0, start, [])]
        g_score = {start: 0}
        visited = set()
        expanded = 0

        while open_set:
            cost, current, path = heapq.heappop(open_set)
            expanded += 1

            if current == goal:
                return path + [current], expanded

            if current in visited:
                continue
            visited.add(current)

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = current[0] + dx, current[1] + dy
                neighbor = (nx, ny)
                if 0 <= nx < len(level[0]) and 0 <= ny < len(level):
                    if level[ny][nx] in [1, 2, 9, 10]:
                        tentative_g = g_score[current] + 1
                        if tentative_g < g_score.get(neighbor, float("inf")):
                            g_score[neighbor] = tentative_g
                            f_score = tentative_g + self.heuristic(neighbor, goal)
                            heapq.heappush(open_set, (f_score, neighbor, path + [current]))

        return [], expanded


class Player:
    def __init__(self):
        num1 = (HEIGHT - 50) // 32
        num2 = WIDTH // 30
        self.direction = "right"
        self.speed = 3

        while True:
            self.x = random.randint(0, 29)
            self.y = random.randint(0, 31)

            if level[self.y][self.x] == 1 or level[self.y][self.x] == 2:
                self.x = self.x * num2 + (0.5 * num2) - 22
                self.y = self.y * num1 + (0.5 * num1) - 22
                break

    def draw_player(self):
        if self.direction == "right":
            screen.blit(player_images_right[counter // 5], (self.x, self.y))
        elif self.direction == "left":
            screen.blit(player_images_left[counter // 5], (self.x, self.y))
        elif self.direction == "up":
            screen.blit(player_images_up[counter // 5], (self.x, self.y))
        elif self.direction == "down":
            screen.blit(player_images_down[counter // 5], (self.x, self.y))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, 45, 45)

    def draw(self):
        if self.direction == "right":
            screen.blit(player_images_right[counter // 5], (self.x, self.y))
        elif self.direction == "left":
            screen.blit(player_images_left[counter // 5], (self.x, self.y))
        elif self.direction == "up":
            screen.blit(player_images_up[counter // 5], (self.x, self.y))
        elif self.direction == "down":
            screen.blit(player_images_down[counter // 5], (self.x, self.y))

    def reset_position(self):
        self.x = starting_x
        self.y = starting_y
        self.direction = None  # hoặc "left" / "up" gì tùy
        self.rect.topleft = (self.x, self.y)

    def move(self):
        if self.direction == "up":
            self.y -= self.speed
        elif self.direction == "down":
            self.y += self.speed
        elif self.direction == "left":
            self.x -= self.speed
        elif self.direction == "right":
            self.x += self.speed

        self.check_collisions()

    def check_collisions(self):
        num1 = (HEIGHT - 50) // 32
        num2 = WIDTH // 30

        grid_x = int((self.x + 22) // num2)
        grid_y = int((self.y + 22) // num1)

        # Check if the next cell in the current direction is not a valid path
        if self.direction == "up":
            if level[grid_y - 1][grid_x] != 1 and level[grid_y - 1][grid_x] != 2:
                self.y = grid_y * num1 + (0.5 * num1) - 22
        elif self.direction == "down":
            if level[grid_y + 1][grid_x] != 1 and level[grid_y + 1][grid_x] != 2:
                self.y = grid_y * num1 + (0.5 * num1) - 22
        elif self.direction == "left":
            if level[grid_y][grid_x - 1] != 1 and level[grid_y][grid_x - 1] != 2:
                self.x = grid_x * num2 + (0.5 * num2) - 22
        elif self.direction == "right":
            if level[grid_y][grid_x + 1] != 1 and level[grid_y][grid_x + 1] != 2:
                self.x = grid_x * num2 + (0.5 * num2) - 22


def draw_board():
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    for i in range(len(level)):
        for j in range(len(level[i])):
            if level[i][j] == 3:
                pygame.draw.line(
                    screen,
                    color,
                    (j * num2 + (0.5 * num2), i * num1),
                    (j * num2 + (0.5 * num2), i * num1 + num1),
                    3,
                )
            if level[i][j] == 4:
                pygame.draw.line(
                    screen,
                    color,
                    (j * num2, i * num1 + (0.5 * num1)),
                    (j * num2 + num2, i * num1 + (0.5 * num1)),
                    3,
                )
            if level[i][j] == 5:
                pygame.draw.arc(
                    screen,
                    color,
                    [
                        (j * num2 - (num2 * 0.4)) - 2,
                        (i * num1 + (0.5 * num1)),
                        num2,
                        num1,
                    ],
                    0,
                    PI / 2,
                    3,
                )
            if level[i][j] == 6:
                pygame.draw.arc(
                    screen,
                    color,
                    [(j * num2 + (num2 * 0.5)), (i * num1 + (0.5 * num1)), num2, num1],
                    PI / 2,
                    PI,
                    3,
                )
            if level[i][j] == 7:
                pygame.draw.arc(
                    screen,
                    color,
                    [(j * num2 + (num2 * 0.5)), (i * num1 - (0.4 * num1)), num2, num1],
                    PI,
                    3 * PI / 2,
                    3,
                )
            if level[i][j] == 8:
                pygame.draw.arc(
                    screen,
                    color,
                    [
                        (j * num2 - (num2 * 0.4)) - 2,
                        (i * num1 - (0.4 * num1)),
                        num2,
                        num1,
                    ],
                    3 * PI / 2,
                    2 * PI,
                    3,
                )
            if level[i][j] == 9:
                pygame.draw.line(
                    screen,
                    "white",
                    (j * num2, i * num1 + (0.5 * num1)),
                    (j * num2 + num2, i * num1 + (0.5 * num1)),
                    3,
                )


def check_collision(player, ghost):
    player_grid_x = int((player.x + 22) // (WIDTH // 30))
    player_grid_y = int((player.y + 22) // ((HEIGHT - 50) // 32))
    ghost_grid_x = int((ghost.x + 22) // (WIDTH // 30))
    ghost_grid_y = int((ghost.y + 22) // ((HEIGHT - 50) // 32))

    return (abs(player_grid_x - ghost_grid_x) < 1.2) and (
        abs(player_grid_y - ghost_grid_y) < 1.2
    )


def display_game_over():
    game_over_font = pygame.font.Font("freesansbold.ttf", 64)
    game_over_text = game_over_font.render("GAME OVER", True, "red")
    screen.blit(game_over_text, (WIDTH // 2 - 200, HEIGHT // 2 - 50))
    pygame.display.flip()
    pygame.time.wait(3000)


def display_duration(duration):
    time_font = pygame.font.Font("freesansbold.ttf", 28)
    duration_text = time_font.render(
        f"Time: {round(float(duration), 2)}s", True, "red"
    )
    screen.blit(duration_text, (WIDTH // 2 - 200, 60))  # bên trái Score

def display_score(score):
    score_font = pygame.font.Font("freesansbold.ttf", 28)
    score_text = score_font.render(f"Score: {score}", True, "yellow")
    screen.blit(score_text, (WIDTH // 2 - 20, 60))  # giữa

def display_lives(lives):
    lives_font = pygame.font.Font("freesansbold.ttf", 28)
    lives_text = lives_font.render(f"Lives: {lives}", True, "white")
    screen.blit(lives_text, (WIDTH // 2 + 160, 60))  # bên phải Score




def check_ghost_collision(ghost1, ghost2):
    ghost1_grid_x = int((ghost1.x + 22) // (WIDTH // 30))
    ghost1_grid_y = int((ghost1.y + 22) // ((HEIGHT - 50) // 32))
    ghost2_grid_x = int((ghost2.x + 22) // (WIDTH // 30))
    ghost2_grid_y = int((ghost2.y + 22) // ((HEIGHT - 50) // 32))

    return (
        (abs(ghost1_grid_x - ghost2_grid_x) < 1)
        and (abs(ghost1_grid_y - ghost2_grid_y) < 1)
        and level[ghost1_grid_y][ghost1_grid_x] in [1, 2, 9]
    )

def save_longest_time(duration):
    try:
        with open("longest_time.txt", "r") as file:
            longest = float(file.read())
    except:
        longest = 0

    if duration > longest:
        with open("longest_time.txt", "w") as file:
            file.write(str(duration))

def load_longest_time():
    try:
        with open("longest_time.txt", "r") as file:
            return float(file.read())
    except:
        return 0


def save_highest_score(score):
    with open("highest_score.txt", "w") as f:
        f.write(str(score))

def load_highest_score():
    try:
        with open("highest_score.txt", "r") as f:
            return int(f.read())
    except:
        return 0
def main_menu():
    menu_font = pygame.font.Font("freesansbold.ttf", 64)
    option_font = pygame.font.Font("freesansbold.ttf", 36)

    selecting = True
    while selecting:
        screen.fill("darkblue")

        title_text = menu_font.render("PACMAN GAME", True, "yellow")
        start_text = option_font.render("Press S to Start", True, "white")
        quit_text = option_font.render("Press Q to Quit", True, "white")
        longest_time = load_longest_time()
        longest_text = option_font.render(f"Longest Time: {round(longest_time,2)}s", True, "white")
        highes_score=load_highest_score()
        highest_text = option_font.render(f"Highest Score: {highes_score}", True, "white")
        screen.blit(title_text, (WIDTH // 2 - 200, HEIGHT // 2 - 200))
        screen.blit(start_text, (WIDTH // 2 - 150, HEIGHT // 2))
        screen.blit(quit_text, (WIDTH // 2 - 150, HEIGHT // 2 + 60))
        screen.blit(longest_text, (WIDTH // 2 - 200, HEIGHT // 2 + 140))
        screen.blit(highest_text, (WIDTH // 2 - 200, HEIGHT // 2 + 180))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    selecting = False  # Start game
                    run_game()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    exit()

def pause_screen(lives):
    paused = True
    pause_font = pygame.font.Font("freesansbold.ttf", 40)
    text = pause_font.render(f"Lost a life! Lives left: {lives}", True, "white")
    subtext = pause_font.render("Press SPACE to continue", True, "yellow")

    while paused:
        screen.fill("black")
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 60))
        screen.blit(subtext, (WIDTH // 2 - subtext.get_width() // 2, HEIGHT // 2 + 10))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = False


def game_over_menu(score, play_time):
    menu_font = pygame.font.Font("freesansbold.ttf", 64)
    option_font = pygame.font.Font("freesansbold.ttf", 36)

    selecting = True
    while selecting:
        screen.fill("darkblue")

      
        # Hiển thị chữ GAME OVER
        game_over_text = menu_font.render("GAME OVER", True, "red")
        screen.blit(game_over_text, (WIDTH // 2 - 200, HEIGHT // 2 - 250))

        # Hiển thị Score và Time
        score_text = option_font.render(f"Score: {score}", True, "yellow")
        time_text = option_font.render(f"Time: {play_time:.2f} seconds", True, "yellow")
        screen.blit(score_text, (WIDTH // 2 - 100, HEIGHT // 2 - 180))
        screen.blit(time_text, (WIDTH // 2 - 100, HEIGHT // 2 - 130))

        # Hiển thị lựa chọn
        play_again_text = option_font.render("Press R to Play Again", True, "white")
        menu_text = option_font.render("Press M to Main Menu", True, "white")
        quit_text = option_font.render("Press Q to Quit", True, "white")

        screen.blit(play_again_text, (WIDTH // 2 - 180, HEIGHT // 2 - 50))
        screen.blit(menu_text, (WIDTH // 2 - 180, HEIGHT // 2 + 10))
        screen.blit(quit_text, (WIDTH // 2 - 140, HEIGHT // 2 + 70))


        display_statistics()

        pygame.display.flip()

        # Bắt sự kiện
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Đảm bảo nhạc đã dừng trước khi chơi lại
                    try:
                        pygame.mixer.music.stop()
                    except:
                        pass
                    return True  # Chơi lại
                elif event.key == pygame.K_q:
                    return False  # Thoát game
                elif event.key == pygame.K_m:
                    # Đảm bảo nhạc đã dừng trước khi quay lại menu
                    try:
                        pygame.mixer.music.stop()
                    except:
                        pass
                    main_menu()

def win_screen():
    selecting = True
    while selecting:
        screen.fill("black")
        win_text = pygame.font.Font(None, 80).render("YOU WIN!", True, "yellow")
        restart = pygame.font.Font(None, 50).render("Press R to Restart", True, "white")
        quit_game = pygame.font.Font(None, 50).render("Press Q to Quit", True, "white")
        screen.blit(win_text, (WIDTH//2 - 150, HEIGHT//2 - 100))
        screen.blit(restart, (WIDTH//2 - 180, HEIGHT//2 + 20))
        screen.blit(quit_game, (WIDTH//2 - 150, HEIGHT//2 + 80))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    run_game()
                    selecting = False
                if event.key == pygame.K_q:
                    pygame.quit()
                    exit()

# Initialize game objects
# player = Player()
# ghosts = [Pink_ghost(), Blue_ghost(), Orange_ghost(), RedGhost()]

# Main game loop
def run_game():
    global counter, count, flicker,player, ghosts, start_time, run, game_over
    lives = 2

    # Reset variables
    counter = 0
    count = 0
    flicker = False
    player = Player()
    ghosts = [Pink_ghost(), Blue_ghost(), Orange_ghost(), RedGhost()]
    start_time = time.time()
    run = True
    game_over = False
    create_dots()
    score = 0
    highest_score = load_highest_score()
     # Phát nhạc nền
    try:
        pygame.mixer.music.play(-1)  # -1 để lặp vô hạn
    except:
        pass


    while run:
        timer.tick(fps)

        if counter < 19:
            counter += 1
            if counter > 3:
                flicker = False
        else:
            counter = 0
            flicker = True

        screen.fill("darkblue")
        draw_board()
        
        # Player
        player.move()
        player.draw_player()

       


        # Dots
        for dot in dots:
            dot.draw()
            if not dot.eaten and player.rect.colliderect(dot.rect):
                dot.eaten = True
                score += 1

        # Ghosts
        for ghost in ghosts:
            ghost.draw_ghost()

        if count >= 0:
            ghosts[0].move()
        if count >= 50:
            ghosts[1].move()
        if count >= 100:
            ghosts[2].move()
        if count >= 150:
            ghosts[3].move()
        count += 1

        # Time display
        duration = calculate_game_duration(start_time)
        display_duration(duration)
        # Hiển thị điểm
        display_score(score)

        display_lives(lives)
        # Check collision with ghosts
        for ghost in ghosts:
            if check_collision(player, ghost):
                lives -= 1  # Mất 1 mạng
                if lives > -1:
                    player.__init__()
                    pygame.time.delay(500)  # Delay nhẹ để tránh double hit
                    pause_screen(lives)  # Hiện pause screen trước khi chơi tiếp
                else:
                    game_over = True



        # Check ghost-to-ghost teleport
        for i in range(len(ghosts)):
            for j in range(i + 1, len(ghosts)):
                if check_ghost_collision(ghosts[i], ghosts[j]):
                    ghosts[j].teleport()

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    player.direction = "up"
                    move_sound.play()
                elif event.key == pygame.K_s:
                    player.direction = "down"
                    move_sound.play()
                elif event.key == pygame.K_a:
                    player.direction = "left"
                    move_sound.play()
                elif event.key == pygame.K_d:
                    player.direction = "right"
                    move_sound.play()
        

        if game_over:
             # Dừng nhạc khi game over
            try:
                pygame.mixer.music.stop()
            except:
                pass
            display_game_over()
            save_longest_time(duration)
            if score > highest_score:
                save_highest_score(score)

            if game_over_menu(score, duration):
                run_game()  # Restart the game cleanly
            run = False

             # Check win
        if all(dot.eaten for dot in dots):
            pygame.mixer.music.stop()
            if score > highest_score:
                save_highest_score(score)
            save_longest_time(duration)
            win_screen()
            running = False

        pygame.display.flip()
      # Đảm bảo dừng nhạc khi kết thúc game
    try:
        pygame.mixer.music.stop()
    except:
        pass

if __name__ == "__main__":
    main_menu()
    run_game()
    pygame.quit()
