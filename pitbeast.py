#!/usr/bin/python
#-*- coding: utf-8 -*-

# Author: bytevsbyte @ beerpwn team

import argparse
import random
import subprocess as sp
from PIL import Image

# EXTRACT the secret from the image colour channels
# Pattern is used to pick a channel as indicator based on the first letter
# and extracting data carried by the other channels listed in the pattern
def pixel_indicator_extract(channels, pattern, nbitlist, check=False, searches=[]):
    indicator = channels[pattern[0]]
    for nbit in nbitlist:
        print('[+] picking %d bit per channel' % nbit)
        bitstring = ""
        for i in range(len(indicator)):
            v = getbinext(indicator[i], 2)[-2:]
            v = int(v, 2)
            f=''; s=''; t=''; a=''
            if v == 0:   #00 yes,no,no
                f = getbinext(channels[pattern[1]][i], nbit)
            elif v == 1: #01 no,yes,no
                s = getbinext(channels[pattern[2]][i], nbit)
            elif v == 2: #10 no,no,yes
                t = getbinext(channels[pattern[3]][i], nbit)
            elif v == 3: #11 no,no,no
                pass
            bitstring += f
            bitstring += s
            bitstring += t
            bitstring += a
        check_string(bitstring, searches=searches)
        write_bitstring_rawfile(bitstring, "temp_data.raw")
        if check:
            check_rawfile("temp_data.raw")
    return None

# HIDE a secret in the colour channels.
# The last nbits of one colour per pixel carry a piece of the secret.
# The last k bits of the indicator channel (k is the number of possibilities)
# tells where the data is stored (in which colour channel)
# Pattern can be specified, but by now the indicator is fixed to alpha channel
def pixel_indicator_hide(channels, secret, nbit, pattern, outfile, width, height):
    k = {0:pattern[1], 1:pattern[2], 2:pattern[3]}
    maskc = int('1'*(8-nbit) + '0'*nbit, 2)     # bit mask carrier
    alpha = list()
    secretbit = ''
    for c in (secret + '\x00'*(len(secret) % nbit)):
        secretbit += getbinext(c, 8)
    toks = [secretbit[i:i+nbit] for i in range(0,len(secretbit),nbit)]
    z = 0
    for i in range(len(channels['r'])):
        if z >= len(toks):
            alpha.append(chr(255))  # TOFIX IF ALPHA EXIST
            continue
        s = random.randint(0,3)
        if s != 3:
            carry = ord(channels[k[s]][i])
            carry = carry & maskc
            carry = carry | int(toks[z], 2)
            channels[k[s]] = channels[k[s]][:i] + chr(carry) + channels[k[s]][i+1:]
            #print("[DEBUG] bits[%d]=%s | indicator=%d | carry=%d" % (z,toks[z],s,carry))
            z += 1
        binalpha = 0b11111100 | s  # TOFIX IF ALPHA EXIST
        alpha.append(chr(binalpha))
        #print('[DEBUG] binalpha='+bin(binalpha)+'\n')
    channels['a'] = alpha
    write_new_image(channels, outfile, width, height)
    return None

# Used more with only RGB channels without alpha, in which case one in r-g-b choice
# is used as the carrier
# NOT CORRECTLY IMPLEMENTED YET
def direct_bits_from_channels():
    ml = len(passwd)*8
    bitstring = ""
    i = 0
    while len(bitstring) < ml:
        flip = (ord(bytesB[i]) + ord(bytesG[i]) + ord(bytesB[i])) % 3
        if flip == 0:   #00 no,no
            bitstring += bin(ord(bytesA[i]))[-2:]
        elif flip == 1: #01 no,yes
            bitstring += bin(ord(bytesA[i]))[-3:]
        elif flip == 2: #10 yes,no
            bitstring += bin(ord(bytesA[i]))[-4:]
        i += 1
    write_bitstring_rawfile(bitstring, outfile)
    checkresult(outfile)
    return None

# Extend string of bit to n length (e.g. 10 extended to 8 bits = 00000010)
def getbinext(char, n):
    return '{0:08b}'.format(ord(char))[-n:]

# Analyze channel passed as argument
def channel_stat(bytes, info='x'):
    stat = dict()
    for c in bytes:
        k = ord(c)
        if not stat.has_key(k):
            stat[k] = 0
        stat[k] += 1
    if len(stat) < 5:
        print('[+] stats channel %-6s: %s' % (info,str(stat)))
    return None

# Useful to search some string in the data obtained and
def check_string(bitstring='', searches=[]):
    for s in searches:
        bitsmatch = ''.join([getbinext(c, 8) for c in s])
        if bitsmatch in bitstring:
            print('[+] ##### MATCH FOUND for %s #####' % s)
    return None

# check the file content with a temporary file
def check_rawfile(fname):
    output = sp.check_output(['file', fname])
    print('[+] file %s' % output.replace('\n',' '))
    return None

def write_bitstring_rawfile(bitstring, outfile):
    toks = [bitstring[i:i+8] for i in range(0,len(bitstring),8)]
    data = [chr(int(t,2)) for t in toks]
    with open(outfile, "w") as f:
        f.write(''.join(data))
    return None

def write_new_image(channels, outfile, width, height):
    outimg = Image.new('RGBA', (width,height), "white")
    pixels_new = outimg.load()
    for i in range(0,height):
        for j in range(0,width):
            index = i * width + j
            r=ord(channels['r'][index])
            g=ord(channels['g'][index])
            b=ord(channels['b'][index])
            a=ord(channels['a'][index])
            pixels_new[j,i] = (r,g,b,a)
    outimg.save(outfile)
    return None


parser = argparse.ArgumentParser(description="""The Pixel Indicator Technique use
one of the colour channels as an INDICATOR and other channels as carriers for the hidden data.
The default option try to extract data from the png image file.
Instead, with the -hide option a new stego image can be created hiding a secret
with the pit technique.""")
#Usually the number of hidden bits doesn't change from pixel to another.
#However it's possible that the indicator tells how many bits take
#from all channel at time instead which channel as before.
parser.add_argument('-n', dest='nbit', type=int, default=None, help='number of bits taken as hidden data from channel/s. If not specified the tool will try from 1 to 8 bits')
parser.add_argument('-p', dest='pattern', type=str, default='argb', help='pattern for indicator (first letter) and carriers (other letters). Default is argb')
parser.add_argument('-c', dest='check', action='store_true', help='check the content of the raw file (creted with extracted data) with linux file command')
parser.add_argument('-w', dest='search', type=str, default='secret,', help='words to search for, in the extracted data (like secret,hello,friend)')
parser.add_argument('-hide', action='store_true', help='hide a secret message/data inside a png image')
parser.add_argument('-s', dest='secret', type=str, default=None, help='secret message when -hide is specified (needs -n -s -o)')
parser.add_argument('-o', dest='outfile', type=str, default=None, help='output file when -hide is specified')
parser.add_argument('file', metavar='file', nargs=1, type=str, help='name of the input file')
args  = parser.parse_args()


channels = dict()
isalpha  = False
imgfile  = Image.open(args.file[0])
imgsplit = imgfile.split()
if len(imgsplit) > 3:
    isalpha = True
    channels['a'] = imgsplit[-1].tobytes()
channels['r'] = imgsplit[0].tobytes()
channels['g'] = imgsplit[1].tobytes()
channels['b'] = imgsplit[2].tobytes()
if args.hide:
    if args.nbit is None:
        print('[-] no number of bits per channel to hide bro!')
        exit(1)
    if args.secret is None:
        print('[-] no secret bro!')
        exit(1)
    if args.outfile is None:
        print('[-] no output file bro!')
        exit(1)
    (width,height) = imgfile.size
    #pixels = imgfile.load()
    print('[+] hiding the message into the image')
    pixel_indicator_hide(channels, args.secret, args.nbit, args.pattern, args.outfile, width, height)
    print('[+] Done! Secret hidden in ' + args.outfile)
else:
    nbit = range(1,9,1)
    if not args.nbit is None:
        nbit = [args.nbit]
    print('[+] extracting hidden data from image')
    #channel_stat(channels['r'], 'red')
    #channel_stat(channels['g'], 'green')
    #channel_stat(channels['b'], 'blue')
    if 'a' in channels:
        channel_stat(channels['a'], 'alpha')
    words = [x for x in args.search.split(',') if x != '']
    pixel_indicator_extract(channels, args.pattern, nbit, check=args.check, searches=words)
    print('[+] Done! Last raw file is on the file system')
