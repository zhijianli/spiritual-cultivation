import datetime
import logging
import json

from bussiness.db_manager import db
from common.const import *
from common.log import logger
from common.config import conf
from common.util import get_user_dir
import os
import base64


DEVICE_CONNECT = 'connect'
DEVICE_DISCONNECT = 'disconnect'
USER_TYPE_NORMAL = 'normal'
USER_TYPE_VIP = 'vip'

FREE_ALLOW_TEXT_COUNT = 10
FREE_ALLOW_IMAGE_COUNT = 2
FREE_ALLOW_GPT4 = 1

PAY_ALLOW_TEXT_COUNT = 200
PAY_ALLOW_IMAGE_COUNT = 10
PAY_ALLOW_GPT4 = 25
PAY_ALLOW_FILE_GPT3 = 10
PAY_ALLOW_FILE_GPT4 = 10


PAY_MONTH_SUBCRIBE = 1 
PAY_COUNT = 2

PACKAGE_TYPE_BASE = 1
PACKAGE_TYPE_PRO = 2
PACKAGE_TYPE_ADVANCE = 6
PACKAGE_TYPE_FILE_GPT3 = 8
PACKAGE_TYPE_FILE_GPT4 = 9


class UserManager:
    def __init__(self):
        self.db_ = db

        self.create_tables()

        self._add_column(T_DEVICE_CONNETION, 'first_time', type='datetime')

        return

    def _add_column(self, table, column, type, size=0):
        sql = f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = '{table}' AND column_name = '{column}'"
        rows = self.db_.query(sql)
        if rows[0][0] < 1:
            sql = f"ALTER TABLE {table} ADD COLUMN {column} "
            if type == 'int':
                sql += ' int '
            elif type == 'varchar':
                sql += f' varchar({size})'
            elif type == 'datetime':
                sql += f' datetime'
            else:
                logger.error(f'type:{type} is not surport')
                return

            sql += ' ;'
            self.db_.update(sql)

    def create_tables(self):
        try:
            # user info
            sql = f" create table if not exists {T_USER_INFO} ( " \
                  "user_id int PRIMARY KEY AUTO_INCREMENT," \
                  "phone_number varchar(16)," \
                  "password varchar(128)," \
                  "user_name varchar(64), " \
                  "type varchar(64), " \
                  "queried_count int, " \
                  "allow_count int, " \
                  "queried_image_count int default 0, " \
                  "allow_image_count int default 0, " \
                  "register_time datetime, " \
                  "INDEX index_phone_number(phone_number)" \
                  ")engine = InnoDB, charset = utf8;"
            self.db_.update(sql)

            # device connection info
            sql = f"create table if not exists {T_DEVICE_CONNETION} ( " \
                  "connection_id int PRIMARY KEY AUTO_INCREMENT," \
                  "ip varchar(64), " \
                  "location varchar(64), " \
                  "device_name varchar(128), " \
                  "device_id varchar(64), " \
                  "queried_count int, " \
                  "allow_count int, " \
                  "queried_image_count int default 0, " \
                  "allow_image_count int default 0, " \
                  "connect_state varchar(16), " \
                  "connect_time datetime, " \
                  "disconnect_time datetime, " \
                  "first_time datetime, " \
                  "share_user_id int" \
                  ")engine = InnoDB, charset = utf8;"
            self.db_.update(sql)

            # phone code
            sql = f"create table if not exists {T_CODE} ( " \
                  "code_id int PRIMARY KEY AUTO_INCREMENT," \
                  "phone_number varchar(16), " \
                  "code char(8), " \
                  "state varchar(32), " \
                  "send_time datetime, " \
                  "valid_time datetime, " \
                  "INDEX index_phone_number(phone_number)" \
                  ")engine = InnoDB, charset = utf8;"
            self.db_.update(sql)

            # login info manager
            sql = f" create table if not exists {T_LOGIN_INFO} ( " \
                  "login_id int PRIMARY KEY AUTO_INCREMENT, " \
                  "connection_id int, " \
                  "user_id int, " \
                  "state varchar(16), " \
                  "login_time datetime, " \
                  "logout_time datetime" \
                  ")engine = InnoDB, charset = utf8;"
            self.db_.update(sql)

            # chat record
            sql = f" create table if not exists {T_CHAT_RECORD} ( " \
                  "record_id int PRIMARY KEY AUTO_INCREMENT, " \
                  "connection_id int, " \
                  "user_id int, " \
                  "query varchar(2048), " \
                  "response varchar(2048), " \
                  "type char(16), " \
                  "query_time datetime, " \
                  "response_time datetime, " \
                  "INDEX index_connection_id(connection_id), " \
                  "INDEX index_user_id(user_id)" \
                  ")engine = InnoDB, charset = utf8;"
            self.db_.update(sql)

        except Exception as e:
            logger.error(e)

        return

    def _get_device_balance(self, data):
        response = {
            'state' : FAILED,
            'queried_count' : 0,
            'allow_count' : 0,
            'error_desc' : 'init'
        }

        try :
            sql = f"SELECT queried_count, allow_count FROM {T_DEVICE_CONNETION} WHERE \
                connection_id = {data['connection_id']} ;"
            rows = self.db_.query(sql)
            for row in rows :
                response['queried_count'] = row[0]
                response['allow_count'] = row[1]

            response['state'] = NORMAL
        except Exception as e :
            logger.error(f'get_device_balance error : {str(e)}')

        return response

    def _get_order_balance(self, order) :
        response = {
            'state': FAILED,
            'allow_count': 0,
            'allow_count_chatgpt': 0,
            'use_count_chatgpt' : 0,
            'allow_count_image': 0,
            'use_count_image' : 0,
            'allow_count_gpt4' : 0,
            'use_count_gpt4' : 0,
            'file_count_chatgpt' : 0,
            'file_count_gpt4' : 0,
            'file_use_chatgpt' : 0,
            'file_use_gpt4' : 0,
            'error_desc': 'perform ok'
        }

        try:
            if order['purchase_type'] == PAY_MONTH_SUBCRIBE:
                if order['package_type'] == PACKAGE_TYPE_BASE :
                    response['allow_count'] = PAY_ALLOW_TEXT_COUNT + FREE_ALLOW_GPT4 + FREE_ALLOW_IMAGE_COUNT
                    response['allow_count_chatgpt'] = PAY_ALLOW_TEXT_COUNT
                    response['allow_count_gpt4'] = FREE_ALLOW_GPT4
                    response['allow_count_image'] = FREE_ALLOW_IMAGE_COUNT
                    response['file_count_chatgpt'] = PAY_ALLOW_FILE_GPT3
                elif order['package_type'] == PACKAGE_TYPE_PRO :
                    response['allow_count'] = PAY_ALLOW_TEXT_COUNT + PAY_ALLOW_IMAGE_COUNT + FREE_ALLOW_GPT4
                    response['allow_count_chatgpt'] = PAY_ALLOW_TEXT_COUNT
                    response['allow_count_image'] = PAY_ALLOW_IMAGE_COUNT
                    response['allow_count_gpt4'] = FREE_ALLOW_GPT4
                    response['file_count_chatgpt'] = PAY_ALLOW_FILE_GPT3
                else :
                    response['allow_count'] = PAY_ALLOW_TEXT_COUNT + PAY_ALLOW_GPT4 + FREE_ALLOW_IMAGE_COUNT
                    response['allow_count_chatgpt'] = PAY_ALLOW_TEXT_COUNT
                    response['allow_count_gpt4'] = PAY_ALLOW_GPT4
                    response['allow_count_image'] = FREE_ALLOW_IMAGE_COUNT
                    response['file_count_gpt4'] = PAY_ALLOW_FILE_GPT4
            else:
                response['allow_count'] = order['chat_allow_num'] + order['painting_allow_num'] + order['gpt4_allow_num']
                response['allow_count_chatgpt'] = order['chat_allow_num']
                response['allow_count_image'] = order['painting_allow_num']
                response['allow_count_gpt4'] = order['gpt4_allow_num']
                response['use_count_image'] = order['painting_use_num']
                response['use_count_chatgpt'] = order['chat_use_num']
                response['use_count_gpt4'] = order['gpt4_use_num']

                if order['package_type'] == PACKAGE_TYPE_FILE_GPT3 :
                    response['file_count_chatgpt'] = order['file_allow_count']
                    response['file_use_chatgpt'] = order['file_use_count']
                elif order['package_type'] == PACKAGE_TYPE_FILE_GPT4 :
                    response['file_count_gpt4'] = order['file_allow_count']
                    response['file_use_gpt4'] = order['file_use_count']

        except Exception as e:
            logger.error(f'_get_order_balance error: {str(e)}')

        return response

    def _get_user_balance(self, data):
        response = {
            'state': FAILED,
            'queried_count': 0,
            'allow_count': 0,
            'allow_count_chatgpt': 0,
            'allow_count_image': 0,
            'allow_count_gpt4' : 0,
            'queried_count_chatgpt' : 0,
            'queried_count_image' : 0,
            'queried_count_gpt4' : 0,
            'file_allow_count_chatgpt' : 0,
            'file_use_count_chatgpt' : 0,
            'file_allow_count_gpt4' : 0,
            'file_use_count_gpt4' : 0,
            'type': 'normal',
            'error_desc': 'perform ok'
        }

        try:
            while True:
                # get user order
                orders = self._get_user_order(data)

                # get user or device query count today
                chat_count = self._get_today_chat_count(data)
                if len(chat_count) < 1:
                    response['state'] = FAILED
                    response['error_desc'] = 'query today count is error'
                    break

                text_count = chat_count[0]['text_count']
                image_count = chat_count[0]['image_count']
                recent_gpt4 = chat_count[0]['gpt4_count']
                today_gpt4 = chat_count[0]['today_gpt4']
                file_count_chatgpt = chat_count[0]['file_count_chatgpt']
                file_use_count_gpt4 = chat_count[0]['file_count_gpt4']

                response['state'] = NORMAL

                response['order'] = orders

                if len(orders) < 1:
                    response['allow_count'] = FREE_ALLOW_TEXT_COUNT + FREE_ALLOW_IMAGE_COUNT
                    response['allow_count_chatgpt'] = FREE_ALLOW_TEXT_COUNT
                    response['allow_count_image'] = FREE_ALLOW_IMAGE_COUNT
                    response['allow_count_gpt4'] = FREE_ALLOW_GPT4
                    if data['user_id'] == '-1' :
                        device_balance = self._get_device_balance(data)
                        response['allow_count'] = device_balance['allow_count']
                        response['allow_count_chatgpt'] = device_balance['queried_count']
                else:
                    response['type'] = 'vip'
                    for order in orders:
                        order_balance = self._get_order_balance(order)
                        response['allow_count'] += order_balance['allow_count']
                        response['allow_count_chatgpt'] += order_balance['allow_count_chatgpt']
                        response['allow_count_image'] += order_balance['allow_count_image']
                        response['allow_count_gpt4'] += order_balance['allow_count_gpt4']

                        response['queried_count_chatgpt'] += order_balance['use_count_chatgpt']
                        response['queried_count_image'] += order_balance['use_count_image']
                        response['queried_count_gpt4'] += order_balance['use_count_gpt4']

                        if order['package_type'] == PACKAGE_TYPE_ADVANCE :
                            today_gpt4 = recent_gpt4

                        response['file_allow_count_chatgpt'] += order_balance['file_count_chatgpt']
                        response['file_allow_count_gpt4'] += order_balance['file_count_gpt4']

                        response['file_use_count_chatgpt'] += order_balance['file_use_chatgpt']
                        response['file_use_count_gpt4'] += order_balance['file_use_gpt4']

                response['queried_count_chatgpt'] += text_count
                response['queried_count_image'] += image_count
                response['queried_count_gpt4'] += today_gpt4
                response['queried_count'] += response['queried_count_chatgpt'] + response['queried_count_image'] + response['queried_count_gpt4']
                response['file_use_count_chatgpt'] = file_count_chatgpt
                response['file_use_count_gpt4'] = file_use_count_gpt4

                response['state'] = NORMAL
                break
        except Exception as e:
            logger.error(f'get_user_balance error: {str(e)}')

        response['allow_count'] = response['allow_count_chatgpt'] + response['allow_count_image'] + response[
            'allow_count_gpt4']
        response['left_budget'] = response['allow_count'] - response['queried_count']
        response['left_chatgpt'] = response['allow_count_chatgpt'] - response['queried_count_chatgpt']
        response['left_image'] = response['allow_count_image'] - response['queried_count_image']
        response['left_gpt4'] = response['allow_count_gpt4'] - response['queried_count_gpt4']
        response['left_file_count_chatgpt'] = response['file_allow_count_chatgpt'] - response['file_use_count_chatgpt']
        response['left_file_count_gpt4'] = response['file_allow_count_gpt4'] - response['file_use_count_gpt4']

        return response

    def add_share_order(self, data):
        response = {
            'state': FAILED,
            'error_desc': 'perform ok'
        }

        try:
            if data['share_user_id'] != '-1' and data['share_user_id'] != '' :
                sql = f"update {T_DEVICE_CONNETION} set share_user_id = {data['share_user_id']} \
                where connection_id = {data['connection_id']};"
                self.db_.update(sql)

                sql = f"INSERT INTO {T_PAY_ORDERS} (user_id, package_type, purchase_type, start_date,\
                 end_date, pay_status, payment_source, chat_allow_num, painting_allow_num, \
                 created_at, updated_at, out_trade_no, total_amount, purchase_date, chat_use_num, \
                 painting_use_num, gpt4_allow_num, gpt4_use_num)  VALUES ({data['share_user_id']}, 5, 2, NOW(), NOW() + \
                 INTERVAL 1 YEAR, 1, 3, 30, 2, NOW(), NOW(), '', 0, NOW(), 0, 0, 0, 0); "
                self.db_.update(sql)
        except Exception as e:
            logger.error(f'get_user_balance error: {str(e)}')

        return response

    def admin_add_balance(self, data):
        response = {
            'state': FAILED,
            'error_desc': 'perform ok'
        }

        try:
            phone_numbers = conf().get('admin_phone')
            if data['phone_number'] not in phone_numbers :
                response['error_desc'] = f"phone number:{data['phone_number']} not admin"
                return response

            sql = f"select user_id from user_info where phone_number = '{data['phone_number']}';"
            rows = self.db_.query(sql)
            if len(rows) < 1 :
                response['error_desc'] = f"there is not phone num: {data['phone_numer']}"
                return response

            user_id = rows[0][0]
            sql = f"select id from pay_orders where user_id = {user_id} and purchase_type = 2 and \
            end_date > now() and pay_status = 1 limit 1;"
            rows = self.db_.query(sql)
            if len(rows) < 1:
                sql = f"INSERT INTO {T_PAY_ORDERS} (user_id, package_type, purchase_type, start_date,\
                                 end_date, pay_status, payment_source, chat_allow_num, painting_allow_num, \
                                 created_at, updated_at, out_trade_no, total_amount, purchase_date, chat_use_num, \
                                 painting_use_num, gpt4_allow_num, gpt4_use_num)  VALUES ({user_id}, 5, 2, NOW(), NOW() + \
                                 INTERVAL 1 YEAR, 1, 4, {data['chatgpt']}, {data['dall_e']}, NOW(), NOW(), '', 0, NOW(), 0, 0, {data['gpt4']}, 0); "
                self.db_.update(sql)
            else :
                order_id = rows[0][0]
                sql = f"update pay_orders set chat_allow_num = chat_allow_num + {data['chatgpt']}, painting_allow_num = painting_allow_num + {data['dall_e']}, gpt4_allow_num = gpt4_allow_num + {data['gpt4']} where id = {order_id};"
                self.db_.update(sql)

            if int(data['file_gpt3_5']) > 0 :
                sql = f"select id from pay_orders where user_id = {user_id} and package_type = {PACKAGE_TYPE_FILE_GPT3} and \
                            end_date > now() and pay_status = 1 limit 1;"
                rows = self.db_.query(sql)
                if len(rows) < 1:
                    sql = f"INSERT INTO {T_PAY_ORDERS} (user_id, package_type, purchase_type, start_date,\
                                                         end_date, pay_status, payment_source, chat_allow_num, painting_allow_num, \
                                                         created_at, updated_at, out_trade_no, total_amount, purchase_date, chat_use_num, \
                                                         painting_use_num, gpt4_allow_num, gpt4_use_num, file_allow_count)  VALUES ({user_id}, {PACKAGE_TYPE_FILE_GPT3}, 2, NOW(), NOW() + \
                                                         INTERVAL 1 YEAR, 1, 4, 0, 0, NOW(), NOW(), '', 0, NOW(), 0, 0, 0, 0, {data['file_gpt3_5']}); "
                    self.db_.update(sql)
                else :
                    order_id = rows[0][0]
                    sql = f"update pay_orders set file_allow_count = file_allow_count + {data['file_gpt3_5']} where id = {order_id};"
                    self.db_.update(sql)

            if int(data['file_gpt4']) > 0 :
                sql = f"select id from pay_orders where user_id = {user_id} and package_type = {PACKAGE_TYPE_FILE_GPT4} and \
                            end_date > now() and pay_status = 1 limit 1;"
                rows = self.db_.query(sql)
                if len(rows) < 1:
                    sql = f"INSERT INTO {T_PAY_ORDERS} (user_id, package_type, purchase_type, start_date,\
                                                         end_date, pay_status, payment_source, chat_allow_num, painting_allow_num, \
                                                         created_at, updated_at, out_trade_no, total_amount, purchase_date, chat_use_num, \
                                                         painting_use_num, gpt4_allow_num, gpt4_use_num, file_allow_count)  VALUES ({user_id}, {PACKAGE_TYPE_FILE_GPT4}, 2, NOW(), NOW() + \
                                                         INTERVAL 1 YEAR, 1, 4, 0, 0, NOW(), NOW(), '', 0, NOW(), 0, 0, 0, 0, {data['file_gpt4']}); "
                    self.db_.update(sql)
                else :
                    order_id = rows[0][0]
                    sql = f"update pay_orders set file_allow_count = file_allow_count + {data['file_gpt4']} where id = {order_id};"
                    self.db_.update(sql)

            response['state'] = NORMAL
        except Exception as e:
            logger.error(f'get_user_balance error: {str(e)}')

        return response

    def connect_device(self, data):
        device_info = {
            'state': NORMAL,
            'error_desc': 'ok',
            'type': 'normal',
            'queried_count': 0,
            'allow_count': 0,
            'queried_count_chatgpt': 0,
            'allow_count_image': 0,
            'new_device': False,
            'order': []
        }

        try:
            # check ip whether has connected 
            query_sql = f"SELECT * FROM {T_DEVICE_CONNETION} WHERE connection_id \
             = {data['connection_id']} or \
                (ip = '{data['ip']}' and disconnect_time > (NOW() - INTERVAL 30 MINUTE) ) ;"

            new_device = False
            result = self.db_.query(query_sql)
            if len(result) > 0:
                sql = f"update {T_DEVICE_CONNETION} set ip = '{data['ip']}', location = '{data['location']}', \
                connect_state = '{DEVICE_CONNECT}', connect_time = NOW(), disconnect_time = NOW() \
                where connection_id = {result[0][0]};"
                self.db_.update(sql)
            else:
                device_info['new_device'] = True
                new_device = True

                # 排除监控测试服务
                if '116' != data['user_id'] :
                    sql = f"insert into {T_DEVICE_CONNETION} (ip, location, device_name, \
                    device_id, queried_count, allow_count, connect_state, connect_time \
                    , disconnect_time, first_time) values ('{data['ip']}', '{data['location']}', '{data['device_name']}', \
                    '{data['device_id']}', 0, {DEVICE_ALLOW_COUNT}, '{DEVICE_CONNECT}', NOW(), NOW(), NOW()) "

                    self.db_.update(sql)

            sql = f"SELECT connection_id, queried_count, allow_count FROM {T_DEVICE_CONNETION} WHERE \
                (ip = '{data['ip']}' and connect_time > (NOW() - INTERVAL 1 MINUTE) ) ;"
            rows = self.db_.query(sql)
            row = rows[0]

            data['connection_id'] = row[0]
            device_info = self._get_user_balance(data)

            device_info['connection_id'] = row[0]
            device_info['new_device'] = new_device
        except Exception as e:
            logger.error('connect_device exception:')
            logger.error(e)
            device_info['state'] = FAILED
            device_info['error_desc'] = str(e)

        return device_info

    def account_login(self, data):
        response = {}

        try:
            # check ip whether has connected
            sql = f"select user_id, phone_number, user_name, password, queried_count, allow_count \
                  from {T_USER_INFO} where phone_number = '{data['phone_number']}'; "
            rows = self.db_.query(sql)
            if len(rows) < 1:
                response['state'] = 'invalid_account'
                response['error_desc'] = 'this phone number is not registered'
            else:
                row = rows[0]
                password = row[3]
                if password != data['password']:
                    response['state'] = 'invalid_password'
                    response['error_desc'] = 'password is error, you can find it by phone code'
                else:
                    response['state'] = NORMAL
                    response['error_desc'] = 'login success'

                    response['user_id'] = row[0]
                    response['phone_number'] = row[1]
                    response['user_name'] = row[2]
                    response['queried_count'] = row[4]
                    response['allow_count'] = row[5]

                data['user_id'] = row[0]
                self.longin(data)

        except Exception as e:
            logger.error('connect_device exception:')
            logger.error(e)
            response['state'] = FAILED
            response['error_desc'] = 'account_login perform error'

        return response

    def set_password(self, data):
        response = {
            "state": NORMAL,
            'error_desc': "perform successly"
        }

        try:
            sql = f"update {T_USER_INFO} set password = '{data['new_password']}' \
                where user_id = {data['user_id']}; "
            self.db_.update(sql)

        except Exception as e:
            logger.error('connect_device exception:')
            logger.error(e)
            response['state'] = FAILED
            response['error_desc'] = 'account_login perform error'

        return response

    def disconnect_device(self, data):
        action = {}

        try:
            sql = f"update {T_DEVICE_CONNETION} set connect_state = '{DEVICE_DISCONNECT}', disconnect_time = NOW() \
             where connection_id = {data['connection_id']};"
            self.db_.query(sql)
        except Exception as e:
            logger.error('disconnect_device exception:')
            logger.error(e)

        return action

    def save_code(self, data):
        status = 'ok'
        try:
            sql = f"insert into {T_CODE} \
                    (phone_number, code, state, send_time) \
                values \
                    ('{data['phone_number']}', '{data['code']}', 'send', NOW());"

            self.db_.update(sql)
        except Exception as e:
            logger.error('save_code exception:')
            logger.error(e)
            status = 'error'

        return status

    def valid_code(self, data):
        status = True
        try:
            sql = f"select * from {T_CODE} \
                    where \
                        phone_number = '{data['phone_number']}' and code = '{data['code']}' \
                            and send_time > (NOW() - INTERVAL 10 MINUTE);"

            rows = self.db_.query(sql)
            if len(rows) < 1:
                status = False
            else:
                sql = f"update {T_CODE} set state = 'valid', valid_time = NOW() " \
                      f"where phone_number = '{data['phone_number']}' \
                            and send_time > (NOW() - INTERVAL 10 MINUTE);"
                self.db_.update(sql)

        except Exception as e:
            logger.error('valid_code exception:')
            logger.error(e)
            status = False

        return status

    def register(self, data):
        try:
            sql = f"insert into {T_USER_INFO} \
                (phone_number, password, type, queried_count, allow_count, register_time) \
                values \
                    ('{data['phone_number']}', '{data['password']}', '{USER_TYPE_NORMAL}', 0, \
                        {DEVICE_ALLOW_COUNT}, NOW())"
            self.db_.update(sql)
        except Exception as e:
            logger.error('register except')
            logger.error(e)

    def login(self, data):
        response = {
            'state': FAILED,
            'error_desc': 'ok',
            'type': 'normal'
        }
        try:
            # select user info
            query_sql = f"select user_id, user_name, queried_count, allow_count , phone_number from {T_USER_INFO} \
                where \
                    phone_number = '{data['phone_number']}' ;"
            rows = self.db_.query(query_sql)

            # register auto
            if len(rows) < 1:
                response['state'] = INVALID_ACCOUNT
            else:
                row = rows[0]

                data['user_id'] = row[0]
                response = self._get_user_balance(data)

                # response['state'] = USER_TYPE_NORMAL
                response['user_id'] = row[0]
                response['user_name'] = row[1]
                # response['queried_count'] = row[2]
                # response['allow_count'] = row[3]
                response['phone_number'] = row[4]

                # insert a login record
                sql = f"insert into {T_LOGIN_INFO} \
                    (connection_id, user_id, state, login_time) \
                        values \
                            ({data['connection_id']}, {response['user_id']}, 'login', NOW());"
                self.db_.update(sql)

        except Exception as e:
            logger.error('longin exception:')
            logger.error(e)

        return response

    def longout(self, data):
        flag = False

        try:
            if '-1' != data['user_id']:
                sql = f"update {T_LOGIN_INFO} set state = 'logout', logout_time = NOW() \
                    where user_id = {data['user_id']} and state = 'login';"
                self.db_.update(sql)

            flag = True
        except Exception as e:
            logger.error('save action exception:')
            logger.error(e)

        return flag

    def chat(self, data):
        connection_id = -1

        try:
            sql = f"insert into {T_CHAT_RECORD} \
                (connection_id, user_id, query, response, type, query_time, response_time) \
                values \
                    ({data['connection_id']}, {data['user_id']}, '{data['prompt']}', '{data['response']}', \
                    '{data['type']}', '{data['query_time']}', '{data['response_time']}' );"

            self.db_.update(sql)

            sql =f"select record_id from {T_CHAT_RECORD} where connection_id = {data['connection_id']} and \
                query_time > now() - interval 3 minute order by query_time desc limit 1;"
            rows = self.db_.query(sql)
            connection_id = rows[0][0]
        except Exception as e:
            logger.error('save chat exception:')
            logger.error(e)

        return connection_id

    def _check_login_state(self, data):
        response = {
            'state': NORMAL,
            'error_desc': 'ok'
        }

        try:
            data['user_id'] = str(data['user_id'])
            if '-1' != data['user_id']:
                # check whether another device login or not
                sql = f"select connection_id from {T_LOGIN_INFO} where user_id = {data['user_id']} \
                               order by login_time desc limit {MAX_DEVICE_COUNT}; "
                rows = self.db_.query(sql)
                if len(rows) < 1:
                    response['state'] = ACCOUNT_NOT_LOGIN
                    response['error_desc'] = 'user_id失效，请重新注册或者登录'
                else:
                    out_of_count = True
                    for row in rows :
                        if int(data['connection_id']) == (row[0]):
                            out_of_count = False
                            break

                    if out_of_count is True :
                        response['state'] = ANOTHER_LOGIN
                        response['error_desc'] = f'已经超过{MAX_DEVICE_COUNT}台设备登录，当前设备下线！'
        except Exception as e:
            response['state'] = FAILED
            response['error_desc'] = str(e)

        return response

    def _get_user_order(self, data):
        order = []
        try:

            data['user_id'] = str(data['user_id'])
            if '-1' != data['user_id']:
                sql = f"select id, purchase_type, package_type, chat_allow_num, chat_use_num, painting_allow_num, \
                      painting_use_num, start_date, end_date , payment_source, gpt4_use_num, gpt4_allow_num, file_use_count, file_allow_count from {T_PAY_ORDERS} where user_id = {data['user_id']} and end_date > NOW() \
                      and  pay_status = 1 and (chat_allow_num > chat_use_num or painting_allow_num > painting_use_num or gpt4_allow_num > gpt4_use_num or file_allow_count > file_use_count) \
                        order by start_date asc;"

                rows = self.db_.query(sql)
                for row in rows:
                    data = {
                        'id': row[0],
                        'purchase_type': row[1],
                        'package_type': row[2],
                        'chat_allow_num': row[3],
                        'chat_use_num': row[4],
                        'painting_allow_num': row[5],
                        'painting_use_num': row[6],
                        'gpt4_use_num' : row[10],
                        'gpt4_allow_num' : row[11],
                        'start_date': row[7],
                        'end_date': row[8],
                        'pay_source' : row[9],
                        'file_use_count' : row[12],
                        'file_allow_count' : row[13]
                    }

                    order.append(data)
        except Exception as e:
            logging.error(f'get user order exception: {str(e)}')

        return order

    def _get_month_file_count(self, data) :
        file_count_chatgpt = 0
        file_count_gpt4 = 0

        try:
            data['user_id'] = str(data['user_id'])
            date_time = datetime.datetime.now()
            type_gpt3 = f'{TYPE_FILE}/{MODEL_GPT3_5}'
            type_gpt4 = f'{TYPE_FILE}/{MODEL_GPT4}'
            if data['user_id'] != '-1':
                sql = f"SELECT     COUNT(CASE WHEN type = '{type_gpt3}' THEN 1 ELSE NULL END) \
                AS file_count_chatgpt,     COUNT(CASE WHEN type = '{type_gpt4}' \
                THEN 1 ELSE NULL END) AS file_count_gpt4 FROM     chat_record WHERE \
                    query_time > '2023-05-01 00:00:00'     AND user_id = {data['user_id']};"
            else:
                sql = f"SELECT     COUNT(CASE WHEN type = '{type_gpt3}' THEN 1 ELSE NULL END) \
                        AS file_count_chatgpt,     COUNT(CASE WHEN type = '{type_gpt4}' \
                        THEN 1 ELSE NULL END) AS file_count_gpt4 FROM     chat_record WHERE \
                            query_time > '2023-05-01 00:00:00'     AND connection_id = {data['connection_id']};"

            rows = self.db_.query(sql)
            file_count_chatgpt = rows[0][0]
            file_count_gpt4 = rows[0][1]


        except Exception as e:
            logger.error(f'_get_month_file_count error: {str(e)}')

        return file_count_chatgpt, file_count_gpt4
    
    def _get_today_chat_count(self, data):
        chat_count = []
        try:
            data['user_id'] = str(data['user_id'])
            date_time = datetime.datetime.now()
            if data['user_id'] != '-1':
                sql = f"SELECT \
                        COUNT(CASE WHEN type = 'text' THEN 1 ELSE NULL END) AS num_queries,\
                        COUNT(CASE WHEN type = 'gpt-4' and (query_time > NOW() - INTERVAL 3 hour) THEN 1 ELSE NULL END) AS num_gpt4 , \
                        COUNT(CASE WHEN type = 'gpt-4' THEN 1 ELSE NULL END) AS today_num_gpt4 , \
                        COUNT(CASE WHEN type = 'image' THEN 1 ELSE NULL END) AS num_image\
                        FROM {T_CHAT_RECORD} \
                        WHERE query_time > '{date_time.year}-{date_time.month}-{date_time.day} 00:00:00' \
                         and user_id = {data['user_id']} ;"
            else:
                sql = f"SELECT \
                                        COUNT(CASE WHEN type = 'text' THEN 1 ELSE NULL END) AS num_queries,\
                                        COUNT(CASE WHEN type = 'gpt-4' and (query_time > NOW() - INTERVAL 3 hour) THEN 1 ELSE NULL END) AS num_gpt4 , \
                                        COUNT(CASE WHEN type = 'gpt-4' THEN 1 ELSE NULL END) AS today_num_gpt4 , \
                                        COUNT(CASE WHEN type = 'image' THEN 1 ELSE NULL END) AS num_image\
                                        FROM {T_CHAT_RECORD} \
                                        WHERE query_time > '{date_time.year}-{date_time.month}-{date_time.day} 00:00:00' \
                                         and connection_id = {data['connection_id']};"

            rows = self.db_.query(sql)
            for row in rows:
                tmp = {
                    'text_count': row[0],
                    'image_count': row[3],
                    'gpt4_count' : row[1],
                    'today_gpt4' : row[2]
                }
                chat_count.append(tmp)

            file_count_chatgpt, file_count_gpt4 = self._get_month_file_count(data)
            chat_count[0]['file_count_chatgpt'] = file_count_chatgpt
            chat_count[0]['file_count_gpt4'] = file_count_gpt4
        except Exception as e:
            logger.error(f'get today chat count error: {str(e)}')

        return chat_count

    def get_query_balance(self, data):
        response = {
            'state': FAILED,
            'queried_count': 0,
            'allow_count': 0,
            'queried_count_chatgpt': 0,
            'allow_count_chatgpt': 0,
            'queried_count_image': 0,
            'allow_count_image': 0,
            'queried_count_gpt4' : 0,
            'allow_count_gpt4' : 0,
            'file_allow_count_chatgpt' : 0,
            'file_use_count_chatgpt' : 0,
            'file_allow_count_gpt4' : 0,
            'file_use_count_gpt4' : 0,
            'order_id' : -1,
        }

        try:
            data['user_id'] = str(data['user_id'])
            order_type = PACKAGE_TYPE_BASE

            while True:
                response_tmp = self._check_login_state(data)
                if response_tmp['state'] != NORMAL:
                    response['state'] = response_tmp['state']
                    response['queried_count'] = 0
                    response['allow_count'] = 0
                    break

                # get user order
                orders = self._get_user_order(data)

                # get user or device query count today
                chat_count = self._get_today_chat_count(data)
                if len(chat_count) < 1:
                    response['state'] = FAILED
                    response['error_desc'] = 'query today count is error'
                    break

                text_count = chat_count[0]['text_count']
                image_count = chat_count[0]['image_count']
                gpt4_count = chat_count[0]['gpt4_count']
                today_gpt4 = chat_count[0]['today_gpt4']
                file_count_chatgpt = chat_count[0]['file_count_chatgpt']
                file_count_gpt4 = chat_count[0]['file_count_gpt4']

                # dispatch balance
                # 1. free account
                if len(orders) < 1:
                    response['order_id'] = -1
                    response['allow_count_chatgpt'] = FREE_ALLOW_TEXT_COUNT
                    response['allow_count_image'] = FREE_ALLOW_IMAGE_COUNT
                    response['allow_count_gpt4'] = FREE_ALLOW_GPT4

                    if data['user_id'] == '-1':
                        device_balance = self._get_device_balance(data)
                        text_count = device_balance['queried_count']
                        allow_count = device_balance['allow_count']

                        response['queried_count_chatgpt'] = text_count
                        response['allow_count_chatgpt'] = allow_count
                        response['queried_count_image'] = image_count
                        response['allow_count_image'] = FREE_ALLOW_IMAGE_COUNT
                        response['allow_count_gpt4'] = FREE_ALLOW_GPT4
                else:
                    for order in orders:
                        order_balance = self._get_order_balance(order)
                        response['allow_count_chatgpt'] += order_balance['allow_count_chatgpt']
                        response['allow_count_gpt4'] += order_balance['allow_count_gpt4']
                        response['allow_count_image'] += order_balance['allow_count_image']
                        response['file_allow_count_chatgpt'] += order_balance['file_count_chatgpt']
                        response['file_allow_count_gpt4'] += order_balance['file_count_gpt4']

                        if response['order_id'] != -1 :
                            continue

                        if data['model'] == MODEL_GPT3_5 and data['type'] == TYPE_TEXT:
                            if text_count < response['allow_count_chatgpt']:
                                response['order_id'] = order['id']
                        elif data['model'] == MODEL_GPT3_5 and data['type'] == TYPE_FILE :
                            if order['package_type'] == PACKAGE_TYPE_FILE_GPT3 or order['package_type'] == PACKAGE_TYPE_ADVANCE  :
                                if order['file_use_count'] < order['file_allow_count']:
                                    response['order_id'] = order['id']
                                    order_type = PACKAGE_TYPE_FILE_GPT3

                        elif data['model'] == MODEL_GPT4 and data['type'] == TYPE_TEXT:
                            if order['package_type'] == PACKAGE_TYPE_ADVANCE and gpt4_count < response['allow_count_gpt4'] :
                                response['order_id'] = order['id']
                                order_type = PACKAGE_TYPE_ADVANCE
                            elif today_gpt4 < response['allow_count_gpt4'] :
                                response['order_id'] = order['id']
                        elif data['model'] == MODEL_GPT4 and data['type'] == TYPE_FILE :
                            if order['package_type'] == PACKAGE_TYPE_FILE_GPT4 or order['package_type'] == PACKAGE_TYPE_ADVANCE :
                                if order['file_use_count'] < order['file_allow_count']:
                                    response['order_id'] = order['id']
                                    order_type = PACKAGE_TYPE_FILE_GPT4

                        elif data['model'] == MODEL_IMAGE and image_count < response['allow_count_image']:
                            response['order_id'] = order['id']

                if data['type'] == TYPE_TEXT:
                    if data['model'] == MODEL_GPT3_5 :
                        if text_count >= response['allow_count_chatgpt']:
                            response['state'] = BUDGET_OVER
                            response['error_desc'] = f'包月用户每天可提问{PAY_ALLOW_TEXT_COUNT}次（防止爬虫），更多用量请按次购买！'
                        else:
                            response['state'] = NORMAL
                    elif data['model'] == MODEL_GPT4 :
                        if order_type == PACKAGE_TYPE_ADVANCE :
                            today_gpt4 = gpt4_count
                            response['queried_count_gpt4'] = gpt4_count

                        if today_gpt4 >= response['allow_count_gpt4']:
                            response['state'] = BUDGET_OVER
                            response['error_desc'] = f'包月旗舰版用户GPT4，每两小时可提问{PAY_ALLOW_GPT4}次，其它情况每日免费2次GPT4，更多用量可购买更多次数'
                        else:
                            response['state'] = NORMAL
                elif data['type'] == TYPE_IMAGE :
                    if data['model'] == MODEL_IMAGE :
                        if image_count >= response['allow_count_image']:
                            response['state'] = BUDGET_OVER
                            response['error_desc'] = f'包月专业版用户画图，每每天可画图{PAY_ALLOW_IMAGE_COUNT}次，其它情况可购买更多次数!'
                        else:
                            response['state'] = NORMAL
                elif data['type'] == TYPE_FILE :
                        if order_type == PACKAGE_TYPE_FILE_GPT3 :
                            if response['file_use_count_chatgpt'] >= response['file_allow_count_chatgpt'] :
                                response['state'] = BUDGET_OVER
                                response['error_desc'] = f"gpt-3.5 文件提问余额已经用完({response['file_use_count_chatgpt']}/{response['file_allow_count_chatgpt']})，请充值文件提问次数"
                            else:
                                response['state'] = NORMAL
                        elif order_type == PACKAGE_TYPE_FILE_GPT4 :
                            if response['file_use_count_gpt4'] >= response['file_allow_count_gpt4'] :
                                response['state'] = BUDGET_OVER
                                response['error_desc'] = f"gpt-4 文件提问余额已经用完({response['file_use_count_gpt4']}/{response['file_allow_count_gpt4']})，请充值文件提问次数"
                            else:
                                response['state'] = NORMAL
                        else :
                            response['state'] = BUDGET_OVER
                            response[
                                'error_desc'] = f"请充值文件提问次数"

                response['queried_count'] = text_count + image_count + today_gpt4
                response['queried_count_chatgpt'] = text_count
                response['queried_count_image'] = image_count
                response['queried_count_gpt4'] = today_gpt4
                response['file_use_count_chatgpt'] = file_count_chatgpt
                response['file_use_count_gpt4'] = file_count_gpt4

                break
        except Exception as e:
            logger.error('get_query_balance action exception:')
            logger.error(e)

        response['allow_count'] = response['allow_count_chatgpt'] + response['allow_count_image'] + response[
            'allow_count_gpt4']
        response['left_budget'] = response['allow_count'] - response['queried_count']
        response['left_chatgpt'] = response['allow_count_chatgpt'] - response['queried_count_chatgpt']
        response['left_image'] = response['allow_count_image'] - response['queried_count_image']
        response['left_gpt4'] = response['allow_count_gpt4'] - response['queried_count_gpt4']
        response['left_file_count_chatgpt'] = response['file_allow_count_chatgpt'] - response['file_use_count_chatgpt']
        response['left_file_count_gpt4'] = response['file_allow_count_gpt4'] - response['file_use_count_gpt4']

        return response

    def update_balance(self, data, res_type):
        flag = False

        try:
            # if -1 != data['user_id'] :
            #     sql = f"update {T_USER_INFO} set queried_count = {data['queried_count']} \
            #            where user_id = {data['user_id']} ;"
            # else :
            sql = f"update {T_DEVICE_CONNETION} set queried_count = queried_count + 1 \
            where connection_id = {data['connection_id']};"
            self.db_.update(sql)

            col_name = 'chat_use_num'
            if res_type == TYPE_IMAGE :
                col_name = 'painting_use_num'
            elif res_type == MODEL_GPT4 :
                col_name = 'gpt4_use_num'
            elif res_type == TYPE_FILE :
                col_name = 'file_use_count'

            sql = f"update pay_orders set {col_name} = {col_name} + 1 \
                 where id = {data['order_id']};"
            self.db_.update(sql)

        except Exception as e:
            logger.error('update_balance  exception:')
            logger.error(e)

        return flag

    def modify_user_info(self, data):
        response = {
            'state': FAILED,
            'error_desc': 'modify_user_info error'
        }

        try:
            if data['phone_number'] != '':
                sql = f"update {T_USER_INFO} set phone_number = '{data['phone_number']}' where user_id = {data['user_id']}; "
                self.db_.update(sql)
            if data['user_name'] != '':
                sql = f"update {T_USER_INFO} set user_name = '{data['user_name']}' where user_id = {data['user_id']}; "
                self.db_.update(sql)
            if data['new_password'] != '':
                sql = f"update {T_USER_INFO} set password = '{data['new_password']}' where user_id = {data['user_id']}; "
                self.db_.update(sql)

            sql = f"select user_name, phone_number, queried_count, allow_count from {T_USER_INFO} where user_id \
                   = {data['user_id']}"
            rows = self.db_.query(sql)
            row = rows[0]

            response['state'] = NORMAL
            response['error_desc'] = 'perform ok'
            response['user_name'] = row[0]
            response['phone_number'] = row[1]
            response['queried_count'] = row[2]
            response['allow_count'] = row[3]
        except Exception as e:
            logger.error('modify_user_info action exception:')
            logger.error(e)

        return response

    def add_balance(self, data):
        response = {
            'state': FAILED,
            'error_desc': 'add_balance error'
        }

        try:
            sql = f"update {T_USER_INFO} set allow_count = allow_count + {DEVICE_ALLOW_COUNT} where user_id = {data['user_id']} \
                  and queried_count + {IMAGE_DECREASE_COUNT} >= allow_count; "
            self.db_.update(sql)

            sql = f"select user_name, phone_number, queried_count, allow_count from {T_USER_INFO} where user_id \
                   = {data['user_id']}"
            rows = self.db_.query(sql)
            row = rows[0]

            response['state'] = NORMAL
            response['error_desc'] = 'perform ok'
            response['user_name'] = row[0]
            response['phone_number'] = row[1]
            response['queried_count'] = row[2]
            response['allow_count'] = row[3]
        except Exception as e:
            logger.error('add_balance action exception:')
            logger.error(e)

        return response

    def delete_chat_history(self, data) :
            response = {
                'state': FAILED,
                'error_desc': 'delete_chat_history error'
            }

            try:
                for record_id in data['record_id'] :
                    sql = f"update {T_CHAT_RECORD} set status = 1 where record_id = {record_id};"
                    self.db_.update(sql)

                response['state'] = NORMAL
                logger.info('response1',response)
            except Exception as e:
                logger.error('delete_chat_history exception:')
                logger.error(e)

            return response
    

    def get_order_list(self, data):
            response = {
                'state': FAILED,
                'error_desc': 'get_order_list error'
            }

            try:
                sql = f"select id, purchase_type, package_type, chat_allow_num, chat_use_num, painting_allow_num, \
                      painting_use_num, start_date, end_date , payment_source, gpt4_use_num, gpt4_allow_num , created_at from {T_PAY_ORDERS} where user_id = {data['user_id']} and \
                      created_at > '{data['start']}' and created_at < '{data['end']}' \
                        order by created_at asc;"

                rows = self.db_.query(sql)
                order = []
                for row in rows:
                    data = {
                        'id': row[0],
                        'purchase_type': row[1],
                        'package_type': row[2],
                        'chat_allow_num': row[3],
                        'chat_use_num': row[4],
                        'painting_allow_num': row[5],
                        'painting_use_num': row[6],
                        'gpt4_use_num' : row[10],
                        'gpt4_allow_num' : row[11],
                        'start_date': row[7],
                        'end_date': row[8],
                        'pay_source' : row[9],
                        'created_at' : row[12]
                    }

                    order.append(data)

                response['order'] = order
                response['state'] = NORMAL

                logger.info('response1',response)
            except Exception as e:
                logger.error('get_order_list exception:')
                logger.error(e)

            return response

    def get_chat_history(self, data):
        response = {
            'state': FAILED,
            'error_desc': 'get_chat_history error'
        }

        user_id = data['user_id']
        connection_id = data['connection_id']
        try:
            if data['user_id'] != '-1' :
                sql = f"select record_id, query_time, query, response, type from {T_CHAT_RECORD} where (user_id = {data['user_id']} \
                                ) and status = 0 order by query_time desc limit {RECORD_PAGE_COUNT} offset {( int(data['page_no']) - 1) * RECORD_PAGE_COUNT };"

                rows = self.db_.query(sql)

                response['error_desc'] = 'perform ok'

                data = []
                for idx in range(len(rows) - 1, -1, -1):
                    row = rows[idx]
                    query_type = row[4]
                    query_type = query_type.replace(f'/{MODEL_GPT3_5}', '')
                    query_type = query_type.replace(f'/{MODEL_GPT4}', '')
                    query = row[2]
                    res_text = row[3]

                    if query_type == TYPE_FILE :
                        query_type = 'file'
                        query = json.loads(query)
                    elif query_type == MODEL_GPT4 :
                        query_type = 'text'
                    elif query_type == TYPE_TEXT:
                        query_type = 'text'
                    elif query_type == TYPE_IMAGE :
                        query_type = 'image'
                        user_dir = get_user_dir(user_id, connection_id)
                        file_path = os.path.join(user_dir, res_text)
                        if not os.path.exists(file_path) :
                            continue

                        # 读取图片文件
                        with open(file_path, 'rb') as file:
                            image_data = file.read()

                        # 编码为Base64
                        res_text = base64.b64encode(image_data).decode('utf-8')

                    tmp = {
                        'record_id' : row[0],
                        'time': str(row[1]),
                        'query': query,
                        'response': res_text,
                        'type': query_type
                    }
                        
                    data.append(tmp)

                response['data'] = data

                logger.info('response1',response)

            response['state'] = NORMAL
        except Exception as e:
            logger.error('get_chat_history exception:')
            logger.error(e)

        # 判断是否为测试用户，如果是测试用户，返回测试数据
        if user_id == '48' or connection_id == '1016':
            response['data'] = []

        return response


user_manager = UserManager()
