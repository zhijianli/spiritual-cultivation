# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import sys
import random
from typing import List

from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> Dysmsapi20170525Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 必填，您的 AccessKey ID,
            access_key_id=access_key_id,
            # 必填，您的 AccessKey Secret,
            access_key_secret=access_key_secret
        )
        # 访问的域名
        config.endpoint = f'dysmsapi.aliyuncs.com'
        return Dysmsapi20170525Client(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:

        statusStr = {
            'OK': '短信发送成功',  # 短信发送成功
            'isv.AMOUNT_NOT_ENOUGH': '余额不足',  # 余额不足
            'isv.DENY_IP_RANGE': 'IP地址限制',  # IP地址限制
        }
        statusNum = {
            'OK': '0',  # 短信发送成功
            'isv.AMOUNT_NOT_ENOUGH': '41',  # 余额不足
            'isv.DENY_IP_RANGE': '43',  # IP地址限制
        }
        status = 'OK'

        # 工程代码泄露可能会导致AccessKey泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html
        client = Sample.create_client('LTAI5tSiuoVc2FPqUkKxuV1t', 'zQ5U3Q2lbUuWP3s1hE4QClvDDgkq94')
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            phone_numbers=args[0],
            sign_name='AI创想师',
            template_code='SMS_276230480',
            template_param='{"code":"'+str(args[1])+'"}'
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            responses = client.send_sms_with_options(send_sms_request, runtime)
            code = responses.body.code
        except Exception as error:
            # 如有需要，请打印 error
            UtilClient.assert_as_string(error.message)

        return statusNum[code], statusStr[code]

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        # 工程代码泄露可能会导致AccessKey泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html
        client = Sample.create_client('LTAI5tSiuoVc2FPqUkKxuV1t', 'zQ5U3Q2lbUuWP3s1hE4QClvDDgkq94')
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            phone_numbers='13616532539',
            sign_name='AI创想师',
            template_code='SMS_276230480',
            template_param='{"code":"654321"}'
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            await client.send_sms_with_options_async(send_sms_request, runtime)
        except Exception as error:
            # 如有需要，请打印 error
            UtilClient.assert_as_string(error.message)


if __name__ == '__main__':
    code = random.randint(100000, 999999)
    code = str(code)
    phone_number = '13616532539'
    status, desc = Sample.main([phone_number,code])
    print(status, desc)