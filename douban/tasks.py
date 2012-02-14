from celery.task import task

from clients import OAuthClient2
from pyfyd.models import DoubanAccount

class Saying(object):
    content = ''
    TEMPLATE = u'''<?xml version='1.0' encoding='UTF-8'?>
<entry xmlns:ns0="http://www.w3.org/2005/Atom" xmlns:db="http://www.douban.com/xmlns/">
<content>{content}</content>
</entry>'''
    
    def __init__(self, content=''):
        self.content = content
        
    @property
    def body(self):
        return self.TEMPLATE.format(content=self.content).encode('utf-8')
    

class Note(object):
    title = ''
    content = ''
    __privacy = 'private'
    __can_reply = 'yes'
    
    TEMPLATE = u'''<?xml version="1.0" encoding="UTF-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
xmlns:db="http://www.douban.com/xmlns/">
<title>{title}</title>
<content>{content}</content>
<db:attribute name="privacy">{privacy}</db:attribute>
<db:attribute name="can_reply">{can_reply}</db:attribute>
</entry>'''
    
    def __init__(self, title='', content='', privacy='private', can_reply='yes'):
        self.title = title
        self.content = content
        self.privacy = privacy
        self.can_reply = can_reply
        
    @property
    def can_reply(self):
        return self.__can_reply
    
    @can_reply.setter
    def can_reply(self, can_reply):
        if not can_reply or can_reply in ['no', 'n']:
            self.__can_reply = 'no'
        else:
            self.__can_reply = 'yes'
            
    @property
    def privacy(self):
        return self.__privacy
    
    @privacy.setter
    def privacy(self, privacy):
        if privacy in ['public', 'friend', 'private']:
            self.__privacy = privacy
        else:
            raise Exception('valid privacy values are: public, friend, private')
        
    @property
    def body(self):
        return self.TEMPLATE.format(title=self.title, content=self.content, 
                                    privacy=self.privacy, 
                                    can_reply=self.can_reply).encode('utf-8')

def _post(uri, post, account):        
    if not isinstance(account, DoubanAccount):
        raise Exception('we need account to be a pyfyd.models.DoubanAccount')
    client = OAuthClient2(account.key, account.secret)
    
    resp, content = client.request(uri, method='POST', body=post.body)
        
    if 201 == int(resp['status']):
        return resp
    else:
        raise Exception('{}: {} when pushing post to douban'.\
                            format(resp['status'], content))
        
@task(name='pyfyd.douban.push_saying', ignore_result=True)
def push_saying(saying, account):
    ''''''
    if not isinstance(saying, Saying):
        raise Exception('pyfyd.douban.tasks.push_saying: the first arg '+
                        'should be a pyfyd.douban.tasks.Saying')
    
    return _post('http://api.douban.com/miniblog/saying', saying, account)

@task(name='pyfyd.douban.push_note', ignore_result=True)
def push_note(note, account): 
    ''''''
    if not isinstance(note, Note):
        raise Exception('pyfyd.douban.tasks.push_note: the first arg '+
                        'should be a pyfyd.douban.tasks.Note')
    
    return _post('http://api.douban.com/notes', note, account)

