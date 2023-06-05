TYPE_FILE = 'FILE'
TYPE_TEXT = "TEXT"
TYPE_IMAGE = "IMAGE_CREATE"
MODEL_GPT3_5 = 'gpt-3.5-turbo'
MODEL_GPT4 = 'gpt-4'
MODEL_IMAGE = 'DALL-E'


FAILED = 'error'
NORMAL = 'normal'
BUDGET_OVER = 'budget_over'
SAFA_BOUN = 'triger_safe_alarm'

INVALID_ACCOUNT = 'invalid_account'
ANOTHER_LOGIN = 'another_login'
ACCOUNT_NOT_LOGIN = 'account_not_login'

URI_UPLOAD_FILE = "/api/upload_file"
URI_GET_USER_FILE = "/api/get_user_file"
URI_DEVICE_LOGIN = "/api/device_login"
URI_SEND_CODE = "/api/send_code"
URI_VALID_CODE = "/api/valid_code"
URI_SET_PASSWORD = "/api/set_password"
URI_ACCOUNT_LOGIN = "/api/account_login"
URI_MODIFY_USER_INFO = '/api/modify_user_info'
URI_ADD_BALANCE = '/api/add_balance'
URI_PAY_ALIPAY = '/api/pay_alipay'
URI_ALIPAY_STATUS = '/api/alipay_status'
URI_ALIPAY_ASYN_CALLBACK = '/api/alipay_asyn_callback'
URI_GET_CHAT_HISTORY = '/api/get_chat_history'
URI_GET_ORDER_LIST = '/api/get_order_list'
URI_GET_MEMBER_LIST = '/api/get_member_list'
URI_GET_MODEL_LIST = '/api/get_model_list'
URI_ADMIN_ADD_BALANCE = '/api/admin_add_balance'
URI_QUERY_POPUP = '/api/query_popup'
URI_GET_FILE = '/api/get_file'
URI_DELETE_CHAT_HISTORY = '/api/delete_chat_history'

URI_QUERY_TEXT = "/ws/ws_query_text"

URI_ADMIN_LOGIN = "/api/admin_login"
URI_STATISTIC_USER = '/api/statistic_user'
URI_STATISTIC_COST = '/api/statistic_cost'
URI_STATISTIC_COMPUTE = '/api/statistic_compute'
URI_STATISTIC_REVENUE = '/api/statistic_revenue'

DEVICE_ALLOW_COUNT = 30
IMAGE_DECREASE_COUNT = 10

T_USER_INFO = 'user_info'
T_LOGIN_INFO = 'login_info'
T_CHAT_RECORD = 'chat_record'
T_DEVICE_CONNETION = 'device_connection'
T_CODE = 'phone_code'
T_PAY_ORDERS = 'pay_orders'

T_POPUP_PAGE = 'popup_page'
T_POPUP_RECORD = 'popup_record'

SERVER_NAME = 'https://ai.menganhealth.cn'

DATA_DIR = './data'
SRC_DIR = './src_file'

MAX_FILE_LEN = int((4096 * 0.5) - 300)
MAX_DEVICE_COUNT = 2
RECORD_PAGE_COUNT = 10