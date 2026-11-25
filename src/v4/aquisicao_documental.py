"""Bounded shared media transport for private documentary acquisition.
No proxy, credential rotation, blind redirects or license inference.
"""
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
import time
import random
import requests

UA={'User-Agent':'CoringaExplica/4.0 (https://github.com/Heitor2404/coringa-news; documentary media research)'}

class AquisiçãoErro(ValueError):
    pass

def retry_after(value, now=None):
    if not value:return None
    try:return max(0,int(value))
    except (TypeError,ValueError):pass
    try:
        dt=parsedate_to_datetime(value)
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
        return max(0,(dt-(now or datetime.now(timezone.utc))).total_seconds())
    except (ValueError,TypeError,OverflowError):return None

class Transporte:
    """One sequential client per job; budgets count actual HTTP attempts and bytes."""
    def __init__(self, *, max_http=12, max_bytes=120_000_000, max_wait=35,
                 session=None, sleep=time.sleep, clock=time.monotonic):
        self.session=session or requests.Session()
        self.sleep=sleep;self.clock=clock
        self.max_http=max_http;self.max_bytes=max_bytes;self.max_wait=max_wait
        self.http=0;self.bytes=0;self.waited=0.;self.events=[];self.blocked=set()
    def get(self,url,hosts,lim):
        u=urlsplit(url)
        if u.scheme!='https' or u.hostname not in hosts or u.username or u.password or u.port not in (None,443):
            raise AquisiçãoErro('ORIGEM_NAO_AUTORIZADA')
        host=u.hostname
        if host in self.blocked:raise AquisiçãoErro('FONTE_SUSPENSA')
        if lim<=0:raise AquisiçãoErro('LIMITE_INVALIDO')
        for i in range(3):
            if self.http>=self.max_http or self.bytes>=self.max_bytes:raise AquisiçãoErro('ORCAMENTO_REDE')
            self.http+=1
            try:
                with self.session.get(url,headers=UA,stream=True,allow_redirects=False,timeout=(10,25)) as r:
                    code=r.status_code;event={'host':host,'status':code,'tentativa':i+1}
                    self.events.append(event)
                    if code==200:
                        length=r.headers.get('Content-Length')
                        if length and length.isdigit():
                            event['content_length']=int(length)
                            event['limite_bytes']=min(lim,self.max_bytes-self.bytes)
                            if int(length)>event['limite_bytes']:
                                event['resultado']='LIMITE_CONTENT_LENGTH'
                                raise AquisiçãoErro('LIMITE_CONTENT_LENGTH')
                        data=bytearray()
                        for chunk in r.iter_content(65536):
                            self.bytes+=len(chunk)
                            if self.bytes>self.max_bytes or len(data)+len(chunk)>lim:
                                raise AquisiçãoErro('LIMITE_BYTES')
                            data.extend(chunk)
                        return bytes(data)
                    if code not in (429,502,503,504):raise AquisiçãoErro('HTTP '+str(code))
                    delay=retry_after(r.headers.get('Retry-After'))
                    reason='HTTP '+str(code)
            except (requests.exceptions.Timeout,requests.exceptions.ConnectionError) as e:
                # Retrying an interrupted GET starts from byte zero. All bytes
                # already received still count; no partial file is authenticated.
                reason=type(e).__name__
                event={'host':host,'status':None,'tentativa':i+1,'resultado':reason}
                self.events.append(event)
                delay=None
            delay=max(5.,delay if delay is not None else 5.*2**i)+random.uniform(0,.4)
            event['retry_after_s']=round(delay,2)
            if i==2 or self.waited+delay>self.max_wait or self.http>=self.max_http or self.bytes>=self.max_bytes:
                self.blocked.add(host)
                raise AquisiçãoErro(reason+' FONTE_SUSPENSA')
            self.sleep(delay);self.waited+=delay
        raise AquisiçãoErro('SEM_RESPOSTA')
    def resumo(self):
        return {'http':self.http,'bytes':self.bytes,'espera_s':round(self.waited,2),
                'fontes_suspensas':sorted(self.blocked),'eventos':self.events}
