# mote-huer

## What is it?

Almost done! It's a Python script that watches a group and a selection of Hue bulbs and fades between their colours on a Pimoroni Mote device (either the [USB Mote host](https://shop.pimoroni.com/products/mote) or the [Mote pHAT](https://shop.pimoroni.com/products/mote-phat)). It's also ready-packaged as a Docker container that, when deployed via [BalenaCloud](https://balena-cloud.com), allows quick setup of Raspberry Pi Zeros with Pimoroni Mote pHats.

## How does it do it?

So far, the Python code does a couple of things: it checks whether the current time is between 1 hour before sunset and a specified 'night' time - if so, it does a little rainbow loop animation on the Mote sticks. Otherwise, it polls the API on my Hue hub to see whether any lights in a room's group are on. If so, it gets the XY colours of those lights, converts them to RGB, puts them all in a big list, works out the distances between the colours (in HSV colourspace) and tries to calculate and display some smooth fades between those colours. If none of them are on, it turns the Mote sticks off.

## Why?

I've got a few Mote hats with Mote sticks, and they're not doing much at the moment. My flat has a lot of Hue (or Hue compatible) bulbs and a couple of strips, and I wondered if there was a way to make the Motes work alongside the Hue stuff. I tried experimenting in OpenHAB, which worked, but had an unpredictable amount of latency for reasons I couldn't be bothered to look into (presumably interrupts from various other scripts running on my OpenHAB server). So I whipped together a short script that accessed the Hue hub API directly, and it worked surprisingly well - latency dropped to under a second. Then I allowed feature creep to set in, wrote all the fading code, and the latency slipped back up, so it's now up to 10 seconds between turning the Hue stuff off and the Mote strips going dark, but to be honest, that's a price I'm willing to pay for pretty fades.

Of course I *could* have simply set up one SD card and cloned it a few times, then plugged each of them in and tweaked appropriate settings. But that's not very IoT, it's not very interesting, and it means deploying any more Motes in future would be a PITA involving pulling the image from one of the working Motes, trying to remember how to configure it, etc. This way, I will hopefully be able to simply burn the appropriate Balena image, burn it, plug in and change a few environment variables from the cloud. Also, it should make it a lot easier to extend the code at a later date.

## Extend the code?

Sure: on the original, private branch, I started out with it just mirroring the (average) colour of the Hue bulbs assigned, or displaying a rainbow loop. I then went nuts and added all the fading, because honestly, average colours are pretty bland and I wanted my Motes to do something nice. I'd like to change the mirroring to smoothly cycle through the colours of the other bulbs, change up the animations for different times, perhaps react to different events (notifications, or people coming home, for example. Perhaps even some different state if I'm listening to music?) and who knows what else. Using Balena *should* make it much easier to add these features without having to mess around ssh/scp-ing into each one.

## Can I use it?

Sure - but be warned that I'm a novice in all of Python, Docker and Balena, and this repo clearly has limited transferability: it requires an existing Hue system (Hub and bulbs), and at least one Raspberry Pi and Pimoroni Mote HAT. Beside that, at the moment the API credentials, as well as the groups' and lights' API endpoints are environment variables, and I don't have the time or the inclination at the moment (this whole project is a procrastination) to write up a proper setup guide on finding suitable values and setting them on your OS, so you'll have to figure them out for yourself.

That said, feel free to take and use any of the code: if you just want the script, then grab either the mote-driver.py script (which works with the pHAT) or the mote-huer.py script (which works with the USB host) and do with them what you will. If you want the BalenaCloud app, you'll want to first branch this repo and then link your Balena app to your branched version (I mean, you're welcome to link to this repo, but I can't promise I won't break it).

## Can I fix it?

Sure. It's *mostly* working ok, but the way I've gone about building in the switchOff() function to turn the lights off when there's no more Hue lights on in the group can *definitely* be improved (perhaps put a killswitch into the shiftingMirror function somehow, so its thread can be instantly terminated and switchOff() called?). Also, it has a tendency to go through some areas of the spectrum it probably shouldn't, and finish up on some 'wrong' colours - that can certainly be improved, but I don't have the time to go through the logs right now. The ULTRA_VERBOSE environment variable might help you out if you're looking to fix this. 

If you do resolve any issues, I'd welcome a Pull Request and happily credit you here.

## Environment Variable Configuration

The current version requires nine Balena Environment Variables, configured as follows:

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
The number of hours before sunset when the rainbow animation should start, eg: 2

## Optional Debugging Environment Variables

There are also three switches for debugging:

#### 'VERBOSE'
Set this to True to have your StdOut spammed to death by lots of messages explaining what's happening at any given moment. This does slow down performance, obviously, so don't leave it on if things are working as they should.

#### 'ULTRA_VERBOSE'
Set this to True if you'd like to see the numbers being sent for each individual pixel during fades: these are channel, pixel, hue (0-360: this isn't actually sent to the pixels, but can be useful for debugging), red, green, blue (all 0-255). Again, don't leave it on unless you want it to run slowly and spam you.

#### DEBUG
When set to True, this ignores the usual script entirely and makes five iterations of a loop that shows a rainbow for 10 seconds, turns everything off for 10 seconds, turns everything on (pure white, rgb=150), and finally turns off for another 10 seconds. This is functionally pretty pointless, but can help to check that your pixel strips and cables are all functioning properly (check the power supply if not).

## Other Notes

Oh yeah, I just remembered I tried to include a Timezone environment variable, but it didn't work for me, so I did a short-term hacky fix where I hardcoded my timezone shift from UTC into every relevant datetime object. You'll want to set that to your own timezone variance to avoid odd behaviour: search the code for **+ timedelta(hours=2)** and replace it with your own value (eg if you're in New York, it should be either **+ timedelta(hours=-5)** or **- timedelta(hours=5)**). I'll fix this up myself at some point, but not right now.
