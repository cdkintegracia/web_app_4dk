import requests, zipfile, io
r = requests.get(url='https://vc4dk.bitrix24.ru/disk/downloadFile/192241/?&ncc=1&filename=%D0%9F%D0%BE%D0%B4%D0%BA%D0%BB%D1%8E%D1%87%D0%B5%D0%BD%D0%B8%D1%8F+%D0%9E%D0%9E%D0%9E+%D0%A7%D1%82%D0%BE+%D0%B4%D0%B5%D0%BB%D0%B0%D1%82%D1%8C+%D0%98%D0%BD%D1%82%D0%B5%D0%B3%D1%80%D0%B0%D1%86%D0%B8%D1%8F+%D0%B7%D0%B0+%D1%81%D0%B5%D0%BD%D1%82%D1%8F%D0%B1%D1%80%D1%8C+2022%D0%B3+%281%29.zip')
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall("/path/to/destination_directory")






