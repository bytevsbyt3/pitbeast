# PIT Stego Tool

## Pixel Indicator Technique

The Pixel Indicator Technique is an Image based steganography method.
It uses one of the colour channels as an Indicator, typically the alpha channel, and other channels as carriers for the hidden data. The hidden data can be stored using from 1 to 8 bits of the colour pixel byte.\
The steganography image can contains text messages or files.

## This script

The tool was originally created to solve a challenge for a CTF.\
Then I revisited it, adding features options and adding the __hide__ functionality.\
In the modified.png image it's stored a secret as a text message. The hidden data can be retrieved launching the script:

```(bash)
python pitbeast.py -n 2 -c modified.png
```

The 'modified.png' image was created with this tool with the command:

```(bash)
python pitbeast.py -hide -o modified.png -n 2 -s "$(cat message.txt)" original.png
```

By using another pattern (-p) you can change the order of the channels that carry the hidden data.

Note that the stego image can contain anything you want.

## Requirements

- python 2.7
- PIL python package

## TODO

Some code fixes\
Porting to python3\
I would like to automate some others variants of the extracting/hiding method.
