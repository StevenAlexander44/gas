from flask import Flask,render_template
from flask_caching import Cache
import httpx
import re
import json

app=Flask(__name__)
app.config['CACHE_TYPE']='SimpleCache'
cache=Cache(app)

@app.route("/")
def index():
    return render_template("map.html")

def penny(dollar):
    return int(float(dollar)*100)

@app.route("/samsclub.csv")
@cache.cached(timeout=1800)
def sams():
    url='https://www.samsclub.com/api/node/vivaldi/browse/v2/clubfinder/list?distance=9999&nbrOfStores=999&singleLineAddr=1'
    headers={'User-Agent':'Mozilla/5.0'}
    sams=httpx.get(url,headers=headers,timeout=10).json()
    result=[]
    for s in sams:
        if 'gasPrices' in s:
            p={g['gradeId']:penny(g['price']) for g in s['gasPrices']}
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
        p={g['fuelTypeId']:penny(g['price']) for g in s['gasPrices']}
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
        p={g['description']:penny(g['unitPrice']) for g in s['price_data'] if str(g['unitPrice'])[-1]=='9'}
        if 'UNLEADED' in p or 'PREMIUM' in p:
            result.append(f"{p.get('UNLEADED','0')},{p.get('PREMIUM','0')},{s['lat']},{s['lng']},{s['phone']}")
    return "\n".join(result)

@app.route("/wawa.csv")
@cache.cached(timeout=1800)
def wawa():
    url='https://www2.wawa.com/handlers/locationbylatlong.ashx?limit=9999&lat=38.2&long=-85.7'
    headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0','Referer':'https://www2.wawa.com'}
    wawa=httpx.get(url,headers=headers).json()['locations']
    result=[]
    for s in wawa:
        p={g['description']:penny(g['price']) for g in s['fuelTypes']}
        if 'Unleaded' in p or 'Premium' in p:
            result.append(f"{p.get('Unleaded','0')},{p.get('Premium','0')},{s['addresses'][1]['loc'][0]},{s['addresses'][1]['loc'][1]},{int(s['locationID'])}")
    return "\n".join(result)

def prowl(url,brand):
    tag={'meijer':'pre','costco':'body'}.get(brand)
    r=httpx.post('http://localhost:8191/v1',json={'cmd':'request.get','url':url,'session':brand})
    return json.loads(re.search(rf'<{tag}>(.*?)<\/{tag}>',r.json()['solution']['response']).group(1))

@app.route("/meijer.csv")
@cache.cached(timeout=1800)
def meijer():
    meijer=prowl('https://www.meijer.com/bin/meijer/store/search/proximity?latitude=38.2&longitude=-85.7&miles=20&numToReturn=10','meijer')['store']
    result=[]
    for s in meijer:
        p=prowl(f"https://www.meijer.com/bin/meijer/store/hours?store-id={s['UnitId']}",'meijer')
        if 'fuelPrices' in p:
            p={g['FuelType'].split('-')[0]:penny(g['FuelPrice']) for g in p['fuelPrices']}
            result.append(f"{p['UNL']},{p['PREM']},{s['latitude']},{s['longitude']},{s['UnitId']}")
    httpx.post('http://localhost:8191/v1',json={'cmd':'sessions.destroy','session':'meijer'})
    return "\n".join(result)

@app.route("/costco.csv")
@cache.cached(timeout=1800)
def costco():
    url='https://ecom-api.costco.com/core/warehouse-locator/v1/warehouses.json?latitude=38.2&longitude=-85.7&limit=10'
    headers={'User-Agent':'Mozilla/5.0','client-identifier':'7c71124c-7bf1-44db-bc9d-498584cd66e5'}
    costco=httpx.get(url,headers=headers).json()['warehouses']
    warehouses={w['warehouseId'] for w in costco}
    p=prowl(f"https://www.costco.com/AjaxGetGasPricesService?warehouseid={'_'.join(warehouses)}",'costco')
    result=[]
    for s in costco:
        w=s['warehouseId']
        result.append(f"{penny(p[w].get('regular','0'))},{penny(p[w].get('premium','0'))},{s['address']['latitude']},{s['address']['longitude']},{w}")
    return "\n".join(result)
