# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from getLecture.items import GetlectureItem
import os

DOUSE_IDS = {"并行与分布式":121448,"计算机网络":121020,"软件安全":121020,"网络认证":121020}
HEADER = "http://sep.ucas.ac.cn/slogin"
ALL_COURSE = 'http://sep.ucas.ac.cn/portal/site/16/801'
COURSE = "http://course.ucas.ac.cn"
specific_course = COURSE + "/portal/site/" + str(121020)
class ExampleSpider(scrapy.Spider):
    name = "course"
    allowed_domains = ["ucas.ac.cn"]
    # start_urls = [HEADER + str(course) for course in DOUSE_IDS.values()]
    start_urls = ["http://sep.ucas.ac.cn/slogin"]

    def __init__(self):
        self.headers = {
                        'Accept-Encoding':'gzip,deflate,sdch',
                        'Accept-Language':'en,zh-CN;q=0.8,zh;q=0.6',
                        'Cache-Control':'max-age=0',
                        'Connection':'keep-alive',
                        }
    def start_requests(self):
        yield Request(HEADER,
                            meta = {'cookiejar': 1},
                            callback = self.login)

    def _log_page(self, response, filename):
        with open(filename, 'w') as f:
            f.write("%s\n%s\n%s\n" % (response.url, response.meta, response.body))

    def login(self,response):
        return [scrapy.FormRequest.from_response(response,
                    formdata={'userName': '******@ict.ac.cn', 'pwd': '*********','sb':'sb'},
                    meta = {'cookiejar':response.meta['cookiejar']},
                    callback=self.after_login)]


    def after_login(self,response):
        return Request( ALL_COURSE,
                        meta = {'cookiejar':response.meta['cookiejar']},
                        headers = self.headers,
                        callback = self.parse_report)

    def parse_report(self,response):
        hxs = HtmlXPathSelector(response)
        targets = hxs.select('//meta[contains(@http-equiv,"refresh")]')
        for i in targets:
            content = i.select('@content').re(r'http.*')
            print content


        yield Request( str(content[0]),
                        meta = {'cookiejar':response.meta['cookiejar']},
                        headers = self.headers,
                        callback = self.get_course)


    def get_course(self,response):
        hxs2 = HtmlXPathSelector(response)
        src = hxs2.select('//frame[contains(@src,"portal")]/@src').extract()
        url = COURSE+str(src[0])
        yield Request( url,
                        meta = {'cookiejar':response.meta['cookiejar']},
                        headers = self.headers,
                        callback = self.get_course2)

    def get_course2(self,response):

        yield Request( specific_course,
                        meta = {'cookiejar':response.meta['cookiejar']},
                        headers = self.headers,
                        callback = self.get_specific)

    def get_specific(self,response):
        hxs = HtmlXPathSelector(response)
        src = hxs.select('//a[contains(@class,"icon-sakai-resources")]/@href').extract()[0]
        print src
        yield Request( src,
                        meta = {'cookiejar':response.meta['cookiejar']},
                        headers = self.headers,
                        callback = self.get_lectures)
    def get_lectures(self,response):
        hxs = HtmlXPathSelector(response)
        src = hxs.select('//iframe[contains(@class,"portletMainIframe")]/@src').extract()[0]
        print src
        yield Request( src,
                        meta = {'cookiejar':response.meta['cookiejar']},
                        headers = self.headers,
                        callback = self.get_real_course)

    def get_real_course(self,response):
        hxs = HtmlXPathSelector(response)
        resources = hxs.select('//td[contains(@class,"specialLink")]')

        for item in resources:
            url =  item.select('.//a/@href').extract()[0]
            # print url.encode('utf-8')
            if u'http' in url:
                yield Request(url,
                              meta = {'cookiejar':response.meta['cookiejar']},
                              headers = self.headers,
                              callback=self.save_file)
            # url = str(item.select('.//a/@href').extract()[0])
            # yield Request(url, callback=self.save_file)


    def save_file(self,response):

        path = os.path.join( "/Users/qiaoyang/Desktop/test" , response.url.split('/')[-1])
        with open(path, "wb") as f:
            f.write(response.body)