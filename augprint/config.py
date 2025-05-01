import typing
from functools import partial
import yaml
from yaml import FullLoader
from loguru import logger
import bodyitems
import rendersteps
import text

type RenderStepClass = typing.Type[rendersteps.RenderStep]

def renderstep_constructor(renderstep: RenderStepClass, loader: yaml.Loader | yaml.FullLoader | yaml.UnsafeLoader, node: yaml.Node):
    node = typing.cast(yaml.MappingNode, node)  
    params = loader.construct_mapping(node, True)
    for k, v in params.items(): #type checking thats only relevant if you really fuck up 
        if not isinstance(k, str):
            logger.warning('Non string key {} in renderstep {} {}. Why did you do this?'.format(k, renderstep, params.get('name', 'with no name.')))
    params = {k: v for k, v in params.items() if isinstance(k, str)} # and make it pass without breaking entirely
    return renderstep(**params)

# tell pyyaml what the renderstep tags mean
def register_renderstep_constructor(name: str, factory: RenderStepClass):   
    FullLoader.add_constructor(name, partial(renderstep_constructor, factory))

register_renderstep_constructor('!ImagePaste', rendersteps.ImagePaste)
register_renderstep_constructor('!ImageArray', rendersteps.ImageArray)
register_renderstep_constructor('!CardBody', rendersteps.CardBody)

def reload():
    global config, format_schema, fonts
    with open('config/config.yaml') as cfg:
        config = yaml.load(cfg, FullLoader)
    format_schema = yaml.load(open('config/' + config['format_schema']), FullLoader)
    fonts = {}

    # load fonts
    for name, style in format_schema['text styles'].items():
        fonts[name] = text.TextStyle(style, name)
    for name, params in format_schema['body items'].items():
        for target, style_name in params['text styles'].items():
            textstyle = fonts[style_name]
            bodyitems.DEFAULT_FONTS[name][target] = textstyle

reload()
