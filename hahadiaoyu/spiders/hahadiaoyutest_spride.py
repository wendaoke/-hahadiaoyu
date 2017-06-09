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
    name = "hahadiaoyutest"
    allowed_domains = ["hahadiaoyu.com"]
    start_urls = [
        "http://www.hahadiaoyu.com/6006-1-35.html"
    ]

    def parse(self, response):
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
          
        item =  HahadiaoyuItem()
        item['content'] = ",".join(content)
        print  item['content']
        #item['content'] = item['content'].replace(u'\xa0', u' ').decode("gbk", "ignore")
        images = soup.find_all("img",id=re.compile("^(aimg_)\d+$"))
        image_urls= []
        item['image_urls'] = [urljoin_rfc(base_url, img["file"]) for img in images]   
        yield item