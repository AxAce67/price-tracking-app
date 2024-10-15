import schedule
import time
import logging
from price_tracker import extract_keyword, get_current_price, update_price_history
from datetime import datetime

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def job():
    logger.info("Starting price update job")
    # ここに追跡したい商品のURLリストを追加
    urls = [
        "https://item.rakuten.co.jp/example/item1",
        "https://item.rakuten.co.jp/example/item2",
        # 追加の商品URLをここに記述
    ]

    for url in urls:
        logger.info(f"Processing URL: {url}")
        keyword = extract_keyword(url)
        if keyword:
            logger.info(f"Extracted keyword: {keyword}")
            product_name, current_price = get_current_price(keyword)
            if current_price:
                logger.info(f"Retrieved price for {product_name}: {current_price}")
                price_history = load_price_history(keyword)
                now = datetime.now()
                price_history.append({'date': now.strftime('%Y-%m-%d %H:%M:%S'), 'price': current_price})
                save_price_history(keyword, price_history)
                last_update = now.strftime('%Y-%m-%d %H:%M:%S')
                save_last_update_time(keyword, last_update)
                logger.info(f"Updated price history and last update time for {keyword}")
            else:
                logger.warning(f"Failed to retrieve price for keyword: {keyword}")
        else:
            logger.warning(f"Failed to extract keyword from URL: {url}")

    logger.info("Finished price update job")

def load_price_history(keyword):
    # 既存の価格履歴を読み込むロジックをここに実装
    return []

def save_price_history(keyword, price_history):
    # ここにキーワードと価格履歴を保存するロジックを実装する
    pass

def save_last_update_time(keyword, last_update):
    # キーワードと最終更新時間をデータベースに保存するロジックをここに実装
    pass

if __name__ == "__main__":
    logger.info("Starting price tracker scheduler")
    schedule.every(1).minutes.do(job)

    # 初回実行
    job()

    while True:
        schedule.run_pending()
        time.sleep(1)