import pymysql
from common.log import logger
from common.const import *
from common.config import conf

DEVICE_CONNECT = 'connect'
DEVICE_DISCONNECT = 'disconnect'
USER_TYPE_NORMAL = 'normal'
USER_TYPE_VIP = 'vip'

class DBManager :
    def __init__(self):
        self.db_ = None
        self.cursor_ = None
        return

    def get_connect(self):
        if self.db_ is not None and self.cursor_ is not None:
            if self.db_.ping() :
                return self.cursor_, self.db_

        db_host = conf().get('db_host')
        db_name = conf().get('db_name')
        db_user = conf().get('db_user')
        db_password = conf().get('db_password')
        db_port = conf().get('db_port')
        self.db_ = pymysql.connect(host=db_host, port=db_port, user=db_user, \
                                   passwd=db_password, db=db_name,
                             charset='utf8', autocommit=True)
        # self.db = pymysql.connect(host='127.0.0.1', port=3306, user='admin', passwd='admin', db=DB,
        #                           charset='utf8', autocommit=True)
        self.cursor_ = self.db_.cursor()

        return self.cursor_, self.db_

    def query(self, sql):
        rows = []
        try:
            logger.info(sql)
            db_cursor, db = self.get_connect()

            db_cursor.execute(sql)

            rows = db_cursor.fetchall()
        except Exception as e :
            logger.error(str(e) + sql)

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

    def insert_pay_orders(self, data):
        response = {
            'state': FAILED,
            'error_desc': 'insert_pay_orders error'
        }
        try:

            # 准备要插入的数据
            out_trade_no = data['out_trade_no']
            user_id = data['user_id']
            package_type = data['package_type']
            total_amount = data['total_amount']
            purchase_type = data['purchase_type']
            purchase_date = data['purchase_date']
            start_date = data['start_date']
            end_date = data['end_date']
            pay_status = data['pay_status']
            payment_source = data['payment_source']
            chat_use_num = data['chat_use_num']
            chat_allow_num = data['chat_allow_num']
            painting_use_num = data['painting_use_num']
            painting_allow_num = data['painting_allow_num']
            gpt4_allow_num = data['gpt4_allow_num']
            gpt4_use_num = data['gpt4_use_num']
            file_use_count = data['file_use_count']
            file_allow_count = data['file_allow_count']

            # 构建插入语句
            insert_sql = f"""
                INSERT INTO {T_PAY_ORDERS} (out_trade_no, user_id, package_type, total_amount, purchase_type, purchase_date, start_date, end_date, pay_status, payment_source,chat_use_num,chat_allow_num,painting_use_num,painting_allow_num,gpt4_allow_num,gpt4_use_num,file_allow_count,file_use_count)
                VALUES ('{out_trade_no}', {user_id}, {package_type}, {total_amount}, {purchase_type}, '{purchase_date}', '{start_date}', '{end_date}', {pay_status}, {payment_source}, {chat_use_num}, {chat_allow_num}, {painting_use_num}, {painting_allow_num}, {gpt4_allow_num}, {gpt4_use_num}, {file_allow_count}, {file_use_count});
                """

            # 执行插入操作
            self.update(insert_sql)

            sql = f"select out_trade_no,user_id from pay_orders where out_trade_no \
                             = {out_trade_no}"
            rows = self.query(sql)
            if len(rows) < 1:
                response['state'] = FAILED
                response['error_desc'] = f"out_trade_no : {out_trade_no} is not exist"
            else:
                row = rows[0]

                response['state'] = NORMAL
                response['error_desc'] = 'perform ok'

        except Exception as e:
            logger.error('insert_pay_orders exception:')
            logger.error(e)

        return response

    def update_pay_orders(self, data):
        response = {
            "state" : NORMAL,
            'error_desc' : "perform successly"
        }

        try:
            sql = f"update {T_PAY_ORDERS} set pay_status = '{data['pay_status']}' \
                where out_trade_no = {data['out_trade_no']}; "
            self.update(sql)

        except Exception as e :
            logger.error('update_pay_orders exception:')
            logger.error(e)
            response['state'] = FAILED
            response['error_desc'] = 'update_pay_orders perform error'

        return response


    def select_pay_orders(self, data):
        response = {
            "state" : NORMAL,
            'error_desc' : "perform successly",
            'package_type': None
        }

        try:
            sql = f"select out_trade_no,user_id,package_type from pay_orders where out_trade_no \
                                         = {data['out_trade_no']}"
            rows = self.query(sql)
            if len(rows) < 1:
                response['state'] = FAILED
                response['error_desc'] = f"out_trade_no : {out_trade_no} is not exist"
            else:
                row = rows[0]
                print('rows',rows)
                response['state'] = NORMAL
                response['package_type'] = row
                response['error_desc'] = 'perform ok'

        except Exception as e :
            logger.error('select_pay_orders exception:')
            logger.error(e)
            response['state'] = FAILED
            response['error_desc'] = 'select_pay_orders perform error'

        return response


db = DBManager()
