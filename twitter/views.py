from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from tweepy import OAuthHandler, API

from pyfyd.models import DuplicatedUsername
from pyfyd.common.views import AuthStartMixin, AuthenticateReturnMixin
from utils import TwitterBackend

class BaseOAuthV(View):
    '''Base class for all views that will use OAuth handler'''
    def __init__(self, *args, **kwargs):
        self.oauth = OAuthHandler(settings.TWITTER_CONSUMER_KEY,
                                  settings.TWITTER_CONSUMER_SECRET,
                                  secure=True)
        super(BaseOAuthV, self).__init__(*args, **kwargs)

        
class AuthStartV(AuthStartMixin, BaseOAuthV):        
    '''
    OAuth start from here.
    
    callback MUST be provieded, either by subclassing or kwargs
    this view will build oauth request and 
    redirect to twitter authorize or auchenticate page
    '''
    callback = False
    signin = False
    
    def get(self, request, signin=True):        
        self.oauth.callback = request.build_absolute_uri(self.get_callback())
        redirect_to = self.oauth.get_authorization_url(self.signin)
        # request token could only being get after get_authorization_url()
        request.session['unauthed_token'] = self.oauth.request_token
        return HttpResponseRedirect(redirect_to)
    
class AuthReturnV(BaseOAuthV):        
    '''
    Twitter redirect user to here after authorize
    
    Subclass MUST override get() to provide actual business logic.
    DO call super get() first to make self.access_token available
    '''
    access_token = None
    
    def get(self, request):
        if request.session['unauthed_token'].key == request.GET['oauth_token']:
            self.oauth.set_request_token(request.GET['oauth_token'], 
                                         settings.TWITTER_CONSUMER_SECRET)
            # give a oauth.OAuthToken object to override
            self.access_token = self.oauth.get_access_token(
                                    request.GET['oauth_verifier'])
        else:
            raise Exception('token not match, something went wrong')
        
        
class AuthenticateReturnV(AuthenticateReturnMixin, AuthReturnV):
    '''
    Return from twitter authenticate
    '''    
    def get(self, request):
        '''
        Try to authenticate user with the access key just returned from twitter
        '''
        # get self.access_token available
        super(AuthenticateReturnV, self).get(request)
        
        try:
            user = authenticate(cid=TwitterBackend.CID,
                                key=self.access_token.key, 
                                secret=self.access_token.secret)
        except DuplicatedUsername:            
            raise # TODO
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
        
        TwitterBackend.link_external(self.access_token.key, 
                                     self.access_token.secret,
                                     request.user)