import requests
import sys
import json

print('osRestTest.py expects 4 parameter: 1. Objectserver Adress, 2. OS REST Port, 3. OS User, 4. OS User PW')

print('Number of arguments: ' + str(len(sys.argv) - 1) + ' arguments.')

if (len(sys.argv) != 5):
    print('There are not 4 arguments, but thanks')
    sys.exit(2)

osRest = str(sys.argv[1])
osRestPort = sys.argv[2]
osLoginUser = str(sys.argv[3])
osLoginPW = str(sys.argv[4])

session = requests.Session()
print('Get Request from http://' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/status?collist=Severity')
print('With User = ' + osLoginUser + ' und Passswort = ' + osLoginPW + ' .')
Response = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/status?collist=Severity', auth=(osLoginUser, osLoginPW))
print(Response)
JsonResponse = Response.json()
print(JsonResponse)
