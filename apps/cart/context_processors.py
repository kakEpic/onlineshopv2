"""
Context processor to make cart available in all templates.
"""
from .cart import Cart


def cart(request):
    """
    Context processor that adds cart to every template.
    """
    return {'cart': Cart(request)}
