from flask import Flask,render_template
from flask_caching import Cache
import httpx

app=Flask(__name__)
app.config['CACHE_TYPE']='SimpleCache'
cache=Cache(app)

@app.route("/")
def index():
    return render_template("map.html")

@app.route("/samsclub.csv")
@cache.cached(timeout=1800)
def sams():
    url='https://www.samsclub.com/api/node/vivaldi/browse/v2/clubfinder/list?distance=9999&nbrOfStores=999&singleLineAddr=1'
    headers={'User-Agent':'Mozilla/5.0'}
    sams=httpx.get(url,headers=headers,timeout=10).json()
    result=[]
    for s in sams:
        if 'gasPrices' in s:
            p={g['gradeId']:int(g['price']*100) for g in s['gasPrices']}
            result.append(f"{p[11]},{p[16]},{s['geoPoint']['latitude']},{s['geoPoint']['longitude']},{s['id']}")
    return "\n".join(result)

@app.route("/murphyusa.csv")
@cache.cached(timeout=1800)
def murphy():
    url='https://service.murphydriverewards.com/api/store'
    headers={'User-Agent':'Mozilla/5.0'}
    murphy=httpx.post(url,headers=headers,json={"pageSize":9999,"range":9999}).json()['data']['stores']
    result=[]
    for s in murphy:
        p={g['fuelTypeId']:int(g['price']*100) for g in s['gasPrices']}
        if 12 in p or 14 in p:
            result.append(f"{p.get(12,'0')},{p.get(14,'0')},{s['latitude']},{s['longitude']},{''.join(c for c in s['phone'] if c.isdigit())}")
    return "\n".join(result)

@app.route("/marathon.csv")
@cache.cached(timeout=1800)
def marathon():
    url='https://www.marathonarcorewards.com/ajax_stations_search.html?reason=get-station-info'
    headers={'User-Agent':'Mozilla/5.0'}
    marathon=httpx.get(url,headers=headers).json()
    result=[]
    for s in marathon:
        p={g['description']:int(float(g['unitPrice'])*100) for g in s['price_data'] if str(g['unitPrice'])[-1]=='9'}
        if 'UNLEADED' in p or 'PREMIUM' in p:
            result.append(f"{p.get('UNLEADED','0')},{p.get('PREMIUM','0')},{s['lat']},{s['lng']},{s['phone']}")
    return "\n".join(result)

@app.route("/meijer.csv")
@cache.cached(timeout=1800)
def meijer():
    url='https://www.meijer.com/bin/meijer/store/search/proximity?latitude=38.3&longitude=-85.7&miles=20&numToReturn=10'
    headers={'User-Agent':'Firefox/140'}
    meijer=httpx.get(url,headers=headers).json()['store']
    result=[]
    for s in meijer:
        p=httpx.get(f"https://www.meijer.com/bin/meijer/store/hours?store-id={s['UnitId']}",headers=headers).json()
        if 'fuelPrices' in p:
            p={g['FuelType'].split('-')[0]:int(g['FuelPrice']*100) for g in p['fuelPrices']}
            result.append(f"{p['UNL']},{p['PREM']},{s['latitude']},{s['longitude']},{s['UnitId']}")
    return "\n".join(result)
