#------------------------------------------------------------------------
# Final Project: Find water
#------------------------------------------------------------------------
#  - Navigate to Inner zone to find water
#       -> don't leave middle zone to outter area (if possible) (red tape)
#       -> don't leave inner zone to middle zone (if possible) (white tape - SOMETIMES READ AS BLUE OR GREEN)
#       -> avoid obstacles placed randomly
#
#------------------------------------------------------------------------

# ------------------- Imports ------------------- #
#!/usr/bin/python3
from __future__ import print_function, division
from final_library import *
import serial
import time
import random
import brickpi3


# ------------------- Tunables ------------------ #
duration_seconds = 200      # TIME  - how long the program will run
backupTime = 1              # TIME  - how long we backup in edge cases

currentZone = 0             # ZONES - which zone we're in
maxZones = 3                # ZONES - how many zones there are total
zoneColor = 0               # ZONES - current color of zone

waterColor = 2              # COLOR - value of blue in array called colors

_lastTurn = -1              # TURNS - last turn direction so we don't get trapped in a corner 
                            #         (0 =  and 1 = )






#========================================================================
# Interpret Command  -  Sends command after Color AND Object check
#========================================================================
# INTAKES: command (string)
# RETURNS: true = keep running program, false = exit program
# PURPOSE: this will decide what action to take based on Color found
# --------------------------------------------------------------------
#  Basic Idea: 
#         
#         1. Check if we found the end (water in inner zone) and tell program we're done
#         
#         2. Check if we're going forward and call necesarry function        
#         
#         3. Check if we've encountered edge of current zone and call necesarry function
#         
#         4. Check if we've encountered an object and call necesarry function
#         
#         5. Go back to main()       
#      
#------------------------------------------------------------------------
def InterpretCMD(retString):

    retValue = True
    global _lastTurn

    # Case 1 - "End of Program"
    if (retString == "Exit"):
        print("[EXIT PROGRAM]...")
        retValue =  False


    # Case 2 - "Go Forward"
    if (retString == "Forward"):
        forward()


    # Case 3 - "Edge of Current Zone" 
    if (retString == "Edge"):
        global backupTime
        _lastTurn = HandleZoneEdge(backupTime, currentZone, _lastTurn)     #      - handle it
        #print("Returned From Edge Case Function...")   # <--- debug statement


    # Case 4 - "Obstacle ahead" 
    if (retString == "Obj"):
        ret = AvoidObstacle(_lastTurn)
        #print("Returned from avoid obstacle...")   # <--- debug statement
        if (ret == -20):            # IF: blue was found during obstacle avoidance
            if (ConfirmBlue()):     #     - IF: Confirm it was blue
                retValue = False    #       -> Tell Program we're done running
        else:                       # ELSE: 
            retValue = True         #    - we're still running
            _lastTurn = ret         #    - value returned was turn direction


    #5. Return to main
    return retValue 




#========================================================================
# Handshake Function - handshake with bot and start timer
#========================================================================
#   -> this will block program until we get response from the controller
#      cmd is 1, used for checking whether the controller has responded
#
#   -> start timer when handshake completes. 
#
#------------------------------------------------------------------------
handshake()

start = time.monotonic()    # TIME  - when we started the program






#========================================================================================
#                                 MAIN FUNCTION   
#========================================================================================
# Basic Idea (within a while loop): 
#           1. go forward
#           2. keep track of which area we're in (Outer, Middle, Inner)
#           3. Avoid obstacles placed randomly and try not to leavy area while doing so
#           4. If in Inner area, look around for water (blue tape)
#
#----------------------------------------------------------------------------------------
# NOTES: 
#    (+)  we make decisions based on color sensor first since if there's an object close,
#         but is in an outer area from where we are, there isn't a point in avoiding it 
#         if we're turning around anyways.
#              
#    (+)  We handle each zone a bit differently. Outer zone, we allow randomization in 
#         which way we turn since we have the space to make it some distance before needing 
#         to turn again. However, we don't have a lot of space to work with in the inner zone,
#         so we limit outselves to MOSTLY one direction. Else, we risk getting caught in a   
#         "corner". 
#
#    (+)  Similar to above note about inner zone, we also keep track of last direction we  
#         turned when dealing with obstacles. we don't want to end up trapped between an 
#         obstacle and another obstacle or a zone edge, so we go the same direction as 
#         we did last.
#         
#    (+)  The hardest part of Obstacle avoidance is checking the color sensor at the same   
#         time.
#         
#
#========================================================================================

ZoneColors = [4, 5, 6]      # <--- This was necesarry due to sensor not reading white correctly and thus messing with ZoneColors.append(foundColor) when entering new zone
                            #      Program 'should' run fine without it - as long as ZoneColors.append(foundColor) is uncommented from (1 - Colors: Step C)

while ((time.monotonic() - start) <= duration_seconds):

    #1. reset any value(s) and read sensors
    delayValue = 0.25
    retString = "Forward"

    foundColor = CheckColorSensor(67)       # --> checks 67 times and accounts for floor color and bad reads
    foundDist = CheckSonicSensor(7)         # --> checks 7 times and returns average of all valid readings



    #------------------------------------------------------------------------------
    # 1 - Colors
    # 
    # STEP INFO: 
    #   - 0 -> 2 are prep steps for decision making
    #     
    #   - A: Checks for End of Program kind of scenarios w/ lots of weird read case checks (compensation checks)
    #   - B: Compensation check for any weird reads on the white tape of inner zone
    #   - C: Check if we're at the edge to next zone and updates info accordingly
    #   - D: Checks if we found any edge cases in the previous checks and updates 'retString' 
    #   - E: Compensation check for any missed line reads and updates info accordingly
    #     
    # NOTES:
    #   - This section has a lot of compensation checks due to the sensor not wanting to work correctly.
    #     We tried a lot of different ways to get it to work, but to no avail except going slow and adding weird case checks.
    #     A good example of this is the color sensor checker function would randomly return green as most read color
    #     and it could have read it on the floor of the outer zone (for some reason?) OR the white tape (which makes more sense).
    #     
    #------------------------------------------------------------------------------  
    if ( foundColor ):
        edgeCase = False        # are we dealing with edge case? 
        
        #0. Print Announcement 
        print("\n[Sensors Check] Color Found!", Colors[foundColor])


        #1. Stop Robot and think for a second/stop any additional motion
        stop()
        time.sleep(0.5)

        
        #2. Account for random reads of Green/Sensor mess ups
        if (foundColor == 3 and currentZone != 1):  # IF: color found was green AND we're not in outter zone
            foundColor = 6                          #   - we probably got a weird read on white, so compensate for that
            currentZone = 2                         #   - since we're assuming white, we'll say our bot is in the middle zone (this will trigger step #A )
            zoneColor = -1                          #   - reset zoneColor to help trigger step #A

        elif (foundColor == 3):                     # ELIF: color found was green AND we're in the outer zone
            foundColor = ZoneColors[0]              #   - compensate for weird read
            currentZone = 1                         #   - ensure this is set correctly
            
        
            
            
        
        #------------------------------------------------------------------------------
        # A - Check for water/endpoint 
        if ((foundColor == waterColor) and (currentZone == maxZones or currentZone == maxZones - 1)):       # IF: we have found blue in inner or middle zone (middle zone check is compensation for sensor not wanting to read red)
            if (ConfirmBlue()):                                                                             #   - IF: it was, in fact, blue we found
                retString = "Exit"                                                                          #       -> say we need to exit program
            else:                                                                                           #   - ELSE: it was actually edge
                edgeCase = True                                                                             #       -> set edgeCase to true

        elif ((foundColor == waterColor or foundColor == 3) and (currentZone != maxZones)):                 # ELIF: we probably read green or blue on white tape
            foundColor = 6                                                                                  #   - compensate for that

        elif (foundColor == waterColor):                                                                    # ELIF: if we just randomly find blue (compensating for sensor read issues)
            if (ConfirmBlue()):                                                                             #   - IF: it was, in fact, blue we found
                retString = "Exit"                                                                          #       -> say we need to exit program
            else:                                                                                           #   - ELSE: it was actually edge
                edgeCase = True                                                                             #       -> set edgeCase to true


        #------------------------------------------------------------------------------
        # B. Check for weird read on white tape (another compensation check)
        #    runs after water check, so we don't have to worry about missing end point
        if ((foundColor != zoneColor) and (currentZone == maxZones)):                       # IF: we have hit our current zone's edge in inner zone and found weird color
            edgeCase = True                                                                 #   - set edgeCase to true   
        

        #------------------------------------------------------------------------------
        # C - Check if we're at the edge to next zone
        if ((foundColor != zoneColor) and (currentZone < maxZones)):        # IF: found edge to next zone (maxZones == 3)
            #ZoneColors.append(foundColor)                                   #   - add color to array of zone colors
            currentZone += 1                                                #   - update zone
            zoneColor = foundColor                                          #   - update color
            retString = "Forward"                                           #   - set retString to Forward
            print("[Zone Change] Zone:", Zones[currentZone])                #   - print announcement 
            print("[Zone Change] Color:", Colors[zoneColor])                #   - print announcement 

        elif ((foundColor != zoneColor) and (currentZone == maxZones)):     # IF: we have hit our current zone's edge in inner zone and found weird color
            edgeCase = True                                                 #   - set edgeCase to true


        #------------------------------------------------------------------------------
        # D - Check if we found edge case to current zone in any of the previous checks
        elif ((edgeCase) or (foundColor == zoneColor)):                       # ELSE: we have hit our current zone's edge
            retString = "Edge"
        

        #------------------------------------------------------------------------------
        # E - Ensure we know where we are... (compsating for skipping any reads/zone changes...)
        # IF: we're in the OUTER zone now, THEN: Update variables accordingly
        if (foundColor == ZoneColors[0]):     # IF: OUTER ZONE CHECK       
            currentZone = 1
            zoneColor = ZoneColors[0]

        # ELIF: we're in the MIDDLE zone now, THEN: Update variables accordingly
        elif (foundColor == ZoneColors[1]):     # ELIF: MIDDLE ZONE CHECK     
            currentZone = 2
            zoneColor = ZoneColors[1]

        # ELIF: we're in the INNER zone now, THEN: Update variables accordingly
        elif (foundColor == ZoneColors[2]):     # ELIF: INNER ZONE CHECK     
            currentZone = 3
            zoneColor = ZoneColors[2]

        elif (foundColor == 2):                 # ELIF: we have somehow found blue...?
            if (ConfirmBlue()):                 #   - IF: confirmation
                retString = "Exit"              #       -> tell program to exit

        else:                                   # ELSE: some error has occured
            print("\n ERROR????\n")             #   - let programmers know (doesn't make it this far usually)



    
    #------------------------------------------------------------------------------
    # 2 - Obstacles
    # 
    #  - Obstacles that are far away may be in another zone, 
    #    so we double check we aren't on the edge of zone right now 
    #
    #  - We also want to make sure we aren't exiting the program,
    #    since it wouldn't matter what the distance found was then
    #
    #------------------------------------------------------------------------------
    if ( (foundDist <= 20) and (retString != "Edge") and (retString != "Exit")):    # CHG: 15 -> 20
        print("\n[Sensors Check] Obstacle Found!")
        retString = "Obj"
        




    #------------------------------------------------------------------------------
    # 3 - Commands
    #       - Interpret choice/take action
    #       - check if we're still running program based on return value
    #           -> if yes, then give a bit of a delay
    #           -> else, break from program
    #------------------------------------------------------------------------------
    if (InterpretCMD(retString)):       # IF: we're still running program
        time.sleep(delayValue)          #   - give cmd a sec to run
    else:                               # ELSE: 
        break                           #    - break out of loop 

                  


#========================================================================
#                       End of Program
#========================================================================
goodbye()   # Stops program and Prints goodbye