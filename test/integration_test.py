import pytest
import yaml
from helper import assert_image_equal_tofile
from printer import parse

@pytest.fixture()
def test_context_manager():
    parser = parse.DataParser()
    with open('test/assets/integration_testing_cards.yaml') as f:
        for doc in yaml.load_all(f, yaml.Loader):
            parser.parse(doc)
    return parser

@pytest.mark.parametrize('card_id,standard_image', [
    pytest.param('CostRender', 'test/example/cards/Cost Rendering.png', 
                 id='Cost Rendering'),
    pytest.param('SigilRender', 'test/example/cards/Sigil Rendering.png', 
                 id='Sigil Rendering'),
    pytest.param('TokenRender', 'test/example/cards/Token Rendering.png', 
                 id='Token Rendering'),
    pytest.param('ConditionalRender', 'test/example/cards/Conditional Rendering.png', 
                 id='Conditional Rendering'),
    pytest.param('TraitRender', 'test/example/cards/Trait Rendering.png', 
                 id='Trait Rendering'),
    pytest.param('DefaultTest', 'test/example/cards/Default Nesting.png', 
                 id='Default Nesting'),
])
def test_fullprocess(test_context_manager, card_id, standard_image):
    image = test_context_manager.print(card_id)
    assert_image_equal_tofile(image, standard_image)
