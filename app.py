from flask import Flask, render_template, send_from_directory
from flask_caching import Cache
import requests

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 1800
cache = Cache(app)

@app.route("/")
def index():
	return render_template("map.html")

@app.route("/gas.svg")
def favicon():
	return send_from_directory(app.static_folder, "gas.svg")

@app.route("/gas.csv")
def gas():
	data = cache.get("gas")
	if data: return data

	result = ["Sams https://www.samsclub.com/local/fuel-center/-/X"]
	for s in samsdata():
		if 'gasPrices' in s:
			p = {11:0,16:0}
			for grade in s['gasPrices']:
				if grade['gradeId'] in p:
					p[grade['gradeId']] = int(grade['price']*100)
			result.append(f"{p[11]},{p[16]},{s['geoPoint']['latitude']},{s['geoPoint']['longitude']},{s['id']}")
	result.append("Costco https://www.costco.com/warehouse-locations-X.html#:~:text=Gas%20Station")
	for s in costcodata():
		if 'US' == s['country'] and 'regular' in s['gasPrices'] and 'PR' != s['state']:
			p = {'regular':0,'premium':0}
			for grade in p:
				p[grade] = int(float(s['gasPrices'][grade])*100)
			result.append(f"{p['regular']},{p['premium']},{s['latitude']},{s['longitude']},{s['displayName']}")
	data = "\n".join(result)
	cache.set("gas", data)
	return data

@app.route("/sams.json")
def samsdata():
	data = cache.get("sams")
	if data: return data

	url = 'https://www.samsclub.com/api/node/vivaldi/browse/v2/clubfinder/list?distance=10000&nbrOfStores=1000&singleLineAddr=10001'
	response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'ztsd'})
	data = response.json()
	cache.set("sams", data)
	return data

@app.route("/costco.json")
def costcodata():
	data = cache.get("costco")
	if data: return data

	url = 'https://www.costco.com/AjaxWarehouseBrowseLookupView?hasGas=true&populateWarehouseDetails=true'
	response = requests.get(url, headers={'User-Agent': 'Mozilla', 'Accept-Encoding': 'gzip'})
	data = response.json()[1:]
	cache.set("costco", data)
	return data
