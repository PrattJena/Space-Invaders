import pygame
import os
import time
import random
import sys

pygame.init()
pygame.font.init()


# Sets width and hieght of game window
WIDTH, HEIGHT = 750, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")


# Load Images
RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))


# Player
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))


# Lasers
BLUE_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
RED_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))


# Background
# Scales the image to fill the background
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))


# Laser class
class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self,vel):
        self.y += vel # vel will be negative if it does up and positive if it goes downward

    def off_screen(self, height):
        return not(self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


# This will be an abstract class from which other player class will inherit
class Ship:
    COOLDOWN = 30 # Half a second since FPS is 60

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None # Ship Image
        self.laser_img = None # Laser Image
        self.lasers = []
        self.cooldown_counter = 0 # We give a cooldown so that we cant spam lasers.

    def cooldown(self):
        if self.cooldown_counter >= self.COOLDOWN:
            self.cooldown_counter = 0
        elif self.cooldown_counter > 0:
            self.cooldown_counter += 1

    def shoot(self):
        if self.cooldown_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cooldown_counter = 1

    def draw(self, window):
        # Draws a given ship_img at the given x and y
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown() # Cooldown for shooting lasers
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT): # If laser is of the screen we remove it
                self.lasers.remove(laser)
            elif laser.collision(obj): # If laser collides with the object which in this case will be player then it will reduce 10 health
                obj.health -= 10
                self.lasers.remove(laser)

    # Returns width and height of the player
    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


# Player
class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health=100)
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER

        # Mask returns the pixels of passed value image which can be used in pixel perfect collision
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (255,0,0), (self.x, self.y + self.ship_img.get_height()+10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0,255,0), (self.x, self.y + self.ship_img.get_height()+10, int(self.ship_img.get_width() * (self.health/self.max_health)), 10))


    def move_lasers(self, vel, objs): # Overriding parent class. Objs is a list of enemy class
        self.cooldown() # Cooldown for shooting lasers
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT): # If laser is of the screen we remove it
                self.lasers.remove(laser)
            else: # If laser collides with the enemy it deletes them from list
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        self.lasers.remove(laser)


# Enemy
class Enemy(Ship):
    # Creating a map to obtain respective ship and lasers to respective colours
    COLOR_MAP = {
                "red" : (RED_SPACE_SHIP, RED_LASER),
                "blue" : (BLUE_SPACE_SHIP, BLUE_LASER),
                "green" : (GREEN_SPACE_SHIP, GREEN_LASER)
                }
    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health=100)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def shoot(self):
        if self.cooldown_counter == 0:
            laser = Laser(self.x-25, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cooldown_counter = 1

    def move(self, vel): # Moves ship downward
        self.y += vel

def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x # Offset tells the distance between the top left corners of two objects
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None # Overlap tells us if they collide where the pixels are actually present

# Draws event on screen and other functionalities
def main():
    # run = True
    FPS = 60
    level = 0
    lives = 10
    player_vel = 4
    laser_vel = 5
    # For this we have to initialise font using pygame at the beginning of the game
    main_font = pygame.font.SysFont("comicsans", 40)
    lost_font = pygame.font.SysFont("comicsans", 60)

    enemies = []
    wave_length = 3
    enemy_vel = 1

    lost = False # Tells if the player lost the game or not
    lost_count = 0
    # Intialize Ship class
    player = Player(325,630)

    clock = pygame.time.Clock() # Sets a limit on FPS

    # It will draw everything thats required by us for the game.
    # We keep it inside a function so that its easy for us
    # And we dont have to pass the parameters every time.
    # It will run only when main will run
    def redraw_window():

        # In pygame the 0,0 coordinate is situated at top left corner
        # Let's suppose we have a square image of side 10
        # Instead of 0,0 we pass 25,25 in .blit
        # Then the image's top left corner will be at 25,25
        WIN.blit(BG,(0,0))

        # Draw text
        lives_label = main_font.render(f"Lives: {lives}", 1, (255,255,255))
        level_label = main_font.render(f"Level: {level}", 1, (255,255,255))

        WIN.blit(lives_label, (10, 10)) # Sets an offset of 10 pixels
        WIN.blit(level_label, (WIDTH - lives_label.get_width() - 10, 10)) # Gets the width of lives_label

        for enemy in enemies: # Draws each enemy to the screen
            enemy.draw(WIN)

        player.draw(WIN)

        if lost:
            lost_label = lost_font.render("You Lost!!", 1, (255,255,255))
            WIN.blit(lost_label, (round(WIDTH/2 - lost_label.get_width()/2), round(HEIGHT/2 - lost_label.get_height()/2))) # Width/2 puts the top left of the text in center.
                                                                                # Since it puts the top left at the center we move it by half its width using get_width()/2
        pygame.display.update() # Allows to update the portion of screen
                                # It draws whatever image is passed to it.


    while True:
        clock.tick(FPS) # Since we set this it will be the same for every screen
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1
        if lost:
            if lost_count > FPS * 3:
                pygame.quit()
                sys.exit(0)
            else:
                continue

        if len(enemies) == 0:
            level += 1 # If enemies are 0 in list level up
            wave_length +=5 # When getting to a new level increase the amount of enemies
            for i in range(wave_length):
                # Taking x, y, and passing the colour from list to the the color in init method in enemy class to ge the respective ship and laser
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1000, -100), random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # run = False
                pygame.quit()
                sys.exit(0) # Closes the game when we hit the cross button
        # Could have been also done inside for loop but it can only move one direction at a time
        # Hence it cant move diagonally

        # Checks every 60 second
        keys = pygame.key.get_pressed() # Returns a dictionary of all the keys and tells if we are pressing it or not
        if keys[pygame.K_LEFT] and player.x - player_vel > 0: # left
            player.x -= player_vel

        # Since we are observing the top left corner hence when we shift our player it will not let the top left corner go off the screen
        # So for looking at the top right of the player we add 50.
        if keys[pygame.K_RIGHT] and player.x + player_vel + player.get_width()  < WIDTH: # right
            player.x += player_vel

        # We subtract the velocity in w because our x in top left corner
        # So if we have to go up we gotta decrease y and vice versa
        if keys[pygame.K_UP] and player.y - player_vel > 0: # up
            player.y -= player_vel

        # We do the same thing in right but instead of top right we are now looking at bottom left
        if keys[pygame.K_DOWN] and player.y + player_vel + player.get_height() + 13 < HEIGHT: # down
            player.y += player_vel

        if keys[pygame.K_SPACE]:
            player.shoot()

        for enemy in enemies[:]: # Makes a copy of list enemies as it creates a reference. See sdeep copying vs shallow copying for more
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            if random.randrange(0, 3*FPS) == 1: # Gives us probability that an enemy will shoot every 3 seconds
                enemy.shoot()

            if collide(enemy, player):
                player.health -=10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT: # Checking if enemy are off the screen
                lives -= 1
                enemies.remove(enemy) # If they are off the window remove them
                                  # This will also help us run the above if loop as the len(list) will hit 0.

        player.move_lasers(-laser_vel, enemies)


main()
