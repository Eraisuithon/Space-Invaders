import pygame
from random import randint, choice
import math

'''
    wav files are downloaded from: https://github.com/attreyabhatt/Space-Invaders-Pygame
'''


class Entity:
    def __init__(self, size, position=None, change=5.0, window=None):
        if position is not None:
            self.x_coordinate = position[0]
            self.y_coordinate = position[1]

        self.size = size
        self.window = window
        self.change = change

    def distance(self, obj):
        x = obj.x_coordinate + obj.size // 2
        y = obj.y_coordinate + obj.size // 2
        self_x = self.x_coordinate + self.size // 2
        self_y = self.y_coordinate + self.size // 2
        return max([abs(x - self_x), abs(y - self_y)])

    def did_collide(self, obj):
        if self.distance(obj) < (obj.size + self.size) // 2:
            return True
        return False

    def move_up(self, change=None):
        if change is None:
            change = self.change
        self.y_coordinate -= change

    def move_down(self, change=None):
        if change is None:
            change = self.change
        self.y_coordinate += change

    def move_left(self, change=None):
        if change is None:
            change = self.change
        self.x_coordinate -= change

    def move_right(self, change=None):
        if change is None:
            change = self.change
        self.x_coordinate += change


class Score(Entity):
    def __init__(self, window=None):
        super().__init__(size=None, change=0, window=window)

        # download any font from dafont.com
        self.font = pygame.font.Font('freesansbold.ttf', 32)
        self.x_coordinate = 10
        self.y_coordinate = 10
        self.score = 0

    def show_score(self):
        score = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.window.screen.blit(score, (self.x_coordinate, self.y_coordinate))


class Bullet(Entity):
    def __init__(self, size=32, position=None, image='bullet.png', change=5, window=None):
        super().__init__(size, position, change, window)

        self.image = pygame.image.load(image)
        self.bullet_sound = pygame.mixer.Sound('laser.wav')
        self.bullet_sound.play()
        self.collision_sound = pygame.mixer.Sound('explosion.wav')

    def play_collision_sound(self):
        self.collision_sound.play()

    def out_of_bounds(self):
        if self.y_coordinate + 32 < 0:
            return True


class Player(Entity):
    def __init__(self, size=64, position=None, image=None, change=5.0, change_y=50, window=None):
        super().__init__(size, position, change, window)

        if image is not None:
            self.image = pygame.image.load(image)

        self.change_y = change_y
        self.direction = choice(['Left', 'Right'])
        self.move = [0, 0]

    def __repr__(self):
        return f"Window({self.size=},({self.x_coordinate},{self.y_coordinate}),{self.change=},{self.change_y=}) "

    def make_move(self):
        self.x_coordinate += self.move[0]
        self.y_coordinate += self.move[1]
        self.window.within_boundary(self)

    def step(self):
        direction = {'Right': 1, 'Left': -1}
        self.x_coordinate += direction[self.direction] * self.change
        if not self.window.within_boundary(self):
            self.change_direction()
            self.y_coordinate += self.change_y

    def change_direction(self):
        self.direction = 'Left' if self.direction == 'Right' else 'Right'

    def player_start(self):
        self.x_coordinate = self.window.width // 2 - self.size // 2
        self.y_coordinate = self.window.height * 4 // 5

    def random_start(self):
        self.x_coordinate = randint(0, self.window.width - self.size)
        self.y_coordinate = randint(self.window.height // 50, self.window.height // 5)


class Window:
    def __init__(self, width, height, image=None, name=None, icon=None):
        if image is not None:
            self.background = pygame.image.load(image)
        if icon is not None:
            self.icon = pygame.image.load(icon)

        self.name = name
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.mixer.music.load('background.wav')
        pygame.mixer.music.play(-1)

    def __repr__(self):
        return f"Window({self.width=},{self.height=},{self.name=},{self.icon=})"

    def set_up(self):
        pygame.display.set_caption(self.name)
        pygame.display.set_icon(self.icon)

    def draw_object(self, obj):
        self.screen.blit(obj.image, (obj.x_coordinate, obj.y_coordinate))

    def draw_background(self):
        self.screen.blit(self.background, (0, 0))

    def within_boundary(self, obj):
        is_within_boundary = True
        if obj.x_coordinate > self.width - obj.size:
            is_within_boundary = False
            obj.x_coordinate = self.width - obj.size
        elif obj.x_coordinate < 0:
            is_within_boundary = False
            obj.x_coordinate = 0

        if obj.y_coordinate > self.height - obj.size:
            is_within_boundary = False
            obj.y_coordinate = self.height - obj.size
        elif obj.y_coordinate < 0:
            is_within_boundary = False
            obj.y_coordinate = 0

        return is_within_boundary


class Game:
    def __init__(self):
        pygame.init()
        self.window = Window(width=800, height=600, image='background.png', name='Space Invaders', icon='ufo.png')

        self.player = Player(size=64, image='player.png', change=4, window=self.window)
        self.player.player_start()
        self.enemies = []
        self.bullets = []
        self.score = Score(window=self.window)

    def display_end(self):
        font_game_over = pygame.font.Font('freesansbold.ttf', 64)
        game_over_text = font_game_over.render("GAME OVER", True, (255, 255, 255))
        self.window.screen.blit(game_over_text, (200, 250))

        font_quit_retry = pygame.font.Font('freesansbold.ttf', 16)
        quit_text = font_quit_retry.render("To Quit Press Q", True, (255, 255, 255))
        self.window.screen.blit(quit_text, (475, 325))

        retry_text = font_quit_retry.render("To Play Again Press R", True, (255, 255, 255))
        self.window.screen.blit(retry_text, (200, 325))

        pygame.display.update()

    def end(self):
        self.display_end()

        retry = False
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    if event.key == pygame.K_r:
                        running = False
                        retry = True
        if retry:
            self.__init__()
            self.run()


    def run(self):
        self.window.set_up()

        for i in range(6):
            enemy = Player(size=64, image='Enemy.png', change=3, change_y=40, window=self.window)
            enemy.random_start()
            self.enemies.append(enemy)

        iterations = 0
        running = True
        while running:
            iterations += 1
            if iterations**(1/2) % 10 == 0:
                enemy = Player(size=64, image='Enemy.png', change=3, change_y=40, window=self.window)
                enemy.random_start()
                self.enemies.append(enemy)

            self.window.draw_background()
            self.score.show_score()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.end()
                        running = False
                    if event.key == pygame.K_LEFT:
                        self.player.move[0] = -self.player.change
                    if event.key == pygame.K_RIGHT:
                        self.player.move[0] = self.player.change
                    if event.key == pygame.K_SPACE:
                        self.bullets.append(Bullet(window=self.window))
                        self.bullets[-1].x_coordinate = self.player.x_coordinate + self.player.size // 2 - \
                                                        self.bullets[-1].size // 2
                        self.bullets[-1].y_coordinate = self.player.y_coordinate - self.bullets[-1].size // 3

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT and self.player.move[0] < 0:
                        self.player.move[0] = 0
                    if event.key == pygame.K_RIGHT and self.player.move[0] > 0:
                        self.player.move[0] = 0

            self.bullets[:] = [bullet for bullet in self.bullets if not bullet.out_of_bounds()]
            index = []
            for i, bullet in enumerate(self.bullets):
                bullet.move_up()
                self.window.draw_object(bullet)

                previous_enemies = len(self.enemies)
                self.enemies[:] = [enemy for enemy in self.enemies if not bullet.did_collide(enemy)]
                score = previous_enemies - len(self.enemies)
                self.score.score += score
                for i in range(score):
                    enemy = Player(size=64, image='Enemy.png', change=3 + (self.score.score * 0.01), change_y=40,
                                   window=self.window)
                    enemy.random_start()
                    self.enemies.append(enemy)

                if score > 0:
                    bullet.play_collision_sound()
                    index.append(i)

            self.bullets[:] = [bullet for i, bullet in enumerate(self.bullets) if i not in index]

            self.player.make_move()
            self.window.draw_object(self.player)

            for enemy in self.enemies:
                enemy.step()
                self.window.draw_object(enemy)

            if any(self.player.did_collide(enemy) for enemy in self.enemies):
                self.end()
                running = False

            pygame.display.update()
