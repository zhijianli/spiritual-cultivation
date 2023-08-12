# encoding:utf-8

from .bot import Bot
from common.config import conf, load_config
from common.log import logger
from common.token_bucket import TokenBucket
from common.expired_dict import ExpiredDict
import openai
import time
from common.const import *


if conf().get('expires_in_seconds'):
    all_sessions = ExpiredDict(conf().get('expires_in_seconds'))
else:
    all_sessions = dict()


# OpenAI对话模型API (可用)
class ChatGPTBot(Bot):
    def __init__(self):
        self.model_config_ = {
            'gpt-3.5-turbo' : 'gpt-3.5-turbo',
            'gpt-4' : 'gpt-4',
            # 'gpt-4': 'gpt-4-32k-0314',
            'DALL-E' : 'dall-e'
        }

        self.user_models_ = {}

        openai.api_key = conf().get('open_ai_api_key')
        if conf().get('open_ai_api_base'):
            openai.api_base = conf().get('open_ai_api_base')
        proxy = conf().get('proxy')
        if proxy:
            openai.proxy = proxy
        if conf().get('rate_limit_chatgpt'):
            self.tb4chatgpt = TokenBucket(conf().get('rate_limit_chatgpt', 20))
        if conf().get('rate_limit_dalle'):
            self.tb4dalle = TokenBucket(conf().get('rate_limit_dalle', 50))

    def clear_memory(self, context):
        Session.clear_session(context['session_id'])

    def add_memory(self, data):
        session_id = data.get('session_id') or data.get('from_user_id')

        Session.build_session_query(data['query'], session_id)

        data['total_tokens'] = len(data['response'])
        if data['total_tokens'] > 0 :
            Session.save_session(data["response"], session_id, data["total_tokens"])

    def save_memory(self, data):
        session_id = data.get('session_id')

        data['total_tokens'] = len(data['response'])
        if data['total_tokens'] > 0 :
            Session.save_session(data["response"], session_id, data["total_tokens"])

    def reply(self, query, context=None):
        # acquire reply content
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            logger.info("[OPEN_AI] query={}".format(query))
            session_id = context.get('session_id') or context.get('from_user_id')
            clear_memory_commands = conf().get('clear_memory_commands', ['#清除记忆'])
            if query in clear_memory_commands:
                Session.clear_session(session_id)
                return '记忆已清除'
            elif query == '#清除所有':
                Session.clear_all_session()
                return '所有人记忆已清除'
            elif query == '#更新配置':
                load_config()
                return '配置已更新'

            session = Session.build_session_query(query, session_id)
            logger.debug("[OPEN_AI] session query={}".format(session))

            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self.reply_text(session, session_id, 0)
            logger.debug("[OPEN_AI] new_query={}, session_id={}, reply_cont={}".format(session, session_id, reply_content["content"]))
            if reply_content["completion_tokens"] > 0:
                Session.save_session(reply_content["content"], session_id, reply_content["total_tokens"])
            return reply_content

        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query, 0)

    def reply_stream(self, query,characterName,context=None):
        # acquire reply content
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            logger.info("[OPEN_AI] query={}".format(query))
            session_id = context.get('session_id') or context.get('from_user_id')
            clear_memory_commands = conf().get('clear_memory_commands', ['#清除记忆'])
            if query in clear_memory_commands:
                Session.clear_session(session_id)
                return '记忆已清除'
            elif query == '#清除所有':
                Session.clear_all_session()
                return '所有人记忆已清除'
            elif query == '#更新配置':
                load_config()
                return '配置已更新'

            if session_id not in self.user_models_ :
                self.user_models_[session_id] = context['model']
            
            if context['model'] != self.user_models_[session_id] :
                Session.clear_session(session_id)
                self.user_models_[session_id] = context['model']

            session = Session.build_session_query(query, session_id,characterName)
            logger.debug("[OPEN_AI] session query={}".format(session))

            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self._reply_text_stream(session, session_id,0)
            # logger.debug("[OPEN_AI] new_query={}, session_id={}, reply_cont={}".format(session, session_id, reply_content["content"]))
            return reply_content

        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query, 0)

    def reply_text(self, session, session_id, retry_count=0) ->dict:
        '''
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        '''
        try:
            if conf().get('rate_limit_chatgpt') and not self.tb4chatgpt.get_token():
                return {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
            response = openai.ChatCompletion.create(
                model= conf().get("model") or "gpt-3.5-turbo",  # 对话模型的名称
                messages=session,
                temperature=conf().get('temperature', 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
                #max_tokens=4096,  # 回复最大的字符数
                top_p=1,
                frequency_penalty=conf().get('frequency_penalty', 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=conf().get('presence_penalty', 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            )
            # logger.info("[ChatGPT] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            return {"total_tokens": response["usage"]["total_tokens"], 
                    "completion_tokens": response["usage"]["completion_tokens"], 
                    "content": response.choices[0]['message']['content']}
        except openai.error.RateLimitError as e:
            # rate limit exception
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.reply_text(session, session_id, retry_count+1)
            else:
                return {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
        except openai.error.APIConnectionError as e:
            # api connection exception
            logger.warn(e)
            logger.warn("[OPEN_AI] APIConnection failed")
            return {"completion_tokens": 0, "content":"我连接不到你的网络"}
        except openai.error.Timeout as e:
            logger.warn(e)
            logger.warn("[OPEN_AI] Timeout")
            return {"completion_tokens": 0, "content":"我没有收到你的消息"}
        except Exception as e:
            # unknown exception
            logger.exception(e)
            Session.clear_session(session_id)
            return {"completion_tokens": 0, "content": "请再问我一次吧"}

    def _reply_text_stream(self, session, session_id,retry_count=0) ->dict:
        '''
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        '''
        try:
            chat_model = self.model_config_[self.user_models_[session_id]]
            if conf().get('rate_limit_chatgpt') and not self.tb4chatgpt.get_token():
                return {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
            response = openai.ChatCompletion.create(
                model= chat_model,  # 对话模型的名称
                messages=session,
                temperature=conf().get('temperature', 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
                # max_tokens=4096,  # 回复最大的字符数
                # max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=conf().get('frequency_penalty', 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=conf().get('presence_penalty', 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                stream=True  # this time, we set stream=True
            )
            # logger.info("[ChatGPT] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            return response
        except openai.error.RateLimitError as e:
            # rate limit exception
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.reply_text(session, session_id, retry_count+1)
            else:
                return {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
        except openai.error.APIConnectionError as e:
            # api connection exception
            logger.warn(e)
            logger.warn("[OPEN_AI] APIConnection failed")
            return {"completion_tokens": 0, "content":"我连接不到你的网络"}
        except openai.error.Timeout as e:
            logger.warn(e)
            logger.warn("[OPEN_AI] Timeout")
            return {"completion_tokens": 0, "content":"我没有收到你的消息"}
        except Exception as e:
            # unknown exception
            logger.exception(e)
            Session.clear_session(session_id)
            return {"completion_tokens": 0, "content": "我没听清，请再问一次吧！"}

    def create_img(self, query, retry_count=0):
        try:
            if conf().get('rate_limit_dalle') and not self.tb4dalle.get_token():
                return "请求太快了，请休息一下再问我吧"
            logger.info("[OPEN_AI] image_query={}".format(query))

            query += ' high quality, 8k'
            response = openai.Image.create(
                prompt=query,    #图片描述
                n=1,             #每次生成图片的数量
                size="512x512"   #图片大小,可选有 256x256, 512x512, 1024x1024
            )
            image_url = response['data'][0]['url']
            logger.info("[OPEN_AI] image_url={}".format(image_url))
            return image_url
        except openai.error.RateLimitError as e:
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] ImgCreate RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.create_img(query, retry_count+1)
            else:
                return "请求太快啦，请休息一下再问我吧"
        except Exception as e:
            logger.exception(e)
            return None

    def check_prefix(self, content, prefix_list):
        for prefix in prefix_list:
            if content.startswith(prefix):
                return prefix
        return None

    def get_query_type(self,query):
        is_image = self.check_prefix(query, conf().get('image_create_prefix'))
        if is_image :
            return TYPE_IMAGE
        else :
            return TYPE_TEXT


class Session(object):
    @staticmethod
    def build_session_query(query, session_id,characterName):
        '''
        build query with conversation history
        e.g.  [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who won the world series in 2020?"},
            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            {"role": "user", "content": "Where was it played?"}
        ]
        :param query: query content
        :param session_id: session id
        :return: query content with conversaction
        '''
        session = all_sessions.get(session_id, [])
        if len(session) == 0:
            system_prompt = ""
            if characterName == "" or characterName is None:
                system_prompt = conf().get("character_desc", "")
            else:
                system_prompt = "我想让你扮演"+characterName+"。我作为一名游客将向你提出各种问题。我希望你只作为"+characterName+"来回答。"
            system_item = {'role': 'system', 'content': system_prompt}
            session.append(system_item)
            all_sessions[session_id] = session
        else:
            first_item = session[0]['content']  # 取出session的第一个数据的content
            system_prompt = "我想让你扮演" + characterName + "。我作为一名游客将向你提出各种问题。我希望你只作为" + characterName + "来回答。"
            if characterName == "知客僧" or first_item != system_prompt:
                system_item = {'role': 'system', 'content': system_prompt}
                session.clear()
                session.append(system_item)
                all_sessions[session_id] = session
        user_item = {'role': 'user', 'content': query}
        session.append(user_item)
        return session

    @staticmethod
    def save_session(answer, session_id, total_tokens):
        max_tokens = conf().get("conversation_max_tokens")
        if not max_tokens:
            # default 3000
            max_tokens = 3000
        max_tokens=int(max_tokens)

        session = all_sessions.get(session_id)
        if session:
            # append conversation
            gpt_item = {'role': 'assistant', 'content': answer}
            session.append(gpt_item)

        # discard exceed limit conversation
        Session.discard_exceed_conversation(session, max_tokens, total_tokens)
    

    @staticmethod
    def discard_exceed_conversation(session, max_tokens, total_tokens):
        dec_tokens = int(total_tokens)
        # logger.info("prompt tokens used={},max_tokens={}".format(used_tokens,max_tokens))
        while dec_tokens > max_tokens:
            # pop first conversation
            if len(session) > 3:
                session.pop(1)
                session.pop(1)
            else:
                break    
            dec_tokens = dec_tokens - max_tokens

    @staticmethod
    def clear_session(session_id):
        all_sessions[session_id] = []

    @staticmethod
    def clear_all_session():
        all_sessions.clear()
