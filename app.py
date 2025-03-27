from flask import Flask,render_template,send_from_directory
from flask_caching import Cache
import requests

app=Flask(__name__)
app.config['CACHE_TYPE']='SimpleCache'
cache=Cache(app)

@app.route("/")
def index():
	return render_template("map.html")

@app.route("/gas.svg")
def favicon():
	return send_from_directory(app.static_folder,"gas.svg")

@app.route("/gas.csv")
@cache.cached(timeout=1800)
def gas():
	result=["Sams https://www.samsclub.com/local/fuel-center/-/X"]
	url='https://www.samsclub.com/api/node/vivaldi/browse/v2/clubfinder/list?distance=10000&nbrOfStores=1000&singleLineAddr=10001'
	sams=requests.get(url,headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'ztsd'}).json()
	for s in sams:
		if 'gasPrices' in s:
			p={g['gradeId']:int(g['price']*100) for g in s['gasPrices']}
			result.append(f"{p[11]},{p[16]},{s['geoPoint']['latitude']},{s['geoPoint']['longitude']},{s['id']}")
	result.append("Costco https://www.costco.com/warehouse-locations-X.html#:~:text=Gas%20Station")
	url='https://www.costco.com/AjaxWarehouseBrowseLookupView?hasGas=true&populateWarehouseDetails=true'
	costco=requests.get(url,headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'gzip'}).json()[1:]
	for s in costco:
		if 'regular' in s['gasPrices'] and s['country']=='US':
			p={g:int(float(s['gasPrices'][g])*100) for g in ['regular','premium']}
			result.append(f"{p['regular']},{p['premium']},{s['latitude']},{s['longitude']},{s['displayName']}")
	return "\n".join(result)
