# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class Product(Item):
    product_id = Field()
    name = Field()
    maker = Field()
    brand = Field()

    volume = Field()       # 容量
    price = Field()        # 本体価格
    description = Field()  # 商品説明
    colors = Field()       # 色 / パターン
    sale_date = Field()    # 発売日
    categories = Field()
    ingredients = Field()  # 関心の高い成分・特徴

    rating = Field()       # クチコミ評価
    point = Field()        # pt
    ranking = Field()      # ランキング

    review_count = Field()
    like_count = Field()
    have_count = Field()     # もってる


class Review(Item):
    user_id = Field()
    product_id = Field()
    review_id = Field()

    rating = Field()             # 1 - 7
    date = Field()
    text = Field()

    product_type = Field()       # 現品, サンプル・テスター, 購入品, モニター・プレゼント

    purchase_location = Field()  # 購入場所
    effects = Field()            # 効果
    colors = Field()             # 色
    product_tags = Field()       # 商品情報
    related_words = Field()      # 関連ワード


class User(Item):
    user_id = Field()
    name = Field()

    age = Field()
    skin_type = Field()
    hair_type = Field()
    hair_volume = Field()
    zodiac = Field()
    blood_type = Field()

    # interests = Field()
    # hobbies = Field()

    review_count = Field()
    verified = Field()

    qa_count = Field()
    favorite_user_count = Field()
    fan_count = Field()
    favorite_brand_count = Field()


class Brand(Item):
    brand_id = Field()
    name = Field()
    maker = Field()

    product_count = Field()
    review_count = Field()
    favorite_count = Field()
