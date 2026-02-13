from typing import Sequence, cast
from loguru import logger
from PIL import ImageDraw
from printer.loaders import open_font_cached 
from collections import namedtuple


# Named tuple representing one layer of a text style
StyleLayer = namedtuple('StyleLayer', ('font', 'offset', 'flags', 'color'))

class TextStyle:
    """Object that represents a way to render text; made of font layers
    """
    def __init__(self, layers: Sequence, name: str | None = None):
        self.name = name
        self.layers = []
        self.ascent = 0
        # We need to pack the parameters from the config file into this object
        for layer in layers:
            # Open the font to use for this text layer
            font = open_font_cached(layer['font'], layer['size'])
            style_layer = StyleLayer(
                # We need to keep the font to use to print
                font,
                # If we were given one, save the layer offset; otherwise there
                # is no offset
                tuple(layer.get('offset', (0,0))),
                # If we were given any, save the layer flags
                set(layer.get('flags', set())),
                # If we were given one, set the color override for this layer.
                # Otherwise, the color is up to the caller.
                tuple(layer['color']) if 'color' in layer else None
            )
            # Unless we were told not to...
            if 'ignore for size' not in style_layer.flags:
                # Find this layer's ascent and check the ascent of the text 
                # style against it.
                ascent : int = style_layer.font.getmetrics()[0]
                # Push the ascent of the style up if the layer is too high
                self.ascent = min(style_layer.offset[0]+ascent, self.ascent)
            # Add the style layer to the style
            self.layers.append(style_layer)
    
    def print_line(self, text: str, img: ImageDraw.ImageDraw, 
                   pos: tuple[int, int], fill: tuple[int, int, int] = (0,0,0), 
                   **kwargs):
        """Draw styled text; passes extra args to ImageDraw.text()
        
        Parameters
        ----------
        img : ImageDraw
            The image draw object to print onto
        text : str
            The text to print
        pos : tuple[int, int]
            The position to draw the text
        color : tuple[int, int, int]
            The color to draw text in, given that no color is specified by
            the style.
        """
        # Unpack the position tuple for convenience
        posx, posy = pos
        # For each style layer...
        for layer in self.layers:
            ox, oy = layer.offset
            # If it was specified use the layer color instead of the line color
            color = fill if layer.color is None else layer.color
            # Draw it at the current position, plus its offset, with the right
            # color and font
            img.text((posx+ox, posy+oy), text, font=layer.font,
                      fill=color, **kwargs)
    
    def get_length(self, text: str) -> int:
        """Get length of a string in this style"""
        # We start with both borders at the start of the text
        left_border, right_border = 0, 0
        # For each style layer...
        for layer in self.layers:
            # Ignore it if it's ignored for this purpose (so that things like
            # dropshadows don't have to mess with text width)
            if 'ignore for size' in layer.flags:
                continue
            # Retrieve it's offsets
            offset_x, oy = layer.offset
            # Get the width of the text in this style layer's font
            width = layer.font.getlength(text)
            # If its offset to the left further than any previous layer, the 
            # offset becomes the new left border
            left_border = min(left_border, offset_x)
            # If its right border is farther right than the rightmost layer so
            # far, it becomes the new right border
            right_border = max(offset_x+width, right_border)
        # the width of a thing is the distance between the two sides of it
        return right_border-left_border
    
    #TODO: Replace with rich text handling
    def wrap(self, text: str, w: int, first_line_offset: int = 0) -> list[str]:
        """Split a string into a list of strings which fit a given width.
        
        Parameters
        ----------
        text : str
            The string to be split
        w : int
            The width of available space in pixels
        first_line_offset : int
            An offset to apply to the first line; negative values can be
            used as hanging indentation
        """
        
        # The first line can be indented (this is mostly to give room for 
        # rendering a sigil name seperately)
        x = first_line_offset
        lines = []
        current_line = []
        # Split the line by spaces, then add a space to each word, to account
        # for the one we ate in the split
        for word in (n+' ' for n in text.split()): 
            # Find the length of the word...
            length = self.get_length(word)
            # And if it's bigger than the remaining space on this line...
            if x + length > w:
                # We're done with this line; append it to the finished list
                lines.append(''.join(current_line))
                # Reset the current line
                current_line = []
                # And reset the space left on the current line
                x = 0
            # Whether it is or not, now we add that word's width to our current
            # line
            x += length
            # And add the word itself to the curret line.
            current_line.append(word)
        # We know there will always be at least one word on a line that isn't
        # wrapped, because for a wrap to happen, such a word must exist
        lines.append(''.join(current_line)) 
        return lines
    
class TextBox():
    """Rectangle that contains text """
    def __init__(self):
        return self