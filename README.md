# cosmebot

A minimal crawler for [@cosme](http://www.cosme.net/), written on top of [Scrapy](http://scrapy.org/)

## Installation

```
git clone https://github.com/mrorii/cosmebot.git
cd cosmebot
pip install -r requirements.txt
```

## Usage

### Crawl & scrape products, reviews, brands, and users

```
scrapy crawl atcosme
```

### Crawl & scrape tags

```
scrapy crawl atcosme-tags -a tag_type=access
scrapy crawl atcosme-tags -a tag_type=submit
```
