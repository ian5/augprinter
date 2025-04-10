import typing
from collections.abc import Collection
from PIL import Image
from loguru import logger
from loaders import open_image_cached, get_image 
from bodyitems import BodyItem

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

class RenderStep:
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
    def __init__(self, default: str|None = None, name: str|None = None, position: typing.Sequence[int] = (0,0), flags: Collection = set()) -> None: #TODO user friendly error handling
        self.name = name
        self.flags = set(flags)
        self.default = open_image_cached(default) if default is not None else None
        self.position = tuple(position)
    
    def draw(self, image: Image.Image, parameters: typing.Mapping=dict()) -> None:
        if self.name in parameters: # Handle when an argument is provided
            paste = parameters[self.name]
            if 'cache' in self.flags: 
                paste = open_image_cached(paste)
        else:
            if 'warn on default' in self.flags:
                logger.warning('No image provided for step {}, defaulting to {}'.format(self.name, self.default) if self.default is not None else 'No image provided for step {}, skipping'.format(self.name))
            if self.default is None:
                return   
            else:
                paste = self.default
        with get_image(paste, self.default) as layer:
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
        self.default = open_image_cached(default)
        self.position = tuple(position)
        self.spacing = spacing

    def draw(self, image: Image.Image, parameters: typing.Mapping=dict()) -> None:
            costx, costy = self.position
            for cost in parameters.get('costs', []):
                path, count, compact = cost
                if 'forceverbose' in self.flags:
                    compact = False
                elif 'forceterse' in self.flags:
                    compact = True
                img = open_image_cached(path) if 'cache' in self.flags else path
                with get_image(img, self.default) as icon:
                    if compact:
                        image.alpha_composite(icon, ((costx-(icon.width-1)),costy-(icon.height//2))) # vertically center the icon 
                        costx -= icon.width+5
                        for c in reversed('{}x'.format(count)):
                            char = open_image_cached('assets/builtin/{}.png'.format(c)) # always cache the numbers
                            image.alpha_composite(char, (costx,costy-4))
                            costx -= 6
                    else:
                        # verbose rendering
                        for i in range(count):
                            image.alpha_composite(icon, ((costx-(icon.width-1)),costy-(icon.height//2)))
                            costx -= icon.width-1
                costx -= self.spacing

class CardBody(RenderStep): #MARK: CardBody
    def __init__(self, size: typing.Sequence[int] = (-1, -1), name: str|None = None, position: typing.Sequence[int] = (0,0)):
        self.position = tuple(position)
        self.name = name
        self.size = tuple(size)
    
    def draw(self, image: Image.Image, parameters: typing.Mapping=dict()):
        children = parameters.get(self.name, [])
        sigilx, sigily = self.position

        for o in children:
            sigily += o.draw(image, self.position+self.size)