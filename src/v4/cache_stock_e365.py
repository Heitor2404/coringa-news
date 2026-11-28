"""24h request cache for contextual stock. No keys or media bytes persisted."""
import hashlib,json,sqlite3,time
from pathlib import Path

class CacheStock:
    TTL=24*3600
    def __init__(self,path,*,clock=time.time):
        self.path=Path(path);self.clock=clock
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def fetch(self,provider,request,load):
        # Only the known non-secret request parameters are used as identity.
        if provider not in ('pexels','pixabay'):raise ValueError('STOCK_PROVIDER')
        if any(k.lower() in ('key','api_key','authorization','wskey') for k in request):raise ValueError('STOCK_CACHE_SECRET')
        k=hashlib.sha256(json.dumps([provider,request],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        db=sqlite3.connect(self.path,timeout=45)
        try:
            db.execute('CREATE TABLE IF NOT EXISTS stock (k TEXT PRIMARY KEY, expires REAL NOT NULL, data TEXT NOT NULL)')
            db.commit()
            # Serialize same-cache requests even across independent processes.
            db.execute('BEGIN IMMEDIATE')
            now=self.clock()
            db.execute('DELETE FROM stock WHERE expires<=?',(now,))
            row=db.execute('SELECT data FROM stock WHERE k=?',(k,)).fetchone()
            if row:
                data=json.loads(row[0]);db.commit()
                return {**data,'cache_hit':True}
            data=load()
            if not isinstance(data,dict) or data.get('status') not in ('LEADS','EMPTY'):raise ValueError('STOCK_CACHE_RESULT')
            encoded=json.dumps(data,ensure_ascii=False,separators=(',',':'))
            if len(encoded.encode())>2_000_000:raise ValueError('STOCK_CACHE_LIMIT')
            db.execute('INSERT OR REPLACE INTO stock VALUES (?,?,?)',(k,self.clock()+self.TTL,encoded))
            db.commit()
            return {**data,'cache_hit':False}
        finally:
            db.close()
