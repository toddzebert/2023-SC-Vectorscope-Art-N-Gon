
import math
import time
# import screen
# import colors
import screennorm
import gc9a01

from vectorscope import Vectorscope

import vectoros
import keyboardcb
import keyleds
import asyncio
import random

_abort=False
_xscale=1
_yscale=1
_web_n_gon = []

# scale=1

# 20K gets about 80/90%.
_big = 28000 # max ~ 32000, also slightly offcenter because of analog bias.
_small = int(_big * -1)
_inc = 800
_wait = 0

_art_n_gons = []
_art_def = {
    'min': 4,
    'max': 12, # @note Range is end-exclusive. 20 worked
    'step': 1,
    'step_mode': 'random',
    'step_param': 30, # Number of samples to get, when in this mode.
    'repeats': 1,
    'size': _big,
    'size_mode': 'random-random',
    'speed': 36,
    'speed_mode': 'range-random',
    'speed_min': 18,
    'speed_max': 72,
    'rotation': 'random',
}

# The main animation loop.
async def tempest_loop(v):
    # print("tempest_loop:", locals()) # debug
    print("tempest_loop.") # debug
    global _abort, _big, _small, _web_n_gon, _art_n_gons, _art_def

    while _abort==False:
        # await draw_n_gone(v, _web_n_gon) # @debug works!

        # await draw_n_gone(v, _art_n_gons[0]) # @debug testing - works!

        '''
        wave.outBuffer_ready = False
        while not v.wave.outBuffer_ready:
            await asyncio.sleep_ms(10) # @debug was 10
        '''

        # @debug testing below - works! testing again...works!
        # v.wave.packX(range(-2**15, 2**15, 2**8))
        # v.wave.packY(range(2**15, -2**15, -2**8))

        '''
        # @debug reboots :(
        print("before v.wave.packX.") # @debug
        i = 100 # I guess? See examplyes.py.
        sine = [int(math.sin((50 * i) + 2 * x * math.pi/256) * 16_000) for x in range(256)]
        cose = [int(math.cos((50 * i) + 2 * x * math.pi/256) * 16_000) for x in range(256)]
        v.wave.packY(sine)
        v.wave.packX(cose)
        '''

        '''
        # @debug doesn't work
        for d in _art_n_gons[0]:
            v.wave.packX(d['points-x'])
            v.wave.packY(d['points-y'])
        '''


        '''
        v.wave.outBuffer_ready = False
        '''

        for gon in _art_n_gons:
            for j in range(_art_def['repeats']):
                if _abort:
                    print("Get out!")
                    break
                await draw_n_gone(v, gon)


        '''
        # testing, works!
        await draw_line(v, _small, _small, _small, _big, 0, _inc)
        await draw_line(v, _small, _big, _big, _big, _inc, 0)
        await draw_line(v, _big, _big, _big, _small, 0, -1 * _inc)
        await draw_line(v, _big, _small, _small, _small, -1 * _inc, 0)
        '''


# @debug testing without this code...
# Pre-calculate the points on a line, given a 'gon (data) element.
def pre_calc_line(d):
    print("pre_calc_line:", locals()) # debug
    d['points-x'] = []
    d['points-y'] = []

    x = d['start'][0]
    y = d['start'][1]
    xDir = 1
    yDir = 1

    if d['end'][0] < d['start'][0]:
        xDir = -1
    if d['end'][1] < d['start'][1]:
        yDir = -1

    while (x * xDir) < (d['end'][0] * xDir) or (y * yDir) < (d['end'][1] * yDir):
        pass # debug

        '''
        # @debug suspect
        # @debug save the point, hopefully d passed by ref...
        # put it in (iterable) List, hopefully it will be OK as is...
        d['points-x'].append(int(x))
        d['points-y'].append(int(y))
        '''

        x += d['delta'][0]
        y += d['delta'][1]

    '''
    # @debug temporary as multiple lines should be appended... (hint, 256)
    original_len = len(d['points-x'])
    current_len = original_len

    # @debug suspect
    while current_len < 256:
        d['points-x'].extend(d['points-x'][0:min(256 - current_len, original_len)])
        d['points-y'].extend(d['points-y'][0:min(256 - current_len, original_len)])
        current_len = len(d['points-x'])
    '''


# Pre-calculate all 'gon (data) elements.
def pre_calc_gon(gon):
    print("pre_calc_gon:", locals()) # debug
    for d in gon:
        if d['type'] == 'line':
            pre_calc_line(d)


# Speed is how many intervals line will be drawn by, so 1 is fastest,
# 32 is good for "big", etc.
def create_n_gon(n, size = _big, speed = 32, rot = ''):
    print("create_n_gon:", locals()) # debug
    n_gon = []
    prev = []
    first = []
    # X, Y coordinates of an regular n-gon:
    # x=cos(2k𝜋/n), y=sin(2k𝜋/n), k=1,2,3...n.
    # Square, n = 4, octagon n = 8, etc.
    # range is stop-exclusive, so add 1.
    for p in range(1, n + 1):
        f = (2 * p * math.pi) / n
        x = int(math.cos(f) * size)
        y = int(math.sin(f) * size)

        # Handle rotation
        if rot == 'random':
            # Find reasonable rotation, based on 1/2 from sides.
            rot_deg = random.randint(0, int((360 / n) // 2))
            rot_rad = math.radians(rot_deg)
            oldX = x
            oldY = y
            x = int(oldX * math.cos(rot_rad) - oldY * math.sin(rot_rad))
            y = int(oldX * math.sin(rot_rad) + oldY * math.cos(rot_rad))

        if not first:
            first = [x, y]

        if prev:
            d = {
                'type': 'line',
                'start': prev,
                'end': [x, y],
                'delta': [
                    int((x - prev[0]) // speed),
                    int((y - prev[1]) // speed),
                ]
            }
            # @debug pre_calc_line(d)
            n_gon.append(d)

        prev = [x, y]

    # Create last line.
    # Confusing naming, but start/end is for current line, not previous.
    start = n_gon[-1]['end']
    end = n_gon[0]['start']

    d = {
        'type': 'line',
        'start': start,
        'end': end,
        'delta': [
            int((end[0] - start[0]) // speed),
            int((end[1] - start[1]) // speed),
        ]
    }

    # @debug pre_calc_line(d)
    n_gon.append(d)

    return n_gon

'''
async def render_line(v, xStart, yStart, xEnd, yEnd, xDelta, yDelta, render = False):
    global _abort, _wait

    x = xStart
    y = yStart
    xDir = 1
    yDir = 1

    if xEnd < xStart:
        xDir = -1
    if yEnd < yStart:
        yDir = -1

    while (x * xDir) < (xEnd * xDir) or (y * yDir) < (yEnd * yDir):
        if _abort:
            print("Get out!")
            break

        # @todo look into "buffer"...
        v.wave.constantX(int(x))
        v.wave.constantY(int(y))
        x += xDelta
        y += yDelta
        await asyncio.sleep_ms(_wait) # @debug was 10
'''

# Draws a line.
async def draw_line(v, xStart, yStart, xEnd, yEnd, xDelta, yDelta):
    print("draw_line:", locals()) # debug
    global _abort, _wait

    x = xStart
    y = yStart
    xDir = 1
    yDir = 1

    if xEnd < xStart:
        xDir = -1
    if yEnd < yStart:
        yDir = -1

    while (x * xDir) < (xEnd * xDir) or (y * yDir) < (yEnd * yDir):
        if _abort:
            print("Get out!")
            break

        # @todo look into "buffer"...
        v.wave.constantX(int(x))
        v.wave.constantY(int(y))
        x += xDelta
        y += yDelta
        await asyncio.sleep_ms(_wait) # @debug was 10


# Convenience function.
async def draw_line_lists(v, start, end, delta):
    print("draw_line_lists:", locals()) # debug
    await draw_line(v, start[0], start[1], end[0], end[1], delta[0], delta[1])


# Draw an n-gon.
async def draw_n_gone(v, n_gon):
    print("draw_n_gone:", locals()) # debug
    for d in n_gon:
        if d['type'] == 'line':
            await draw_line_lists(v, d['start'], d['end'], d['delta'])


# Handle abort (Menu) key.
def do_abort(key):
    global _abort
    _abort=True


# @todo ?
def do_xscale(key):
    global _xscale
    _xscale+=1
    if _xscale>6:
        _xscale=1


# @todo ?
def do_yscale(key):
    global _yscale
    _yscale+=1
    if _yscale>6:
        _yscale=1


from vos_state import vos_state

async def slot_main(v):
    global _abort,_continue, _web_n_gon, _big, _art_n_gons, _art_def
# So... Press D (or whatever is configured) and note the message below. Press Range to start the demo
# The demo will run until you press Menu. LEVEL/RANGE will change frequency of X and Y in steps
# Note that if you don't yield occasionaly, you don't get key scanning

    # @debug below don't work
    # scr = screen.Screen()
    # scr.tft.fill(colors.BLACK)

    # v.get_screen().clear() # @debug testing - nope

    # vos_state.show_menu = False # @debug nope

    # fill_model(gc9a01.WHITE) # @debug breaks!
    # cursor()

    # watch the keys
    mykeys=keyboardcb.KeyboardCB({ keyleds.KEY_LEVEL: do_xscale, keyleds.KEY_RANGE: do_yscale, keyleds.KEY_MENU: do_abort})

    # _web_n_gon = create_n_gon(3, _big // 6, 34) # @note works!!! but not 3 :(

    # Vars.
    r = 1
    s = _art_def['speed']
    rng = range(_art_def['min'], _art_def['max'], _art_def['step'])

    # Handle step mode.
    if 'step_mode' in _art_def:
        # @todo check if we have other options besides "random".
        source_rng = rng
        rng = []
        for i in range(_art_def['step_param']):
            rng.append(random.choice(source_rng))

    # Handle size mode.
    for i in rng:
        if 'size_mode' in _art_def:
            # @todo check if we have other options besides "random".
            r = random.randint(1, 5)

            if _art_def['size_mode'] == 'random-random':
                r = random.randint(1, r)

        # Handle speed mode.
        if 'speed_mode' in _art_def:
            s = random.randint(_art_def['speed_min'], _art_def['speed_max'])

        # N-gon it!
        _art_n_gons.append(create_n_gon(i, _art_def['size'] // r, s, rot = _art_def['rotation']))

    await tempest_loop(v)

    print("OK done")
