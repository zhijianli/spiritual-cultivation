import time

from .db_manager import db
from common.const import *
from common.log import logger
from datetime import datetime


T_ADMIN = 'admin'
T_DEVICE_USAGE = 'device_usage'
T_PAY_ORDERS = 'pay_orders'


class Statistic :
    def __init__(self) :
        self.db_ = db
        self._create_tables()

        self._add_admin('13883372441', '123456')
    
    def _create_tables(self):
        try:
            # create admin info
            sql = f" create table if not exists {T_ADMIN} ( " \
                  "user_id int PRIMARY KEY AUTO_INCREMENT, " \
                  "phone_number varchar(32) UNIQUE, " \
                  "password varchar(128), " \
                  "level char(32) " \
                  ")engine = InnoDB, charset = utf8;"
            self.db_.update(sql)

            # create device resource
            sql = f" create table if not exists {T_DEVICE_USAGE} ( " \
                  "usage_id int PRIMARY KEY AUTO_INCREMENT, " \
                  "cpu float, " \
                  "per_cpu varchar(256), " \
                  "mem_used float, " \
                  "mem_total float, " \
                  "swap_used float, " \
                  "swap_total float, " \
                  "disk_used float, " \
                  "disk_total float, " \
                  "net_recv float, " \
                  "net_sent float, " \
                  "collect_time datetime " \
                  ")engine = InnoDB, charset = utf8;"
            self.db_.update(sql)

        except Exception as e :
            logger.error(e)

        return
    
    def _add_admin(self, phone, password) :
        sql = f"select * from {T_ADMIN} where phone_number = '{phone}';"
        rows = self.db_.query(sql)
        if len(rows) < 1 :
            sql = f"insert into {T_ADMIN} (phone_number, password, level) values \
                ('{phone}', '{password}', 'normal'); "
            self.db_.update(sql)

    def login_admin(self, data) :
        response = {
            'state': FAILED,
            'error_desc': 'login_admin error'
        }

        try:
            sql = f"select user_id from  {T_ADMIN} where phone_number = '{data['phone_number']}' \
                and password = '{data['password']}'; "
            rows = self.db_.query(sql)

            if len(rows) < 1 :
                response['state'] = FAILED,
                response['error_desc'] = 'phone_number or password is error'
            else :
                row = rows[0]

                response['state'] = NORMAL
                response['error_desc'] = 'perform ok'
                response['user_id'] = str(row[0])
        except Exception as e:
            logger.error('login_admin exception:')
            logger.error(e)

        return response

    def _exist_admin(self, data) :
        exist = False

        try:
            sql = f"select * from {T_ADMIN} where user_id = {int(data['user_id'])};"
            rows = self.db_.query(sql)
            if len(rows) > 0 :
                exist = True
        except Exception as e:
            logger.error('_exist_admin exception:')
            logger.error(e)

        return exist
    
    def statistic_computer_usage(self, data) :
        response = {
            'state': FAILED,
            'error_desc': 'statistic_computer_usage error'
        }

        try:
            if self._exist_admin(data) :

                # sql = f"select cpu, mem_used, mem_total, swap_used, swap_total, disk_used, \
                #     disk_total, net_recv, net_sent, collect_time from \
                #           {T_DEVICE_USAGE} where collect_time > '{data['start_time']}' \
                #             and collect_time < '{data['end_time']}'; "
                types = data['type']
                sql = f"select collect_time , {types} from \
                          {T_DEVICE_USAGE} where collect_time >= '{data['start_time']}' \
                            and collect_time <= '{data['end_time']}'; "
                rows = self.db_.query(sql)
                datas = []
                for row in rows :
                    datas.append(list(row))

                response['data'] = rows
                response['error_desc'] = 'perform ok'
                response['state'] = NORMAL
            else :
                response['error_desc'] = f"admin id : {data['user_id']} is not exist"
                response['state'] = FAILED
        except Exception as e:
            logger.error('statistic_computer_usage exception:')
            logger.error(e)

        return response
    
    def statistic_user(self, data) :
        response = {
            'state': FAILED,
            'error_desc': 'statistic_user error'
        }

        try:
            if self._exist_admin(data) :
                user_level = data['user_level']
                duration = data['duration']
                start_time = data['start_time']
                end_time = data['end_time']

                if user_level == 'device_add' or user_level == 'device_connect' :
                    table_name = T_DEVICE_CONNETION
                    if user_level == 'device_add' :
                        column_name = 'first_time'
                    else :
                        column_name = 'connect_time'
                elif user_level == 'user_add' :
                    table_name = T_USER_INFO
                    column_name = 'register_time'
                else :
                    table_name = T_CHAT_RECORD
                    column_name = 'query_time'

                if duration == 'minute':
                    sql = f"SELECT DATE_FORMAT({column_name}, '%Y-%m-%d %H:%i:00') AS hour, \
                                               COUNT(*) AS num_connections \
                                                FROM {table_name} \
                                                WHERE {column_name} >= '{start_time}' AND {column_name} <= '{end_time}' \
                                                GROUP BY hour order by hour asc;"
                elif duration == 'hour' :
                    sql = f"SELECT DATE_FORMAT({column_name}, '%Y-%m-%d %H:00:00') AS hour, \
                           COUNT(*) AS num_connections \
                            FROM {table_name} \
                            WHERE {column_name} >= '{start_time}' AND {column_name} <= '{end_time}' \
                            GROUP BY hour order by hour asc;"
                else :
                    sql = f"SELECT DATE({column_name}) AS date, COUNT(*) AS num_connections \
                                               FROM {table_name} \
                                               WHERE {column_name} >= '{start_time}' AND {column_name} <= '{end_time}' \
                                               GROUP BY date order by date asc;"
                
                rows = self.db_.query(sql)
                data = []
                for row in rows :
                    row = list(row)
                    date_time = row[0]
                    if isinstance(date_time, str) :
                        date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")

                    if duration == 'hour' :
                        need_time = f'{date_time.day} {date_time.hour}'
                    elif duration == 'minute' :
                        need_time = f'{date_time.hour}:{date_time.minute}'
                    else :
                        need_time = f'{date_time.month}-{date_time.day}'

                    data.append([need_time, row[1]])

                response['data'] = data
                response['error_desc'] = 'perform ok'
                response['state'] = NORMAL
            else :
                response['error_desc'] = f"admin id : {data['user_id']} is not exist"
                response['state'] = FAILED
        except Exception as e:
            logger.error('add_balance action exception:')
            logger.error(e)

        return response
    
    def statistic_cost(self, data) :
        response = {
            'state': FAILED,
            'error_desc': 'add_balance error'
        }

        try:
            if self._exist_admin(data) :
                type = data['type']
                types = '('
                if type == 'all' :
                     types += 'text, image'
                     types += ')'
                elif type == 'text' :
                    types += 'text'
                    types += ')'
                else :
                    types += 'image'
                    types += ')'
                
                show_format = data['show_format']
                start_time = data['start_time']
                start_time = start_time.replace('：', ':')

                end_time = data['end_time']
                end_time = end_time.replace('：', ':')

                duration = data['duration']
                time_format = '%y-%m-%d 00:00:00'
                if duration == 'hour' :
                    time_format = '%y-%m-%d %H:00:00'
                elif duration == 'minute' :
                    time_format = '%y-%m-%d %H:%I:00'

                sql = f"SELECT DATE_FORMAT(query_time, '{time_format}') AS hour, \
                                               SUM(CHAR_LENGTH(query) + CHAR_LENGTH(response)) AS word_count,\
                                               COUNT(CASE WHEN type = 'text' THEN 1 ELSE NULL END) AS num_queries,\
                                               COUNT(CASE WHEN type = 'image' THEN 1 ELSE NULL END) AS num_image\
                                                FROM {T_CHAT_RECORD}\
                                                WHERE query_time > '{start_time}' AND query_time < '{end_time}'\
                                                GROUP BY hour order by hour asc;"

                datas = self.db_.query(sql)
                rows = []

                per_word_price = 0.002 / 750 * 7
                per_image_price = 0.018 * 7
                str_format = ''
                str_format = "%y-%m-%d %H:%M:%S"

                for data in datas:
                    word_count = int(data[1])
                    text_count = data[2]
                    image_count = data[3]

                    row = list(data)
                    date_time = row[0]
                    if isinstance(date_time, str) :

                        date_time = datetime.strptime(date_time, str_format)

                    if duration == 'hour':
                        need_time = f'{date_time.day} {date_time.hour}'
                    elif duration == 'minute':
                        need_time = f'{date_time.hour}:{date_time.minute}'
                    else :
                        need_time = f'{date_time.month}-{date_time.day}'

                    if show_format == 'query_word_count':
                        rows.append([need_time, word_count])
                    elif show_format == 'query_count' :
                        if type == 'all' :
                            rows.append([need_time, text_count + image_count])
                        elif type == 'text' :
                            rows.append([need_time, text_count])
                        else :
                            rows.append([need_time, image_count])
                    else :
                        if type == 'all' :
                            money = word_count * per_word_price + image_count * per_image_price
                            rows.append([need_time, money])
                        elif type == 'text' :
                            money = word_count * per_word_price
                            rows.append([need_time, money])
                        else :
                            money = image_count * per_image_price
                            rows.append([need_time, money])

                response['data'] = rows
                response['error_desc'] = 'perform ok'
                response['state'] = NORMAL
            else :
                response['error_desc'] = f"admin id : {data['user_id']} is not exist"
                response['state'] = FAILED
        except Exception as e:
            logger.error('add_balance action exception:')
            logger.error(e)

        return response
    
    def save_device_usage(self, data) :
        response = {
            'state': FAILED,
            'error_desc': 'statistic_computer_usage error'
        }

        try:
            sql = f"insert into {T_DEVICE_USAGE} (cpu, per_cpu, mem_used, mem_total, \
                swap_used, swap_total, disk_used, disk_total, net_recv, net_sent, \
                collect_time) values \
                ({data['cpu']}, '{str(data['per_cpu'])}', {data['mem_used']}, {data['mem_total']}, \
                {data['swap_used']}, {data['swap_total']}, \
                {data['disk_used']}, {data['disk_total']}, {data['net_recv']}, {data['net_sent']}, NOW()); "
            self.db_.update(sql)
            
            response['error_desc'] = 'perform ok'
            response['state'] = NORMAL
        except Exception as e:
            logger.error('statistic_computer_usage exception:')
            logger.error(e)

        return response

    def statistic_computer_revenue(self, data):
        response = {
            'state': FAILED,
            'error_desc': 'statistic_computer_revenue error'
        }

        try:
            if self._exist_admin(data):
                # sql = f"select sum(total_amount) from {T_PAY_ORDERS} \
                #  where pay_status = '{data['pay_status']}' \
                #             and package_type = '{data['package_type']}' \
                #             and start_date >= '{data['start_time']}' \
                #             and end_date <= '{data['end_time']}'; "
                conditions = []

                if data['pay_status']:
                    conditions.append(f"pay_status = '{data['pay_status']}'")
                if data['package_type']:
                    conditions.append(f"package_type = '{data['package_type']}'")
                conditions.append(f"start_date >= '{data['start_time']}'")
                conditions.append(f"start_date <= '{data['end_time']}'")

                sql = f"select DATE(start_date) as date, sum(total_amount) from {T_PAY_ORDERS} where " + " and ".join(conditions) + " group by DATE(start_date);"

                rows = self.db_.query(sql)
                datas = []
                for row in rows:
                    datas.append(list(row))

                response['data'] = rows
                response['error_desc'] = 'perform ok'
                response['state'] = NORMAL
            else:
                response['error_desc'] = f"user id : {data['user_id']} is not exist"
                response['state'] = FAILED
        except Exception as e:
            logger.error('statistic_computer_revenue exception:')
            logger.error(e)

        return response


static_handler = Statistic()