import json
from alibabacloud_iqs20241111 import models
from alibabacloud_iqs20241111.client import Client
from alibabacloud_tea_openapi import models as open_api_models
from Tea.exceptions import TeaException


class Search:
    def __init__(self):
        with open('../qq-bot.json', 'r', encoding='utf-8') as file:
            cg = json.load(file)
        config = open_api_models.Config(**cg['search_online'])
        config.endpoint = f'iqs.cn-zhangjiakou.aliyuncs.com'        
        self.client = Client(config)

    
    def process(self, response):
        results=''
        for page in response.body.page_items:
            results+=f'title:{page.title}\ncontent:{page.main_text}\n'
        return results

    def query(self, problem) -> None:
        run_instances_request = models.GenericSearchRequest(
            query=problem,
            time_range="NoLimit"
        )
        try:
            response = self.client.generic_search(run_instances_request)
            #print(f"api success, requestId:{response.body.request_id}, size :{len(response.body.page_items)}")
            res = self.process(response)
            #print(res)
            return res
        except TeaException as e:
            code = e.code
            request_id = e.data.get("requestId")
            message = e.data.get("message")
            print(f"api exception, requestId:{request_id}, code:{code}, message:{message}")

search = Search()
def search_online(problem):
    return search.query(problem)


if __name__ == '__main__':
    problem = input('问题：')
    print(search.query(problem))