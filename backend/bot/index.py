import json
import os
import psycopg2
from datetime import datetime

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def handler(event: dict, context) -> dict:
    """Telegram бот для CoinFlip с админ-панелью"""
    method = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    try:
        update = json.loads(event.get('body', '{}'))
        
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            text = message.get('text', '')
            
            admin_id = int(os.environ.get('ADMIN_TELEGRAM_ID', '0'))
            
            if text == '/start':
                keyboard = {
                    'inline_keyboard': [[
                        {
                            'text': '🎮 Играть в CoinFlip',
                            'web_app': {'url': os.environ.get('GAME_URL', 'https://coin-toss-betting-ga.poehali.app')}
                        }
                    ]]
                }
                send_message(chat_id, 'Добро пожаловать в CoinFlip! Нажмите кнопку ниже, чтобы начать игру.', keyboard)
            
            elif text == '/admin' and user_id == admin_id:
                show_admin_menu(chat_id)
            
            elif text == '/stats' and user_id == admin_id:
                show_stats(chat_id)
            
            else:
                send_message(chat_id, 'Используйте /start чтобы начать игру')
        
        elif 'callback_query' in update:
            callback = update['callback_query']
            chat_id = callback['message']['chat']['id']
            user_id = callback['from']['id']
            data = callback['data']
            
            admin_id = int(os.environ.get('ADMIN_TELEGRAM_ID', '0'))
            
            if user_id != admin_id:
                answer_callback(callback['id'], 'Доступ запрещён')
                return {'statusCode': 200, 'body': 'ok', 'isBase64Encoded': False}
            
            if data == 'admin_stats':
                show_stats(chat_id)
            elif data == 'admin_players':
                show_players(chat_id)
            elif data == 'admin_transactions':
                show_transactions(chat_id)
            
            answer_callback(callback['id'], '')
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'ok': True}),
            'isBase64Encoded': False
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }

def send_message(chat_id: int, text: str, reply_markup: dict = None):
    import urllib.request
    import urllib.parse
    
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    
    req = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(data).encode('utf-8'),
        method='POST'
    )
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def answer_callback(callback_id: str, text: str):
    import urllib.request
    import urllib.parse
    
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/answerCallbackQuery'
    
    data = {
        'callback_query_id': callback_id,
        'text': text
    }
    
    req = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(data).encode('utf-8'),
        method='POST'
    )
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def show_admin_menu(chat_id: int):
    keyboard = {
        'inline_keyboard': [
            [{'text': '📊 Общая статистика', 'callback_data': 'admin_stats'}],
            [{'text': '👥 Список игроков', 'callback_data': 'admin_players'}],
            [{'text': '💰 Транзакции', 'callback_data': 'admin_transactions'}]
        ]
    }
    send_message(chat_id, '<b>🔧 Админ-панель</b>\n\nВыберите действие:', keyboard)

def show_stats(chat_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*), SUM(balance), SUM(total_games), SUM(wins) FROM players')
    stats = cur.fetchone()
    
    cur.execute('SELECT COUNT(*) FROM games WHERE created_at > NOW() - INTERVAL \'24 hours\'')
    games_today = cur.fetchone()[0]
    
    cur.execute('SELECT SUM(amount) FROM transactions WHERE type = \'deposit\' AND status = \'completed\'')
    total_deposits = cur.fetchone()[0] or 0
    
    cur.execute('SELECT SUM(amount) FROM transactions WHERE type = \'withdrawal\' AND status = \'completed\'')
    total_withdrawals = cur.fetchone()[0] or 0
    
    cur.close()
    conn.close()
    
    text = f'''<b>📊 Статистика CoinFlip</b>

👥 <b>Игроки:</b> {stats[0]}
💰 <b>Общий баланс:</b> {float(stats[1] or 0):.2f} TON
🎮 <b>Всего игр:</b> {stats[2] or 0}
🏆 <b>Побед:</b> {stats[3] or 0}

📅 <b>Игр за 24ч:</b> {games_today}

💵 <b>Депозиты:</b> {float(total_deposits):.2f} TON
💸 <b>Выводы:</b> {float(total_withdrawals):.2f} TON
'''
    
    send_message(chat_id, text)

def show_players(chat_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT username, balance, total_games, wins FROM players ORDER BY balance DESC LIMIT 10')
    players = cur.fetchall()
    
    cur.close()
    conn.close()
    
    text = '<b>👥 Топ-10 игроков</b>\n\n'
    
    for i, player in enumerate(players, 1):
        username = player[0] or 'Аноним'
        balance = float(player[1])
        total_games = player[2]
        wins = player[3]
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        
        text += f'{i}. @{username}\n'
        text += f'   💰 {balance:.2f} TON | 🎮 {total_games} игр | 📈 {win_rate:.1f}% побед\n\n'
    
    send_message(chat_id, text)

def show_transactions(chat_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT t.type, t.amount, t.status, t.created_at, p.username 
        FROM transactions t 
        JOIN players p ON t.player_id = p.id 
        ORDER BY t.created_at DESC 
        LIMIT 15
    ''')
    transactions = cur.fetchall()
    
    cur.close()
    conn.close()
    
    text = '<b>💰 Последние транзакции</b>\n\n'
    
    type_emoji = {
        'deposit': '⬇️',
        'withdrawal': '⬆️',
        'win': '🎉',
        'loss': '❌'
    }
    
    for txn in transactions:
        txn_type = txn[0]
        amount = float(txn[1])
        status = txn[2]
        created = txn[3].strftime('%d.%m %H:%M')
        username = txn[4] or 'Аноним'
        
        emoji = type_emoji.get(txn_type, '•')
        text += f'{emoji} {txn_type.upper()} | {amount:.2f} TON\n'
        text += f'   @{username} | {status} | {created}\n\n'
    
    send_message(chat_id, text)
