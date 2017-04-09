import scrapy
import time
import re
import sys
from hahadiaoyu.items import HahadiaoyuItem
from bs4 import BeautifulSoup 

reload(sys)
sys.setdefaultencoding('gbk')

class HahadiaoyuSpider(scrapy.Spider):
    name = "hahadiaoyu"
    allowed_domains = ["hahadiaoyu.com"]
    start_urls = [
        "http://www.hahadiaoyu.com/forum.php?gid=36"
    ]

    def parse(self, response):
        data = response.body  
        soup = BeautifulSoup(data, "html5lib") 
        for tag in soup.find_all("td",class_=re.compile("fl_icn")):
          item = HahadiaoyuItem()
          item["link"] = tag.find("a").get('href')
          yield scrapy.Request(item['link'], self.parse_item)

    def parse_item(self, response):
        data = response.body  
        soup = BeautifulSoup(data, "html5lib")
        for tag in soup.find_all("tbody",id=re.compile("^(normalthread_)\d+$|^(stickthread_)\d+$")):
          item = HahadiaoyuItem()
          item["author"] = tag.find("td","by").cite.a.get_text() 
          item["title"] = tag.find("a",class_="s xst").get_text()
          item["link"] = tag.find("a",class_="s xst").get('href')
          yield scrapy.Request(url=item['link'], meta={'item':item}, callback=self.parse_post)

        nextpage = soup.find("a",class_="nxt")
        if nextpage:
          yield scrapy.Request(nextpage.get("href"), self.parse_item)

    def parse_post(self, response):
        data = response.body
        soup = BeautifulSoup(data, "html5lib")
        divlst = soup.find_all("div","attach_nopermission attach_tips")
        for rdiv in divlst :
          rdiv.decompose()
        table = soup.find("div","t_fsz").table
        content = []
        for txt in table.find_all("td",id=re.compile("^(postmessage_)\d+$")):
          content.append(txt.get_text())
        item = response.meta['item']
        item['content'] = "".join(content)
        item['content'] = item['content'].replace(u'\xa0', u' ').decode("gbk", "ignore")
        yield item