# Base code made by: NeuralNine (Florian Dedov)
# Added functionnality made by: Us (Jean-Pierre Masri-Clermont, Maxime Boileau, Japhpa N., Fares Hamour et Simon Gary)


import math
import sys

import neat
import pygame
import pickle


WIDTH = 1920
HEIGHT = 1080

CAR_SIZE_X = 60
CAR_SIZE_Y = 60

BORDER_COLOR = (255, 255, 255, 255) # Color To Crash on Hit
LINE_COLOR = (255, 255, 0, 255) # Color to deduct points on touch 


current_generation = 0 # Generation counter

# Files used in the simulation
car_png = 'car.png'
map_png = 'map12.png'
config_path = './config.txt'

# Global lists used
cars = []
original_pos = [[171,163],[171,499],[171,915],[959,163],[959,499],[959,915],[1337,163],[1337,499],[1337,915]]


class Car:

    def __init__(self, initx, inity):
        # Load Car Sprite and Rotate
        self.sprite = pygame.image.load(car_png).convert() # Convert Speeds Up A Lot
        self.sprite = pygame.transform.scale(self.sprite, (CAR_SIZE_X, CAR_SIZE_Y))
        self.rotated_sprite = self.sprite 

        # Spawn car at the original position
        self.position = [initx, inity] # Starting Position
        self.angle = 0
        self.speed = 0

        #Create de car hitbox
        self.hitbox = (self.position[0], self.position[1], CAR_SIZE_X, CAR_SIZE_Y)

        self.speed_set = False # Flag For Default Speed Later on

        self.center = [self.position[0] + CAR_SIZE_X / 2, self.position[1] + CAR_SIZE_Y / 2] # Calculate Center

        self.radars = [] # List For Sensors / Radars
        self.drawing_radars = [] # Radars To Be Drawn

        self.alive = True # Boolean To Check If Car is Crashed

        self.distance = 0 # Distance Driven
        self.time = 0 # Time Passed
        
        #Initializing the corners
        length = 0.5 * CAR_SIZE_X
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

    def draw(self, screen):
        screen.blit(self.rotated_sprite, self.position) # Draw Sprite
        self.hitbox = (self.position[0], self.position[1], CAR_SIZE_X, CAR_SIZE_Y)
        pygame.draw.rect(screen, (255,0,0), self.hitbox,2) #OPTIONAL darw hitboxes
        self.draw_radar(screen) #OPTIONAL FOR SENSORS

    def draw_radar(self, screen):
        # Optionally Draw All Sensors / Radars
        for radar in self.radars:
            position = radar[0]
            pygame.draw.line(screen, (0, 255, 0), self.center, position, 1)
            pygame.draw.circle(screen, (0, 255, 0), position, 5)

    def check_collision(self, game_map):
        self.alive = True
        for point in self.corners:
            # If Any Corner Touches Border Color -> Crash
            # Assumes Rectangle
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.alive = False
                break
    
    def check_line(self, game_map): 
        self.alive = True
        for point in self.corners:
            # If Any Corner Touches Line Color -> Penalty
            # Assumes Rectangle
            if game_map.get_at((int(point[0]), int(point[1]))) == LINE_COLOR:
                self.distance -= 10*self.speed
                break
    
    def check_radar(self, degree, game_map):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # While We Don't Hit BORDER_COLOR AND length < 300 (just a max) -> go further and further
        
        while not game_map.get_at((x, y)) == BORDER_COLOR and length < 300 and not colide_radar_with_hitbox(self, x, y):
            length = length + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # Calculate Distance To Border And Append To Radars List
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])
    
    def update(self, game_map):
        # Set The Speed To 20 For The First Time
        # Only When Having 4 Output Nodes With Speed Up and Down
        if not self.speed_set:
            self.speed = 20
            self.speed_set = True

        # Get Rotated Sprite And Move Into The Right X-Direction
        # Don't Let The Car Go Closer Than 20px To The Edge
        self.rotated_sprite = self.rotate_center(self.sprite, self.angle)
        self.position[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.position[0] = max(self.position[0], 20)
        self.position[0] = min(self.position[0], WIDTH - 120)

        # Increase Distance and Time
        self.distance += self.speed
        self.time += 1
        
        # Same For Y-Position
        self.position[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        self.position[1] = max(self.position[1], 20)
        self.position[1] = min(self.position[1], WIDTH - 120)

        # Calculate New Center
        self.center = [int(self.position[0]) + CAR_SIZE_X / 2, int(self.position[1]) + CAR_SIZE_Y / 2]

        # Calculate Four Corners
        # Length Is Half The Side
        length = 0.5 * CAR_SIZE_X
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

        # Check Collisions And Clear Radars
        self.check_line(game_map)
        self.check_collision(game_map)
        self.radars.clear()

        # From -90 To 120 With Step-Size 45 Check Radar
        for d in range(-90, 120, 45):
            self.check_radar(d, game_map)

    def get_data(self,game_map):
        # Get Distances To Border and if touches the yellow line
        radars = self.radars
        return_values = [0, 0, 0, 0, 0,False]
        
        for i, radar in enumerate(radars):
                return_values[i] = int(radar[1] / 30)
        
        
        for point in self.corners:
            # If Any Corner Touches Line Color -> Penalty
            # Assumes Rectangle
            if game_map.get_at((int(point[0]), int(point[1]))) == LINE_COLOR:
                return_values[5] = True
                break
            

        return return_values

    def set_is_alive(self, is_alive):
        self.alive = is_alive

    def is_alive(self):
        # Basic Alive Function
        return self.alive

    def get_reward(self):
        # Calculate Reward (Maybe Change?)
        # return self.distance / 50.0
        #return self.distance / (CAR_SIZE_X / 2)
        return self.distance 
    

    def rotate_center(self, image, angle):
        # Rotate The Rectangle
        rectangle = image.get_rect()
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_rectangle = rectangle.copy()
        rotated_rectangle.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
        return rotated_image

def colide_radar_with_hitbox(radarCar, x, y):

    global cars
    for car in cars:
        if x == None or y == None or radarCar.hitbox[0] == None or radarCar.hitbox[0] == None:
            return False

        if car is radarCar or car.hitbox is None:
            continue

        if radarCar.is_alive() and car.is_alive():
            if x >= car.hitbox[0] and x <= car.hitbox[0] + CAR_SIZE_X and y >= car.hitbox[1] and y <= car.hitbox[1] + CAR_SIZE_Y: 
                return True
    return False
        

def run_simulation(genomes, config):
    
    # Empty Collections For Nets and Cars
    nets = []
    global cars
    cars = []

    # Initialize PyGame And The Display
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

    # For All Genomes Passed Create A New Neural Network
    inst_count = 0
    
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        if inst_count >= 9:
            break
        
        cars.append(Car(original_pos[inst_count][0],original_pos[inst_count][1]))
        inst_count += 1
    
    # Clock Settings
    # Font Settings & Loading Map
    clock = pygame.time.Clock()
    generation_font = pygame.font.SysFont("Arial", 30)
    alive_font = pygame.font.SysFont("Arial", 20)
    game_map = pygame.image.load(map_png).convert() # Convert Speeds Up A Lot

    global current_generation
    current_generation += 1

    
    
    # Simple Counter To Roughly Limit Time (Not Good Practice)
    counter = 0
    First_loop = True

    while True:
        # Make sure no genome have a fitness set to "None" 
        if First_loop:
            for i, g in genomes:
                if g.fitness == None:
                    g.fitness = 0
            First_loop = False
                    
        # Exit On Quit Event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)


        # For Each Car Get The Acton It Takes and check if it collisions with other cars
        
        counter_car = 0
        
        for i, car in enumerate(cars):
            x = counter_car + 1
            car_carshed = False
            while x < len(cars):
                car_test = cars[x]
                if car.is_alive() and car_test.is_alive() and check_hitbox_collision(car, car_test) and x != counter_car: #delete both cars
                    car_test.set_is_alive(False)
                    car_carshed = True
                x += 1
            
            counter_car += 1
        
            if car_carshed:
                car.set_is_alive(False)
            else:
                output = nets[i].activate(car.get_data(game_map))
                choice = output.index(max(output))
                if choice == 0:
                    car.angle += 5 # Left
                elif choice == 1:
                    car.angle -= 5 # Right
                elif choice == 2:
                    if(car.speed - 2 >= 10):
                        car.speed -= 2 # Slow Down
                else:
                    if(car.speed + 2 <= 50):
                        car.speed += 2 # Speed Up
            
        
        # Check If Car Is Still Alive
        # Increase Fitness If Yes And Break Loop If Not
        still_alive = 0
        for i, car in enumerate(cars):
            if car.is_alive():
                still_alive += 1
                car.update(game_map)
                genomes[i][1].fitness += car.get_reward()

        if still_alive == 0:
            break

        counter += 1
        if counter == 30 * 40: # Stop After About 20 Seconds
            break

        # Draw Map And All Cars That Are Alive
        screen.blit(game_map, (0, 0))
        for car in cars:
            if car.is_alive():
                car.draw(screen)
        
        # Display Info
        text = generation_font.render("Generation: " + str(current_generation), True, (0,0,255))
        text_rect = text.get_rect()
        text_rect.center = (900, 450)
        screen.blit(text, text_rect)

        text = alive_font.render("Still Alive: " + str(still_alive), True, (0, 0, 255))
        text_rect = text.get_rect()
        text_rect.center = (900, 490)
        screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(60) # 60 FPS

def check_hitbox_collision(car1, car2):
    
    x_sus = car1.hitbox[0] - car2.hitbox[0]
    y_sus = car1.hitbox[1] - car2.hitbox[1]
    
    if x_sus <= CAR_SIZE_X and x_sus >= 0-CAR_SIZE_X:
        if y_sus <= CAR_SIZE_Y and y_sus >= 0-CAR_SIZE_Y:
            return True
    return False

def replay_genome(config_path, winner_path="winner.pkl"):
    # Load requried NEAT config
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    # Unpickle saved winner
    with open(winner_path, "rb") as f:
        car = pickle.load(f)

    # Convert loaded agent into required data structure
    cars = []
    for n in range(9):
        cars.append((n, car))

    # Return list of agents
    return cars



if __name__ == "__main__":
    
    # Load Config
    #config_path = "./config.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    # Create Population And Add Reporters
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    
    
    ##### Chose the way you want to run the simulation #####
    """
    # Run simulation generations without saving the best agent
    population.run(run_simulation, 10000)
    """

    """
    # Run simulation a number of generations equal to num_gen and then save the best agent
    num_gen = 2000
    winner = population.run(run_simulation, num_gen)
    with open("winner.pkl", "wb") as f:
        pickle.dump(winner, f)
        f.close()
    """
    # Run simulation with only the best agent in loop
    while True: 
        run_simulation(replay_genome(config_path),config)
    