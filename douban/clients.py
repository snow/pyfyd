import cgi
from oauth2 import Client, Consumer, Token, Request, SignatureMethod_HMAC_SHA1

from django.conf import settings

_signature_method = SignatureMethod_HMAC_SHA1()
API_HOST = 'http://api.douban.com'
AUTH_HOST = 'http://www.douban.com'
REQUEST_TOKEN_URL = AUTH_HOST + '/service/auth/request_token'
ACCESS_TOKEN_URL = AUTH_HOST + '/service/auth/access_token'
AUTHORIZATION_URL = AUTH_HOST + '/service/auth/authorize'

class OAuthClient2(Client):
    '''Douban client that use OAuth'''
    token = None
    consumer = None
    
    def __init__(self, access_key=None, access_secret=None, *args, **kwargs):
        self.consumer = Consumer(settings.DOUBAN_API_KEY, 
                                 settings.DOUBAN_API_SECRET)
        if access_key and access_secret:
            self.token = Token(access_key, access_secret)
        
        super(OAuthClient2, self).__init__(self.consumer, self.token, 
                                           *args, **kwargs)
        
    def request(self, uri, method='GET', headers={}, *args, **kwargs):
        if method in ('POST', 'PUT'):
            headers.update({
                'Content-Type': 'application/atom+xml; charset=utf-8'
            })
            
        return super(OAuthClient2, self).request(uri, method=method, 
                                                 headers=headers, *args,
                                                 **kwargs)
        
    def fetch_token(self, request):
        resp, content = self.request(request.url, headers=request.to_header())
        
        if 200 == int(resp['status']):
            token = Token.from_string(content)
            params = cgi.parse_qs(content, keep_blank_values=False)
            user_id = params.get('douban_user_id',[None])[0]
            return token.key,token.secret, user_id
        else:
            raise Exception('{}: {}'.format(resp['status'], content))        

    def get_request_token(self):
        request = Request.from_consumer_and_token(self.consumer, 
                                                  http_url=REQUEST_TOKEN_URL)
        request.sign_request(_signature_method, self.consumer, None)
        return self.fetch_token(request)[:2]

    def get_authorization_url(cls, request_key, request_secret, callback=None):
        token = Token(request_key, request_secret)
        request = Request.from_token_and_callback(token=token, 
                                                  http_url=AUTHORIZATION_URL, 
                                                  callback=callback)
        return request.to_url()
 
    def get_access_token(self, request_key=None, request_secret=None, token=None):
        if request_key and request_secret:
            request_token = Token(request_key, request_secret)
        assert request_token is not None
        request = Request.from_consumer_and_token(self.consumer, 
                                                  token=request_token, 
                                                  http_url=ACCESS_TOKEN_URL)
        request.sign_request(_signature_method, self.consumer, request_token)
        return self.fetch_token(request)[:3]
 
    
    