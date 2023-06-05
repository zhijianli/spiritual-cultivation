import os
import requests
from .const import *
from .log import logger
from .config import conf


def get_dir(file=__file__):
    return os.path.dirname(file)


def get_location_info(ip_address):
    response = requests.get(f"http://freeapi.ipip.net/{ip_address}")

    if response.status_code == 200:
        data = response.json()
        if data["status"] == "success":
            return data
        else:
            logger.error(f"Error: {data['message']}")
            return None
    else:
        logger.error(f"Error: HTTP status code {response.status_code}")
        return None


def create_session_id(req_data):
    # session_id = req_data['connection_id']
    # if req_data['user_id'] != '-1' and req_data['user_id'] != '':
    #    session_id = req_data['user_id']
    session_id = 111
    return session_id


def download_file(url, dst_file):
    res = True
    try:
        proxy = conf().get('proxy')
        proxys = proxy.replace('http', 'https')
    
        proxies = {
                'http': proxy,
                # 'https': proxys,
            }

        response = requests.get(url, stream=True, proxies=proxies)
        response.raise_for_status()
        with open(dst_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    except Exception as e:
        logger.error(f"download file:{dst_file}, from: {url} failed: {str(e)}")
        res = False
    
    return res

def get_user_dir(user_id, connection_id) :
    if user_id == '-1' :
        user_dir = os.path.join(DATA_DIR, user_dir, connection_id)
    else :
        user_dir = os.path.join(DATA_DIR, user_id)
    
    return user_dir