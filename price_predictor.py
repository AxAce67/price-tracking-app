import os
import pandas as pd
from datetime import datetime, timedelta
import google.generativeai as genai
import logging
from config import GOOGLE_API_KEY

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini APIの設定
genai.configure(api_key=GOOGLE_API_KEY)

def predict_price(price_history):
    df = pd.DataFrame(price_history)
    df['date'] = pd.to_datetime(df['date'], format='mixed', dayfirst=False)
    
    # Gemini 1.5 Flashモデルの選択
    model = genai.GenerativeModel("gemini-1.5-flash")
    logger.info("Gemini 1.5 Flash model selected")

    # Geminiへの入力テキストの作成
    input_text = f"""以下は商品の価格履歴データです：
{df.to_string()}

このデータに基づいて以下を予測してください：
1. 明日の予測価格
2. 最適な購入時期（何日後か）
3. その時の予測価格

結果は数値のみ、カンマ区切りで返してください。
データが不十分な場合や予測が困難な場合は、インターネットの情報を参照して、この商品カテゴリの一般的な価格動向や最適な購入時期について説明してください。"""

    logger.info(f"Input text prepared: {input_text[:100]}...")  # 最初の100文字のみログ出力

    # Geminiによる予測
    logger.info("Calling Gemini API for prediction...")
    try:
        response = model.generate_content(input_text)
        logger.info("Gemini API call successful")
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        raise

    # レスポンスの解析
    logger.info(f"Raw response from Gemini: {response.text}")
    prediction = response.text.strip()
    try:
        # カンマで分割して数値に変換できるか試みる
        values = prediction.split(',')
        tomorrow_price = float(values[0])
        days_to_best = int(values[1])
        best_price = float(values[2])
        logger.info(f"Prediction parsed successfully: Tomorrow: {tomorrow_price}, Days to best: {days_to_best}, Best price: {best_price}")
        return round(tomorrow_price), days_to_best, round(best_price)
    except (ValueError, IndexError):
        # 数値に変換できない場合は、テキストの説明を返す
        logger.info("Prediction not possible. Returning explanation.")
        return "予測不可", prediction, ""
