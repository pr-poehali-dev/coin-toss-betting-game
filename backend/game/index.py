import json
import os
import psycopg2
from decimal import Decimal
import random

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def handler(event: dict, context) -> dict:
    """API для игровой механики CoinFlip с TON интеграцией"""
    method = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if method == 'POST':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'get_or_create_player':
                telegram_id = body.get('telegram_id')
                username = body.get('username', '')
                
                cur.execute(
                    'SELECT id, balance, total_games, wins, total_winnings FROM players WHERE telegram_id = %s',
                    (telegram_id,)
                )
                player = cur.fetchone()
                
                if not player:
                    cur.execute(
                        'INSERT INTO players (telegram_id, username, balance) VALUES (%s, %s, %s) RETURNING id, balance, total_games, wins, total_winnings',
                        (telegram_id, username, 100.0)
                    )
                    player = cur.fetchone()
                    conn.commit()
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'player_id': player[0],
                        'balance': float(player[1]),
                        'total_games': player[2],
                        'wins': player[3],
                        'total_winnings': float(player[4])
                    }),
                    'isBase64Encoded': False
                }
            
            elif action == 'play':
                player_id = body.get('player_id')
                bet_amount = Decimal(str(body.get('bet_amount', 0)))
                selected_side = body.get('selected_side')
                
                cur.execute('SELECT balance FROM players WHERE id = %s', (player_id,))
                player = cur.fetchone()
                
                if not player:
                    return {
                        'statusCode': 404,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Player not found'}),
                        'isBase64Encoded': False
                    }
                
                balance = player[0]
                
                if balance < bet_amount:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Insufficient balance'}),
                        'isBase64Encoded': False
                    }
                
                result_side = 'heads' if random.random() > 0.5 else 'tails'
                won = result_side == selected_side
                win_amount = bet_amount * 2 if won else Decimal(0)
                
                new_balance = balance + bet_amount if won else balance - bet_amount
                
                cur.execute(
                    'UPDATE players SET balance = %s, total_games = total_games + 1, wins = wins + %s, total_winnings = total_winnings + %s WHERE id = %s',
                    (new_balance, 1 if won else 0, win_amount, player_id)
                )
                
                cur.execute(
                    'INSERT INTO games (player_id, bet_amount, selected_side, result_side, won, win_amount) VALUES (%s, %s, %s, %s, %s, %s)',
                    (player_id, bet_amount, selected_side, result_side, won, win_amount)
                )
                
                if won:
                    cur.execute(
                        'INSERT INTO transactions (player_id, type, amount, status) VALUES (%s, %s, %s, %s)',
                        (player_id, 'win', win_amount, 'completed')
                    )
                else:
                    cur.execute(
                        'INSERT INTO transactions (player_id, type, amount, status) VALUES (%s, %s, %s, %s)',
                        (player_id, 'loss', bet_amount, 'completed')
                    )
                
                conn.commit()
                
                cur.execute('SELECT balance, total_games, wins, total_winnings FROM players WHERE id = %s', (player_id,))
                updated_player = cur.fetchone()
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'result_side': result_side,
                        'won': won,
                        'win_amount': float(win_amount),
                        'balance': float(updated_player[0]),
                        'total_games': updated_player[1],
                        'wins': updated_player[2],
                        'total_winnings': float(updated_player[3])
                    }),
                    'isBase64Encoded': False
                }
            
            elif action == 'create_deposit':
                player_id = body.get('player_id')
                amount = Decimal(str(body.get('amount', 0)))
                
                cur.execute(
                    'INSERT INTO transactions (player_id, type, amount, status) VALUES (%s, %s, %s, %s) RETURNING id',
                    (player_id, 'deposit', amount, 'pending')
                )
                transaction_id = cur.fetchone()[0]
                conn.commit()
                
                ton_wallet = os.environ.get('TON_WALLET_ADDRESS', '')
                memo = f'DEPOSIT_{transaction_id}'
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'transaction_id': transaction_id,
                        'ton_wallet': ton_wallet,
                        'amount': float(amount),
                        'memo': memo
                    }),
                    'isBase64Encoded': False
                }
            
            elif action == 'create_withdrawal':
                player_id = body.get('player_id')
                amount = Decimal(str(body.get('amount', 0)))
                ton_address = body.get('ton_address')
                
                cur.execute('SELECT balance FROM players WHERE id = %s', (player_id,))
                player = cur.fetchone()
                
                if not player or player[0] < amount:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Insufficient balance'}),
                        'isBase64Encoded': False
                    }
                
                cur.execute(
                    'INSERT INTO transactions (player_id, type, amount, ton_address, status) VALUES (%s, %s, %s, %s, %s) RETURNING id',
                    (player_id, 'withdrawal', amount, ton_address, 'pending')
                )
                transaction_id = cur.fetchone()[0]
                
                cur.execute('UPDATE players SET balance = balance - %s WHERE id = %s', (amount, player_id))
                conn.commit()
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'transaction_id': transaction_id,
                        'status': 'pending'
                    }),
                    'isBase64Encoded': False
                }
        
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    except Exception as e:
        conn.rollback()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
    finally:
        cur.close()
        conn.close()
