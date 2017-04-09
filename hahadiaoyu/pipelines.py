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
                update hahadiaoyu set title = %s, content = %s, link = %s, author = %s, updated = %s where linkmd5id = %s
            """, (item['title'], item['content'], item['link'], item['author'], now, linkmd5id))
          #  print """
          #      update hahadiaoyu set title = %s, content = %s, link = %s, author = %s, updated = %s where linkmd5id = %s
          #  """, (item['title'], item['content'], item['link'], item['author'], now, linkmd5id)
        else:
            conn.execute("""
                insert into hahadiaoyu(linkmd5id, title, content, link, author, updated) 
                values(%s, %s, %s, %s, %s, %s)
            """, (linkmd5id, item['title'], item['content'], item['link'], item['author'], now))
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