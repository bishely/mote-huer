import threading
import schedule
import requests  # available at: https://github.com/kennethreitz/requests
from os import getenv
from datetime import datetime
from datetime import timedelta
from rgbxy import Converter  # available at: https://github.com/benknight/hue-python-rgb-converter
from rgbxy import GamutC
from colorsys import hsv_to_rgb
from colorsys import rgb_to_hsv
import motephat as mote  # available at: https://github.com/pimoroni/mote-phat
import time

verbose = getenv('VERBOSE')
if verbose == "True":
    verbose = True
else:
    verbose = False

ultra_verbose = getenv('ULTRA_VERBOSE')
if ultra_verbose == "True":
    ultra_verbose = True
else:
    ultra_verbose = False

debug = getenv('DEBUG')
if debug == "True":
    debug = True
else:
    debug = False

if debug == True:
    print("debug mode active")
    print("this will loop five times and then stop")
    channels = [0, 1, 2, 3]
    mote.set_brightness(0.2)
    x = 0
    while x < 5:
        print("doing a rainbow for 10 seconds")
        current_time = datetime.now()
        while datetime.now() < (current_time + timedelta(seconds=10)):
            h = time.time() * 50
            for channel in range(4):
                for pixel in range(16):
                    hue = (h + (channel * 64) + (pixel * 4)) % 360
                    r, g, b = [int(c * 255) for c in hsv_to_rgb(hue / 360.0, 1.0, 1.0)]
                    mote.set_pixel(channel + 1, pixel, r, g, b)
            mote.show()
            time.sleep(0.01)
        print("rainbow time over")
        print("lights out - clear and show - for 10 seconds")
        mote.clear()
        mote.show()
        time.sleep(10)
        print("lights on for 10 seconds")
        for channel in channels:
            for pixel in range(16):
                mote.set_pixel(channel, pixel, 150, 150, 150)
        mote.show()
        time.sleep(10)
        print("lights out - set 0 bright and clear - for 10 seconds")
        mote.set_brightness(0)
        mote.clear()
        mote.show()
        time.sleep(10)
        x += 1
else:
    # We're not in Debug mode, so here's the main script

    # Friendly messages for verbose mode
    if verbose == True:
        print("Starting moteDriver in Verbose mode")
    else:
        print("Starting moteDriver")

    # Get Environment Variables for Config
    hub_ip = getenv('HUB_IP')
    api_key = getenv('API_KEY')
    group_no = getenv('GROUP_NO')
    lights = getenv('LIGHTS_LIST').split(",")
    latitude = getenv('LATITUDE')
    longitude = getenv('LONGITUDE')
    night = datetime.strptime((getenv('NIGHT_TIME')), "%H:%M:%S") + timedelta(hours=2)
    reset = datetime.strptime((getenv('RESET_TIME')), "%H:%M:%S") + timedelta(hours=2)
    presunset = int(getenv('PRE_SUNSET'))

    sunset = 0  # Triggers call to getSunset
    wasOn = False  # Possibly get rid of this?

    anythingOn = False

    # Friendly messages for verbose mode
    if verbose == True:
        print(" ")
        print("hub_ip = " + hub_ip)
        print("api_key = " + api_key)
        print("group_no = " + group_no)
        print("lights =")
        print(lights)
        print("latitude = " + latitude)
        print("longitude = " + longitude)
        print(" ")

    # Initialise Mote
    channels = [0, 1, 2, 3]
    mote.clear()
    mote.show()
    if verbose == True:
        print("motePhat initialised")


    # Function to fetch sunset time based on Latitude/Longitude
    def getSunset():
        if verbose == True:
            print(" ")
            print("getSunset called")
        url = "https://api.sunrise-sunset.org/json"
        parameters = "lat=" + latitude + "&lng=" + longitude

        r = requests.get(url, params=parameters)

        sunset = datetime.strptime(str(r.json()['results']['sunset']), "%I:%M:%S %p")
        sunset = sunset + timedelta(hours=2)
        output = (sunset - timedelta(hours=presunset)).time()
        if verbose == True:
            print("sunset reported as " + str(sunset))
            print("calculating to start presunset routine at " + str(output))
            print(" ")
        return output


    # Function to check whether any lights in the monitored group are on, returns boolean
    def isAnythingOn():
        global anythingOn
        if verbose == True:
            print(" ")
            print("isAnthingOn called")
        endpoint = "http://" + hub_ip + "/api/" + api_key + "/groups/" + group_no
        status = requests.get(endpoint)
        if verbose == True:
            print("getting request from: " + str(endpoint))
            if status.json()['state']['any_on'] == True:
                print
                print("returning True")
                print(" ")
                anythingOn = True
            else:
                print("returning False")
                print(" ")
                anythingOn = False
            return
        else:
            if status.json()['state']['any_on'] == True:
                anythingOn = True
            else:
                anythingOn = False
            return


    # Function to log the (XY tuple) colours of the monitored lights
    def colourLogger():
        if verbose == True:
            print(" ")
            print("colourLogger called")
        url = "http://" + hub_ip + "/api/" + api_key + "/lights/"
        lightsOn = 0
        colours = []

        for light in lights:
            endpoint = url + light
            if verbose == True:
                print("getting light state from: " + str(endpoint))
            status = requests.get(endpoint)
            if status.json()['state']['on'] == True:
                if verbose == True:
                    print("that light is on")
                lightsOn += 1
                xy = status.json()['state']['xy']
                colours.append(xy)
                if verbose == True:
                    print("added colour " + str(xy) + " to colours")
                    con = Converter(GamutC)
                    rough = con.xy_to_rgb(xy[0], xy[1])
                    r = rough[0]
                    g = rough[1]
                    b = rough[2]
                    print("that's roughly r=" + str(r) + " g=" + str(g) + " b=" + str(b))
            else:
                if verbose == True:
                    print("that light is not on")
                else:
                    pass
        if verbose == True:
            print(" ")
        return colours, lightsOn


    # shiftingMirror needs to pass add_direction

    def fader(start_hue, end_hue, add_direction, steps, seq):
        if verbose == True:
            print(" ")
            print("fader called")
            print("start_hue is " + str(start_hue))
            print("end_hue is " + str(end_hue))
        if anythingOn == True:
            # Set silly verbose vars and move hue one step away from hue
            if add_direction == True:
                direction = "clockwise"  # Going clockwise
                hue = (start_hue - steps) % 360  # Move a step away from hue
            else:
                direction = "anticlockwise"  # Going anticlockwise
                hue = (start_hue + steps) % 360  # Move a step away from hue

            if verbose == True:
                print(" ")
                print("going from start_hue to end_hue " + direction)

        if anythingOn == True:
            # Loop to fade from start_hue to end_hue
            x = 0
            hue = start_hue
            if seq == True:
                while x < 65:
                    for channel in range(4):
                        for pixel in range(16):
                            if add_direction == True:
                                hue = (hue + steps) % 360
                            else:
                                hue = (hue - steps) % 360
                            colour = hsv_to_rgb(hue / 360.0, 1.0, 1.0)
                            r = int(colour[0] * 255)
                            g = int(colour[1] * 255)
                            b = int(colour[2] * 255)
                            if ultra_verbose == True:
                                print("set c" + str(channel + 1) + "p" + str(pixel) + " to hue " + str(
                                    hue % 360) + " or r=" + str(r) + " g=" + str(g) + " b=" + str(b))
                            if anythingOn == False:
                                switchoff()
                                break
                            else:
                                # Set each pixel one by one to the appropriate colour
                                mote.set_pixel(channel + 1, pixel, r, g, b)
                                mote.show()
                                x += 1
                                time.sleep(0.01)
            if seq == False:
                while x < 65:
                    for channel in range(4, -1, -1):
                        for pixel in range(16, -1, -1):
                            if add_direction == True:
                                hue = (hue + steps) % 360
                            else:
                                hue = (hue - steps) % 360
                            colour = hsv_to_rgb(hue / 360.0, 1.0, 1.0)
                            r = int(colour[0] * 255)
                            g = int(colour[1] * 255)
                            b = int(colour[2] * 255)
                            if ultra_verbose == True:
                                print("set c" + str(channel + 1) + "p" + str(pixel) + " to hue " + str(
                                    hue % 360) + " or r=" + str(r) + " g=" + str(g) + " b=" + str(b))
                            if anythingOn == False:
                                switchoff()
                                break
                            else:
                                # Set each pixel one by one to the appropriate colour
                                mote.set_pixel(channel + 1, pixel, r, g, b)
                                mote.show()
                                x += 1
                                time.sleep(0.01)

            if verbose == True:
                print("fade from start_hue to end_hue complete")
                print("setting all pixels to end_hue, " + str(hue) + ", or r=" + str(r) + " g=" + str(g) + " b=" + str(
                    b))

        if anythingOn == True:
            seq = not seq
            setAll(r, g, b, seq)

        return

    def lightCalculator(lights, lightsOn):
        if verbose == True:
            print(" ")
            print("lightCalculator called")
            print("lights monitored:")
            print(lights)
            print("number of lights on: " + str(lightsOn))
            print(" ")
            print("converting colours:")

        colours = []
        con = Converter(GamutC)

        # Get each bulb's hue and append to the colours list
        for index in range(lightsOn):
            if verbose == True:
                print("colour " + str(index))
                print(lights[index][0], lights[index][1])
            rgb = con.xy_to_rgb(lights[index][0], lights[index][1])
            hsv = rgb_to_hsv(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
            h = int((hsv[0] * 360)) % 360
            colours.append(h)
            if verbose == True:
                print("Hue calculated as " + str(h) + " and added to list")
                print(" ")

        colours.sort()
        no_of_colours = len(colours)

        if no_of_colours == 0:
            return
        elif no_of_colours == 1:
            if verbose == True:
                print("only one light detected. Creating two neighbouring colours and going clockwise")
            colour1 = colours[0] - 45
            colour2 = colours[0]
            colour3 = colours[0] + 45
            add_direction = True
            colours = []
            colours.append(colour1)
            colours.append(colour2)
            colours.append(colour3)
            no_of_colours = 3
        else:
            if ((colours[1] - colours[0] + 360) % 360 < (360 / no_of_colours)):
                if verbose == True:
                    print("going clockwise (1)")
                add_direction = True
            elif ((colours[0] + 360 - colours[-1] % 360) < (360 / no_of_colours)):
                if verbose == True:
                    print("2 going anticlockwise (2)")
                add_direction = False
            elif ((colours[1] - colours[0] + 360) % 360 < (2 * (360 / no_of_colours))):
                if verbose == True:
                    print("3 going clockwise (3)")
                add_direction = True
            elif ((colours[0] + 360 - colours[-1] % 360) < (2 * (360 / no_of_colours))):
                if verbose == True:
                    print("4 going anticlockwise (4)")
                add_direction = False
            else:
                if verbose == True:
                    print("couldn't find an efficient path: going clockwise, anyway (5)")

        output = []

        if verbose == True:
            print(" ")
            print("doing maths to calculate fades!")
            print(" ")
        for x in range(no_of_colours):

            this_colour = colours[x]
            try:
                next_colour = colours[x + 1]
            except:
                    next_colour = colours[0]
                    add_direction = not add_direction

            if add_direction == True:
                if this_colour > next_colour:
                    distance = (360 - this_colour + next_colour)
                elif this_colour < next_colour:
                    distance = next_colour - this_colour
                else:
                    distance = 0
            else:
                if this_colour < next_colour:
                    distance = (360 + this_colour) - next_colour
                elif this_colour > next_colour:
                    distance = this_colour - next_colour
                else:
                    distance = 0
            output.append([this_colour, next_colour, (distance / 64.0), add_direction])
            
        if verbose == True:
            print("lightCalculator has finished, output is: ")
            print(output)
            
        return output

    def setAll(r, g, b, seq):
        if verbose == True:
            print(" ")
            print("setAll called")
            print("colour is r=" + str(r) + " g=" + str(g) + " b=" + str(b))
        # Set all pixels to hue_1
        if seq == True:
            for channel in range(4):
                for pixel in range(16):
                    mote.set_pixel(channel + 1, pixel, r, g, b)
                    if anythingOn == False:
                        switchoff()
                        break
                    else:
                        mote.show()
        if seq == False:
            for channel in range(4, -1, -1):
                for pixel in range(16, -1, -1):
                    mote.set_pixel(channel + 1, pixel, r, g, b)
                    if anythingOn == False:
                        switchoff()
                        break
                    else:
                        mote.show()
        if verbose == True:
            print("sleeping 5 seconds")
        time.sleep(5)
        return

    # Function to do the heavy lifting of fading between three colours
    def shiftingMirror():
        global anythingOn
        seq = False
        if verbose == True:
            print(" ")
            print("shiftingMirror called")
        global wasOn
        if anythingOn == True:
            if anythingOn == True:
                lights, lightsOn = colourLogger()
                if verbose == True:
                    print("colourLogger returned lights and lightsOn")

            if anythingOn == True:
                maneuvers = lightCalculator(lights, lightsOn)
                if verbose == True:
                    print("lightCalculator returned maneuvers")
                    print("setting start_colour")
                start_colour = maneuvers[0][0]

            if anythingOn == True:
                colour = hsv_to_rgb((start_colour / 360.0), 1.0, 1.0)

                r = int(colour[0] * 255)
                g = int(colour[1] * 255)
                b = int(colour[2] * 255)

            if anythingOn == True:
                setAll(r, g, b, seq)

            if anythingOn == True:
                for maneuver in maneuvers:
                    start = maneuver[0]
                    end = maneuver[1]
                    steps = maneuver[2]
                    direction = maneuver[3]
                    seq = not seq
                    if verbose == True:
                        print("current maneuver:")
                        print("start = " + str(start))
                        print("end = " + str(end))
                        print("steps = " + str(steps))
                        print("direction = " + str(direction))
                    if anythingOn == True:
                        fader(start, end, direction, steps, seq)
                if verbose == True:
                    print("maneuvers complete")
                    print("setting all pixels to start_colour")
                if anythingOn == True:
                    seq = not seq
                    setAll(r, g, b, seq)
                return

        else:  # Hey, remember when checked if anythingOn was True? If not, do this:
            if verbose == True:
                print("anythingOn is False.")
                print(" ")
            switchoff()
            return

    # Function to turn all pixels on all channels off
    def switchoff():
        if verbose == True:
            print(" ")
            print("switchOff called")
        mote.clear()
        mote.show()
        return

    # Function to cycle through a rainbow, shamelessly cribbed from Pimoroni's examples
    # (Hat tip to @gadgetoid)
    def rainbow():
        if verbose == True:
            print(" ")
            print("rainbow called")
        current_time = datetime.now().time()
        while current_time < night.time():
            h = time.time() * 50
            for channel in range(4):
                for pixel in range(16):
                    hue = (h + (channel * 64) + (pixel * 4)) % 360
                    r, g, b = [int(c * 255) for c in hsv_to_rgb(hue / 360.0, 1.0, 1.0)]
                    mote.set_pixel(channel + 1, pixel, r, g, b)
            mote.show()
            time.sleep(0.01)
            current_time = datetime.now().time()

    # Function to run other functions in threaded mode
    def run_threaded(job_func):
        job_thread = threading.Thread(target=job_func)
        job_thread.start()

    # Function to decide what time it is and which light animation to run
    def controller():
        if verbose == True:
            print(" ")
            print("controller called")
        global sunset
        global night
        global reset
        # This needs to be run threaded, or else it will block up the main thread
        while True:
            try:
                if sunset == 0:
                    reset = datetime.now() + timedelta(hours=2)
                    if verbose == True:
                        print("sunset is not set")
                        print("storing reset time as: " + str(reset))
                        print("getting time of sunset:")
                    sunset = getSunset()
                    if verbose == True:
                        print(sunset)
                current_time = datetime.now() + timedelta(hours=2)
                if current_time > (reset + timedelta(hours=24)):
                    if verbose == True:
                        print(" ")
                        print("Resetting sunset")
                    sunset = 0
                if current_time.time() > sunset:  # If we're past sunset
                    if current_time.time() < night.time():                  # And it isn't yet night
                        if verbose == True:
                            print("current time is past sunset, before night, so rainbows!")
                        rainbow()                                           # Bring the colours!
                    else:
                        if verbose == True:
                            print("current time is past sunset and past night, so mirror")
                        shiftingMirror()                                    # Otherwise, run mirror: average the
                else:                                                       # bulbs that are on and put them on Mote
                    if verbose == True:
                        print("current time is not past sunset, so mirror")
                    shiftingMirror()
            except KeyboardInterrupt:
                if verbose == True:
                    print("exception - keyboard interrupt")
                mote.clear()
                mote.show()
                return


    # Here begins the important stuff

    run_threaded(controller)                                    # Start the controller running in a separate thread
    schedule.every(10).seconds.do(run_threaded, isAnythingOn)   # Check isAnythingOn every ten seconds
    while True:
        schedule.run_pending()                                  # Check to see if we need to run isAnythingOn
        time.sleep(1)                                           # then sleep for a second.
