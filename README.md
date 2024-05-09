# Fish seller strapi-bot

A simple script that allows you to sell fish via telegram bot.

## Environment

### Requirements

Python3 should be already installed. 
Then use `pip` (or `pip3`, if there is a conflict with Python2) to install dependencies:
```bash
pip install -r requirements.txt
```

### Environment variables

- TG_TOKEN
- DB_HOST
- DB_PORT
- DB_NUM

1. Put `.env` file in root directory.
2. `.env` contains text data without quotes.

For example, if you print `.env` content, you will see:

```bash
$ cat .env
TELEGRAM_TOKEN=7026667473:AAE...
DB_HOST=localhost
DB_PORT=6379
DB_NUM=0
```

#### How to get

Create a chatbot to get its token with [BotFather](https://telegram.me/BotFather). Install Redis local database
[here](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/).

### Install strapi

Fork strapi from [here](https://github.com/duke-doki/strapi-fish). Follow [this](https://github.com/strapi/strapi)
instructions to set up environment.

```bash
yarn develop
```


### Run

Launch on Linux(Python 3) or Windows:
```bash
python strapi_bot.py
```

## Project Goals

The code is written for educational purposes on online-course for web-developers [dvmn.org](https://dvmn.org/).
 
