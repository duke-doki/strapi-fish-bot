import logging

import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, \
    CommandHandler, Filters

from strapi_fetcher import StrapiFetcher

_database = None

logger = logging.getLogger(__name__)


def start(update, context, fetcher):
    chat_id = update.message.chat_id
    send_menu_setup(context, chat_id, fetcher)
    return "HANDLE_MENU"


def handle_menu(update, context, fetcher):
    if update.callback_query:
        query = update.callback_query
        chat_id = query.message.chat_id
        query.answer()
        user_reply = query.data
        if user_reply == 'Моя корзина':
            send_cart_setup(context, chat_id, fetcher)
            return "HANDLE_CART"
        else:
            product_id = query.data
            product, image = fetcher.get_product_by_id(product_id)
            caption = product['data']['attributes']['Description']
            keyboard = [
                [InlineKeyboardButton('Назад', callback_data='Назад')],
                [InlineKeyboardButton('Добавить в корзину',
                                      callback_data=f'Добавить в корзину:{product_id}')],
                [InlineKeyboardButton('Моя корзина',
                                      callback_data='Моя корзина')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_photo(
                chat_id,
                photo=image,
                caption=caption,
                reply_markup=reply_markup
            )
            context.bot.delete_message(chat_id,
                                       message_id=query.message.message_id)
            return "HANDLE_DESCRIPTION"


def handle_description(update, context, fetcher):
    if update.callback_query:
        chat_id = update.callback_query.message.chat_id
        user_reply = update.callback_query.data

        if user_reply == 'Назад':
            send_menu_setup(context, chat_id, fetcher)
            return "HANDLE_MENU"
        elif 'Добавить в корзину' in user_reply:
            product_id = user_reply.split(':')[1]
            context.user_data['product_id'] = product_id
            keyboard = [
                [InlineKeyboardButton(
                    num,
                    callback_data=num)]
                for num in ['1', '5', '10']
            ]
            keyboard.append(
                [
                    InlineKeyboardButton('Моя корзина',
                                         callback_data='Моя корзина'),
                    InlineKeyboardButton('В меню',
                                         callback_data='В меню')
                ],
            )
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(
                chat_id,
                text='Выберите количество рыбы в кг:',
                reply_markup=reply_markup
            )
            return "HANDLE_QUANTITY"
        elif user_reply == 'Моя корзина':
            send_cart_setup(context, chat_id, fetcher)
            return "HANDLE_CART"


def handle_quantity(update, context, fetcher):
    if update.callback_query:
        query = update.callback_query
        chat_id = query.message.chat_id
        query.answer()
        user_reply = query.data
        if user_reply == 'Моя корзина':
            send_cart_setup(context, chat_id, fetcher)
            return "HANDLE_CART"
        elif user_reply == 'В меню':
            send_menu_setup(context, chat_id, fetcher)
            return "HANDLE_MENU"
        elif user_reply.isdigit():
            quantity = int(user_reply)
            product_id = context.user_data['product_id']
            fetcher.create_or_update_cart(chat_id, {product_id: quantity})
            context.bot.send_message(
                chat_id,
                text='Добавлено!',
            )
            send_menu_setup(context, chat_id, fetcher)
            return "HANDLE_MENU"


def handle_cart(update, context, fetcher):
    if update.callback_query:
        query = update.callback_query
        chat_id = query.message.chat_id
        query.answer()
        user_reply = query.data
        if user_reply == 'В меню':
            send_menu_setup(context, chat_id, fetcher)
            return "HANDLE_MENU"
        elif user_reply == 'Оплата':
            context.bot.send_message(
                chat_id,
                text='Пожалуйста, пришлите ваш email'
            )
            return "WAITING_EMAIL"
        elif 'Удалить' in user_reply:
            cart_product_id = user_reply.split(':')[1]
            fetcher.delete_cart_product(cart_product_id)
            context.bot.send_message(
                chat_id,
                text='Продукт успешно удален!'
            )
            send_menu_setup(context, chat_id, fetcher)
            return "HANDLE_MENU"


def waiting_email(update, context, fetcher):
    user_reply = update.message.text
    chat_id = update.message.chat_id
    email_response = fetcher.add_email_to_cart(chat_id, user_reply)
    if not email_response:
        context.bot.send_message(
            chat_id,
            text='Попробуйте еще раз'
        )
        return "WAITING_EMAIL"
    else:
        email = fetcher.get_email_by_id(chat_id)
        context.bot.send_message(
            chat_id,
            text=f'Почта {email} успешно сохранена'
        )
        send_menu_setup(context, chat_id, fetcher)
        return "HANDLE_MENU"


def send_menu_setup(context, chat_id, fetcher):
    products = fetcher.fetch_products()['data']
    keyboard = [
        [InlineKeyboardButton(
            product['attributes']['Title'],
            callback_data=product['id'])]
        for product in products
    ]
    keyboard.append(
        [InlineKeyboardButton('Моя корзина',
                              callback_data='Моя корзина')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id,
        text='Меню:',
        reply_markup=reply_markup
    )


def send_cart_setup(context, chat_id, fetcher):
    products = fetcher.get_cart_products_by_id(chat_id)
    if not products:
        message = 'Ваша корзина пуста'
    else:
        message = '\n'.join(
            [f'{product} - {info[1]} kg' for product, info in
             products.items()])

    keyboard = [
        [InlineKeyboardButton(
            f'Удалить {title}',
            callback_data=f'Удалить:{info[0]}')]
        for title, info in products.items()
    ]
    keyboard.append(
        [InlineKeyboardButton('В меню', callback_data='В меню')])
    keyboard.append(
        [InlineKeyboardButton('Оплата', callback_data='Оплата')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id,
        text=message,
        reply_markup=reply_markup
    )


def handle_users_reply(update, context, fetcher):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': lambda update, context: start(update, context, fetcher),
        'HANDLE_MENU': lambda update, context: handle_menu(update, context, fetcher),
        'HANDLE_DESCRIPTION': lambda update, context: handle_description(update, context, fetcher),
        'HANDLE_QUANTITY': lambda update, context: handle_quantity(update, context, fetcher),
        'HANDLE_CART': lambda update, context: handle_cart(update, context, fetcher),
        'WAITING_EMAIL': lambda update, context: waiting_email(update, context, fetcher),
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():
    global _database
    if _database is None:
        database_num = env.str("DB_NUM")
        database_host = env.str("DB_HOST")
        database_port = env.str("DB_PORT")
        _database = redis.Redis(host=database_host, port=database_port,
                                db=database_num)
    return _database


if __name__ == '__main__':
    env = Env()
    env.read_env()

    starapi_token = env.str('API_TOKEN')
    host = env.str('HOST', 'localhost')
    port = env.str('PORT', '1337')
    headers = {'Authorization': f'bearer {starapi_token}'}

    fetcher = StrapiFetcher(host, port, headers)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    token = env.str("TG_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CallbackQueryHandler(
            lambda update, context: handle_users_reply(
                update,
                context,
                fetcher
            )
        )
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            lambda update, context: handle_users_reply(
                update,
                context,
                fetcher
            )
        )
    )
    dispatcher.add_handler(
        CommandHandler(
            'start',
            lambda update, context: handle_users_reply(
                update,
                context,
                fetcher
            )
        )
    )
    updater.start_polling()
    updater.idle()
