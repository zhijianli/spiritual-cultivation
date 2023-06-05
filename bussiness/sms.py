# coding=utf-8
import urllib
import urllib.request
import requests
import json


class SMS :
    def __init__(self) :
        pass

    def md5(self, str):
        import hashlib
        m = hashlib.md5()
        m.update(str.encode("utf8"))
        return m.hexdigest()

    def send_content(self, phone_num, content) :
        statusStr = {
            '0': '短信发送成功',
            '-1': '参数不全',
            '-2': '服务器空间不支持,请确认支持curl或者fsocket,联系您的空间商解决或者更换空间',
            '30': '密码错误',
            '40': '账号不存在',
            '41': '余额不足',
            '42': '账户已过期',
            '43': 'IP地址限制',
            '50': '内容含有敏感词'
        }

        smsapi = "http://api.smsbao.com/"
        # 短信平台账号
        user = 'xiangbaosong'
        # 短信平台密码
        password = self.md5('Xl2016xl')

        # 要发送短信的手机号码
        phone = phone_num

        # 取消代理设置
        urllib.request.ProxyHandler({'http': None})

        data = urllib.parse.urlencode({'u': user, 'p': password, 'm': phone, 'c': content})
        send_url = smsapi + 'sms?' + data
        response = urllib.request.urlopen(send_url)
        the_page = response.read().decode('utf-8')
        print(statusStr[the_page])

        return the_page, statusStr[the_page]

    def send_msg(self, phone_num, code) :
        statusStr = {
            '0': '短信发送成功',
            '-1': '参数不全',
            '-2': '服务器空间不支持,请确认支持curl或者fsocket,联系您的空间商解决或者更换空间',
            '30': '密码错误',
            '40': '账号不存在',
            '41': '余额不足',
            '42': '账户已过期',
            '43': 'IP地址限制',
            '50': '内容含有敏感词'
        }

        smsapi = "http://api.smsbao.com/"
        # 短信平台账号
        user = 'xiangbaosong'
        # 短信平台密码
        password = self.md5('Xl2016xl')
        # 要发送的短信内容
        content = '短信内容'
        # 要发送短信的手机号码
        phone = phone_num

        content = f'{phone[-4:]}你好， 您的验证码为：{code}， 【AI创想师】'
        data = urllib.parse.urlencode({'u': user, 'p': password, 'm': phone, 'c': content})
        send_url = smsapi + 'sms?' + data
        response = urllib.request.urlopen(send_url)
        the_page = response.read().decode('utf-8')
        print(statusStr[the_page])

        return the_page, statusStr[the_page]