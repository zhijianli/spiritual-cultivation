# encoding:utf-8

import json
import os


config = {}


def get_dir(file=__file__):
    return os.path.dirname(file)


root_dir = get_dir()
config_path = f"{root_dir}/config.json"


def load_config():
    global config

    if not os.path.exists(config_path):
        raise Exception('配置文件不存在，请根据config-template.json模板创建config.json文件')

    config_str = read_file(config_path)
    # 将json字符串反序列化为dict类型
    config = json.loads(config_str)

def set_default() :
    load_config()

    if 'db_host' not in config :
        config['db_host'] = 'ai.menganhealth.cn'

    if 'db_name' not in config :
        config['db_name'] = 'webchat_dev'

    if 'db_user' not in config :
        config['db_user'] = 'admin'

    if 'db_password' not in config :
        config['db_password'] = '123456'

    if 'db_port' not in config :
        config['db_port'] = 3306

    if 'admin_phone' not in config :
        phones = [
            '13883372441'
        ]
        config['admin_phone'] = phones

    global  config_path
    with open(config_path, 'w') as f :
        json.dump(config, f, indent=4, ensure_ascii=False)


def get_root():
    return os.path.dirname(os.path.abspath( __file__ ))


def read_file(path):
    with open(path, mode='r', encoding='utf-8') as f:
        return f.read()


def conf():
    global config
    if len(config) == 0 :
        load_config()

    return config
