from environs import Env


env = Env()
env.read_env()
starapi_token = env.str('API_TOKEN')
host = env.str('HOST', 'localhost')
port = env.str('PORT', '1337')
headers = {'Authorization': f'bearer {starapi_token}'}
