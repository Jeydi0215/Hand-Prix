import os
import sys
import cv2
import pygame as pg
from cvzone.HandTrackingModule import HandDetector
import random

class Character:
    def __init__(self, image_path, initial_rect, size=(190, 340)):
        self.image = pg.image.load(image_path).convert_alpha()
        self.image = pg.transform.scale(self.image, size)
        self.rect = self.image.get_rect(center=initial_rect)

    def update(self, surface, hand_pos):
        if hand_pos:
            self.rect.center = hand_pos
        surface.blit(self.image, self.rect)

class Background(pg.sprite.Sprite):
    def __init__(self, image_file, location, speed=(0, 4), rotation_angle=0):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.image.load(image_file).convert_alpha()
        self.image = pg.transform.rotate(self.image, rotation_angle)
        self.image = pg.transform.scale(self.image, (1920, 1080))
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location
        self.speed = speed
        self.rect2 = self.image.get_rect()
        self.rect2.top = self.rect.bottom

    def update(self):
        self.rect.top += self.speed[1]
        self.rect2.top += self.speed[1]

        if self.rect.top >= 600:
            self.rect.top = self.rect2.bottom
        if self.rect2.top >= 600:
            self.rect2.top = self.rect.top

        return self.image

class Obstacle:
    def __init__(self, image_path, initial_position, size=(150, 150), speed=(0, 3)):
        self.image = pg.image.load(image_path).convert_alpha()
        self.image = pg.transform.scale(self.image, size)
        self.rect = self.image.get_rect(topleft=initial_position)
        self.speed = speed

    def update(self, surface, paused=False):
        if not paused:
            self.rect.top += self.speed[1]
        if self.rect.top > 1080:
            self.rect.top = -self.rect.height
            self.rect.left = random.randint(0, 1920 - self.rect.width)
        surface.blit(self.image, self.rect)

def game_event_loop():
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            sys.exit()

def main(surface, player, hand_pos, background, obstacles, game_state):
    game_event_loop()
    surface.fill((0, 0, 0))

    surface.blit(background.image, background.rect)
    surface.blit(background.image, background.rect2)

    if game_state["paused"]:
        font = pg.font.Font(None, 74)
        pause_text = font.render("Game Over", True, (255, 0, 0))
        surface.blit(pause_text, (840, 500))
        return

    player.update(surface, hand_pos)

    for obstacle in obstacles:
        obstacle.update(surface)
        if player.rect.colliderect(obstacle.rect):
            print("Collision detected! Pausing the game.")
            game_state["paused"] = True

if __name__ == "__main__":
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pg.init()

    screen = pg.display.set_mode((1920, 1080))
    pg.display.set_caption("Hand Prix")
    MyClock = pg.time.Clock()

    background = Background("./Assets/road.png", (0, 0), speed=(0, 1), rotation_angle=90)

    image_path = "./Assets/player.png"
    MyPlayer = Character(image_path, (960, 950))  # Start near the bottom of the screen

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Webcam could not be opened.")
        sys.exit()

    detector = HandDetector(maxHands=1)

    obstacle_image = "./Assets/bato.png"
    obstacles = []

    for _ in range(5):
        pos = (random.randint(0, 1920 - 150), random.randint(-500, -100))
        while MyPlayer.rect.colliderect(pg.Rect(pos, (150, 150))):  
            pos = (random.randint(0, 1920 - 150), random.randint(-500, -100))
        obstacles.append(Obstacle(obstacle_image, pos))

    game_state = {"paused": False}  

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to capture image from webcam")
            continue

        frame = cv2.flip(frame, 1)
        hands, img = detector.findHands(frame)

        hand_pos = None
        if hands:
            hand_center = hands[0]['center']
            hand_pos = (hand_center[0], hand_center[1])

        game_event_loop()
        main(screen, MyPlayer, hand_pos, background, obstacles, game_state)

        pg.display.update()
        MyClock.tick(60)

    cap.release()
    pg.quit()
