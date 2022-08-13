#!/usr/bin/env python3
import math
from PIL import Image
import itertools
import functools
from collections import namedtuple
import sys
import enum


# Courtesy stackoverflow
# https://stackoverflow.com/a/41200105
def split_every(n, iterable):
    iterable = iter(iterable)
    yield from iter(lambda: list(itertools.islice(iterable, n)), [])


# Everything else is unlicense

lfold = functools.reduce


SimpleColor = namedtuple('SimpleColor', 'r g b')


class EscapeType(enum.Enum):
    RESET = 0
    BOLD = 1
    UNDERLINE = 2
    FOREGROUND = 3
    BACKGROUND = 4

    @staticmethod
    def typeof(v):
        if v == 0:
            return EscapeType.RESET
        elif v == 1:
            return EscapeType.BOLD
        elif v == 4:
            return EscapeType.UNDERLINE
        elif v in range(30, 39):
            return EscapeType.FOREGROUND
        elif v in range(40, 49):
            return EscapeType.BACKGROUND
        

class EscapeCode:
    def __init__(self, *args):
        self.codes = set(args)
        self.types = set(map(EscapeType.typeof, self.codes))

    @property
    def foreground(self):
        return self.types == {EscapeType.FOREGROUND}

    @property
    def background(self):
        return self.types == {EscapeType.BACKGROUND}

    @property
    def string(self):
        code = ';'.join(map(str, self.codes))
        return f'\033[{code}m'

    def __str__(self):
        return self.string

    def __repr__(self):
        codes = ', '.join(map(str, self.codes))
        return f'EscapeCode({codes})'


class EscapedString:
    def __init__(self):
        self.active_codes = set()
        self.active_types = set()
        self.codestring = []

    def __append_code(self, c):
        # saves an introducer
        pre_zero = set()
        # if active codes has codes not in the new code
        if self.active_types - c.types:
            pre_zero = {0}
            self.active_codes = set()
            self.active_types = set()
        # only add differing codes
        new_codes = c.codes - self.active_codes
        new_escape = EscapeCode(*(pre_zero | new_codes))
        if new_codes:
            self.codestring.append(new_escape)
            # set to the target codes instead of the new ones, otherwise
            # active codes could accumulate foregrounds or backgrounds
            # which would prevent repeats
            self.active_codes = c.codes
            self.active_types |= c.types

    def append(self, v):
        if type(v) == EscapeCode:
            self.__append_code(v)
        elif type(v) == str:
            self.codestring.append(v)
        else:
            raise TypeError('Invalid type.')
        return self

    def extend(self, a):
        for i in a:
            self.append(i)
        return self

    def __str__(self):
        return ''.join(map(str, self.codestring))

    def __repr__(self):
        return 'EscapedString(...)'
        

class Color:
    def __init__(self, hexcode=None, colortuple=None):
        if hexcode:
            self.__from_hex(hexcode)
        elif tuple:
            self.__from_tuple(colortuple)
        else:
            raise ValueError('No color provided.')

    def __float_from_int(self):
        self.float = SimpleColor(
            self.int.r / 256,
            self.int.g / 256,
            self.int.b / 256)

    def __from_hex(self, hexcode):
        if len(hexcode) == 7:
            r = hexcode[1:3]
            g = hexcode[3:5]
            b = hexcode[5:7]
        elif len(hexcode) == 4:
            r = hexcode[1:2]
            g = hexcode[2:3]
            b = hexcode[3:4]
            r += r
            g += g
            b += b
        else:
            raise ValueError('Invalid hex code.')
        self.int = SimpleColor(
            int(r, 16),
            int(g, 16),
            int(b, 16))
        self.__float_from_int()

    def __from_tuple(self, colortuple):
        self.int = SimpleColor(
            colortuple[0],
            colortuple[1],
            colortuple[2])
        self.__float_from_int()

    @property
    def hex(self):
        return ('#'
            + f'{self.int.r:02x}'
            + f'{self.int.g:02x}'
            + f'{self.int.b:02x}')

    @property
    def tuple(self):
        return (self.int.r, self.int.g, self.int.b)

    def __repr__(self):
        return f'{Color(hexcode={self.hex})}'


class TextColor:
    def __init__(self, escape_code, name, hexcode):
        self.color = Color(hexcode)
        self.name = name
        self.escape_code = EscapeCode(escape_code)

    def __repr__(self):
        return f'TextColor({repr(self.escape_code)}, {self.name}, {self.color.hex})'


class TextImage:
    def __init__(self, data, width):
        self.data = data
        self.width = width

    def __color_text(self, tc: TextColor):
        char = '█' if tc.escape_code.foreground else ' '
        return (tc.escape_code, char)

    def as_text(self):
        textual = map(self.__color_text, self.data)
        rows = split_every(self.width, textual)
        rows = map(
            lambda r: lfold(
                lambda v, x: v.extend(x),
                r, EscapedString()),
            rows)
        return '\n'.join(map(str, rows))


# 0 = clear
# 1 = bold
# 4 = underline

fg = [
    (30, 'gray', '#4F545C'),
    (31, 'red', '#DC322F'),
    (32, 'green', '#859900'),
    (33, 'marigold', '#B58900'),
    (34, 'blue', '#268BD2'),
    (35, 'magenta', '#D33682'),
    (36, 'teal', '#2AA198'),
    (37, 'white', '#FFF'),
    (38, 'default', '#B9BBBE')
]

bg = [
    (40, 'solarized', '#002B36'),
    (41, 'orange', '#CB4B16'),
    (42, 'satbluegray', '#586E75'),
    (43, 'bluegray', '#657B83'),
    (44, 'gray', '#839496'),
    (45, 'lavender', '#6C71C4'),
    (46, 'lightgray', '#93A1A1'),
    (47, 'white', '#FDF6E3'),
    (48, 'default', '#2F3136')
]


fg = itertools.starmap(TextColor, fg)
bg = itertools.starmap(TextColor, bg)
colors = list(itertools.chain(fg, bg))

invalid_color = TextColor(35, 'magenta', '#D33682')


def distance(c1, c2):
    r = (c2.int.r - c1.int.r)**2
    g = (c2.int.g - c1.int.g)**2
    b = (c2.int.b - c1.int.b)**2
    return r + g + b


def best_color(target, candidates):
    pairs = itertools.zip_longest(candidates, [], fillvalue=target)
    distances = map(
        lambda x: (x[0], distance(x[0].color, x[1])),
        pairs)
    best = functools.reduce(
        lambda v, x: x if x[1] < v[1] else v,
        distances,
        (None, math.inf))
    return best


def convert_python(image):
    data = image.getdata()
    data = map(lambda x: Color(colortuple=x), data)
    quantized = map(lambda x: best_color(x, colors), data)
    text = map(lambda x: x[0], quantized)
    return TextImage(text, image.width)


# This is the closest to black
# Used in the PIL convert function
black = TextColor(40, 'solarized', '#002B36')

reverse_dict = {c.color.hex: c for c in colors}


def get_palette():
    color_tuples = map(lambda x: x.color.tuple, colors)

    full_palette = itertools.islice(
        itertools.chain(
            color_tuples,
            itertools.repeat((0, 0, 0))
        ), 0, 256)

    color_palette = functools.reduce(lambda v, x: v + x, full_palette)
    color_palette = map(int, color_palette)
    palette = Image.new('P', (1, 1))
    palette.putpalette(color_palette)
    return palette


palette = get_palette()

def convert_pil(image, dither=Image.Dither.FLOYDSTEINBERG):
    image = image.convert('RGB')
    image = image.quantize(palette=palette, dither=dither)
    # Use invalid color of black since the palette has true black after the
    # textual colors.
    return convert_direct(image, black)


def convert_direct(image, extra=invalid_color):
    data = image.getdata()
    texts = map(lambda x: (colors + [extra])[min(x, len(colors))], data)
    return TextImage(texts, image.width)


def get_dimensions(width, height, image, char_ratio=0.47):
    if width and not height:
        height = round(width * (image.height / image.width) * char_ratio)
    elif height and not width:
        width = round(height * (image.width / image.height) * 1/char_ratio)
    elif not height and not width:
        width = round(image.width * 1/char_ratio)
        height = image.height
    
    return (width, height)


def main():
    import argparse

    converters = {
        'pil_floyd': convert_pil,
        'pil': lambda i, s: convert_pil(i, s, Image.NONE),
        'distance': convert_python,
        'direct': convert_direct
    }

    scalers = {
        'nearest': Image.Resampling.NEAREST,
        'box': Image.Resampling.BOX,
        'bilinear': Image.Resampling.BILINEAR,
        'hamming': Image.Resampling.HAMMING,
        'bicubic': Image.Resampling.BICUBIC,
        'lanczos': Image.Resampling.LANCZOS
    }

    parser = argparse.ArgumentParser(
        description="Convert images into Discord-compatible text art.")
    parser.add_argument('image')
    parser.add_argument('--width', type=int, default=None,
        help="Target width, if not specified, will be determined by height.")
    parser.add_argument('--height', type=int, default=None,
        help="Target height, if not specified, will be determined by width.")
    parser.add_argument('--char-ratio', type=float, default=0.47,
        help="Character ratio, corrects for characters being taller than they"
            + " are wide.")
    parser.add_argument('--quantizer', choices=converters.keys(),
        default='pil_floyd',
        help="Algorithm to convert colors to the palette."
            + " Use direct for images already in the palette.")
    parser.add_argument('--scaler', choices=scalers.keys(),
        default='bicubic',
        help="Downscaling algorithm. Use nearest for pixel art.")
    args = parser.parse_args()

    convert = converters[args.quantizer]
    scaler = scalers[args.scaler]

    image = Image.open(args.image)

    dimensions = get_dimensions(args.width, args.height, image, args.char_ratio)

    print(f'Using dimensions {dimensions}', file=sys.stderr)

    image = image.resize(dimensions, resample=scaler)

    text = convert_pil(image.resize(dimensions)).as_text()
    print(text)

    length_adjust = 8 + 4 # for the code block
    max_length = 2000 - length_adjust
    max_nitro_length = 4000 - length_adjust

    account_type = 'no'
    if len(text) < max_length:
        account_type = 'non-nitro'
    elif len(text) < max_nitro_length:
        account_type = 'nitro'

    print(EscapeCode(0).string, file=sys.stderr)

    print(f'Length: {len(text)} (sendable by {account_type} accounts)',
        file=sys.stderr)
    print(f'{len(text) / (dimensions[0] * dimensions[1]):.2f} equivalent bytes per pixel',
        file=sys.stderr)


if __name__ == '__main__':
    main()
