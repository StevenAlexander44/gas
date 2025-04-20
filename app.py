from flask import Flask,render_template,send_from_directory
from flask_caching import Cache
import httpx

app=Flask(__name__)
app.config['CACHE_TYPE']='SimpleCache'
cache=Cache(app)

@app.route("/")
def index():
    return render_template("map.html")

@app.route("/gas.svg")
def favicon():
    return send_from_directory(app.static_folder,"gas.svg")

@app.route("/samsclub.csv")
@cache.cached(timeout=1800)
def sams():
    url='https://www.samsclub.com/api/node/vivaldi/browse/v2/clubfinder/list?distance=10000&nbrOfStores=1000&singleLineAddr=10001'
    headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'ztsd'}
    sams=httpx.get(url,headers=headers,timeout=10).json()
    result=[]
    for s in sams:
        if 'gasPrices' in s:
            p={g['gradeId']:int(g['price']*100) for g in s['gasPrices']}
            result.append(f"{p[11]},{p[16]},{s['geoPoint']['latitude']},{s['geoPoint']['longitude']},{s['id']}")
    return "\n".join(result)

@app.route("/costco.csv")
@cache.cached(timeout=1800)
def costco():
    url='https://www.costco.com/AjaxWarehouseBrowseLookupView?hasGas=true&populateWarehouseDetails=true'
    headers={'Accept':'*/*','Accept-Encoding':'gzip,deflate,br,zstd','Accept-Language':'en','Referer':'costco.com','Sec-Fetch-Mode':'cors','User-Agent':'Mozilla/5.0 Firefox/140.0'}
    costco=httpx.Client(http2=True).get(url,headers=headers,timeout=60).json()[1:]
    result=[]
    for s in costco:
        if 'regular' in s['gasPrices'] and s['country']=='US':
            p={g:int(float(s['gasPrices'][g])*100) for g in ['regular','premium']}
            result.append(f"{p['regular']},{p['premium']},{s['latitude']},{s['longitude']},{s['displayName']}")
    return "\n".join(result)
