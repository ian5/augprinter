import copy
from typing import Sequence
from loguru import logger
from PIL import Image
from PIL import ImageDraw
from loaders import open_font_cached 

class TextStyle:
    """Object that represents a way to render text; made of font layers
    """
    def __init__(self, layers: Sequence, name: str | None = None):
        self.name = name
        self.layers = []
        for layer in layers:
            style_layer = copy.copy(layer)
            style_layer['font'] = open_font_cached(style_layer['font'], style_layer['size'])
            style_layer['offset'] = tuple(style_layer.get('offset', (0,0)))
            style_layer['flags'] = set(style_layer.get('flags', set()))
            if 'color' in style_layer:
                style_layer['color'] = tuple(style_layer['color'])
            self.layers.append(style_layer)
    
    def print_line(self, text: str, img: ImageDraw.ImageDraw, pos: tuple[int, int], fill: tuple[int, int, int] = (0,0,0), **kwargs):
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
        posx, posy = pos
        for layer in self.layers:
            ox, oy = layer['offset']
            img.text((posx+ox, posy+oy), text, font=layer['font'], fill=layer.get('color', fill), **kwargs)
    
    def get_length(self, text: str) -> int:
        left_border, right_border = 0, 0
        for layer in self.layers:
            if 'ignore for width' in layer.get('flags', {}):
                continue
            width = layer['font'].getlength(text)
            offset_x, oy = layer['offset']
            left_border = min(left_border, offset_x)
            right_border = max(offset_x+width, right_border)
        return right_border-left_border

    def wrap(self, text: str, w: int, first_line_offset: int = 0) -> list[str]: #TODO: Replace with rich text handling
        """Split a string into a list of strings that each fit within a given horizontal space.
        
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
        
        logger.debug('wrapping string "{}" with style {}'.format(text, self.name))
        x = first_line_offset
        lines = []
        current_line = []
        for word in (n+' ' for n in text.split()): # Add a space to each word, to account for the one we ate in the split
            length = self.get_length(word)
            if x + length > w:
                x = 0
                lines.append(''.join(current_line))
                current_line = []
            x += length
            current_line.append(word)
        lines.append(''.join(current_line)) # We know there will always be at least one word on a line that isn't wrapped, because for a wrap to happen such a word must exist
        return lines