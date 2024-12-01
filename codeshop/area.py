from urllib.parse import urlencode
from urllib.request import urlopen
import json

def arnum(areanum):
    area=areanum.split('查地方 ')[1]
    ans=str(mareacode(area))
    ans=ans.replace('[','').replace(']','')
    if "1000060" in ans:
        return "没有查到该区号，请确认区号是否正确，指令有无多余标点字符和空格。"
    else:
        return "区号"+area+"的对应地为: "+ans
def arname(areaname):
    area=areaname.split('查区号 ')[1]
    if "三沙" in area:
        ans="0898"
    else:
        ans=str(mareaname(area))
        ans=ans.replace('[','').replace(']','')
    if "1000060" in ans:
        return "没有查到该地方，请确认地方是否正确，是否为地级行政区划正式名称，指令有无多余标点字符和空格。"
    else:
        return "地方 "+area+" 的区号为: "+ans
def mareacode(area):#根据区号查询地方
    url = 'http://api.k780.com'
    params = {
      'app' : 'life.areacode',
      'areacode' : area,
      'appkey' : '73847',
      'sign' : '66107e84b89b9eba439b35daa9eb54a4',
      'format' : 'json',     
    }
    params = urlencode(params)
    f = urlopen('%s?%s' % (url, params))
    nowapi_call = f.read()
    a_result = json.loads(nowapi_call)
    if a_result:
      if a_result['success'] != '0':
        print(a_result['result'])
        data=a_result['result']
        simcalls = [item['simcall'] for item in data['lists']]  
        return simcalls
      else:
        print(a_result['msgid']+' '+a_result['msg'])
        return a_result['msgid']+' '+a_result['msg']
    else:
      print('Request nowapi fail.')
      return 'Request nowapi fail.'
def mareaname(area):#根据地方查询区号
    url = 'http://api.k780.com'
    params = {
      'app' : 'life.areacode',
      'areaname' : area,
      'appkey' : '73847',
      'sign' : '66107e84b89b9eba439b35daa9eb54a4',
      'format' : 'json',
    }
    params = urlencode(params)
    f = urlopen('%s?%s' % (url, params))
    nowapi_call = f.read()
    a_result = json.loads(nowapi_call)
    if a_result:
      if a_result['success'] != '0':
        print(a_result['result'])
        data=a_result['result']
        simcalls = [item['areacode'] for item in data['lists']]  
        return simcalls
      else:
        return a_result['msgid']+' '+a_result['msg']
    else:
      return 'Request nowapi fail.'