# -*- coding: utf-8 -*-

import re

from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from cosmebot.items import Product, Review, User, Brand


def convert_to_float_if_float(s):
    try:
        return float(s)
    except ValueError:
        return s


def convert_to_int_if_int(s):
    try:
        return int(s)
    except ValueError:
        return s


class AtcosmeSpider(CrawlSpider):
    name = "atcosme"
    allowed_domains = ["cosme.net"]
    download_delay = 1.0

    start_urls = (
        'http://www.cosme.net/',
    )

    rules = (
        # Product
        # 'http://www.cosme.net/product/product_id/10084858/top'
        Rule(LxmlLinkExtractor(allow=(r'product/product_id/\d+/top',)),
             follow=True, callback='parse_product'),

        # Review
        # Review list for a product
        # 'http://www.cosme.net/product/product_id/10084858/reviews'
        # 'http://www.cosme.net/product/product_id/10084858/reviews/p/2'
        Rule(LxmlLinkExtractor(allow=(r'product/product_id/\d+/reviews(/p/\d+)?$',)),
             follow=True),

        # Review detail
        # 'http://www.cosme.net/product/product_id/10084858/review/505170404'
        Rule(LxmlLinkExtractor(allow=(r'product/product_id/\d+/review/\d+$',)),
             follow=True, callback='parse_review'),

        # Review list for a user
        # 'http://my.cosme.net/open_entry_reviewlist/list/user_id/1359201/dst/1'

        # User
        # 'http://my.cosme.net/open_top/show/user_id/1359201'
        Rule(LxmlLinkExtractor(allow=(r'open_top/show/user_id/\d+$',)),
             follow=False, callback='parse_user'),

        # Brand
        # 'http://www.cosme.net/brand/brand_id/493/top'
        Rule(LxmlLinkExtractor(allow=(r'brand/brand_id/\d+/top$',)),
             follow=True, callback='parse_brand'),

        # Brand -> Product Pagination
        # http://www.cosme.net/brand/brand_id/493/products
        # http://www.cosme.net/brand/brand_id/493/products/page-5
        Rule(LxmlLinkExtractor(allow=(r'brand/brand_id/\d+/products/(page-\d+)?$',)),
             follow=True),
    )

    def parse_review(self, response):
        review = Review()

        user_link = response.xpath('//div[@class="reviewer-info"]/a[1]/@href') \
                            .extract()[0]
        review['user_id'] = int(re.findall('user_id/(\d+)', user_link)[0])
        review['product_id'] = int(re.findall(r'product/product_id/(\d+)',
                                   response.url)[0])
        review['review_id'] = int(re.findall(r'review/(\d+)', response.url)[0])

        rating = response.css('p.reviewer-rating::text').extract()[0]
        review['rating'] = convert_to_int_if_int(rating)

        if response.css("p.mobile-date"):
            date = response.css("p.mobile-date::text").extract()[0]
        else:
            date = response.css("p.date::text").extract()[0]
        review['date'] = date

        # FIXME: remove newline from <a>
        review['text'] = [sentence.strip() for sentence
                          in response.css('p.read *::text').extract()
                          if sentence.strip()]
        review['product_type'] = response.css("dl.item-status > dd > ul > li::text") \
                                         .extract()

        self._parse_review_tag_list(response, review)
        yield review

    _tag_mappings = {
        u'購入場所': 'purchase_location',
        u'効果': 'effects',
        u'色': 'colors',
        u'商品情報': 'product_tags',
        u'関連ワード': 'related_words',
    }

    def _parse_review_tag_list(self, response, review):
        def _group_dds(tags):
            dt = None
            dds = []
            for tag in tags:
                if tag.extract().startswith('<dt>'):
                    if dt and dds:
                        yield dt, dds
                    dt = tag
                    dds = []
                elif tag.extract().startswith('<dd>'):
                    dds.append(tag)
            if dt and dds:
                yield dt, dds

        children = response.css('div.tag-list > dl > dt,div.tag-list > dl > dd')
        for dt, dds in _group_dds(children):
            key = dt.xpath('./text()').extract()[0]
            values = [dd.xpath('./descendant-or-self::*/text()').extract()[0]
                      for dd in dds]
            if key in self._tag_mappings:
                review[self._tag_mappings[key]] = values

    def parse_product(self, response):
        product = Product()

        product['product_id'] = int(re.findall(r'product/product_id/(\d+)/top',
                                    response.url)[0])
        product['name'] = response.css('h2.item-name > *.pdct-name > a::text') \
                                  .extract()[0]

        product['maker'] = response.css('dl.maker > dd > a::text').extract()[0]
        product['brand'] = response.css('dl.brand-name > dd > a::text').extract()[0]

        product['description'] = [
            sentence.strip() for sentence
            in response.css('dl.item-description > dd').xpath('.//text()').extract()
            if sentence.strip()
        ]

        category_spans = response.css('dl.item-category > dd > span')
        product['categories'] = [
            u' '.join([categ.strip() for categ in category])
            for category in [category_span.xpath('.//text()').extract()
                             for category_span in category_spans]
        ]

        rating = response.xpath("//p[@itemprop='ratingValue']/text()").extract()[0]
        product['rating'] = convert_to_float_if_float(rating)

        point = response.css('p.point::text').extract()
        if point:
            product['point'] = convert_to_float_if_float(point[0].replace('pt', ''))

        self._parse_product_rating(response, product)

        review_count = response.css('ul.select-top li.review > a > span.num::text') \
                               .extract()
        if review_count:
            review_count = review_count[0].replace('(', '').replace(')', '')
            product['review_count'] = convert_to_int_if_int(review_count)

        self._parse_product_counts(response, product)

        colors = response.css('.color-ptn span.color-txt::text').extract()
        if colors:
            product['colors'] = colors

        yield product

    _product_count_mapping = {
        u'Like': 'like_count',
        u'Have': 'have_count',
    }

    def _parse_product_counts(self, response, product):
        lis = response.css('div.info-related > ul.rev-btn > li')
        for li in lis:
            text = u' '.join(li.xpath('.//text()').extract())

            for key in self._product_count_mapping:
                if key not in text:
                    continue
                count = li.css('span.num::text').extract()
                if count:
                    mapped_key = self._product_count_mapping[key]
                    product[mapped_key] = convert_to_int_if_int(count[0])

    _product_rating_mapping = {
        u'ランキング': 'ranking',
        u'容量・本体価格': '-',
        u'発売日': 'sale_date',
    }

    def _parse_product_rating(self, response, product):
        lis = response.css('div.rating > ul.info-rating > li')
        for li in lis:
            key = li.css('.info-ttl::text').extract()[0]
            if key not in self._product_rating_mapping:
                continue

            if key == u'ランキング':
                ranking = li.css('.info-ranking > span::text').extract()
                category = li.css('.info-ctg > a::text').extract()

                value = []
                if ranking:
                    value.append(convert_to_int_if_int(ranking[0]))
                if category:
                    value.append(category[0])
            else:
                value = li.css('.info-desc::text').extract()[0]

            if key == u'容量・本体価格':
                if u'・' in value:
                    values = value.split(u'・')
                    product['volume'] = values[0].strip()
                    product['price'] = values[1].strip()
                else:
                    if u'円' in value:
                        product['price'] = value
                    else:
                        product['volume'] = value
            else:
                product[self._product_rating_mapping[key]] = value

    def parse_user(self, response):
        user = User()

        user['user_id'] = int(re.findall(r'user_id/(\d+)', response.url)[0])
        user['name'] = response.css('p.name > span::text').extract()[0]

        review_count = response.css('div#new-review > h3 > span.number::text') \
                               .extract()[0].replace(u'件', '')
        user['review_count'] = convert_to_int_if_int(review_count)

        user['verified'] = bool(response.css('span.ico-cmn-auth'))

        self._parse_user_personal(response, user)
        self._parse_user_activities(response, user)

        brand_count = response.css('div#brand > p.view-more > a::text').extract()
        if brand_count:
            count = re.findall('\d+', brand_count[0])
            user['favorite_brand_count'] = convert_to_int_if_int(count[0])

        yield user

    _personal_mappings = {
        u'肌質': 'skin_type',
        u'髪質': 'hair_type',
        u'髪量': 'hair_volume',
        u'星座': 'zodiac',
        u'血液型': 'blood_type',
    }

    def _parse_user_personal(self, response, user):
        for li in response.css('ul.personal > li'):
            values = li.xpath('./text()').extract()
            key = values[0]

            # HACK: the html structure sucks, so we have to resort to counting
            if len(values) == 1:
                # Contained <a>
                value = li.xpath('./a/text()').extract()[0]
            else:
                # Did not contain <a>
                value = values[1]

            if key == u'年齢':
                age = value.replace(u'歳', '')
                user['age'] = convert_to_int_if_int(age)
            elif key in self._personal_mappings:
                user[self._personal_mappings[key]] = value

    _user_activity_mapping = {
        u'chieco': 'qa_count',
        u'お気入りﾒﾝﾊﾞｰ': 'favorite_user_count',
        u'Fan数': 'fan_count',
    }

    def _parse_user_activities(self, response, user):
        lis = response.css('ul.activities > li')
        for li in lis:
            text = u' '.join(li.xpath('.//text()').extract())
            for key in self._user_activity_mapping:
                if key not in text:
                    continue
                count = li.css('span::text').extract()
                if count:
                    mapped_key = self._user_activity_mapping[key]
                    user[mapped_key] = convert_to_int_if_int(count[0])

    def parse_brand(self, response):
        brand = Brand()

        brand['brand_id'] = int(re.findall(r'brand/brand_id/(\d+)/top',
                                response.url)[0])
        brand['name'] = response.css('div.title01 > h2::text').extract()[0]
        brand['maker'] = response.css('dd.maker > a::text').extract()[0]

        for key, klass in (('product_count', 'productNumber'),
                           ('review_count', 'reviewNumber'),
                           ('favorite_count', 'clipNumber')):
            count = response.css('dt.{0} + dd > a::text'.format(klass)).extract()
            if count:
                count = count[0].replace(u'件', '').replace(u'人', '')
                brand[key] = convert_to_int_if_int(count)
        yield brand
