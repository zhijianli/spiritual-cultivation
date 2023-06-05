from .query_text import QueryText
from common.const import *
from bussiness.chat_gpt_bot import ChatGPTBot


class CmdManager :
    def __init__(self):
        self.chatgpt_ = ChatGPTBot()

        self.cmd_handler_ = {
            QueryText(self.chatgpt_).name_ : QueryText(self.chatgpt_),
        }

    async def perform(self, client, data):
        cmd = data['cmd']
        if cmd not in self.cmd_handler_ :
            desc = f'cmd : {cmd} is not surport'

            response = {
                'state' : FAILED,
                'error_desc' : desc
            }

            return response

        return await self.cmd_handler_[cmd].perform(client, data)