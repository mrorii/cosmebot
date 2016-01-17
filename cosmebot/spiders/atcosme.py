# -*- coding: utf-8 -*-
import scrapy


class AtcosmeSpider(scrapy.Spider):
    name = "atcosme"
    allowed_domains = ["cosme.net"]
    start_urls = (
        'http://www.cosme.net/',
    )

    def parse(self, response):
        pass
