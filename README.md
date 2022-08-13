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

## Copyright

Public domain (Unlicense).