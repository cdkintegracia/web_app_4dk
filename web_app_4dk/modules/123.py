import requests

r = requests.get('https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/Square_Yellow.svg/1200px-Square_Yellow.svg.png')
with open('test.png', 'wb') as file:
    file.write(r.content)