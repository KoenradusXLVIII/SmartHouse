import requests
import json

url = u'https://api.instagram.com/oauth/access_token'
data = {
    u'client_id': '6e8dabab213f49c08b88a7027baa1cf7',
    u'client_secret': '809a071ca108460a87761a78325e6f67',
    u'code': '4649af0956b24c7591606754dca161b1',
    u'grant_type': u'authorization_code',
    u'redirect_uri': 'http://www.joostverberk.nl'
}

response = requests.post(url, data=data)

account_data = json.loads(response.content)