import pymysql
from common.log import logger
from common.const import *
from common.config import conf


T_USER_INFO = 'user_info'
T_LOGIN_INFO = 'login_info'
T_CHAT_RECORD = 'chat_record'
T_DEVICE_CONNETION = 'device_connection'
T_CODE = 'phone_code'
T_ADMIN = 'admin'
T_DEVICE_USAGE = 'device_usage'

DEVICE_CONNECT = 'connect'
DEVICE_DISCONNECT = 'disconnect'
USER_TYPE_NORMAL = 'normal'
USER_TYPE_VIP = 'vip'


class DBManager :
    def __init__(self):
        self.db_ = None
        self.cursor_ = None

        self.create_tables()

        return

    def get_connect(self):
        if self.db_ is not None and self.cursor_ is not None:
            return self.cursor_, self.db_

        db_host = conf().get('db_host')
        db_name = conf().get('db_name')
        db_user = conf().get('db_user')
        db_password = conf().get('db_password')
        self.db_ = pymysql.connect(host=db_host, port=3306, user=db_user, \
                                   passwd=db_password, db=db_name,
                             charset='utf8', autocommit=True)
        # self.db = pymysql.connect(host='127.0.0.1', port=3306, user='admin', passwd='admin', db=DB,
        #                           charset='utf8', autocommit=True)
        self.cursor_ = self.db_.cursor()

        return self.cursor_, self.db_

    def create_tables(self):
        try:
            # create admin info
            sql = f" create table if not exists {T_ADMIN} ( " \
                  "user_id int PRIMARY KEY AUTO_INCREMENT, " \
                  "phone_number int, " \
                  "password varchar(128), " \
                  "level char(32) " \
                  ")engine = InnoDB, charset = utf8;"
            self.update(sql)

            # create device resource
            sql = f" create table if not exists {T_DEVICE_USAGE} ( " \
                  "usage_id int PRIMARY KEY AUTO_INCREMENT, " \
                  "cpu varchar(128), " \
                  "mem_used varchar(32), " \
                  "mem_total varchar(32), " \
                  "swap_used varchar(32), " \
                  "swap_total varchar(32), " \
                  "disk_used varchar(32), " \
                  "disk_total varchar(32), " \
                  "network_receive varchar(32), " \
                  "network_sent varchar(32), " \
                  "collect_time datetime " \
                  ")engine = InnoDB, charset = utf8;"
            self.update(sql)

        except Exception as e :
            logger.error(e)

        return

    def query(self, sql):
        rows = []
        try:
            logger.info(sql)
            db_cursor, db = self.get_connect()

            db_cursor.execute(sql)

            rows = db_cursor.fetchall()
        except Exception as e :
            logger.error(e + sql)

        return rows

    def update(self, sql):
        try:
            logger.info(sql)
            db_cursor, db = self.get_connect()
            db_cursor.execute(sql)
            db.commit()

            return True

        except Exception as e:
            print(e)
            print(sql)
            logger.error(e)
            logger.error(sql)

        return False

    def connect_device(self, data):
        device_info = {}

        try:
            # check ip whether has connected 
            query_sql = f"SELECT * FROM {T_DEVICE_CONNETION} WHERE connection_id \
             = {data['connection_id']} or \
                (ip = '{data['ip']}' and disconnect_time > (NOW() - INTERVAL 10 MINUTE) ) ;"

            result = self.query(query_sql)
            if len(result) > 0 :
                sql = f"update {T_DEVICE_CONNETION} set ip = '{data['ip']}', location = '{data['location']}', \
                connect_state = '{DEVICE_CONNECT}', connect_time = NOW(), disconnect_time = NOW() \
                where connection_id = {result[0][0]};"
                self.query(sql)
            else :
                sql = f"insert into {T_DEVICE_CONNETION} (ip, location, device_name, \
                device_id, queried_count, allow_count, connect_state, connect_time \
                , disconnect_time) values ('{data['ip']}', '{data['location']}', '{data['device_name']}', \
                '{data['device_id']}', 0, {DEVICE_ALLOW_COUNT}, '{DEVICE_CONNECT}', NOW(), NOW()) "

                self.update(sql)

                result = self.query(query_sql)

            result = result[0]
            device_info['queried_count'] = result[5]
            device_info['allow_count'] = result[6]
            device_info['connection_id'] = result[0]
        except Exception as e :
            logger.error('connect_device exception:')
            logger.error(e)

        return device_info
    
    def account_login(self, data):
        response = {}

        try:
            # check ip whether has connected 
            sql = f"select user_id, phone_number, user_name, password, queried_count, allow_count \
                  from {T_USER_INFO} where phone_number = '{data['phone_number']}'; "
            rows = self.query(sql)
            if len(rows) < 1 :
                response['state'] = 'invalid_account'
                response['error_desc'] = 'this phone number is not registered'
            else :
                row = rows[0]
                password = row[3]
                if password != data['password'] :
                    response['state'] = 'invalid_password'
                    response['error_desc'] = 'password is error, you can find it by phone code'
                else :
                    response['state'] = NORMAL
                    response['error_desc'] = 'login success'

                    response['user_id'] = row[0]
                    response['phone_number'] = row[1]
                    response['user_name'] = row[2]
                    response['queried_count'] = row[4]
                    response['allow_count'] = row[5]

        except Exception as e :
            logger.error('connect_device exception:')
            logger.error(e)
            response['state'] = FAILED
            response['error_desc'] = 'account_login perform error'

        return response
    
    def set_password(self, data):
        response = {
            "state" : NORMAL,
            'error_desc' : "perform successly"
        }

        try:
            sql = f"update {T_USER_INFO} set password = '{data['new_password']}' \
                where user_id = {data['user_id']}; "
            self.update(sql)

        except Exception as e :
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
            self.query(sql)  
        except Exception as e :
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

            self.update(sql)  
        except Exception as e :
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

            rows = self.query(sql)
            if len(rows) < 1 :
                status = False
            else :
                sql = f"update {T_CODE} set state = 'valid', valid_time = NOW() " \
                      f"where phone_number = '{data['phone_number']}' \
                            and send_time > (NOW() - INTERVAL 10 MINUTE);"
                self.update(sql)

        except Exception as e :
            logger.error('valid_code exception:')
            logger.error(e)
            status = False

        return status

    def longin(self, data):
        user_info = None 

        try:
            # insert a login record
            sql = f"insert into {T_LOGIN_INFO} \
                (connection_id, state, login_time) \
                    values \
                        ({data['connection_id']}, 'login', NOW());"
            self.update(sql)

            # select user info
            query_sql = f"select user_id, user_name, queried_count, allow_count from {T_USER_INFO} \
                where \
                    phone_number = '{data['phone_number']}' ;"
            rows = self.query(query_sql)
            if len(rows) < 1 :
                sql = f"insert into {T_USER_INFO} \
                    (phone_number, password, type, queried_count, allow_count, register_time) \
                    values \
                        ('{data['phone_number']}', '{data['password']}', '{USER_TYPE_NORMAL}', 0, \
                            {DEVICE_ALLOW_COUNT * 2}, NOW())"
                self.update(sql)

                rows = self.query(query_sql)

            row = rows[0]
            response = {
                'user_id' : row[0],
                'user_name' : row[1],
                'queried_count' : row[2],
                'allow_count' : row[3]
            }
        except Exception as e :
            logger.error('longin exception:')
            logger.error(e)

        return response

    def longout(self, data):
        flag = False

        try:
            if -1 != data['user_id'] :
                sql = f"update {T_LOGIN_INFO} set state = 'logout', logout_time = NOW() \
                    where \
                        user_id = {data['user_id']};"
                self.update(sql)

            flag = True
        except Exception as e :
            logger.error('save action exception:')
            logger.error(e)

        return flag

    def chat(self, data):
        flag = False

        try:
            sql = f"insert into {T_CHAT_RECORD} \
                (connection_id, user_id, query, response, type, query_time, response_time) \
                values \
                    ({data['connection_id']}, {data['user_id']}, '{data['prompt']}', '{data['response']}', \
                    '{data['type']}', '{data['query_time']}', '{data['response_time']}' );"
                
            self.update(sql)
        except Exception as e :
            logger.error('save chat exception:')
            logger.error(e)

        return flag

    def get_query_balance(self, data):
        response = {
            'queried_count' : 0,
            'allow_count' : 0
        }

        try:
           sql = ''
           data['user_id'] = int(data['user_id'])
           if -1 != data['user_id'] :
               sql = f"select queried_count, allow_count from {T_USER_INFO} \
               where user_id = '{data['user_id']}';"
           else :
               sql = f"select queried_count, allow_count from {T_DEVICE_CONNETION} \
               where connection_id = {data['connection_id']};"

           rows = self.query(sql)
           row = rows[0]
           response['queried_count'] = row[0]
           response['allow_count'] = row[1]
        except Exception as e:
            logger.error('get_query_balance action exception:')
            logger.error(e)

        return response

    def update_balance(self, data):
        flag = False

        try:
            if -1 != data['user_id'] :
                sql = f"update {T_USER_INFO} set queried_count = {data['queried_count']} \
                       where user_id = {data['user_id']} ;"
            else :
                sql = f"update {T_DEVICE_CONNETION} set queried_count = {data['queried_count']} \
                where connection_id = {data['connection_id']};"

            self.update(sql)
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
            if data['phone_number'] != '' :
                sql =f"update {T_USER_INFO} set phone_number = '{data['phone_number']}' where user_id = {data['user_id']}; "
                self.update(sql)
            if data['user_name'] != '' :
                sql =f"update {T_USER_INFO} set user_name = '{data['user_name']}' where user_id = {data['user_id']}; "
                self.update(sql)
            if data['new_password'] != '' :
                sql =f"update {T_USER_INFO} set password = '{data['new_password']}' where user_id = {data['user_id']}; "
                self.update(sql)

            sql = f"select user_name, phone_number, queried_count, allow_count from {T_USER_INFO} where user_id \
                   = {data['user_id']}"
            rows = self.query(sql)
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
            self.update(sql)

            sql = f"select user_name, phone_number, queried_count, allow_count from {T_USER_INFO} where user_id \
                   = {data['user_id']}"
            rows = self.query(sql)
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

    def login_admin(self, data) :
        response = {
            'state': FAILED,
            'error_desc': 'login_admin error'
        }

        try:
            sql = f"select user_id from  {T_ADMIN} where phone_number = '{data['phone_number']}' \
                and password = '{data['password']}'; "
            rows = self.query(sql)

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
            rows = self.query(sql)
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

                # sql = f"select user_id, cpu, mem_used, mem_total, swap_used, swap_total, disk_used, \
                #     disk_total, network_receive, network_sent, collect_time from \
                #           {T_DEVICE_USAGE} where collect_time > '{data['start_time']}' \
                #             and collect_time < '{data['end_time']}'; "
                types = data['type']
                sql = f"select {types} from \
                          {T_DEVICE_USAGE} where collect_time > '{data['start_time']}' \
                            and collect_time < '{data['end_time']}'; "
                rows = self.query(sql)
                
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
            'error_desc': 'add_balance error'
        }

        try:
            if self._exist_admin(data) :

                # sql = f"select user_id, cpu, mem_used, mem_total, swap_used, swap_total, disk_used, \
                #     disk_total, network_receive, network_sent, collect_time from \
                #           {T_DEVICE_USAGE} where collect_time > '{data['start_time']}' \
                #             and collect_time < '{data['end_time']}'; "
                types = data['type']
                sql = f"select {types} from \
                          {T_DEVICE_USAGE} where collect_time > '{data['start_time']}' \
                            and collect_time < '{data['end_time']}'; "
                rows = self.query(sql)
                
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
    
    def statistic_cost(self, data) :
        response = {
            'state': FAILED,
            'error_desc': 'add_balance error'
        }

        try:
            if self._exist_admin(data) :

                # sql = f"select user_id, cpu, mem_used, mem_total, swap_used, swap_total, disk_used, \
                #     disk_total, network_receive, network_sent, collect_time from \
                #           {T_DEVICE_USAGE} where collect_time > '{data['start_time']}' \
                #             and collect_time < '{data['end_time']}'; "
                types = data['type']
                sql = f"select {types} from \
                          {T_DEVICE_USAGE} where collect_time > '{data['start_time']}' \
                            and collect_time < '{data['end_time']}'; "
                rows = self.query(sql)
                
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
    

db_statistic = DBManager()