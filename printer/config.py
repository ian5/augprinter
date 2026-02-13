import typing
from functools import partial
import yaml
from loguru import logger
from printer import bodyitems
from printer import rendersteps
from printer import text

def renderstep_constructor(
        # We need a *class* to construct an instance, so the type hint is odd
        renderstep: type[rendersteps.RenderStep], 
        loader: yaml.Loader | yaml.FullLoader | yaml.UnsafeLoader,
        node: yaml.MappingNode):
    """
    Construct a renderstep from a yaml specification; used by the yaml parser.

    Parameters
    ----------
    renderstep : rendersteps.RenderStep
        The render step class to instance
    loader : yaml.Loader | yaml.FullLoader | yaml.UnsafeLoader
        The yaml loader to handle the yaml parsing
    node : yaml.MappingNode
        The node containing parameters; usually passed by the library
    """
    # Convert the yaml node into a dictionary so we can use it 
    params = loader.construct_mapping(node, True)
    # Warning on non string keys should make mistakes easier to understand
    for k in (k for k in params.keys() if not isinstance(k, str)):
        logger.warning('Non string key {} in renderstep {} {}. Why did you do this?'.format(k, renderstep, params.get('name', 'with no name.')))
    # Strip non string keys to pass the renderstep as parameters
    params = {k: v for k, v in params.items() if isinstance(k, str)}
    return renderstep(**params)

# Tell pyyaml what the renderstep tags mean
def register_renderstep_constructor(name: str,
                                    factory: type[rendersteps.RenderStep]): 
    """Register a renderstep constructor with a yaml tag. 

    Parameters
    ----------
    name : str
        The tag to use for the renderstep type
    factory : RenderStep
        A function that creates a renderstep; will be provided the tag's
        children as parameters.
    """
    # A partial is used to set the body item this constructor will handle
    yaml.FullLoader.add_constructor(name, partial(renderstep_constructor, 
                                                  factory))

register_renderstep_constructor('!ImagePaste', rendersteps.ImagePaste)
register_renderstep_constructor('!ImageArray', rendersteps.ImageArray)
register_renderstep_constructor('!CardBody', rendersteps.CardBody)

# Annotations to help with using config items in other contexts
renderstep_styles : typing.Mapping[str, text.TextStyle] 
fonts : typing.Mapping[str, text.TextStyle]

def reload():
    # Importing this module lets a piece of code see the configuration data
    global config, format_schema, fonts, renderstep_styles
    # We only need the file itself until the yaml parser is done
    with open('config/config.yaml') as cfg:
        config = yaml.load(cfg, yaml.FullLoader)
    # The main config file tells us which format schema(s) to load
    # TODO: multiple format schemas (for addenda, mostly)
    format_schema = yaml.load(open('config/' + config['format_schema']),
                              yaml.FullLoader)

    fonts = {}
    # Fetch each text style
    for name, style in format_schema['text styles'].items():
        # ...instantiate it, and add it to our font registry
        fonts[name] = text.TextStyle(style, name) 

    # For each body item that has a set of default text styles in the config...
    for name, params in format_schema['body items'].items():
        # Get each of those defined styles...
        for target, style_name in params['text styles'].items():
            # And set them as the default style in that body item's class
            bodyitems.body_items[name].set_default_font(target, fonts[style_name])
    # For each text area witha a default label style...
    renderstep_styles = {}
    for name, style in format_schema['label styles'].items():
        # Fetch the TextStyle object and hold onto it.
        renderstep_styles[name] = fonts[style]
        

reload()
