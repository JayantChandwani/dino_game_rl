from sre_constants import JUMP
import pygame
from enum import Enum
import os
import random

# Constants
FPS = 24 
GROUND_HEIGHT = 425

class Controller:
    def __init__(self, dino):
        self.dino = dino
        self.key_states = {
            'jump': False,
            'duck': False
        }
    
    def reset(self, dino):
        """Reset controller key states"""
        self.dino = dino
        self.key_states = {'jump': False, 'duck': False}
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                self.key_states['jump'] = True
            elif event.key == pygame.K_DOWN:
                self.key_states['duck'] = True

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                self.key_states['duck'] = False
    
    def update(self):
        if self.key_states['jump']:
            self.dino.jump()
            self.key_states['jump'] = False 

        if self.key_states['duck']:
            self.dino.duck()
        else:
            self.dino.stand()

class Ground:
    def __init__(self, y_position=GROUND_HEIGHT, speed=300):
        self.image = pygame.image.load(os.path.join("assets", "other", "ground.png"))
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.y = y_position
        self.speed = speed
        
        self.x1 = 0
        self.x2 = self.width
        
    def update(self, dt, game_speed):
        move_distance = self.speed * game_speed * dt
        self.x1 -= move_distance
        self.x2 -= move_distance
        
        if self.x1 + self.width < 0:
            self.x1 = self.x2 + self.width
        if self.x2 + self.width < 0:
            self.x2 = self.x1 + self.width
    
    def draw(self, screen):
        screen.blit(self.image, (self.x1, self.y))
        screen.blit(self.image, (self.x2, self.y))
        
    def reset(self):
        self.x1 = 0
        self.x2 = self.width

class Dino(pygame.sprite.Sprite):
    # State enum at class level
    class State(Enum):
        RUNNING = 0
        DUCKING = 1
        JUMPING = 2
        DEAD = 3
        START = 4
    
    # Physics constants
    JUMP_VELOCITY = -450
    GRAVITY = JUMP_VELOCITY ** 2 / 200 
    GROUND_Y = GROUND_HEIGHT + 10
    
    def __init__(self):
        super().__init__()
        self.images = {
            self.State.RUNNING: [
                pygame.image.load(os.path.join("assets", "dino", "dino_run_1.png")),
                pygame.image.load(os.path.join("assets", "dino", "dino_run_2.png"))
            ],
            self.State.DUCKING: [
                pygame.image.load(os.path.join("assets", "dino", "dino_duck_1.png")),
                pygame.image.load(os.path.join("assets", "dino", "dino_duck_2.png"))
            ],
            self.State.JUMPING: pygame.image.load(os.path.join("assets", "dino", "dino_jump.png")),
            self.State.DEAD: pygame.image.load(os.path.join("assets", "dino", "dino_dead.png")),
            self.State.START: pygame.image.load(os.path.join("assets", "dino", "dino_start.png")),
        }
        
        # Scale down all images
        scale_factor = 0.65  
        self.width = int(self.images[self.State.RUNNING][0].get_width() * scale_factor)
        self.height = int(self.images[self.State.RUNNING][0].get_height() * scale_factor)
        for state, img in self.images.items():
            if isinstance(img, list):  
                for i in range(len(img)):
                    width = int(img[i].get_width() * scale_factor)
                    height = int(img[i].get_height() * scale_factor)
                    self.images[state][i] = pygame.transform.scale(img[i], (width, height))
            else:  
                self.images[state] = pygame.transform.scale(img, (self.width, self.height))
                
        self.GROUND_Y -= self.height 
    
        self.state = self.State.START
        self.x = 60
        self.y = self.GROUND_Y 
        self.y_velocity = 0
        
        # Animation tracking
        self.animation_index = 0
        self.animation_time = 0
        self.animation_speed = 0.1  # seconds per frame
        
        # For pygame.sprite.Sprite
        self.image = self.images[self.State.START]
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
    
    def update(self, dt):
        """Update dino physics and animation"""
        
        # Don't update if dead
        if self.state == self.State.DEAD:
            return
        
        # Apply gravity
        if self.state == self.State.JUMPING:
            self.y_velocity += self.GRAVITY * dt
            self.y += self.y_velocity * dt
            
            # Land on ground
            if self.y >= self.GROUND_Y:
                self.y = self.GROUND_Y
                self.y_velocity = 0
                self.state = self.State.RUNNING

        # Update animation for states with multiple frames
        if self.state in [self.State.RUNNING, self.State.DUCKING]:
            self.animation_time += dt
            if self.animation_time >= self.animation_speed:
                self.animation_time = 0
                self.animation_index = (self.animation_index + 1) % 2
                self.image = self.images[self.state][self.animation_index]
        else:
            self.image = self.images[self.state]
        
        # Update rect position and size
        self.rect.x = self.x
        self.rect.y = int(self.y)
        
        # Update rect size to match current image (important for ducking)
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()
        
        # When ducking, align bottom of rect to ground
        if self.state == self.State.DUCKING:
            self.rect.bottom = int(self.GROUND_Y + self.height)  # Align to ground level
    
    def jump(self):
        """Make the dino jump"""
        if self.state in [self.State.RUNNING, self.State.START]:  # Allow jump from START
            self.state = self.State.JUMPING
            self.y_velocity = self.JUMP_VELOCITY
    
    def duck(self):
        """Make the dino duck"""
        if self.state in [self.State.RUNNING, self.State.START]:  # Allow duck from START
            self.state = self.State.DUCKING

    def stand(self):
        """Stop ducking"""
        if self.state == self.State.DUCKING:
            self.state = self.State.RUNNING
        elif self.state == self.State.START:  
            self.state = self.State.RUNNING
    
    def die(self):
        """Set dino to dead state"""
        if self.state != self.State.DEAD:
            self.state = self.State.DEAD
            self.y_velocity = 0
            self.image = self.images[self.State.DEAD]  

    def is_alive(self):
        """Check if dino is alive"""
        return self.state != self.State.DEAD
    
    def draw(self, screen):
        """Draw the dino"""
        screen.blit(self.image, self.rect)

class Cactus(pygame.sprite.Sprite):
    SCALING_FACTOR = 0.65
    
    def __init__(self, x, y):
        super().__init__()
        self.images = [
            pygame.image.load(os.path.join("assets", "cactus", "small_cactus_1.png")),
            pygame.image.load(os.path.join("assets", "cactus", "small_cactus_2.png")),
            pygame.image.load(os.path.join("assets", "cactus", "small_cactus_3.png")),
            pygame.image.load(os.path.join("assets", "cactus", "large_cactus_1.png")),
            pygame.image.load(os.path.join("assets", "cactus", "large_cactus_2.png")),
            pygame.image.load(os.path.join("assets", "cactus", "large_cactus_3.png")),
        ]
        self.idx = random.randint(0, len(self.images) - 1)
        self.width = int(self.images[self.idx].get_width() * self.SCALING_FACTOR)
        self.height = int(self.images[self.idx].get_height() * self.SCALING_FACTOR)
        self.image = pygame.transform.scale(self.images[self.idx], (self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y - self.height
    
    def update(self, dt, game_speed):
        move_distance = 300 * game_speed * dt
        self.rect.x -= move_distance
    
    def draw(self, screen):
        screen.blit(self.image, self.rect)
        

class Bird(pygame.sprite.Sprite):
    SCALING_FACTOR = 0.70
    
    def __init__(self, x, y_level):
        """
        Args:
            x: Starting x position
            y_level: Height level (0=low, 1=mid, 2=high)
        """
        super().__init__()
        self.images = [
            pygame.image.load(os.path.join("assets", "bird", "bird_1.png")),
            pygame.image.load(os.path.join("assets", "bird", "bird_2.png"))
        ]
        
        # Scale images
        self.width = int(self.images[0].get_width() * self.SCALING_FACTOR)
        self.height = int(self.images[0].get_height() * self.SCALING_FACTOR)
        for i in range(len(self.images)):
            self.images[i] = pygame.transform.scale(self.images[i], (self.width, self.height))
        
        # Animation
        self.animation_index = 0
        self.animation_time = 0
        self.animation_speed = 0.15
        
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        
        # Position based on height level
        # Level 1: mid-high (borderline - can jump or duck)
        # Level 2: high (MUST duck - too high to jump over)
        height_levels = [GROUND_HEIGHT - 70, GROUND_HEIGHT - 92]
        self.rect.x = x
        self.rect.y = height_levels[y_level]
    
    def update(self, dt, game_speed):
        # Move bird
        move_distance = 350 * game_speed * dt
        self.rect.x -= move_distance
        
        # Update animation
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.animation_time = 0
            self.animation_index = (self.animation_index + 1) % 2
            self.image = self.images[self.animation_index]
    
    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Score:
    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.font = pygame.font.Font(None, 36)  # Correct: (None, 36) not (file_path=None, size=36)
    
    def update(self, dt, game_speed):
        """Increment score based on time and game speed"""
        self.score += 10 * game_speed * dt  # 10 points per second at 1x speed
    
    def reset(self):
        """Reset score for new game"""
        if self.score > self.high_score:
            self.high_score = self.score
        self.score = 0
    
    def draw(self, screen, x=500, y=20):
        """Draw score and high score on screen"""
        score_text = self.font.render(f"Score: {int(self.score)}", True, (255, 255, 255))
        screen.blit(score_text, (x, y))
        
        if self.high_score > 0:
            high_score_text = self.font.render(f"HI: {int(self.high_score)}", True, (200, 200, 200))
            screen.blit(high_score_text, (x, y + 40))

class Game:
    def __init__(self, width=640, height=480):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Dino Game")
        self.clock = pygame.time.Clock() 
        self.speed = 1.0 
        self.running = True
        self.game_over = False
        self.dt = 0
        
        # Game Objects
        self.dino = Dino()
        self.controller = Controller(self.dino)
        self.ground = Ground()
        self.obstacles = pygame.sprite.Group()
        self.score = Score()
        
        self.spawn_timer = 0
        self.spawn_interval = 2.0
        self.min_spawn_interval = 1.0
    
    def check_collisions(self):
        """Check if dino collided with any obstacle"""
        if not self.dino.is_alive():
            return
        
        # Check collision with each obstacle
        for obstacle in self.obstacles:
            if pygame.sprite.collide_rect(self.dino, obstacle):
                self.dino.die()
                self.game_over = True
                return
    
    def reset_game(self):
        """Reset game to initial state"""
        self.dino = Dino()
        self.controller = Controller(self.dino)  # Update controller reference
        self.obstacles.empty()
        self.score.reset()
        self.speed = 1.0
        self.spawn_timer = 0
        self.game_over = False
    
    def handle_game_over_input(self, event):
        """Handle restart on space/enter when game over"""
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self.reset_game()
    
    def spawn_obstacle(self):
        """Randomly spawn either a cactus or a bird"""
        obstacle_type = random.choice(['cactus', 'cactus', 'bird'])
        
        if obstacle_type == 'cactus':
            obstacle = Cactus(self.screen.get_width(), GROUND_HEIGHT + 10)
        else:
            y_level = random.choices([0, 1], weights=[30, 70])[0]
            obstacle = Bird(self.screen.get_width(), y_level)
        
        self.obstacles.add(obstacle)
    
    def update_obstacles(self):
        if not self.game_over:
            self.update_spawn_timer()
        
        for obstacle in list(self.obstacles):
            obstacle.update(self.dt, self.speed if not self.game_over else 0)  # Stop on game over
            if obstacle.rect.right < 0:
                self.obstacles.remove(obstacle)
    
    def update_spawn_timer(self):
        self.spawn_timer += self.dt
        
        adjusted_interval = max(self.spawn_interval / self.speed, self.min_spawn_interval)
        random_interval = adjusted_interval * random.uniform(0.7, 1.3)
        
        if self.spawn_timer >= random_interval:
            self.spawn_obstacle()
            self.spawn_timer = 0
    
    def draw_game_over(self):
        """Draw game over message"""
        font = pygame.font.Font(None, 48)  # Fix this line too
        game_over_text = font.render("GAME OVER", True, (255, 255, 255))
        restart_text = font.render("Press SPACE to restart", True, (200, 200, 200))
        
        text_rect = game_over_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 30))
        restart_rect = restart_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 20))
        
        self.screen.blit(game_over_text, text_rect)
        self.screen.blit(restart_text, restart_rect)

    def run(self):
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.game_over:
                    self.handle_game_over_input(event)
                else:
                    self.controller.handle_event(event)
            
            if not self.game_over:
                # Update game state only when alive
                self.speed += 0.01 * self.dt
                self.speed = min(self.speed, 3.0)

                self.controller.update()
                self.dino.update(self.dt)
                self.ground.update(self.dt, self.speed)
                self.score.update(self.dt, self.speed)
                
                # Check collisions
                self.check_collisions()
            
            # Always update obstacles (they stop on game over)
            self.update_obstacles()
            
            # Draw everything
            self.screen.fill((0, 0, 0))
            self.obstacles.draw(self.screen)
            self.ground.draw(self.screen)
            self.dino.draw(self.screen)
            self.score.draw(self.screen)
            
            if self.game_over:
                self.draw_game_over()
            
            pygame.display.update()

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()