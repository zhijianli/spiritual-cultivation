from .client_cmd import ClientCmd
from common.filter import DFAFilter
from common.const import *
from datetime import datetime
from common.util import create_session_id
import re
import json

# 增加敏感词过滤器
gfw = DFAFilter()
# gfw.parse(f"{get_dir(__file__)}/../../docs/sensitive/政治类.txt")
# gfw.parse(f"{get_dir(__file__)}/docs/sensitive/涉枪涉爆违法信息关键词.txt")
# gfw.parse(f"{get_dir(__file__)}/docs/sensitive/色情类.txt")
# gfw.parse(f"{get_dir(__file__)}/docs/sensitive/敏感词大库.txt")


def get_first_n_chars(text, n):
    words = text.split(' ')
    count = 0
    result = ''
    for word in words:
        if re.search('[\u4e00-\u9fff]', word):  # 检查是否包含中文字符
            if count + len(word) > n:
                result += word[ : n - count]
                return result
            count += len(word)
        else:  # 英文单词
            if count + 1 > n:
                return result
            count += 1
        result += word + ' '
    return result

class QueryText(ClientCmd):
    def __init__(self, chat_bot):
        super().__init__()
        self.chatgpt_ = chat_bot

        self.name_ = 'query_text'
        self.response_iter_ = None

    async def send(self, client, res):
        msg = json.dumps(res, ensure_ascii=False)

        await client.send_text(msg)
        data = await client.receive_text()

        data = json.loads(data)
        return data
    
    async def perform(self, websocket, req_data):
        res = {
            'state': 'finish',
            'type': 'text',
            'data': ''
        }
        chat_text = ''
        finish_content = ''
        context = dict()
        context['session_id'] = create_session_id(req_data)
        context['type'] = TYPE_TEXT
        context['model'] = 'gpt-3.5-turbo'

        query_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # if (check_sensitive(gfw, req_data['prompt'])):
        #     chat_text = "问题中包含敏感词，请重新输入！"
        #
        #     # send word to client one by one
        #     res['data'] = chat_text
        #     res['state'] = 'finish'
        #     res['type'] = 'text'
        #     await self.send(websocket, res)
        #     return None

        # request openai
        response = self.chatgpt_.reply_stream(req_data['prompt'],req_data['characterName'],context)
        if isinstance(response, dict) and response['completion_tokens'] == 0 :
            res['data'] = response['content']
            res['state'] = 'continue'
            res['type'] = 'text'

            chat_text = response['content']
            await self.send(websocket, res)

        else :
            chat_text = ''

            # send word to client one by one
            for chunk in response:
                chunk_message = chunk['choices'][0]['delta']  # extract the message
                if 'content' not in chunk_message:
                    continue

                res['data'] = chunk_message['content']
                res['state'] = 'continue'
                res['type'] = 'text'

                data = await self.send(websocket, res)
                if data['cmd'] == 'stop':
                    # response.clear()
                    response = ""
                    break

                chat_text += res['data']

        # finish
        res['state'] = 'finish'
        res['data'] = finish_content
        res['type'] = 'text'

        await self.send(websocket, res)

        tmp_data = {
            'session_id' : context['session_id'],
            'response' : chat_text
        }
        self.chatgpt_.save_memory(tmp_data)
            
        return None
