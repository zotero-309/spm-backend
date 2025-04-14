import math
from flask import jsonify, request
from app.monitoring import monitoring_blueprint
from app import db
from app.models import WFHApplication, WFHSchedule,Employee, WFHWithdrawal
from sqlalchemy import and_,or_
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests
from app import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import pytz
import hashlib


@monitoring_blueprint.route('/telenoti/<string:username>', methods=['GET'])
def send_notification(username):
    try:
        def hash_ip(ip):
            return hashlib.sha256(ip.encode()).hexdigest()[:8]  # shorten for readability

        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
        hashed_ip = hash_ip(user_ip)
        singapore_tz = pytz.timezone('Asia/Singapore')
        now_sg = datetime.now(singapore_tz).strftime('%d/%m/%Y, %I:%M:%S %p')
        message = f"✅ {username} just logged in to the WFH platform at {now_sg} from IP: {hashed_ip}"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()

        return jsonify({'message': 'Telegram notification sent'}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"Telegram API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': f"Unexpected error: {str(e)}"}), 500




@monitoring_blueprint.route('/telenotierror/<string:username>', methods=['GET'])
def send_notificationerror(username):
    try:
        def hash_ip(ip):
            return hashlib.sha256(ip.encode()).hexdigest()[:8]  # shorten for readability

        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
        hashed_ip = hash_ip(user_ip)

        # Ensure timezone-aware datetime
        singapore_tz = pytz.timezone('Asia/Singapore')
        now_sg = datetime.now(singapore_tz).strftime('%d/%m/%Y, %I:%M:%S %p')

        message = f"❌ {username} just failed to log in to the WFH platform at {now_sg} from IP: {hashed_ip}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()

        return jsonify({'message': 'Telegram notification sent'}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"Telegram API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': f"Unexpected error: {str(e)}"}), 500
