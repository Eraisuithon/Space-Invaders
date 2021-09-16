import pygame
from random import randint, choice
import json
import os
from bisect import bisect
from sys import exit

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
        self.font = self.window.base_font(32)
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
        self.collision_sound.set_volume(.7)

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
        self.base_font = lambda x: pygame.font.Font('freesansbold.ttf', x)

        self.name = name
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.mixer.music.load('background.wav')
        pygame.mixer.music.play(-1)


    def __repr__(self):
        return f"Window({self.width=},{self.height=},{self.name=},{self.icon=})"

    def create_file_if_it_does_not_exist(self):
        if not os.path.exists('Scores.txt'):
            with open('Scores.txt', 'w') as file:
                json.dump([], file)
                return
        if os.stat('Scores.txt').st_size == 0:
            with open('Scores.txt', 'w') as file:
                json.dump([], file)

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

        self.window.create_file_if_it_does_not_exist()

        self.player = Player(size=64, image='player.png', change=4, window=self.window)
        self.player.player_start()
        self.enemies = []
        self.bullets = []
        self.score = Score(window=self.window)
        self.bullet_countdown = 250
        self.clock = pygame.time.Clock()
        self.freeze = False

    def start_over(self):
        self.__init__()
        self.run()

    def add_name(self):
        user_text = ''
        running = True
        while running:
            self.window.draw_background()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        if user_text:
                            self.save_to_file(user_text)
                            return
                    else:
                        user_text += event.unicode

            text_surface = self.window.base_font(32).render(f"Name: {user_text}", True, (255, 255, 255))
            self.window.screen.blit(text_surface, (0, 0))

            pygame.display.update()

    def display_end(self):
        self.window.draw_background()

        font_game_over = self.window.base_font(64)
        game_over_text = font_game_over.render("GAME OVER", True, (255, 255, 255))
        self.window.screen.blit(game_over_text, (200, 250))

        font_quit_retry_score = self.window.base_font(16)
        quit_text = font_quit_retry_score.render("To Quit Press Q", True, (255, 255, 255))
        self.window.screen.blit(quit_text, (475, 325))

        retry_text = font_quit_retry_score.render("To Play Again Press R", True, (255, 255, 255))
        self.window.screen.blit(retry_text, (200, 325))

        score_text = font_quit_retry_score.render("To Add Your Score Press S", True, (255, 255, 255))
        self.window.screen.blit(score_text, (200, 350))

        pygame.display.update()

    def save_to_file(self, name):
        with open('Scores.txt') as file:
            data = json.load(file)
        if data:
            data.reverse()
            second_column = [data[i][1] for i in range(len(data))]
            index = bisect(second_column, self.score.score)
            data.insert(index, (name, self.score.score))
            data.reverse()
            if len(data) > 10:
                data.pop()
        else:
            data.append((name, self.score.score))
        with open('Scores.txt', 'w') as file:
            json.dump(data, file)

    def display_scores(self):
        with open('Scores.txt') as file:
            data = json.load(file)

        text_font = self.window.base_font(32)
        for i, name_score in enumerate(data):
            text = text_font.render(f"{name_score[0]} : {name_score[1]}", True, (255, 255, 255))
            self.window.screen.blit(text, (0, i * 50))

        pygame.display.update()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_r:
                        return
                    if event.key == pygame.K_q:
                        pygame.quit()
                        exit()


    def end(self):
        self.display_end()

        score = False
        retry = False
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        pygame.quit()
                        exit()
                    if event.key == pygame.K_r:
                        running = False
                        retry = True
                    if event.key == pygame.K_s:
                        running = False
                        score = True
        if score:
            self.add_name()
            self.display_scores()
            self.start_over()
        elif retry:
            self.start_over()

    def run(self):
        self.window.set_up()

        for i in range(6):
            enemy = Player(size=64, image='Enemy.png', change=3, change_y=40, window=self.window)
            enemy.random_start()
            self.enemies.append(enemy)

        start_time = pygame.time.get_ticks()
        running = True

        easteregg = ''

        # I subtract the cooldown so the first time can fire normally
        bullets_counter = pygame.time.get_ticks()-self.bullet_countdown
        while running:
            curr_time = pygame.time.get_ticks() - start_time
            if curr_time ** (1 / 2) % 50 == 0:
                enemy = Player(size=64, image='Enemy.png', change=3, change_y=40, window=self.window)
                if self.freeze:
                    enemy.change = 0
                enemy.random_start()
                self.enemies.append(enemy)

            self.window.draw_background()
            self.score.show_score()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.end()
                        running = False
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player.move[0] = -self.player.change
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player.move[0] = self.player.change

                    if event.key == pygame.K_SPACE and curr_time - bullets_counter > self.bullet_countdown:
                        bullets_counter = pygame.time.get_ticks()
                        self.bullets.append(Bullet(window=self.window))
                        self.bullets[-1].x_coordinate = self.player.x_coordinate + self.player.size // 2 - \
                                                        self.bullets[-1].size // 2
                        self.bullets[-1].y_coordinate = self.player.y_coordinate - self.bullets[-1].size // 3

                    if event.key == pygame.K_BACKSPACE:
                        easteregg = easteregg[:-1]
                    elif event.key != pygame.K_RETURN:
                        easteregg += event.unicode
                    if event.key == pygame.K_RETURN and easteregg.lower()=='big pie':
                        self.score.score = 314159265358979323846264338327950288
                        self.end()
                        running = False
                    if event.key == pygame.K_RETURN and easteregg.lower()  == 'freeze':
                        self.freeze = True
                        for enemy in self.enemies:
                            enemy.change = 0
                    if event.key == pygame.K_RETURN:
                        easteregg = ''



                if event.type == pygame.KEYUP:
                    if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and self.player.move[0] < 0:
                        self.player.move[0] = 0
                    if (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and self.player.move[0] > 0:
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
                for _ in range(score):
                    enemy = Player(size=64, image='Enemy.png', change=3 + (self.score.score * 0.01), change_y=40,
                                   window=self.window)
                    if self.freeze:
                        enemy.change = 0
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

            if running:
                pygame.display.update()
            self.clock.tick(120)
