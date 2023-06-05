from bussiness.db_manager import db
from common.const import *
from common.log import logger
import abc
import inspect


class PopupBase(metaclass=abc.ABCMeta) :
    def __init__(self) :
        self.db_ = db
        self.name = ''
        self.desc = ''
        self.start_time = ''
        self.end_time = ''
        self.priority = 0
        self.popup_link = ''
        self.jump_link = ''

        self.set_value()

    @abc.abstractstaticmethod
    def set_value(self) :
        pass

    def create_popup(self) :
        try :
            if self.name == '' or self.popup_link == '':
                return
            
            # check weather exist popuo or not
            sql = f"select * from {T_POPUP_PAGE} where name = '{self.name}';"
            rows = self.db_.query(sql)
            if len(rows) < 1 :
                # add popup
                sql = f"insert into {T_POPUP_PAGE} (name, popup_desc, priority, status, start, end, \
                    create_time, popup_link, jump_link) values ('{self.name}', '{self.desc}', {self.priority}, \
                        0, '{self.start_time}', '{self.end_time}', now(), '{self.popup_link}', '{self.jump_link}');"
                self.db_.update(sql)
        except Exception as e :
            logger.error(f'create popuo obeject error: {str(e)}')

        return
    
    @abc.abstractclassmethod
    def perform(self, req_data, user_portrait) :
        pass

class Popup618(PopupBase) :
    def __init__(self) :
        super().__init__()
    
    def set_value(self) :
        try:
            self.name = '6.18'
            self.priority = 1
            self.desc = '从6月17号起，连续3天活动，会员套餐7折销售'
            self.start_time = '2023-6.17 00:00:00'
            self.end_time = '2023-6-20 00:00:00'
            self.popup_link_pc = '618_pc.jpg'
            self.popup_link_phone = '618_phone.jpg'
            self.jump_link = '/#/page/vip'
        except Exception as e :
            logger.error(f'popu618 set value error: {str(e)}')

        return
    
    def perform(self, req_data, user_portrait) :
        popup_link = ''
        try:
            # get recent 3 days order
            sql = f"select * from pay_orders where user_id = {req_data['user_id']} \
                and created_at > now() - interval 3 day;"
            rows = self.db_.query(sql)

            if req_data['user_id'] == '3' :
                if req_data['device'] == 'pc' :
                    popup_link = self.popup_link_pc
                else :
                    popup_link = self.popup_link_phone
                
            if len(rows) < 1 :
                # caculate avg query count
                avg_query = user_portrait['query_count'] / user_portrait['login_count']
                if avg_query > 3 :
                    if req_data['device'] == 'pc' :
                        popup_link = self.popup_link_pc
                    else :
                        popup_link = self.popup_link_phone

        except Exception as e :
            logger.error(f'618 perform error: {str(e)}')

        return popup_link
    

class PopupVIPDateout(PopupBase) :
    def __init__(self) :
        super().__init__()
    
    def set_value(self) :
        try:
            self.name = 'vip_expired'
            self.priority = 1
            self.desc = '您的VIP还有7天到期，老会员现在续费有很大优惠'
            self.start_time = '2023-6.17 00:00:00'
            self.end_time = '2025-6-20 00:00:00'
            self.popup_link = 'vip_expire.html'
            self.jump_link = '/#/page/vip'
        except Exception as e:
            logger.error(f'vip expired set value error: {str(e)} ')

        return
    
    def perform(self, req_data, user_portrait) :
        popup_link = ''
        try:
            if req_data['user_id'] == '-1' :
                return popup_link
            
            # get user subcribe vip order that will be expired recent 7 day
            sql = f"select * from pay_orders where user_id = {req_data['user_id']} \
                and purchase_type = 1 and end_date - interval 7 day > now();"
            rows = self.db_.query(sql)
            if len(rows) > 0:
                popup_link = self.popup_link
        
        except Exception as e:
            logger.error(f'vip expired perform error: {str(e)} ')

        return popup_link
    

class PopupManager:
    def __init__(self):
        self.db_ = db

        self._create_tables()

        self.popup_handlers_ = {
            Popup618().name : Popup618(),
            PopupVIPDateout().name : PopupVIPDateout()
        }

        self._init_popup()

        return

    def _init_popup(self) :
        try:
            for _, popup in self.popup_handlers_.items() :
                popup.set_value()
                popup.create_popup()
        except Exception as e:
            logger.error(f'{inspect.currentframe().f_code.co_name} error: {str(e)} ')
        return
    
    def _create_tables(self):
        try:
            # user info
            sql = f" create table if not exists {T_POPUP_PAGE} ( " \
                  "popup_id int PRIMARY KEY AUTO_INCREMENT," \
                  "name varchar(64), " \
                  "popup_desc varchar(512), " \
                  "priority int default 0, " \
                  "status int default 0, " \
                  "popup_link varchar(256), " \
                  "jump_link varchar(256), " \
                  "start datetime," \
                  "end datetime," \
                  "create_time datetime " \
                  ")engine = InnoDB, charset = utf8;"
            self.db_.update(sql)

            sql = f" create table if not exists {T_POPUP_RECORD} ( " \
                  "record_id int PRIMARY KEY AUTO_INCREMENT," \
                  "user_id int, " \
                  "connection_id int, " \
                  "popup_id int, " \
                  "popup_status int, " \
                  "popup_time datetime " \
                  ")engine = InnoDB, charset = utf8;"
            self.db_.update(sql)

        except Exception as e :
            logger.error(f'create table error: {str(e)}')
    
    def _user_portrait(self, req_data) :
        user_portrait = {}

        try:
            # check sigup state
            if req_data['user_id'] == '-1' :
                user_portrait['sigup'] = False
            else :
                user_portrait['sigup'] = True

            # statistic query count
            if req_data['user_id'] != '-1' :
                sql = f"select count(*) from {T_CHAT_RECORD} where user_id \
                    = {req_data['user_id']};"
            else :
                sql = f"select count(*) from {T_CHAT_RECORD} where connection_id \
                    = {req_data['connection_id']};"
            rows = self.db_.query(sql)
            user_portrait['query_count'] = rows[0][0]

            # statistic login count
            if req_data['user_id'] != '-1' :
                sql = f"select count(*) from {T_LOGIN_INFO} where user_id \
                    = {req_data['user_id']};"
            else:
                sql = f"select count(*) from {T_LOGIN_INFO} where connection_id \
                    = {req_data['connection_id']};"
            rows = self.db_.query(sql)
            user_portrait['login_count'] = rows[0][0]
        
        except Exception as e:
            logger.error(f'{inspect.currentframe().f_code.co_name} error: {str(e)} ')

        return user_portrait

    def _get_all_popup(self) :
        # get all valid popup
        all_popup = []
        try:
            sql = f"select popup_id, name, popup_desc, priority, popup_link, jump_link from {T_POPUP_PAGE} \
                where status = 0 and end > now() order by priority desc;"
            rows = self.db_.query(sql)
            for row in rows :
                tmp = {
                    'popup_id' : row[0],
                    'name' : row[1],
                    'desc' : row[2],
                    'priority' : row[3],
                    'popup_link' : row[4],
                    'jump_link' : row[5]
                }

                all_popup.append(tmp)
        except Exception as e:
            logger.error(f'{inspect.currentframe().f_code.co_name} error: {str(e)} ')

        return all_popup
    
    def _select_popup(self, req_data, user_portrait, all_popup) :
        # order by priority
        for one_popup in all_popup :
            popup_link = self.popup_handlers_[one_popup['name']].perform(req_data, user_portrait)
            if popup_link != '' :
                one_popup['popup_link'] = popup_link
                return one_popup

        return None
    
    def _get_popup_record(self, req_data) :
        today_popup = []

        try:
            if req_data['user_id'] != '-1' :
                sql = f"select record_id, popup_id, popup_status from {T_POPUP_RECORD} \
                    where user_id = {req_data['user_id']} and popup_time > now() \
                        - interval 1 day and popup_status = 0;"
            else:
                sql = f"select record_id, popup_id, popup_status from {T_POPUP_RECORD} \
                    where user_id = {req_data['connection_id']} and popup_time > now()\
                        - interval 1 day and popup_status = 0;"
            
            rows = self.db_.query(sql)
            for row in rows :
                tmp = {
                    'record_id' : row[0],
                    'popup_id' : row[1],
                    'status' : row[2]
                }
                today_popup.append(tmp)
        except Exception as e:
            logger.error(f'{inspect.currentframe().f_code.co_name} error: {str(e)} ')

        return today_popup
    
    def _add_popup_record(self, req_data, popup) :
        try:
            sql = f"insert into {T_POPUP_RECORD} (user_id, connection_id, popup_id \
                , popup_status, popup_time) values ({req_data['user_id']}, {req_data['connection_id']}, \
                    {popup['popup_id']}, 0, now());"
            self.db_.update(sql)
        except Exception as e:
            logger.error(f'{inspect.currentframe().f_code.co_name} error: {str(e)} ')

        return
    
    def query_popup(self ,req_data) :
        res = {
            'state': FAILED,
            'error_desc': "'there is not popup for the user'",
            'popup_link' : ''
        }

        try:
            today_popup = self._get_popup_record(req_data)
            if len(today_popup) > 0 :
                desc = f"user_id: {req_data['user_id']} or connection_id: {req_data['connection_id']} has popup"
                logger.info(desc)
                res['error_desc'] = desc
                res['state'] = NORMAL
                return res
            
            # user portrait
            user_portrait = self._user_portrait(req_data)
            if user_portrait['query_count'] < 10 or user_portrait['login_count'] < 3 :
                desc = f'query_count < 10 or login_count < 3'
                logger.info(str(req_data) + desc)
                res['error_desc'] = desc
                res['state'] = NORMAL
                return res

            # get all popup items
            all_popup = self._get_all_popup()

            # select one popup
            # perform special popup strategydesc
            popup = self._select_popup(req_data, user_portrait, all_popup)

            # update popup state
            if popup is not None :
                if req_data['user_id']  != '3' :
                    self._add_popup_record(req_data, popup)

                res['state'] = NORMAL
                res['error_desc'] = popup['desc']

                src_dir = SRC_DIR[2:]
                res['popup_link'] = f"{URI_GET_FILE}/{popup['popup_link']}"
                res['jump_link'] = popup['jump_link']

                return res
            
            res['state'] = NORMAL
        except Exception as e:
            desc = f'{inspect.currentframe().f_code.co_name} error: {str(e)} '
            logger.error(desc)
            res['error_desc'] = desc

        return res


g_popup_manager = PopupManager()