# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import signals
import codecs
from twisted.enterprise import adbapi
from datetime import datetime
from hashlib import md5
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.exceptions import DropItem
from scrapy.http import Request
import MySQLdb
import MySQLdb.cursors
class TutorialPipeline(object):
    def process_item(self, item, spider):
        return item
class MySQLStorePipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool
    
    @classmethod
    def from_settings(cls, settings):
        dbargs = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset='utf8',
            cursorclass = MySQLdb.cursors.DictCursor,
            use_unicode= True,
        )
        dbpool = adbapi.ConnectionPool('MySQLdb', **dbargs)
        return cls(dbpool)

    #pipeline默认调用
    def process_item(self, item, spider):
        d = self.dbpool.runInteraction(self._do_upinsert, item, spider)
        d.addErrback(self._handle_error, item, spider)
  #      d.addBoth(lambda _: item)
        return item
    #将每行更新或写入数据库中
    def _do_upinsert(self, conn, item, spider):
        linkmd5id = self._get_linkmd5id(item)
        print linkmd5id
        now = datetime.utcnow().replace(microsecond=0).isoformat(' ')
        conn.execute("""
                select 1 from hahadiaoyu where linkmd5id = %s
        """, (linkmd5id, ))
        ret = conn.fetchone()

        if ret:
            conn.execute("""
               update hahadiaoyu set title = %s,category=%s, content = %s, link = %s, author = %s, updated = %s where linkmd5id = %s
               """, (item['title'], item['category'],item['content'], item['link'], item['author'], now, linkmd5id))
          #  print """
          #      update hahadiaoyu set title = %s, content = %s, link = %s, author = %s, updated = %s where linkmd5id = %s
          #  """, (item['title'], item['content'], item['link'], item['author'], now, linkmd5id)
        else:
            conn.execute("""
                insert into hahadiaoyu(linkmd5id, title,category, content, link, author, updated) 
                values(%s, %s, %s, %s, %s, %s, %s)
            """, (linkmd5id, item['title'],item['category'], item['content'], item['link'], item['author'], now))
         #   print """
         #      insert into hahadiaoyu(linkmd5id, title, content, link, author, updated)
         #       values(%s, %s, %s, %s, %s, %s)
         #   """, (linkmd5id, item['title'], item['content'], item['link'], item['author'], now)
    #获取url的md5编码
    def _get_linkmd5id(self, item):
        #url进行md5处理，为避免重复采集设计
        return md5(item['link']).hexdigest()
    #异常处理
    def _handle_error(self, failure, item, spider):
        print(failure)

class MyImagePipelines(ImagesPipeline):
    def get_media_requests(self, item, info):
            for image_url in item['image_urls']:
                # 这里我把item传过去,因为后面需要用item里面的name
                yield Request(image_url, meta={'item': item})
    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no images")
        return item
    def file_path(self, request, response=None, info=None):
        item = request.meta['item']
        # 从URL提取图片的文件名
        image_guid = request.url.split('/')[-1]
        # 拼接最终的文件名,格式:full/
        filename = u'full/{0}/{1}'.format(self._get_md5id(item), image_guid)
        return filename
    
    def _get_md5id(self, item):
        #url进行md5处理，为避免重复采集设计
        return md5(item['link']).hexdigest()