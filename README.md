# mote-huer

## What is it?

Almost done! It's a Docker container that, when deployed via [BalenaCloud](https://balena-cloud.com), allows me to quickly setup Raspberry Pi Zeros with [Pimoroni Mote pHats](https://shop.pimoroni.com/products/mote-phat) that work alongside the Philips Hue bulbs in a given room to add accent lighting.

## How does it do it?

So far, the Python code does a couple of things: it checks whether the current time is between 1 hour before sunset and a specified 'night' time - if so, it does a little rainbow loop animation on the Mote sticks. Otherwise, it polls the API on my Hue hub to see whether any lights in a room's group are on. If so, it gets the XY colours of those lights, converts them to RGB, averages them, and displays the average colour on the Mote sticks. If none of them are on, it turns the Mote sticks off.

## Why?

I've got a few Mote hats with Mote sticks, and they're not doing much at the moment. My flat has 29 Hue (or Hue compatible) bulbs, and I wondered if there was a way to make the Motes work alongside the Hue bulbs. I tried experimenting in OpenHAB, which worked, but had an unpredictable amount of latency for reasons I couldn't be bothered to look into (presumably interrupts from various other scripts running on my OpenHAB server). So I whipped together a short script that accessed the Hue hub API directly, and it worked surprisingly well - latency dropped to under a second. 

Of course I *could* simply set up one SD card and clone it a few times, then plug each of them in and tweak appropriate settings. But that's not very IoT, it's not very interesting, and it means deploying any more Motes in future would be a PITA involving pulling the image from one of the working Motes, trying to remember how to configure it, etc. This way, I will hopefully be able to simply burn the appropriate Balena image, burn it, plug in and change a few environment variables from the cloud. Also, it should make it a lot easier to extend the code at a later date.

## Extend the code?

Sure: at the moment it just either mirrors the (average) colour of the Hue bulbs it's assigned to, or displays a rainbow loop. I'd like to change the mirroring to smoothly cycle through the colours of the other bulbs, change up the animations for different times, perhaps react to different events (notifications, or people coming home, for example. Perhaps even some different state if I'm listening to music?) and who knows what else. Using Balena *should* make it much easier to add these features without having to mess around ssh/scp-ing into each one.

## Can I use it?

If you're reading this now, sure - but be warned that I'm a novice in all of Python, Docker and Balena, and this repo clearly has limited transferability: it requires an existing Hue system (Hub and bulbs), and at least one Raspberry Pi and Pimoroni Mote HAT. Beside that, at the moment the API credentials, as well as the groups' and lights' API endpoints are all hardcoded. I'll try to change these to environment variables soon (I'm thinking a config file is probably the best way, but I'm not sure how well Balena will handle that idea, so it might have to be manual entry of a bunch of vars).

## Environment Variable Configuration

The current version uses nine Balena Environment Variables, configured as follows:

#### 'HUB_IP'
Enter your Hue Hub's IPv4 Address eg: 192.168.1.100

#### 'API_KEY'
Enter your Hue Hub API key. This is a long (40 characters?) string of gibberish, so should look something like: ~jef7YHD9kL39rUnej1aPv9kdNso6GxuiJ7oPDmW

#### 'GROUP_NO'
Enter the group number that your Hue lights belong to, eg: 1

#### 'LIGHTS_LIST'
Enter a square bracketed list of space-separated numbers, where the numbers correspond to the numbers assigned by the Hue API to the bulbs in the room, eg: [1 2 3]

#### 'LATITUDE'
The latitude of your room (for sunset calculation), eg: 27.1750151

#### 'LONGITUDE'
The longitude of your room (for sunset calculation), eg: 78.0399665

#### 'NIGHT_TIME'
The time you want the Mote to go back to mirroring the Hue bulbs. This should be in the format 20:30:00 for Eight Thirty PM

#### 'RESET_TIME'
The time when the script should fetch your local sunset time, format as above, eg: 23:59:00

#### 'PRE_SUNSET'
The number of hours before sunset when the animation should start, eg: 2

#### NB:
It might be a good idea for me to add a switch to turn the sunset function on or off, making the Lat/Long/Night/Reset/Pre-Sunset variables optional. 
