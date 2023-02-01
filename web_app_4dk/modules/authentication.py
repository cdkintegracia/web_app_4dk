import base64


def authentication(key):
    credentials = {
        'Bitrix': 'aHR0cHM6Ly92YzRkay5iaXRyaXgyNC5ydS9yZXN0LzMxMS83OG5vdXZ3ejlkcnNvbnkwLw==',
        'Google': 'Yml0cml4MjQtZGF0YS1zdHVkaW8tMjI3OGM3YmZiMWE3Lmpzb24=',
    }
    return base64.b64decode(credentials[key]).decode('utf-8')

