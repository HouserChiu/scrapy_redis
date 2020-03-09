# -*- coding: utf-8 -*-
import scrapy
import re
from fang.items import NewHouseItem,ESFHouseItem
from scrapy_redis.spiders import RedisSpider

class SfwSpider(RedisSpider):
    name = 'sfw'
    allowed_domains = ['fang.com']
    # 改成分布式
    # start_urls = ['https://www.fang.com/SoufunFamily.htm']
    redis_key = 'fang:start_urls'

    def parse(self, response):
        trs = response.xpath("//div[@class='outCont']//tr")
        province = None
        for tr in trs:
            tds = tr.xpath(".//td[not(@class)]")
            # 省份在第一个tds标签里
            province_td = tds[0]
            province_text = province_td.xpath(".//text()").get()
            province_text = re.sub(r'\s', '', province_text)
            if province_text:
                province = province_text
            #不爬取海外城市房源
            if province == '其它':
                continue
            # 城市在第二个tds标签里
            city_td = tds[1]
            city_links = city_td.xpath(".//a")
            for city_link in city_links:
                city = city_link.xpath(".//text()").get()
                city_url = city_link.xpath(".//@href").get()
                #构建新房的url
                url_model = city_url.split('.')
                schme = url_model[0]  #https://anqing
                domain = url_model[1] #fang
                end = url_model[2] #com/
                newhouse_url = schme + '.newhouse.' + domain + '.' + end + 'house/s/'
                #构建二手房的url
                esf_url = schme + '.esf.' + domain + '.' + end
                # print('城市: %s%s' %(province,city))
                # print('新房链接: %s' %(newhouse_url))
                # print('二手房链接：%s' %(esf_url))
                # 已经得到了省份和城市的信息，传递
                yield scrapy.Request(url=newhouse_url,callback=self.parse_newhouse,meta={'info':(province,city)})
                yield scrapy.Request(url=esf_url,callback=self.parse_esf,meta={'info':(province,city)})


    def parse_newhouse(self,response):
        province,city = response.meta.get('info')
        lis = response.xpath("//div[contains(@class,'nl_con')]/ul/li")
        for li in lis:
            name = li.xpath(".//div[@class='nlcd_name']/a/text()").get()

            house_type_list = li.xpath(".//div[contains(@class,'house_type')]/a/text()").getall()
            house_type_list = list(map(lambda x:re.sub(r'\s','',x),house_type_list))
            rooms = list(filter(lambda x:x.endswith('居'),house_type_list))
            area = ''.join(li.xpath(".//div[contains(@class,'house_type')]/text()").getall())
            area = re.sub(r'\s|－|/', '', area)
            address = li.xpath("//div[@class='address']/a/@title").get()
            #district = li.xpath("//span[@class='sngrey']").get()
            district = ''.join(li.xpath("//div[@class='address']/a//text()").getall())
            #district = re.search(r'.*\[(.*?)\].*',district_text).group(1)
            sale = li.xpath(".//div[contains(@class,'fangyuan')]/span/text()").get()
            price = ''.join(li.xpath(".//div[@class='nhouse_price']//text()").getall())
            price = re.sub(r'\s|广告','',price)
            origin_url = li.xpath(".//div[@class='nlcd_name']/a/@href").get()

            item = NewHouseItem(name=name,rooms=rooms,area=area,address=address,district=district,sale=sale,price=price,origin_url=origin_url,province=province,city=city)
            yield item

        next_url = response.xpath("//div[@class='page']//a[@class='next']/@href").get()
        if next_url:
            # join到newhouse_url
            yield scrapy.Request(url=response.urljoin(next_url),callback=self.parse_newhouse,meta={'info':(province,city)})


    def parse_esf(self,response):
        province,city = response.meta.get('info')
        dls = response.xpath("//div[contains(@class,'shop_list')]/dl")
        for dl in dls:
            item = ESFHouseItem(province=province,city=city)
            item['name'] = dl.xpath(".//p[@class='add_shop']/a/@title").get()
            infos = dl.xpath(".//p[@class='tel_shop']/text()").getall()
            infos = list(map(lambda x:re.sub(r'\s', '', x),infos))
            for info in infos:
                if "厅" in info:
                    item['rooms'] = info
                elif "层" in info:
                    item['floor'] = info
                elif "向" in info:
                    item['toward'] = info
                elif "m" in info:
                    item['area'] = info
                else:
                    item['year'] = info

            item['address'] = dl.xpath(".//p[@class='add_shop']/span/text()").get()
            prices = ''.join(dl.xpath(".//dd[@class='price_right']/span[1]//text()").getall())
            item['price'] = re.sub(r'\s', '', prices)
            item['unit'] = ''.join(dl.xpath(".//dd[@class='price_right']/span[2]//text()").getall())
            detail_url = dl.xpath(".//h4[@class='clearfix']/a/@href").get()
            origin_url = response.urljoin(detail_url)
            item['origin_url'] = origin_url
            yield item
        next_url = response.xpath("//div[@class='page_al']/p/a/@href").get()
        yield scrapy.Request(url=response.urljoin(next_url),callback=self.parse_esf,meta={"info":(province,city)})

















