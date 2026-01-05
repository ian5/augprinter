import pytest
from printer import parse

def test_sigil_loading():
    context = parse.CardContext()
    context.load({
        "type": "sigils",
        "contents": [
            {"name": "spam",
            "text": "Lorem ipsum dolor sit amet",
            "icon": "test/assets/Sprinter.png"}
            ]
        })
    assert context.get_sigil("spam"), "get_sigil failed to return"
    # Using the icon because there's feasible contexts in which the text
    # changing could be correct
    assert context.get_sigil("spam").icon == "test/assets/Sprinter.png", "get_sigil returned with incorrect icon"

def test_cost_loading():
    context = parse.CardContext()
    context.load({
        "type": "costs",
        "contents": [
            {"name": "spam",
            "icon": "test/assets/Blood.png",
            "fold": 5}
            ]
        })
    assert context.get_cost("spam"), "get_cost failed to return"
    assert context.get_cost("spam").fold == 5, "get_cost returned with incorrect fold"

def test_cost_names():
    context = parse.CardContext()
    context.load({
        "type": "costs",
        "contents": [
            {"name": ["spam", "eggs"],
            "icon": "test/assets/Blood.png",
            "fold": 5}
            ]
        })
    assert context.get_cost("spam"), "First name failed to retrieve"
    assert context.get_cost("eggs"), "Second name failed to retrieve"
    assert context.get_cost("spam") == context.get_cost("eggs"), "Names return unequal costs"

def test_cost_shadowing():
    context = parse.CardContext()
    context.load({
        "type": "costs",
        "contents": [
            {"name": "spam",
            "icon": "test/assets/Blood.png",
            "fold": 5}
            ]
        })
    assert context.get_cost("spam").fold == 5, "Initial cost set failure"
    context.load({
        "type": "costs",
        "contents": [
            {"name": "spam",
            "icon": "test/assets/Blood.png",
            "fold": 3}
            ]
        })
    assert context.get_cost("spam").fold == 3, "Cost shadowing failure"