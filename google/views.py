#from django.views.generic import View
import logging

from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from openid.consumer import consumer

from pyfyd.google.utils import get_openid_start_url, parse_hybrid_response,\
                                    GoogleBackend                                    
from pyfyd.models import DuplicatedUsername
from pyfyd.common.views import AuthStartMixin, AuthenticateReturnMixin

class BaseV(View):
    '''Base class for all views that will use openid consumer'''
    _consumer = False
    _openidstore = False
        
    def get_openid_store(self):
        from openid.store.memstore import MemoryStore
        
        if not self._openidstore:
            self._openidstore = MemoryStore()
        return self._openidstore
        
    def get_consumer(self, session):
        if not self._consumer:
            self._consumer = consumer.Consumer(session, self.get_openid_store())
        return self._consumer

        
class AuthStartV(AuthStartMixin, BaseV):        
    '''
    start from here.
    
    callback MUST be provieded, either by subclassing or kwargs
    this view will build openid request and 
    redirect to google authorize page
    '''
    callback = False
    
    def get(self, request):
        callback = request.build_absolute_uri(self.get_callback())
        c = self.get_consumer(request.session)
        trust_root = request.build_absolute_uri('/')        
        
        return HttpResponseRedirect(get_openid_start_url(c, trust_root,
                                                         callback))
    
class AuthReturnV(BaseV):        
    '''
    Google redirect user to here after authorize
    
    Subclass MUST override get() to provide actual business logic.
    DO call super get() first to make self.access_token available
    '''
    user_attrs = None
    access_token = None
    
    def get(self, request):
        c = self.get_consumer(request.session)
        resp = c.complete(request.GET, request.build_absolute_uri(request.path))
        
        if consumer.SUCCESS == resp.status:
            self.user_attrs, self.access_token = parse_hybrid_response(resp)
        else:
            # TODO openid failed
            raise Exception('openid auth failed')
            
    
class AuthenticateReturnV(AuthenticateReturnMixin, AuthReturnV):
    '''
    Return from Google authenticate
    '''    
    def get(self, request):
        '''
        Try to authenticate user with the google info
        '''
        # get self.access_token and self.ax_resp available
        super(AuthenticateReturnV, self).get(request)
        
        try:
            user = authenticate(cid=GoogleBackend.CID,
                                key=self.access_token.key, 
                                secret=self.access_token.secret,
                                user_attrs=self.user_attrs)
        except DuplicatedUsername:            
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
        
        GoogleBackend.link_external(self.access_token.key, 
                                    self.access_token.secret, 
                                    request.user,
                                    user_attrs=self.user_attrs)            