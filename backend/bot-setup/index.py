import json
import os
import urllib.request
import urllib.parse

def handler(event: dict, context) -> dict:
    """Настройка Telegram бота - установка webhook и команд"""
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
    
    token = os.environ['TELEGRAM_BOT_TOKEN']
    bot_webhook_url = os.environ.get('BOT_WEBHOOK_URL', '')
    
    try:
        if method == 'POST':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'set_webhook':
                webhook_url = body.get('webhook_url', bot_webhook_url)
                
                url = f'https://api.telegram.org/bot{token}/setWebhook'
                data = urllib.parse.urlencode({'url': webhook_url}).encode('utf-8')
                
                req = urllib.request.Request(url, data=data, method='POST')
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                
                commands_url = f'https://api.telegram.org/bot{token}/setMyCommands'
                commands_data = {
                    'commands': json.dumps([
                        {'command': 'start', 'description': 'Запустить игру'},
                        {'command': 'admin', 'description': 'Админ-панель'}
                    ])
                }
                commands_encoded = urllib.parse.urlencode(commands_data).encode('utf-8')
                
                req2 = urllib.request.Request(commands_url, data=commands_encoded, method='POST')
                with urllib.request.urlopen(req2) as response2:
                    commands_result = json.loads(response2.read().decode('utf-8'))
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'webhook': result,
                        'commands': commands_result
                    }),
                    'isBase64Encoded': False
                }
            
            elif action == 'get_info':
                url = f'https://api.telegram.org/bot{token}/getMe'
                
                req = urllib.request.Request(url, method='GET')
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                
                webhook_url = f'https://api.telegram.org/bot{token}/getWebhookInfo'
                req2 = urllib.request.Request(webhook_url, method='GET')
                with urllib.request.urlopen(req2) as response2:
                    webhook_info = json.loads(response2.read().decode('utf-8'))
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'bot': result,
                        'webhook': webhook_info
                    }),
                    'isBase64Encoded': False
                }
        
        url = f'https://api.telegram.org/bot{token}/getMe'
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(result),
            'isBase64Encoded': False
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
