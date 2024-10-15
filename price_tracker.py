import pandas as pd
import requests
from datetime import datetime
import logging
import json
import os
import re
from bs4 import BeautifulSoup
from config import RAKUTEN_APP_ID, RAKUTEN_AFFILIATE_ID

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_keyword(url):
    patterns = [
        r'/([^/]+)/\?',
        r'/([^/]+)/$',
        r'/([^/]+)$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1).replace('-', ' ')
    logger.error(f"Failed to extract keyword from URL: {url}")
    return None

def get_current_price_and_image(keyword):
    logger.info(f"Fetching current price and image for keyword: {keyword}")
    endpoint = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "affiliateId": RAKUTEN_AFFILIATE_ID,
        "keyword": keyword,
        "hits": 1,
        "format": "json"
    }
    
    response = requests.get(endpoint, params=params)
    logger.info(f"API response status code: {response.status_code}")
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch data. Status code: {response.status_code}")
        logger.error(f"Response content: {response.text}")
        return None, None, None

    data = response.json()
    if 'Items' not in data or len(data['Items']) == 0:
        logger.error("No items found")
        return None, None, None

    item = data['Items'][0]['Item']
    logger.info(f"Retrieved item: {item['itemName']} with price: {item['itemPrice']}")
    return item['itemName'], item['itemPrice'], item['mediumImageUrls'][0]['imageUrl']

def get_price_history(url):
    keyword = extract_keyword(url)
    if not keyword:
        return pd.DataFrame(columns=['date', 'price']), "URLが無効です", 0, "未更新", None

    product_name, current_price, product_image_url = get_current_price_and_image(keyword)
    if not product_name or not current_price:
        return pd.DataFrame(columns=['date', 'price']), "価格データの取得に失敗しました", 0, "未更新", None

    price_history = load_price_history(keyword)
    
    # 現在の価格を価格履歴に追加し、最終更新時刻を更新
    now = datetime.now()
    price_history.append({'date': now.strftime('%Y-%m-%d %H:%M:%S'), 'price': current_price})
    save_price_history(keyword, price_history)
    last_update = now.strftime('%Y-%m-%d %H:%M:%S')
    save_last_update_time(keyword, last_update)
    
    logger.info(f"Product Name: {product_name}")
    logger.info(f"Current Price: {current_price}")
    logger.info(f"Last Update: {last_update}")
    logger.info(f"Product Image URL: {product_image_url}")
    logger.debug(f"Price History: {price_history}")

    return pd.DataFrame(price_history), product_name, current_price, last_update, product_image_url

def load_price_history(keyword):
    filename = f"price_history_{keyword.replace(' ', '_')}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def save_price_history(keyword, price_history):
    filename = f"price_history_{keyword.replace(' ', '_')}.json"
    with open(filename, 'w') as f:
        json.dump(price_history, f)

def save_last_update_time(keyword, last_update):
    filename = f"last_update_{keyword.replace(' ', '_')}.txt"
    with open(filename, 'w') as f:
        f.write(last_update)

def get_last_update_time(keyword):
    filename = f"last_update_{keyword.replace(' ', '_')}.txt"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read().strip()
    return "未更新"

def update_price_history(keyword, current_price):
    price_history = load_price_history(keyword)
    now = datetime.now()
    price_history.append({'date': now.strftime('%Y-%m-%d %H:%M:%S'), 'price': current_price})
    save_price_history(keyword, price_history)
    save_last_update_time(keyword)
    logger.info(f"Updated price history for {keyword}: {current_price}")