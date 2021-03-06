import urllib.parse
import urllib.request
import requests
import re
import os
from lxml import etree
from selenium import webdriver
# 导入界面设计文件
from PySide2.QtWidgets import QApplication, QMessageBox
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import  QIcon

class status:
    def __init__(self):
        self.keyword = ''
        self.ui = QUiLoader().load('get_car_data.ui')
        self.ui.keyword.setPlaceholderText('在这里输入搜索关键字！')
        self.ui.driver_edit.setPlaceholderText('默认路径./chromedriver.exe')
        self.ui.start.clicked.connect(self.start)
        self.ui.driver.clicked.connect(self.change_driver)
        self.ui.clear.clicked.connect(self.clear)
        self.headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, compress',
            'Accept-Language': 'en-us;q=0.5,en;q=0.3',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'
        }

        self.decode_require_list={   '车型名称':"车型",
                        '能源类型':'能源类型',
                        '环保标准':'环保标准',
                        '变速箱类型':'变速箱类型',
                        '最大马力(Ps)':"马力(Ps)",
                        '长*宽*高(mm)':'长*宽*高(mm)',
                        '工信部综合油耗(L/100km)':"工信部",                      
                        '驱动方式':"驱动方式",
                        '整备质量(kg)':"(kg)",
                        '上市时间':"上市",
                        '车身结构':"车身结构"                    
                                            }
        
        self.decode_require_list2={  '助力类型':'类型',
                                    '厂商指导价(万元)':"厂",
                                    '轴距(mm)':'(mm)',
                                    '排量(L)': '</span>(L)',
                                    '气缸数(个)':'</span>(个)'}
        
        self.decode_require_list3 = {'空调温度控制方式':"空调温度控制方式"}
        
        self.all_data = []
        self.order = []
        
        self.jskeys = []
        self.jsvalues = []

    def start(self):
        # 将开始按钮变灰，防止用户多次点击，出现未知bug
        self.ui.start.setEnabled(False)
        # 获取汽车模型具体名称,作为搜索的关键字
        self.keyword = self.ui.keyword.text()
        # 将汽车模型进行urlencode
        baidu_result_url = self.decode()
        # 将模型名称作为关键字进行搜索,返回配置页链接
        model_url=self.get_model_url(baidu_result_url)
        if model_url != '': 
            # 获取模型配置页的url
            config_url = self.get_config_url(model_url)
            if config_url != '': 
                # 解析config_url,获取需要的参数
                data = self.get_data(config_url)
                # 清洗数据
                self.clean_data(data)
                # 组合数据
                combine_data = self.combine(self.order,self.all_data)
                # 输出数据在客户端
                self.ui.result.append(combine_data)
                self.ui.result.ensureCursorVisible()
            else:
                QMessageBox.information(self.ui,'没找到！','请检查你的关键字信息是否出错或者换一个关键字匹配')
        else:
                QMessageBox.information(self.ui,'没找到！','请检查你的关键字信息是否出错或者换一个关键字匹配')
        # 开始按钮重新使能  
        self.ui.start.setEnabled(True)
    
    def change_driver(self):
        self.driver_address = self.ui.driver_edit.text()

    def clear(self):
        self.ui.result.clear()
    
    # js去混淆
    def analysis_js(self):
        #解析数据的json
        alljs = ("var rules = '2';"
                    "var document = {};"
                    "function getRules(){return rules}"
                    "document.createElement = function() {"
                    "      return {"
                    "              sheet: {"
                    "                      insertRule: function(rule, i) {"
                    "                              if (rules.length == 0) {"
                    "                                      rules = rule;"
                    "                              } else {"
                    "                                      rules = rules + '#' + rule;"
                    "                              }"
                    "                      }"
                    "              }"
                    "      }"
                    "};"
                    "document.querySelectorAll = function() {"
                    "      return {};"
                    "};"
                    "document.head = {};"
                    "document.head.appendChild = function() {};"

                    "var window = {};"
                    "window.decodeURIComponent = decodeURIComponent;")
        
        try:
            js = re.findall('(\(function\([a-zA-Z]{2}.*?_\).*?\(document\);)', self.content)
            for item in js:
                alljs = alljs + item
        except Exception as e:
            print('makejs function exception')
        newHtml = "<html><meta http-equiv='Content-Type' content='text/html; charset=utf-8' /><head></head><body>    <script type='text/javascript'>"
        alljs = newHtml + alljs+" document.write(rules)</script></body></html>"
        f = open("./test.html","w",encoding="utf-8")
        f.write(alljs)
        f.close()
        self.driver_address = "./chromedriver.exe"
        chrome_option = webdriver.ChromeOptions() 
        chrome_option.add_argument('--incognito') 
        chrome_option.add_argument('headless')
        driver = webdriver.Chrome(self.driver_address,options=chrome_option)
        all_add = os.getcwd()
        driver.get("file:///"+all_add+'/test.html')
        text = driver.find_element_by_tag_name('body').text
        tool1 = text.split('#.')
        for tool2 in tool1[1:]:
            self.jskeys.append(tool2.split(':')[0])
            self.jsvalues.append(re.findall('".*?"',tool2)[0][1:-1])
        os.remove("./test.html")


        
        

    # 对模型名称进行编码
    def decode(self,):
        decodedUrl = urllib.parse.quote(self.keyword)
        baidu_result_url='https://www.baidu.com/s?ie=utf-8&wd='+decodedUrl
        return baidu_result_url
   
    # 获取baidu中的搜索结果链接
    def get_model_url(self,baidu_result_url):
        result_url_list=[]
        result = ''
        res = requests.get(baidu_result_url,headers=self.headers,timeout = 5).text
        res_decode = etree.HTML(res)
        xpath = res_decode.xpath('//*[@class="t"]/a/@href')#用xpath来提取百度搜索结果url链接
        for i in xpath:
            url = i 
            try:
                r = requests.get(url,headers =self.headers , timeout = 2)
                result_url_list.append(r.url)
            except:
                print('无法链接')
        # 搜索汽车之家的链接
        key_word = 'www.autohome.com.cn'
        for url in result_url_list:
            if key_word  in url:
                result = url
                break
        return result
            
   
    # 生成汽车配置页链接
    def get_config_url(self,model_url):
        key_word = 'https://car.autohome.com.cn/config/spec/'
        key_number = model_url.split('/')[-2]
        if key_number.isdigit():
            model_config_url = key_word+key_number+'.html'
        else :
            model_config_url = ''
        return model_config_url

        
   
    # 解析配置页链接，获取数据
    def get_data(self,config_url):
        self.all_data = []
        self.order = []
        self.content = requests.get(config_url,headers=self.headers,timeout = 5).text
        self.analysis_js()
        data1 = ""
        # 获取配置信息
        config = re.search('var config = (.*?){1,};',self.content)
        if config!= None:
            data1 = config.group(0)
        data5 = eval(data1[13:-1])['result']['paramtypeitems']
        for data in data5:
            d1 = data['paramitems']
            for d2 in d1:
                for key,value in self.decode_require_list.items():
                    if value in d2['name']:
                        self.order.append(key)
                        self.all_data.append(d2['valueitems'])
                        break

        # 处理难处理的数据
        flag = 0
        for data in data5:
            d1 = data['paramitems']
            for d2 in d1:
                for keys,values in self.decode_require_list2.items():
                    if values in d2['name']:
                        if values == '</span>(个)':
                            if '每缸' not in d2['name']:
                                self.order.append(keys)
                                self.all_data.append(d2['valueitems'])
                                break
                        elif self.jskeys[self.jsvalues.index('助力')] in d2['name']:
                            self.order.append(keys)
                            self.all_data.append(d2['valueitems'])
                            break
                        elif self.jskeys[self.jsvalues.index('轴距')] in d2['name']:
                            self.order.append(keys)
                            self.all_data.append(d2['valueitems'])
                            break
            
                        elif self.jskeys[self.jsvalues.index('排量')] in d2['name']:
                            self.order.append(keys)
                            self.all_data.append(d2['valueitems'])
                            break

                        elif values == '厂':
                            if len(d2['name']) > 60:
                                self.order.append(keys)
                                self.all_data.append(d2['valueitems'])



        # 获取空调信息
        option = re.search('var option = (.*?)};',self.content)
        if option != None:
            data2 = option.group(0)
        data5 = eval(data2[13:-1])['result']['configtypeitems']
        for data in data5:
            d1 = data['configitems']
            for d2 in d1:
                for key,value in self.decode_require_list3.items():
                    if value in d2['name']:
                        self.order.append(key)
                        self.all_data.append(d2['valueitems'])
                        break
        

    def clean_data(self,data):
        count =0
        c2 = 0
        for label in self.order:
            c2 += 1 
            if (label == '环保标准' ) :
                count += 1
                if (count == 2):
                    self.all_data.pop(self.order.index(label))
                    self.order.pop(self.order.index(label))
               
            elif (label =='车身结构'):
                i = c2-1
                if not (re.search(r'\d', self.all_data[i][0]['value'])):
                    self.all_data.pop(i)
                    self.order.pop(i)

    def combine(self,order,data):
        require_data = ""
        for i,j in zip(order,data[:-1]):
            if i == '助力类型':
                if '电动' in j[0]['value']:
                    require_data = require_data + i +':'+ '电动助力  '
                else:
                    require_data = require_data + i +':'+ '机械液压助力  '
            elif i == '驱动方式':
                str = re.findall('[\u4e00-\u9fa5]',j[0]['value'])
                res = ""
                ss  =[]
                too = re.findall("'.*?'",j[0]['value'])
                for to in too:
                    ss.append(to[1:-1])
                for s in ss:
                    str.append(self.jsvalues[self.jskeys.index(s)])
                for t in str:
                    res += t
                require_data = require_data + i +':'+ res +'  '
                    

            else:
                require_data = require_data + i +':'+ j[0]['value']+'  '
        require_data = require_data + order[-1] +':'+ data[-1][0]['sublist'][0]['subname']+'  '
        return require_data


app = QApplication([])
app.setWindowIcon(QIcon('logo.png'))
test = status()
test.ui.show()
app.exec_()
test.update_flag=False


