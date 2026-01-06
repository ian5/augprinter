import pytest
from printer import parse

@pytest.mark.parametrize('name,raw', [
    pytest.param(
        "eggs",
        {
            "contents": [
                {
                    "type": "sigil",
                    "id": "spam",
                    "name": "eggs",
                    "text": "Lorem ipsum dolor sit amet",
                    "icon": "test/assets/Sprinter.png"
                }]},
        id="direct_type"
    ),
    pytest.param(
        "eggs",
        {
            "default": {
                "type": "sigil",
            },
            "contents": [
                {
                    "id": "spam",
                    "name": "eggs",
                    "text": "Lorem ipsum dolor sit amet",
                    "icon": "test/assets/Sprinter.png"
                }]},
        id="default_type_inheritance"
    ),
    pytest.param(
        "eggs",
        {
            "default": {
                "type": "sigil",
            },
            "contents": [
                {
                    "id": "spam",
                    "name": "this should be shadowed",
                    "text": "Lorem ipsum dolor sit amet",
                    "icon": "test/assets/Sprinter.png"
                },
                {
                    "id": "spam",
                    "name": "eggs",
                    "text": "Lorem ipsum dolor sit amet",
                    "icon": "test/assets/Sprinter.png"
                }
                ]},
        id="shadowing"
    ),
    pytest.param(
        "eggs",
        {
            "default": {
                "name": "eggs",
            },
            "contents": [
                {   
                    "type": "group",
                    "default": {
                        "type": "sigil"
                    },
                    "contents": [
                        {
                            "id": "spam",
                            "text": "Lorem ipsum dolor sit amet",
                            "icon": "test/assets/Sprinter.png"
                        }]}]},  
        id="group_inheritance"
    ),
])
def test_sigil_loading(name, raw):
    context = parse.CardContext()
    context.load(raw)
    assert context.get_sigil("spam"), "get_sigil failed to return"
    assert context.get_sigil("spam").name == name, "get_sigil returned with incorrect name"

@pytest.mark.parametrize('fold,raw', [
    pytest.param(
        3,
        {
            "contents": [
                {
                    "type": "cost",
                    "id": "spam",
                    "icon": "test/assets/Blood.png",
                    "fold": 3
                }]},
        id="direct_type"
    ),
    pytest.param(
        3,
        {
            "default": {
                "type": "cost",
            },
            "contents": [
                {
                    "id": "spam",
                    "icon": "test/assets/Blood.png",
                    "fold": 3
                }]},
        id="default_type_inheritance"
    ),
    pytest.param(
        3,
        {
            "default": {
                "type": "cost",
            },
            "contents": [
                {
                    "id": "spam",
                    "icon": "test/assets/Blood.png",
                    "fold": 5
                },
                {
                    "id": "spam",
                    "icon": "test/assets/Blood.png",
                    "fold": 3
                }]},
        id="shadowing" 
    ),
    pytest.param(
        3,
        {
            "default": {
                "fold": 3,
            },
            "contents": [
                {   
                    "type": "group",
                    "default": {
                        "type": "cost"
                    },
                    "contents": [
                        {
                            "id": "spam",
                            "icon": "test/assets/Blood.png"
                        }]}]},  
        id="group_inheritance"
    ),
])
def test_cost_loading(fold, raw):
    context = parse.CardContext()
    context.load(raw)
    assert context.get_cost("spam"), "get_cost failed to return"
    assert context.get_cost("spam").fold == fold, "get_cost returned with incorrect fold"