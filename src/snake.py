from sys import stdout
from time import sleep
from pynput.keyboard import Key, Listener
from random import randint
import curses,threading

# location blocks for snake
class Snake_Body_Block:
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.reference = [x,y]

# snake object composed of Snake_Body_Block
class Snake:
    # compose snake of {length} blocks along {initial_y} 
    def __init__(self, initial_x, initial_y, length, grid_size):
        self.blocks = [Snake_Body_Block(x,initial_y) for x in range(initial_x,initial_x-length,-1)]
        self.grid_size = grid_size
        self.direction = [1,"x"] # [1 (right/up)/-1 (left/down), "x"/"y" (plane)]
        self.status = "OK"

    # add block behind last block in-line with current direction of travel
    def add_block(self):
        if self.direction[1] == "x":
            self.blocks.append(Snake_Body_Block(self.blocks[len(self.blocks)-1].x+self.direction[0],self.blocks[len(self.blocks)-1].y))
        else:
            self.blocks.append(Snake_Body_Block(self.blocks[len(self.blocks)-1].x,self.blocks[len(self.blocks)-1].y+self.direction[0]))

    """
    call add_block() if in same location as food block,
    don't allow out of boundary and don't allow to hit self,
    otherwise move one block in direction of travel
    """
    def move(self,food):
        # add new snake block one block up in current direction of travel
        if self.direction[1] == "x":
            self.blocks.insert(0,Snake_Body_Block(self.blocks[0].x+self.direction[0],self.blocks[0].y))
        elif self.direction[1] == "y":
            self.blocks.insert(0,Snake_Body_Block(self.blocks[0].x,self.blocks[0].y+self.direction[0]))
        # remove last block in snake
        self.blocks.pop(len(self.blocks)-1)

        # check if outside grid boundary
        if self.blocks[0].x > self.grid_size or self.blocks[0].y > self.grid_size or self.blocks[0].x < 0 or self.blocks[0].y < 0:
            self.status = "BOUNDARY"

        # check if hit self
        elif any(x.reference == [self.blocks[0].x,self.blocks[0].y] for x in self.blocks[1:]):
            self.status = "SELF"

        #check if hit food
        elif self.blocks[0].x == food.x and self.blocks[0].y == food.y:
            self.add_block()
            food.randomise_location(self.blocks)
    
    # change direction of travel based on last key pressed, don't allow to run back on itself
    def change_direction(self,key):
        key = key.upper()
        if key == "KEY_UP" or key == "W":
            direction = [-1,"y"]
        elif key == "KEY_RIGHT" or key == "D":
            direction = [1,"x"]
        elif key == "KEY_DOWN" or key == "S":
            direction = [1,"y"]
        elif key == "KEY_LEFT" or key == "A":
            direction = [-1,"x"]

        # if direction is not opposite to current direction
        if not(self.direction[1] == direction[1] and self.direction[0] == (direction[0])*-1):
            self.direction = direction

# co-ordinates of food
class Food:
    # set random location on grid that doesn't
    def randomise_location(self,snake_pos):
        while True:
            x = randint(0,self.grid_size-1)
            y = randint(0,self.grid_size-1)
            if [x,y] not in snake_pos:
                self.x = x
                self.y = y
                break

    # initialise by randomising location inside grid boundary
    def __init__(self,grid_size,snake_pos):
        self.grid_size = grid_size
        self.randomise_location(snake_pos)

class Grid:
    # set grid size
    def __init__(self,x,y,snake_char,food_char,unoccupied_char,horizontal_padding="  "):
        self.grid = []
        self.grid_size = {"x":x,"y":y}
        self.snake_char = snake_char
        self.food_char = food_char
        self.unoccupied_char = unoccupied_char
        self.horizontal_padding = horizontal_padding

    # render snake position and food line by line
    def render(self,snake_pos,food):
        # get pos of snake and food
        occupied_snake = [[block.x,block.y] for block in snake_pos]
        occupied_food = [food.x,food.y]

        # render each line
        for y in range(self.grid_size["y"]):
            for x in range(self.grid_size["x"]):
                try:
                    # add horizontal padding first
                    stdscr.addstr(y,x*len(self.horizontal_padding),self.horizontal_padding)
                    
                    # then char depending on status of coordinate
                    if [x,y] in occupied_snake:
                        stdscr.addstr(y,x*len(self.snake_char),self.snake_char)
                    elif [x,y] == occupied_food:
                        stdscr.addstr(y,x*len(self.food_char),self.food_char)
                    elif y == 0 and x == 0:
                        stdscr.addstr(y,x*3,f"{len(snake_pos):003}")
                    else:
                        stdscr.addstr(y,x*len(self.unoccupied_char),self.unoccupied_char)
                except curses.error:
                    # renderer error
                    pass
        stdscr.refresh()

# run grid renderer designated for new thread in process
def render(grid,snake,food,fps):
    # while snake not outside boundary or hit self
    while snake.status=="OK":
        grid.render(snake.blocks,food)
        snake.move(food)
        # since the only change in the frame is snake moving, only render at the same speed as the snake moves
        sleep(1/(fps))

# run game
def main(win):
    # initialse grod, snake and food block
    g = Grid(x=16,y=16,snake_char="#",food_char="@",unoccupied_char="⋅",horizontal_padding="  ")
    s = Snake(initial_x=0,initial_y=10,length=5,grid_size=g.grid_size["x"])
    f = Food(grid_size=g.grid_size["x"],snake_pos=s.blocks)

    win.nodelay(False)
    key=""
    win.clear()

    # setup renderer loop
    renderer = threading.Thread(target=render,args=[g,s,f,8.5])
    renderer.start()

    # check game hasn't ended
    while renderer.isAlive():
        try:
            # change direction on keypress
            key = win.getkey()
            s.change_direction(key)
        except Exception:
            # no input
            pass

# if run from terminal play game loop
if __name__ == "__main__":
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    try:
        curses.wrapper(main)
    finally:
        curses.echo()
        curses.nocbreak()
        curses.endwin()