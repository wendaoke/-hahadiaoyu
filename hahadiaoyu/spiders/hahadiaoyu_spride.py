import scrapy
import time
import re
import sys
from hahadiaoyu.items import HahadiaoyuItem
from bs4 import BeautifulSoup 
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc
reload(sys)
sys.setdefaultencoding('gbk')

class HahadiaoyuSpider(scrapy.Spider):
    name = "hahadiaoyu"
    allowed_domains = ["hahadiaoyu.com"]
    start_urls = [
      "http://www.hahadiaoyu.com/forum.php?gid=1",
        "http://www.hahadiaoyu.com/forum.php?gid=36"
    ]

    def parse(self, response):
        data = response.body  
        soup = BeautifulSoup(data, "html5lib") 
        for tag in soup.find_all("td",class_=re.compile("fl_icn")):
          item = HahadiaoyuItem()
          item["link"] = tag.find("a").get('href')
          yield scrapy.Request(url=item['link'], callback=self.parse_item)

    def parse_item(self, response):
        data = response.body  
        soup = BeautifulSoup(data, "html5lib")
        item = HahadiaoyuItem()
        item["category"] = soup.find("h1",class_="xs2").a.get_text()
        for tag in soup.find_all("tbody",id=re.compile("^(normalthread_)\d+$|^(stickthread_)\d+$")):
          item["author"] = tag.find("td","by").cite.a.get_text() 
          item["title"] = tag.find("a",class_="s xst").get_text()
          item["link"] = tag.find("a",class_="s xst").get('href')
          print item
          yield scrapy.Request(url=item['link'], meta={'item':item}, callback=self.parse_post)

        nextpage = soup.find("a",class_="nxt")
        if nextpage:
          yield scrapy.Request(nextpage.get("href"), self.parse_item)

    def parse_post(self, response):
        data = response.body
        base_url = get_base_url(response)
        soup = BeautifulSoup(data, "html5lib")
        divlst = soup.find_all("div","attach_nopermission attach_tips")
        for rdiv in divlst :
          rdiv.decompose()
        content = []
        typeoption = soup.find("div","typeoption")
        if typeoption:
          table = typeoption.table          
          for txt in table.find_all("td"):
            content.append(txt.get_text())    

        table = soup.find("div","t_fsz").table
        if table:
          for txt in table.find_all("td",id=re.compile("^(postmessage_)\d+$")):
            content.append(txt.get_text())
          
        item = response.meta['item']
        item['content'] = ",".join(content)
        #item['content'] = item['content'].replace(u'\xa0', u' ').decode("gbk", "ignore")
        images = soup.find_all("img",id=re.compile("^(aimg_)\d+$"))
        image_urls= []
        item['image_urls'] = [urljoin_rfc(base_url, img["file"]) for img in images]   
        yield item