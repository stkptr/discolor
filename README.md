# Discolor

*Convert any image into a low-resolution, color approximated textual
representation for use on Discord.*

Discolor is a converter for images that scales them down and converts them into
strings of spaces and full blocks with control sequence graphics rendition
([ANSI](https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters))
codes to change the text color. The text images can be displayed in Discord code
blocks by using `ansi` as the language (currently only supported on
browser/desktop).

## Examples

![Image of Tux the penguin compared to converted version](/ctux.png)

![Test pixel art image compared to converted version](/ctest.png)

## Usage

```
usage: discolor.py [-h] [--width WIDTH] [--height HEIGHT]
                   [--char-ratio CHAR_RATIO]
                   [--quantizer {pil_floyd,pil,distance,direct}]
                   [--scaler {nearest,box,bilinear,hamming,bicubic,lanczos}]
                   image

Convert images into Discord-compatible text art.

positional arguments:
  image

optional arguments:
  -h, --help            show this help message and exit
  --width WIDTH         Target width, if not specified, will be determined by
                        height.
  --height HEIGHT       Target height, if not specified, will be determined by
                        width.
  --char-ratio CHAR_RATIO
                        Character ratio, corrects for characters being taller
                        than they are wide.
  --quantizer {pil_floyd,pil,distance,direct}
                        Algorithm to convert colors to the palette. Use direct
                        for images already in the palette.
  --scaler {nearest,box,bilinear,hamming,bicubic,lanczos}
                        Downscaling algorithm. Use nearest for pixel art.
```

### Example usage

Convert pixel art made with the [palette](Discord-dark.gpl):  
`./discolor.py --quantizer direct --scaler nearest sprite.png`

Convert a photo:  
`./discolor.py --width 30 photo.jpeg`

Convert a photo and copy it to the clipboard:  
`./discolor.py --width 30 photo.jpeg | xclip -selection clipboard`


## How it works

Discolor first scales the image to an appropriate size. The size is determined
by user input, as well as (if one of width or height is not specified) the
aspect ratio of the characters used. This ensures pixels are square, even though
the underlying characters used are rectangular.

Once rescaled, it is quantized, reducing the color depth to match the amount of
colors available in the palette. This step may involve dithering, which adds
colored noise to blend colors into one another to attempt to increase the
perceived color depth.

Finally, the converted textual pixels are catenated together. This process is
smart, and makes sure that only changes to the color of the textual pixel
produce a corresponding escape code. Further, only escape code transitions that
require a reset (0m) will get one. Together, these greatly reduce the amount of
characters needed to display a given image.

## For best results

Ideally, your image will have as little *transitions* as possible.
A transition is when one color is changed for another along a row of pixels.
For instance, if a row alternates between blue and red every other pixel, it
will have a lot of transitions, whereas a solid green row will have none.

The catenation process can reduce the amount of characters used for a given row,
but only if it has few transitions. Rows of the same color can use the same
color introducer. Making your image use long stretches of the same color will
produce a smaller output than if it had transitions.

If you have an image that is not pre-quantized/posterized, the `pil` and
`distance` quantizers will produce output with the fewest transitions. Since
`pil_floyd` uses dithering, it will produce many transitions. For images with a
lot of color, this dithering process could greatly increase the final size.

For the best results, quantize your image before conversion to text. This can be
done by using the [GIMP color palette](/Discord-dark.gpl) and running a quantize
or posterize with that palette. You can experiment until you get a result with a
good balance of quality, size, and transitions. This can then be converted to
text with:

`./discolor.py --quantizer direct --scaler nearest image.png`

The direct quantizer directly converts colors into the palette, making invalid
ones pink/magenta. The nearest scaler prevents new colors from being added to
the final result.

## Copyright

Public domain (Unlicense).