import os
from flask import Flask, render_template, request, redirect, url_for, Response
from price_tracker import get_price_history
from price_predictor import predict_price
import plotly.graph_objs as go
import plotly.utils
from datetime import datetime, timedelta
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine
import logging
import traceback
import json
import time
from config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD

current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'templates')
static_dir = os.path.join(current_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベース設定
engine = create_engine('sqlite:///jobs.sqlite')
jobstores = {
    'default': SQLAlchemyJobStore(engine=engine)
}

scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
    else:
        url = request.args.get('url')
    
    if url:
        price_history, product_name, current_price, last_update_str, product_image_url = get_price_history(url)
        
        if price_history.empty:
            return render_template('error.html', message="価格データの取得に失敗しました。URLを確認してください。")
        
        tomorrow_price, days_to_best, best_price = predict_price(price_history)
        
        # 予測が不可能な場合の処理
        prediction_impossible = tomorrow_price == "予測不可"
        explanation = days_to_best if prediction_impossible else None
        
        # グラフの生成
        fig = go.Figure(data=[go.Scatter(x=price_history['date'], y=price_history['price'], mode='lines+markers')])
        fig.update_layout(
            title='価格推移',
            xaxis_title='日付',
            yaxis_title='価格 (円)',
            yaxis=dict(
                tickformat=',d',
                ticksuffix='円',
                tickmode='array',
                tickvals=price_history['price'].unique(),  # 実際の価格値のみをティックとして使用
            )
        )
        graph_json = plotly.utils.PlotlyJSONEncoder().encode(fig)
        
        # last_updateを文字列からdatetimeオブジェクトに変換し、UTCからJSTに変換
        utc = pytz.UTC
        jst = pytz.timezone('Asia/Tokyo')
        last_update_utc = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=utc)
        last_update_jst = last_update_utc.astimezone(jst)
        
        return render_template('result.html', 
                               price_history=price_history, 
                               tomorrow_price=tomorrow_price,
                               days_to_best=days_to_best,
                               best_price=best_price,
                               prediction_impossible=prediction_impossible,
                               explanation=explanation,
                               product_name=product_name, 
                               current_price=current_price,
                               graph_json=graph_json,
                               last_update=last_update_jst,
                               product_image_url=product_image_url,
                               url=url)
    
    return render_template('index.html')

@app.route('/email_notification_progress')
def email_notification_progress():
    def generate():
        steps = ['通知設定を保存中', '確認メールを準備中', 'メールサーバーに接続中', '確認メールを送信中', '設定を完了中']
        for i, step in enumerate(steps):
            time.sleep(0.5)  # シミュレーション用の遅延
            progress = min(100, int((i + 1) / len(steps) * 100))
            yield f"data: {json.dumps({'progress': progress, 'step': step})}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.route('/set_email_notification', methods=['POST'])
def set_email_notification():
    email = request.form['email']
    url = request.form['url']
    target_price = float(request.form['target_price'])
    product_name = request.form['product_name']
    
    # スケジューラーにジョブを追加
    job_id = f"price_check_{url}"
    scheduler.add_job(
        check_price_and_notify,
        'interval',
        minutes=60,  # 1時間ごとにチェック
        id=job_id,
        replace_existing=True,
        args=[url, target_price, email]
    )
    
    logger.info(f"通知設定が保存されました: email={email}, url={url}, target_price={target_price}, product_name={product_name}")
    
    # 設定確認メールを送信
    send_confirmation_email(email, url, target_price, product_name)
    
    return redirect(url_for('email_sent', email=email, url=url, target_price=target_price, product_name=product_name))

@app.route('/email_sent')
def email_sent():
    email = request.args.get('email')
    url = request.args.get('url')
    target_price = request.args.get('target_price')
    product_name = request.args.get('product_name')
    return render_template('email_sent.html', email=email, url=url, target_price=target_price, product_name=product_name)

def send_confirmation_email(to_email, url, target_price, product_name):
    subject = f"価格通知設定の確認: {product_name}"
    body = f"""以下の内容で価格通知が設定されました：

商品名: {product_name}
商品URL: {url}
目標価格: {target_price}円

価格が目標に達した際にお知らせします。"""
    
    msg = MIMEMultipart()
    msg['From'] = f"価格追跡アプリ <{SMTP_USERNAME}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"設定確認メールを {to_email} に送信しました。")
    except Exception as e:
        logger.error(f"設定確認メール送信中にエラーが発生しました: {str(e)}")
        # ここではエラーを再発生させず、ログに記録するだけにします

@app.route('/test_email', methods=['GET'])
def test_email():
    test_email = SMTP_USERNAME  # テスト用に自分のメールアドレスを使用
    try:
        send_email_notification(
            test_email,
            "テスト商品",
            10000,
            9000
        )
        return f"テストメールが {test_email} に正常に送信されました。"
    except Exception as e:
        logger.error(f"テストメール送信中にエラーが発生しました: {str(e)}")
        return f"テストメール送信中にエラーが発生しました: {str(e)}", 500

def check_price_and_notify(url, target_price, email):
    price_history, product_name, current_price, _, _ = get_price_history(url)
    
    if current_price <= target_price:
        send_email_notification(email, product_name, current_price, target_price)
        # 通知後、ジョブを削除
        scheduler.remove_job(f"price_check_{url}")
        logger.info(f"Price target reached for {url}. Job removed.")

def send_email_notification(to_email, product_name, current_price, target_price):
    subject = f"{product_name}の価格が目標に達しました"
    body = f"{product_name}の現在の価格が{current_price}円になり、目標価格{target_price}円に達しました。"

    msg = MIMEMultipart()
    msg['From'] = f"価格追跡アプリ <{SMTP_USERNAME}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"通知メールを {to_email} に送信しました。")
    except Exception as e:
        logger.error(f"通知メール送信中にエラーが発生しました: {str(e)}")

@app.errorhandler(Exception)
def handle_exception(e):
    # エラーの詳細をログに記録
    app.logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
    
    # デバッグモードの場合は詳細なエラー情報を表示
    if app.debug:
        error_details = traceback.format_exc()
    else:
        error_details = None
    
    # エラーページ��レンダリング
    return render_template('error.html', 
                           message="予期せぬエラーが発生しました。",
                           error_details=error_details), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
                           message="ページが見つかりません。"), 404

@app.route('/test_error')
def test_error():
    # 意図的に例外を発生させる
    raise Exception("This is a test error")

@app.route('/progress')
def progress():
    def generate():
        steps = ['URLの検証', '商品情報の取得', '価格履歴の取得', '価格予測の計算', 'グラフの生成']
        for i, step in enumerate(steps):
            for j in range(10):  # 各ステップを10の小ステップに分割
                time.sleep(0.02)  # 20ミリ秒ごとに更新
                progress = min(100, int((i * 10 + j) / (len(steps) * 10) * 100))
                yield f"data: {json.dumps({'progress': progress, 'step': step})}\n\n"
        # 最後に100%を確実に送信
        yield f"data: {json.dumps({'progress': 100, 'step': '完了'})}\n\n"
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    if not all([SMTP_USERNAME, SMTP_PASSWORD]):
        logger.error("エラー: SMTPの認証情報が設定されていません。環境変数 SMTP_USERNAME と SMTP_PASSWORD を設定してください。")
        exit(1)
    else:
        logger.info("SMTPの認証情報が正しく設定されています。")
    
    app.run(host='0.0.0.0', port=8080, debug=True)