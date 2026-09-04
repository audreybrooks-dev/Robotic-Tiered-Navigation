# =============================================================================
# PRIZM Serial Control Library for RP3 (task1_library.py)
# -----------------------------------------------------------------------------
#  THE SETUP SECTION
#        -> Tracking
#        -> Communication
#
#  THE COMMANDS SECTION
#        -> Sensors
#        -> Movement
#        -> Randomization
#
# =============================================================================


# ------------------- Improrts ------------------- #
#!/usr/bin/python3
from __future__ import print_function, division
import brickpi3
import serial
import time
import random


# ------------------- Tunables ------------------ #



#========================================================================================
#                              THE SETUP SECTION
#========================================================================================
#   TRACKING: 
#           -> Zone Tracking Setup
#           -> Color Sensor Setup:
#   
#   COMMUNICATIONS: 
#           -> Comms Setup
#           Handshake()        ->  setup for prizm and RP3 communications
#           cmdSend(ser, cmd)  ->  used for sending cmds to prizm and recieving acks
#           goodbye()          ->  sends goodbye to user and stops the bot
#   
#========================================================================================



#========================================================================
# TRACKING - Zone Tracking Setup
#------------------------------------------------------------------------
#    - Declares Zone array containing the different areas in trial
#    - Declares currentZone variable for tracking which zone we're in 
#      currently
#------------------------------------------------------------------------
Zones = ["NONE", "OUTER", "MIDDLE", "INNER"]
#          0        1         2        3
currentZone = 0


#========================================================================
# TRACKING - COLOR Sensor Setup
#------------------------------------------------------------------------
#    - Establishes brickpi3 object
#    - Sets sensor type         (NOTE: ASSUMES COLOR SENSOR IS IN PORT 1)
#    - Declares color array 
#------------------------------------------------------------------------
BP = brickpi3.BrickPi3()
BP.set_sensor_type(BP.PORT_1, BP.SENSOR_TYPE.EV3_COLOR_COLOR)
Colors = ["None", "Black", "Blue", "Green", "Yellow", "Red", "White", "Brown"]
#           0       1        2       3        4        5       6        7



#========================================================================
# COMMUNICATIONS - Comms Setup
#------------------------------------------------------------------------
#   Variable setup for port, baudrate, and ser
#------------------------------------------------------------------------
port = "/dev/ttyUSB0"  # change if needed
baudrate = 9600
ser = serial.Serial(port, baudrate=baudrate, timeout=1)


#========================================================================
# COMMUNICATIONS - Handshake Function 
#------------------------------------------------------------------------
#   -> this will block program until we get response from the controller
#      cmd is 1, used for checking whether the controller has responded
#------------------------------------------------------------------------
def handshake():
    print("*** Press the GREEN button to start the robot ***")
    time.sleep(1.5)
    
    while True:
        print("--- Sending out handshaking signal ---")
        if cmdSend(ser, '1'):
            print("!!! Connected to the robot !!!")
            ser.readall()       # Clear the serial receive buffer
            break
        print("*** Try again ***")
        time.sleep(0.2)


#========================================================================
# COMMUNICATIONS - Command Sender Function
#------------------------------------------------------------------------
#   -> this will send commands to PRIZM and retrieve the ACK that the 
#      PRIZM responds with. 
#------------------------------------------------------------------------
def cmdSend(ser, cmd):
    msg = str(cmd) + "\n"
    ser.write(msg.encode())
    ack_origin = ser.readline()
    ack = ack_origin[:-2].decode("utf-8")
    return ack


#========================================================================
# COMMUNICATIONS - Goodbye Function
#------------------------------------------------------------------------
#   -> Prints goodbye to user and alerts them the program is done running
#   -> also stops bot for us
#------------------------------------------------------------------------
def goodbye():
    print("\n\n===================================")            # TODO: Would be interesting to have stats here...
    print("You have made it to the water!")
    print("Thanks for Running the bot!")
    print("Robot OFF")        
    print("===================================")
    ack = stop() #  send stop command to robot
    #print(ack)  # debug stuff





#========================================================================================
#                             THE COMMANDS SECTION
#========================================================================================
#   SENSORS: 
#           get_color()          ->  Reads Color sensor (doesn't use cmdSend())
#           get_distance()       ->  Reads Distance sensor via PRIZM in Centimeters
#           CheckColorSensor(n)  ->  Reads Color sensor n times (uses get_color())
#           CheckSonicSensor(n)  ->  Reads Distance sensor n times (uses get_distance)
#   
#   MOVEMENT: 
#           forward()     ->   Tells bot to go in the facing direction
#           backward()    ->   Tells bot to go in the opposite direction of what its facing 
#           stop()        ->   stops bot (hard stop)
#           turn_left()   ->   tells bot to turn left
#           turn_right()  ->   tells bot to turn right  
#   
#  RANDOMIZATION:
#           randomTurn()  ->  return either 0 or 1 to determine whether we turn left or right
#           randomDeg()   ->  return random float between 0.5 and 4.5 for how long we turn
#
#========================================================================================


#========================================================================
# SENSORS - Get Color Function
#------------------------------------------------------------------------
#   -> read color sensor attached to RP3 and return found color 
#------------------------------------------------------------------------
def get_color():
    try:
        return BP.get_sensor(BP.PORT_1)
    except brickpi3.SensorError:
        return 0  # None
    

#========================================================================
# SENSORS - Get Distance Function
#------------------------------------------------------------------------
#   -> tell bot to read distance sensor and return ack/found dist
#------------------------------------------------------------------------
def get_distance():
    ack = cmdSend(ser, 2)
    return ack


#========================================================================
# SENSORS - Determine Color Read
#------------------------------------------------------------------------
# INTAKES: n for how many times to read the sensor
# RETURNS: the most common read color
#
# NOTES: 
#   -> this will read the sensor n times to determine what color was read
#   -> this should solve the error of reading yellow/blue on white tape
#   -> may have to combine blue/black/brown for carpet
#   -> got help debugging the dictionary bit with AI, since I'm not great at those
# 
# Color Reminder:    0  ->  nothin      //not counted
#                    1  ->  Black       //not counted
#                    2  ->  Blue 
#                    3  ->  Green 
#                    4  ->  Yellow 
#                    5  ->  Red 
#                    6  ->  White 
#                    7  ->  Brown       //not counted
#------------------------------------------------------------------------
def CheckColorSensor(n):
    ret = 0         # Returning value, default = 0
    reads = []      # array to hold values read

    #1. Read colors (n) times / Fill our reads[] with values
    for i in range(n):               
        value = get_color()                     #   -> grab value from sensor
        if (value >= 1 and value <= 7):         #   -> IF value is a number 1 though 7:
            reads.append(value)                 #     --> add it to our accepted reads
    

    #2. make sure SOMETHING was read
    if not reads:
        return ret # currently = -1


    #3. Count up our findings
    ColorCount = {}  # dictionary to store colors and the amount of times they've been read
    for j in reads:
        if j not in ColorCount:     #   -> IF we have not read this color before: 
            ColorCount[j] = 1       #     --> add spot for it
        else:                       #   -> ELSE: we've read it before
            ColorCount[j] += 1      #     --> so add to its count


    #4. Find our which color was read the most
    mostRead = 0    # our highest found color count
    for k in ColorCount:
        if (ColorCount[k] > mostRead):  # IF newcolor has more readings than our previous champion:
            mostRead = ColorCount[k]    #   -> store count of color that has the most readings
            ret = k                     #   -> store color that has the most readings
    

    #5. account for floor and no reads
    if (ret <= 1 or ret == 7):
        ret = 0


    #6. Return color that was read the most
    return ret  # SHOULDN'T BE = -1 NOW, BUT CHECK IN MAIN FUNCTION



#========================================================================
# SENSORS - Determine Distance Reading
#------------------------------------------------------------------------
# INTAKES: n = how many times to read the sensor
# RETURNS: the average reading found amoung valid sensor readings
#------------------------------------------------------------------------
def CheckSonicSensor(n):
    #0. Setup w/ Variables
    sensorCMD = ""      # command to grab sensor reading
    reads = []          # array to hold values read
    totalCount = 0      # total count of valid readings
    ret = -1            # Returning value, default = -1

    #1. Read distance (n) times / Fill our reads[] with values
    for i in range(n):  
        returning = get_distance()              #  -> Send cmd to check sensor
        value = int(returning)                  #  -> convert to integer
        if (value > 0):                         #  -> IF value is a valid reading:
            reads.append(value)                 #    --> add it to our accepted reads
            totalCount += 1

    #2. Make sure SOMETHING was read
    if not reads:
        print("ERROR: No distances read!")
        print("check the sensor is in the right port? \n NOTE: we are using port 1")
        return ret # currently = -1

    #3. Count up and store avg in returning value (ret)
    for j in reads:
        totalCount += j #don't know why THIS works and not reads[j], but ok
        #print(j)

    ret = totalCount / len(reads)

    #4. Return avg distance read
    return ret





#========================================================================
# SENSORS - Blue tape special case
#------------------------------------------------------------------------
# INTAKES: n = how many times to read the sensor
# RETURNS: the average reading found amoung valid sensor readings
#------------------------------------------------------------------------
# --- Blue tape special case ---
def ConfirmBlue():
    """
    Simple double-check for BLUE tape.
    Returns True if blue is confirmed, False otherwise.
    """
    blues = 2
    first = CheckColorSensor(41)

    if (first != blues):
        return False      # wasn't blue in the first place

    # pause to remove motion noise
    stop()
    time.sleep(0.20)

    second = CheckColorSensor(11)
    if (second != blues):
        return False      # wasn't blue in the first place
    return True



#========================================================================
# SENSORS - Blue tape special case      VRS. 2.0
#------------------------------------------------------------------------
# INTAKES: n/a
# RETURNS: True if blue is confirmed, False otherwise.
# NOTES:   Simple double-check for BLUE tape.
#           involves small movement iterations to check 
#   
#------------------------------------------------------------------------
def ConfirmBlueTwo():
    blue = 2
    blueFound = 0
    threshhold = 4                                    # <--- NOTE: might edit number count.. 
    angle_time = 0.35  # small turn (~30-35 degrees)


    #1. Check once more in current position
    ret = CheckColorSensor(37)
    if (ret != blue): # wasn't blue in the first place
        return False      
    else:
        blueFound += 1


    #2. move around a bit and check
    ret = CBT_Helper(angle_time)
    if (ret == -1):   #other was found
        return False    
    blueFound += ret


    #3. move forward a bit and check            <--- NOTE: might edit to ensure no collisions w/ obstacles
    forward()
    time.sleep(0.2)
    stop()
    ret = CheckColorSensor(37)
    if (ret != blue): # wasn't blue in the first place
        return False      
    blueFound += 1
 
    if (blueFound < threshhold):           
        return False

    return True                



def CBT_Helper(angle_time):

    def helper(duration):
        blue = 2
        start = time.monotonic()
        while (time.monotonic() - start < duration):

            chk = CheckColorSensor(11)

            if ( chk == blue ):
                found += 1
                        
            else:   # Abort immediately if tape detected (zone safety)
                print("Edge detected - stopping turn early.")
                return -1

            time.sleep(0.02)

        stop()
        return found


    #=========================================================
    #1. move around to the left and check
    print("[Check] Checking to the LEFT")
    turn_left()
    ret = helper(angle_time)
    if (ret == -1):
        return ret
    bluesFound += ret


    #2. move around to the right and check 
    print("[Check] Checking to the RIGHT")
    turn_right()
    ret = helper(angle_time * 2)
    if (ret == -1):
        return ret
    bluesFound += ret


    #3. Return blues found
    return bluesFound











#========================================================================
# MOVEMENT - GO FORWARD
#------------------------------------------------------------------------
#   -> tell bot to go forward, return ack
#------------------------------------------------------------------------
def forward():
    return cmdSend(ser, '3')


#========================================================================
# MOVEMENT - GO BACKWARD
#------------------------------------------------------------------------
#   -> tell bot to go backward, return ack
#------------------------------------------------------------------------
def backward():
    return cmdSend(ser, '4')


#========================================================================
# MOVEMENT - STOP MOVEMENT
#------------------------------------------------------------------------
#   -> tell bot to stop moving, return ack
#------------------------------------------------------------------------
def stop():
    return cmdSend(ser, '5')


#========================================================================
# MOVEMENT - TURN LEFT
#------------------------------------------------------------------------
#   -> tell bot to turn left, return ack
#------------------------------------------------------------------------
def turn_left():
    return cmdSend(ser, '6')


#========================================================================
# MOVEMENT - TURN RIGHT
#------------------------------------------------------------------------
#   -> tell bot to turn right, return ack
#------------------------------------------------------------------------
def turn_right():
    return cmdSend(ser, '7')


#========================================================================
# MOVEMENT - Back up 
#------------------------------------------------------------------------
#   -> tell bot to back it up until given distance
#   NOTE: ended up not used due to team wanting to control backup a bit more 
#         and had other plans that didn't work out
#------------------------------------------------------------------------
def backup_dist(StopPoint):
    #1. stop robot
    stop()

    #2. back up a bit until StopPoint
    while (True):
        backward()
        dist = CheckSonicSensor(3)
        if (dist >= 25):
            stop()
            break






#========================================================================
# MOVEMENT - Edge Handler
#------------------------------------------------------------------------
#   -> pick random direction and degree and align bot with that
#------------------------------------------------------------------------
def HandleZoneEdge(backupTime, currentZone, _lastTurn):                 # WE'VE HIT THE EDGE!!!!
    print("We've reached end of current zone:", Zones[currentZone])     #   - print announcement
    backward()                                                          #   - we need to back it up and..
    time.sleep(backupTime * 2)                                          #   - give it a sec to run
    stop()                                                              #   - stop the bot
    return ChangeDirection(currentZone, _lastTurn)                      #   - change direction we're heading





#========================================================================
# MOVEMENT - Change Direction (mostly randomly)
#------------------------------------------------------------------------
#  -> pick (sometimes random) direction and random degree and align bot 
#
# NOTE: we found that bigger angles worked better for us, 
#       especially since the bot had to go slow.
#       We also wanted to only turn one direction when in middle and inner
#       zones, thus we kept track via _lastTurn...
#       ^ still ended up going different ways 1/3-ish times
#------------------------------------------------------------------------

boundStop = 4.75
boundStart = 1.25

def ChangeDirection(currentZone, _lastTurn):
    global boundStop
    global boundStart

    #1. pick random direction and random degree
    randomT = randomTurn()
    randomD = randomDeg(boundStart, boundStop)
    ret = -1


    #2. Align bot...
    if (currentZone == 1):  
        boundStop = 8
        boundStart = 3.85        
        ret = randomT
        if ( randomT == 1 ):    # left
            turn_left()
        else:                   # right
            turn_right()
    else: 
        ret = _lastTurn
        boundStop = 6
        boundStart = 1.75
        if ( _lastTurn == 1 ):  # left
            turn_left()
        else:                   # right
            turn_right()
    
    time.sleep(randomD)


    #3. Stop bot
    stop()


    #4. return turn direction
    return ret 




#========================================================================
# RANDOMIZATION - randomTurn()
#------------------------------------------------------------------------
#   -> return either 0 or 1 to determine whether we turn left or right
#------------------------------------------------------------------------
def randomTurn():
    return random.randint(0, 1)


#========================================================================
# RANDOMIZATION - randomDeg()
#========================================================================
#   -> return random float between 0.5 and 4.5 for how long we turn
#------------------------------------------------------------------------
def randomDeg(boundStart, boundStop):
    return random.uniform(boundStart, boundStop)







# ============================================================================
# TASKS - AvoidObstacle_ZoneSafe()
# ----------------------------------------------------------------------------
# Simple avoidance with:
#   -> Back up
#   ->  Try turn (80-110 degrees)
#   ->  Abort if tape detected
#   ->  Retry opposite direction if needed
#   ->  Memory-based bias
#   ->  Guaranteed to stay inside the current zone
# ============================================================================

_lastTurnMemory = 0  # persists across calls

def AvoidObstacle(_lastTurn):
    global _lastTurnMemory

    
    # ----------------------------------------------------------------------
    # 1. BACK UP AWAY FROM THE OBSTACLE
    # ----------------------------------------------------------------------
    print("\n[Avoid Obstacle] Obstacle detected - backing up safely.")
    backward()
    time.sleep(0.95)

    stop()
    time.sleep(0.02)


    # ----------------------------------------------------------------------
    # 2. PICK TURN DIRECTION (memory-based)
    # ----------------------------------------------------------------------
    if random.random() < 0.40:
        turnDir = 1 - _lastTurnMemory
    else:
        turnDir = _lastTurnMemory

    turnStart = 2.5
    turnEnd = 4.0                              
    turnTime = randomDeg(turnStart, turnEnd)


    

    # ================================================================
    # SAFE TURN with BLUE CONFIRMATION
    # ================================================================
    def _safe_turn(duration):
        start = time.monotonic()
        while ( (time.monotonic() - start) < duration ):
            color = CheckColorSensor(55)

            # --- Blue tape special case ---
            if (color == 2):
                if ConfirmBlue():         # true blue
                    stop()
                    return 2
                else:
                    pass                  # ignore false blue and continue

            # --- Normal tape detection ---
            elif (color != 0):
                stop()
                return 1

            time.sleep(0.015)

        stop()
        return 0





    # ----------------------------------------------------------------------
    # 3. TRY THE CHOSEN TURN DIRECTION
    # ----------------------------------------------------------------------
    if (turnDir == 0):
        turn_left()
        aborted = _safe_turn(turnTime)
    else:
        turn_right()
        aborted = _safe_turn(turnTime)


    # ----------------------------------------------------------------------
    # 4. IF TURN WAS ABORTED, TRY OPPOSITE DIRECTION
    # ----------------------------------------------------------------------
    if (aborted == 2): #found blue!
        return -20

    elif (aborted == 1): #found other color/edge :(
        print("[Avoid Obstacle] Tape detected - switching direction!")

        turnDir = 1 - turnDir
        retryTime = turnTime * 0.7   

        if (turnDir == 1):
            turn_left()
            _safe_turn(retryTime)
        else:
            turn_right()
            _safe_turn(retryTime)




    # ----------------------------------------------------------------------
    # 5. UPDATE TURN MEMORY
    # ----------------------------------------------------------------------
    _lastTurnMemory = turnDir

    print("[Avoid Obstacle] Zone-safe avoidance complete.\n")
    return _lastTurnMemory
