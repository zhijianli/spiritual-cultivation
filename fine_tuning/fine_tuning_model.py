import os
import openai
import time
from common.config import conf, load_config
import json


openai.api_key = conf().get('open_ai_api_key')
file_path = "/home/mocuili/github/spiritual-cultivation/test/fine-tuning-test.jsonl"
#
# # 上传文件
# upload_result = openai.File.create(
#   file=open(file_path, "rb"),
#   purpose='fine-tune'
# )
#
# file_id = upload_result['id']
# print("file_id = "+file_id)
#
# time.sleep(10)
#
# # 开始训练
# fineTuning_result = openai.FineTuningJob.create(training_file=file_id, model="gpt-3.5-turbo")
# print(fineTuning_result)
# time.sleep(30)

# 查询微调模型状态

while True:
    status_result = openai.FineTuningJob.retrieve('ftjob-cf8YGSeA8pj2xCVsan13JUFw')

    fine_tuned_model = status_result['fine_tuned_model']

    if not fine_tuned_model:
        print("微调未完成")
        time.sleep(10)
    else:
        print("微调已完成，fine_tuned_model=" + fine_tuned_model)

        # 使用模型
        response = openai.ChatCompletion.create(
            model=fine_tuned_model,
            messages=[{'role': 'system', 'content': '我想让你扮演釜托寺的知客僧。我作为一名游客将向你提出各种问题。我希望你只作为釜托寺的知客僧来回答。'},
                      {'role': 'user', 'content': '釜托寺需要义工吗？'}],
        )

        print(response.choices[0].message['content'])
        break







# # List 10 fine-tuning jobs
# result2 = openai.FineTuningJob.list(limit=10)
# print(result2)
#
# # Cancel a job
# openai.FineTuningJob.cancel("ft-abc123")
#
# # List up to 10 events from a fine-tuning job
# openai.FineTuningJob.list_events(id="ft-abc123", limit=10)
#
# # Delete a fine-tuned model (must be an owner of the org the model was created in)
# openai.Model.delete("ft-abc123")


