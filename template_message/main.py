#!/usr/bin/python3
#coding=utf-8
import Iciba

if __name__ == '__main__':
    # 微信配置
    wechat_config = {
        # 'appid': 'wx6877f171abaa0b50', #(No.1)此处填写公众号的appid
        # 'appsecret': 'ffeef22284a962743fa6027f86983b36', #(No.2)此处填写公众号的appsecret
        # 'template_id': '0dJTMvyqnmPvfKe4CQ34Oh-ZOkAQf4Kms_X9onsbHrg' #(No.3)此处填写公众号的模板消息ID

        'appid': 'wx75b9f68f06a4531b',  # (No.1)此处填写公众号的appid
        'appsecret': '53be5b50004bc6aa5b55094d74ea709c',  # (No.2)此处填写公众号的appsecret
        'template_id': 'yLhYlHr50EUbuGHkgNX_oulRSnWqyGC37i7Q59DhcfY'
    }
    
    # 用户列表
    openids = [
        # 'ovQOB6YIelUbTBiZEhPYC9N_Iwd8', #(No.4)此处填写你的微信号（微信公众平台上的微信号）
        # 'oAl8yxMAhhzJLu7tYnGy1WZXIp7I', #刘师兄的openid
        'oAl8yxC88GIzV15S3mM-lcn1a2OU', #我自己的openid
        # 'oAl8yxKkfsAIutHtJhblnC27pKkE',#法净的openid
        #'xxxxx', #如果有多个用户也可以
        #'xxxxx',
    ]

    # 执行
    icb = Iciba.iciba(wechat_config)

    '''
    run()方法可以传入openids列表，也可不传参数
    不传参数则对微信公众号的所有用户进行群发
    '''
    # icb.run(openids)
    icb.run()


