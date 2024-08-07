import json
from io import BytesIO

import requests


class StrapiFetcher:
    def __init__(self, host, port, headers):
        self.host = host
        self.port = port
        self.headers = headers

    def fetch_products(self):
        url = f'http://{self.host}:{self.port}/api/products'

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        products = response.json()
        return products

    def get_product_by_id(self, product_id):
        url = f'http://{self.host}:{self.port}/api/products/{product_id}'
        params = {'populate': 'Picture'}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        product = response.json()
        image_url = \
        product['data']['attributes']['Picture']['data'][0]['attributes']['url']
        image_url = f'http://{self.host}:{self.port}{image_url}'
        image = self.download_image(image_url, product_id)
        return product, image

    def download_image(self, url, pic_id):
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        image_data = BytesIO(response.content)
        return image_data

    def create_or_update_cart(self, chat_id, products: dict):
        url = f'http://{self.host}:{self.port}/api/carts'
        params = {'filters[chat_id][$eq]': chat_id, 'populate': '*'}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        response_cart = response.json()

        self.headers['Content-Type'] = 'application/json'
        product_carts_ids = []
        for product_id, product_quantity in products.items():
            product_cart = self.create_product_cart(product_id, product_quantity)
            product_cart_id = product_cart['data']['id']
            product_carts_ids.append(product_cart_id)
        cart_products = {
            'connect': [
                product_cart_id for product_cart_id in product_carts_ids
            ]
        }

        if not response_cart['data']:
            data = {
                'data': {
                    'chat_id': str(chat_id),
                    'cart_products': cart_products
                }
            }
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(data)
            )
        else:
            cart_id = response_cart['data'][0]['id']
            data = {
                'data': {
                    'cart_products': cart_products
                }
            }
            url = f'{url}/{cart_id}'
            response = requests.put(
                url,
                headers=self.headers,
                data=json.dumps(data)
            )
        response.raise_for_status()

        return response.json()

    def create_product_cart(self, product_id, quantity=1):
        url = f'http://{self.host}:{self.port}/api/cart-products'
        self.headers['Content-Type'] = 'application/json'
        data = {
            'data': {
                'product': product_id,
                'quantity': quantity
            }
        }
        response = requests.post(
            url,
            headers=self.headers,
            data=json.dumps(data)
        )
        response.raise_for_status()

        return response.json()

    def get_cart_products_by_id(self, chat_id):
        url = f'http://{self.host}:{self.port}/api/carts'
        params = {'filters[chat_id][$eq]': chat_id, 'populate': '*'}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        cart = response.json()
        if cart['data']:
            cart_products_ids = [
                cart['id'] for cart in cart['data'][0]['attributes']['cart_products']['data']
            ]
            cart_products_quantity = [
                cart['attributes']['quantity'] for cart in
                cart['data'][0]['attributes']['cart_products']['data']
            ]
            ids_with_quantity = dict(zip(cart_products_ids, cart_products_quantity))
        else:
            return None

        products = {}
        for product_id, quantity in ids_with_quantity.items():
            cart_product = self.get_cart_product_by_id(product_id)
            product_title = cart_product['data']['attributes']['product']['data']['attributes']['Title']
            products[product_title] = [product_id, quantity]

        return products

    def get_cart_product_by_id(self, cart_product_id):
        url = f'http://{self.host}:{self.port}/api/cart-products/{cart_product_id}'
        params = {'populate': '*'}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        cart_product = response.json()
        return cart_product

    def delete_cart_product(self, cart_product_id):
        url = f'http://{self.host}:{self.port}/api/cart-products/{cart_product_id}'
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()

        cart_product = response.json()
        return cart_product

    def add_email_to_cart(self, chat_id, email):
        url = f'http://{self.host}:{self.port}/api/carts'
        params = {'filters[chat_id][$eq]': chat_id, 'populate': '*'}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        response_cart = response.json()

        cart_id = response_cart['data'][0]['id']
        self.headers['Content-Type'] = 'application/json'
        data = {
            'data': {
                'email': email
            }
        }
        url = f'{url}/{cart_id}'
        response = requests.put(
            url,
            headers=self.headers,
            data=json.dumps(data)
        )
        response.raise_for_status()
        email_response = response.json()
        if 'error' in email_response:
            return None
        else:
            return email_response

    def get_email_by_id(self, chat_id):
        url = f'http://{self.host}:{self.port}/api/carts'
        params = {'filters[chat_id][$eq]': chat_id, 'populate': '*'}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        cart = response.json()
        email = cart['data'][0]['attributes']['email']

        return email
