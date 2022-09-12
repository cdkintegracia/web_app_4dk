import requests
import zeep

#header = {'content-type': 'application/soap+xml'}
headers = {
    'Authorization': 'Basic Yml0cml4OlNla1hkNA==',
    'Content-Type': 'text/xml; charset=utf-8',

}

body = """<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:par="http://buhphone.com/PartnerWebAPI2" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:core="http://v8.1c.ru/8.1/data/core" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <soap:Header/>
   <soap:Body>
      <par:GetClientUsageStatistics>
         <par:Params>
            <Property xmlns="http://v8.1c.ru/8.1/data/core" name="Period">
             <Value xsi:type="xs:dateTime">2022-09-12T01:00:00</Value>
           </Property>
         </par:Params>
      </par:GetClientUsageStatistics>
   </soap:Body>
</soap:Envelope>"""

url ='https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl'

r = requests.post(url, data=body, headers=headers)

client = zeep.Client(url)

print(client.service)

