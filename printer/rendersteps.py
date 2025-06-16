import typing
from collections.abc import Collection
from PIL import Image
from loguru import logger
from printer.loaders import open_image_cached, get_image 
from printer.bodyitems import BodyItem

# def draw_layer(image: Image.Image, items: typing.Sequence[dict], params: dict) -> None: #MARK: Draw Layer
#     for step in items:
#         step = typing.cast(dict, step)
#         match step['type']: #would this be better as more objects instead of a switch statement
#             # the answer is absolutely, right?
#             # i'll go through the code and make sure i'm not obviously fucking this up though
#             case 'paste': # Paste an image at a specified location
#                 identifier = step.get('name', None)
#                 flags = step.get('flags', {})
#                 if 'default' not in step: 
#                     logger.error('No default image provided for paste {}, skipping step'.format(identifier if identifier else 'Unnamed'))
#                     continue
#                 position = step.get('position', (0,0))
#                 default = step['default']

#                 default_image = open_image_cached(default)
#                 if identifier in params: # Handle when an argument is provided
#                     img = params[identifier]
#                     if 'cache' in flags: 
#                         img = open_image_cached(img)
#                 else:
#                     img = default_image
#                     if 'warn on default' in flags:
#                         logger.warning('No image provided for step {}, defaulting to {}'.format(step['name'], step['default']))
#                 with get_image(img, default=default_image) as layer:
#                     image.alpha_composite(layer,position)

#             case 'cost row':
#                 identifier = step['name']
#                 costx, costy = step['position']
#                 spacing = step.get('spacing', 2)
#                 costs = params.get(identifier, [])
#                 flags = step.get('flags', {})

#                 for cost in costs:
#                     path, count, compact = cost
#                     if 'forceverbose' in flags:
#                         compact = False
#                     elif 'forceterse' in flags:
#                         compact = True
#                     img = open_image_cached(path) if 'cache' in flags else path
#                     with get_image(img, default=open_image_cached('assets/builtin/costerror.png')) as icon:
#                         if compact:
#                             image.alpha_composite(icon, ((costx-(icon.width-1)),costy-(icon.height//2))) # vertically center the icon 
#                             costx -= icon.width+5
#                             for c in reversed('{}x'.format(count)):
#                                 char = open_image_cached('assets/builtin/{}.png'.format(c)) # always cache the numbers
#                                 image.alpha_composite(char, (costx,costy-4))
#                                 costx -= 6
#                         else:
#                             # verbose rendering
#                             for i in range(count):
#                                 image.alpha_composite(icon, ((costx-(icon.width-1)),costy-(icon.height//2)))
#                                 costx -= icon.width-1
#                     costx -= spacing

class RenderStep():
    """Base class for card rendering layers"""
    def __init__(self) -> None:
        pass

    def __repr__(self):
        return '{}{}'.format(type(self).__name__, str(self.__dict__))
    

class ImagePaste(RenderStep): #MARK: ImagePaste
    """Layer an image over the card at a specified location.

    RenderStep flags
        cache
            All images loaded by this renderstep will be cached, 
            instead of only the default image. 
        warn on default
            A warning will be logged if this step is printed without a
            set value.
    
    Parameters
    ----------
    default : str
        Path to the image to paste if none is set by parameters. If an ImagePaste has no default 
        and no provided image, it will render nothing.
    name : str
        Name that parameters can use to address this renderstep
    position : tuple[int, int]
        Position the top left corner of the image is drawn to
    flags : set
        A set; passing certain strings will cause additional behavior.
    """
    def __init__(self, default: str|None = None, name: str|None = None, 
                 position: typing.Sequence[int] = (0,0), 
                 flags: Collection = set()) -> None: 
        #TODO user friendly error handling
        self.name = name
        self.flags = set(flags)
        # If a default was provided, it might get used a lot, so cache it
        self.default = (open_image_cached(default) if default is not None 
                        else None)
        self.position = tuple(position)
    
    def draw(self, image: Image.Image, 
             parameters: typing.Mapping=dict()) -> None:
        # Check if this step is slated to have its content replaced
        if self.name in parameters:
            # If it is, that's what we're putting on the card
            overlay = parameters[self.name]
            # oh also cache it if we were told to
            if 'cache' in self.flags: 
                overlay = open_image_cached(overlay)
        else: # No image was provided for this step
            # Warn the user about the unspecified image if they asked us to
            if 'warn on default' in self.flags:
                logger.warning('No image provided for step {}, defaulting to {}'.format(self.name, self.default) 
                               if self.default is not None else 'No image provided for step {}, skipping'.format(self.name))
            # If we have a default, use that; if not, skip rendering entirely
            if self.default is not None:
                overlay = self.default
            else:
                return   
        # Open and apply the image to the card
        with get_image(overlay) as layer:
            image.alpha_composite(layer, self.position)

class ImageArray(RenderStep): #MARK: ImageArray
    """Draw an array of icons, collapsing them if they're too large.
    
    RenderStep flags
        cache
            All images loaded by this renderstep will be cached, 
            instead of only the default image. 
        forceverbose
            This array will always draw as many icons as requested, even
            if told otherwise.
        forceterse
            This array will always draw a single icon and a count, even if
            told otherwise.

    Parameters
    ----------
    default : str or None = None
        If provided, the icon to draw when an image is not found
    name : str = None
        Name that parameters can use to address this renderstep
    position : tuple[int, int] = (0,0)
        Position the top left corner of the array is drawn to
    flags : set = {}
        A set; passing certain strings will cause additional behavior.
    spacing : int = 2
        Amount of extra padding between icons in the array.
    """
    def __init__(self, default: str|None = None, name: str|None = None, position: typing.Sequence[int] = (0,0), flags: Collection = set(), spacing: int = 2) -> None:
        self.name = name
        self.flags = flags
        # If a default was provided, it might get used a lot, so cache it
        self.default = open_image_cached(default)
        self.position = tuple(position)
        self.spacing = spacing

    def draw(self, image: Image.Image, parameters: typing.Mapping=dict()) -> None:
            # The first icon is drawn where the renderstep is 
            iconx, icony = self.position
            # For each icon we're drawing
            for icon in parameters.get(self.name, []):
                # Unpack the information about the icon
                img, count, compact = icon
                # If we've been asked to ignore the compact option, do that
                if 'forceverbose' in self.flags:
                    compact = False
                elif 'forceterse' in self.flags:
                    compact = True
                # If we've been asked to, cache the icon's image
                img = open_image_cached(img) if 'cache' in self.flags else img
                # Open the image if we didn't cache it
                with get_image(img, self.default) as icon:
                    # Compact rendering
                    if compact:
                        # TODO: magic number cleanup
                        # Draw an icon centered vertically on the
                        # current position
                        image.alpha_composite(icon, ((iconx-(icon.width-1)),
                                                     icony-(icon.height//2)))
                        # not sure honestly TODO: come back to this and unfuck the comments
                        iconx -= icon.width+5
                        # We draw the digits right to left, so reverse them
                        for c in reversed('{}x'.format(count)):
                            # The digits will be used in every compact
                            # icon rendering, so we always cache them
                            char = open_image_cached('assets/builtin/{}.png'.format(c))
                            # Draw the number centered vertically
                            image.alpha_composite(char, (iconx,icony-4))
                            iconx -= 6
                    # Verbose rendering
                    else:
                        for i in range(count):
                            # Draw one icon centered vertically on the 
                            # renderstep position, the specified number of 
                            # times, shifting left each time.
                            image.alpha_composite(icon, ((iconx-(icon.width-1)),icony-(icon.height//2)))
                            iconx -= icon.width-1
                # Put space in between each different cost
                iconx -= self.spacing

class CardBody(RenderStep): #MARK: CardBody
    def __init__(self, size: typing.Sequence[int] = (-1, -1), name: str|None = None, position: typing.Sequence[int] = (0,0)):
        self.position = tuple(position)
        self.name = name
        self.size = tuple(size)
    
    def draw(self, image: Image.Image, parameters: typing.Mapping=dict()):
        # Get the list of body items this step has been told to render; if
        # none are provided, default to an empty list
        children = parameters.get(self.name, [])
        # Start drawing at the renderstep position
        itemx, itemy = self.position
        # For each body item
        for o in children:
            # Draw it, then move the next one down by the amount it returned.
            # We provide both the position and size of the bodyitem box, for 
            # items with mixed widths
            itemy += o.draw(image, (itemx, itemy)+self.size)