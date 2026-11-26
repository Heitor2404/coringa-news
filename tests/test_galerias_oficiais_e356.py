import pytest
from src.v4 import galerias_oficiais_e356 as G
class T:
    def __init__(self,*rows):self.rows=iter(rows);self.calls=[]
    def get(self,url,hosts,lim):self.calls.append(url);return next(self.rows).encode()
def test_nist_form_and_type():
    t=T('<form method="get"><label for="s">Keyword</label><input id="s" name="keys"></form>',
        '<a href="/image/antenna">Antenna robot</a><a href="/video/antenna">Antenna video</a>')
    r=G.discover('antenna','nist','foto',transport=t)
    assert r['mode']=='GET_FORM_QUERY' and len(r['candidates'])==1
    assert 'keys=antenna' in t.calls[1]
def test_noaa_direct_and_limit():
    page='https://oceanexplorer.noaa.gov/multimedia/example/'
    html='<p>Credit</p><p>NOAA Ocean Exploration, expedition</p><a href="https://archive.oceanexplorer.noaa.gov/a.mp4">SD version (mp4, 17.5 MB)</a><a href="https://archive.oceanexplorer.noaa.gov/b.mp4">HD version (mp4, 222 MB)</a><a href="https://evil.test/a.mp4">SD version</a>'
    r=G.receipt(page,'noaa','video',transport=T(html))
    assert len(r['variants'])==1 and r['variants'][0]['size']==17500000 and not r['publish']
def test_nist_third_party_and_no_guessed_video():
    page='https://www.nist.gov/image/example'
    with pytest.raises(ValueError):G.receipt(page,'nist','foto',transport=T('<p>Credit</p><p>Third party</p>'))
    r=G.receipt('https://www.nist.gov/video/example','nist','video',transport=T('<p>Credit</p><p>NIST</p><a href="https://www.kaltura.com/x">Watch</a>'))
    assert r['status']=='NO_DIRECT_VARIANT'
def test_noaa_no_form_is_not_global_empty():
    r=G.discover('unmatched','noaa','video',transport=T('<p>gallery</p>'))
    assert r['status']=='PARTIAL_NO_MATCH'
