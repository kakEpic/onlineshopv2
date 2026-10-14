"""
Session-based Shopping Cart

Usage:
    from apps.cart.cart import Cart
    cart = Cart(request)
    cart.add(product, quantity=1)
    cart.remove(product)
    cart.clear()
"""
from decimal import Decimal

from django.conf import settings

from apps.products.models import Product


CART_SESSION_ID = 'cart'


class Cart:
    """
    A session-based shopping cart.
    """

    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def __iter__(self):
        """
        Iterate over the items in the cart and get products from DB.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        products_dict = {str(p.id): p for p in products}

        cart = self.cart.copy()
        for product_id, item in cart.items():
            if product_id in products_dict:
                item['product'] = products_dict[product_id]
                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['quantity']
                yield item

    def __len__(self):
        """
        Count total items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.

        Args:
            product: Product instance
            quantity: Number to add
            override_quantity: If True, replace quantity instead of adding
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.final_retail_price),
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        # Remove if quantity is 0 or less
        if self.cart[product_id]['quantity'] <= 0:
            del self.cart[product_id]

        self.save()

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        """
        Mark the session as modified to make sure it gets saved.
        """
        self.session.modified = True

    def clear(self):
        """
        Remove cart from session.
        """
        del self.session[CART_SESSION_ID]
        self.save()

    def get_total_price(self):
        """
        Calculate total price of all items in the cart.
        """
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def get_item_count(self):
        """
        Get total number of items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_items(self):
        """
        Get cart items with product objects.
        """
        return list(self)

    def is_empty(self):
        """
        Check if cart is empty.
        """
        return len(self.cart) == 0

    def update_quantity(self, product, quantity):
        """
        Update the quantity of a specific product.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            if quantity <= 0:
                self.remove(product)
            else:
                self.cart[product_id]['quantity'] = quantity
                self.save()

    def contains(self, product):
        """
        Check if a product is in the cart.
        """
        return str(product.id) in self.cart

    def get_item(self, product):
        """
        Get cart item for a specific product.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            item = self.cart[product_id].copy()
            item['product'] = product
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            return item
        return None
