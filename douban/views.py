from oauth2 import Token

from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import authenticate, login

#from utils import DoubanBackend
#from pyfyd.models import DuplicatedUsername
from pyfyd.utils import ThirdpartyAuthBackend
from pyfyd.models import DoubanAccount
from pyfyd.common.views import AuthStartMixin, AuthenticateReturnMixin
from clients import OAuthClient2

class BaseV(View):
    '''Base class for all views that will use douban oauth client'''
    def __init__(self, *args, **kwargs):
        super(BaseV, self).__init__(*args, **kwargs)
        
        self.client = OAuthClient2()    
        
class AuthStartV(AuthStartMixin, BaseV):        
    '''
    start from here.
    
    callback MUST be provieded, either by subclassing or kwargs
    this view will build openid request and 
    redirect to douban authorize page
    '''
    callback = False
    
    def get(self, request):
        callback = request.build_absolute_uri(self.get_callback())
        request_token = Token(*self.client.get_request_token())
        request.session['request_token'] = request_token
        
        go_to = self.client.get_authorization_url(request_token.key, 
                                                  request_token.secret, 
                                                  callback)        
        return HttpResponseRedirect(go_to)
    
class AuthReturnV(BaseV):        
    '''
    douban redirect user to here after authorize
    
    Subclass MUST override get() to provide actual business logic.
    DO call super get() first to make self.access_token available
    '''
    access_token = None
    uid = None
    
    def get(self, request):
        request_token = request.session.get('request_token', False)
        if request_token and request_token.key == request.GET['oauth_token']:        
            key, secret, uid = self.client.get_access_token(request_token.key, 
                                                            request_token.secret)
            if key and secret:
                self.access_token = Token(key, secret)
                self.uid = uid
            else:
                raise Exception('failed to get access token')
        else:
            raise Exception('where did u come from?')
            
    
class AuthenticateReturnV(AuthenticateReturnMixin, AuthReturnV):
    '''
    Return from douban authenticate
    '''    
    def get(self, request):
        '''
        Try to authenticate user with the douban info
        '''
        # get self.access_token and self.uid available
        super(AuthenticateReturnV, self).get(request)
        
        account = DoubanAccount.get_from_token(key=self.access_token.key, 
                                               secret=self.access_token.secret,
                                               uid=self.uid)
        # DoesNotExist or MoreThanOneResult exception may raise here
        account = DoubanAccount.get_linked(account)        
        try:
            user = authenticate(account=account, cid=ThirdpartyAuthBackend.CID)
        except Exception:            
            # TODO
            raise 
        else:
            if user:
                login(request, user)
                return self.success(user)
            else:
                return self.failed()
            
class AuthorizeReturnV(AuthReturnV):
    def get(self, request):
        '''
        Update access key and other info to user account
        '''
        # get self.access_token and self.uid available
        super(AuthorizeReturnV, self).get(request)
        
        DoubanAccount.link_external(request.user,
                                    key=self.access_token.key, 
                                    secret=self.access_token.secret)
        
#        DoubanBackend.link_external(self.access_token.key, 
#                                    self.access_token.secret,
#                                    request.user,  
#                                    uid=self.uid)