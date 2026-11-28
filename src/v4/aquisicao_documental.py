"""Bounded shared media transport for private documentary acquisition.
No proxy, credential rotation, blind redirects or license inference.
"""
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit,urljoin
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
    def get(self,url,hosts,lim,*,redirect_policy=None,_redirects=0):
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
                    if code in (301,302,303,307,308):
                        location=r.headers.get('Location')
                        if not location:raise AquisiçãoErro('REDIRECT_SEM_LOCATION')
                        try:
                            target=urljoin(url,location);dest=urlsplit(target)
                            event['redirect_host']=dest.hostname
                            # Never log a signed URL, query parameters or API credentials.
                            permitted=(redirect_policy is not None and _redirects<2 and
                                dest.scheme=='https' and dest.hostname in hosts and not dest.username
                                and not dest.password and dest.port in (None,443) and not dest.fragment
                                and redirect_policy(url,target))
                        except (ValueError,TypeError):permitted=False
                        event['redirect_permitido']=bool(permitted)
                        if not permitted:raise AquisiçãoErro('REDIRECT_PENDENTE_'+str(code))
                        # Explicitly release the previous response before making
                        # the next budget-accounted GET, never send API keys.
                        r.close()
                        return self.get(target,hosts,lim,redirect_policy=redirect_policy,_redirects=_redirects+1)
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
