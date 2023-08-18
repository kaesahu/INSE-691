from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import random


def calculate_waiting_time():
    users = random.randint(100, 500)
    total_bikes = random.randint(100, 200)
    ride_time_per_user = 50
    n_stations = 5# Number of stations
    bikes_per_station = total_bikes // n_stations
    
    available_riders = min(users, bikes_per_station * n_stations)
    
    if available_riders == 0:
        return 0  # No waiting time if no riders or bikes are available
    
    total_ride_time = available_riders * ride_time_per_user
    waiting_time = (total_ride_time - 1)  # Subtract 1 minute for last rider to finish riding
    
    return waiting_time



class Station(Agent):
    def __init__(self, unique_id, model, x, y):
        super().__init__(unique_id, model)
        self.x = x
        self.y = y
        self.bikes_available = 5  # Initial number of bikes at each station
        self.waiting_time = calculate_waiting_time()
        self.users_waiting = 0
        
        
        
    def step(self):
        users_here = [agent for agent in self.model.grid.get_cell_list_contents([(self.x, self.y)]) if isinstance(agent, User)]
        for user in users_here:
            if self.bikes_available > 0:
                self.bikes_available -= 1
                if self.users_waiting > 0:
                    self.users_waiting -= 1
            else:
                self.users_waiting += 1
                self.waiting_time += 1  # Increment waiting time for each user who couldn't get a bike

class User(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def move(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)
        
    def step(self):
        self.move()

class BikeShareModel(Model):
    def __init__(self, N_users=100, width=10, height=10):
        self.num_users = N_users
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        
        # Create 5 stations
        station_coords = [(2,2), (2,7), (5,5), (7,2), (7,7)]
        for i, coords in enumerate(station_coords):
            x, y = coords
            station = Station(i, self, x, y)
            self.grid.place_agent(station, (x, y))
            self.schedule.add(station)
            
        # Create users
        for i in range(self.num_users):
            user = User(i+5, self)  # start IDs from 5 since we have 5 stations
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(user, (x, y))
            self.schedule.add(user)
            
        self.datacollector = DataCollector(
            {"Waiting_Time": "waiting_time"}
        )
        
    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

def agent_portrayal(agent):
    if isinstance(agent, Station):
        portrayal = {
            "Shape": "rect", "Filled": "true", "w": 0.8, "h": 0.8,
            "Layer": 0, "Color": "green", "text": f"{agent.waiting_time}", "text_color": "white"
        }
        return portrayal

grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)

server = ModularServer(BikeShareModel, [grid], "Bike Share Model", {"N_users": 100, "width": 10, "height": 10})
server.launch(port=5651)
