from flask import Flask, jsonify, render_template
import requests
import time
import threading  # Background thread (backend)

Total_number_of_symbols = 0

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.json.sort_keys = False 


funding_data_cache = []

def get_all_symbols():
    all_assets_url = "https://fapi.binance.com/fapi/v1/exchangeInfo"  #Binance API
    data = requests.get(all_assets_url).json()  #Convert to json so that can be the handleable object in Python

    symbols = []
    for item in data["symbols"]:  # When do data["symbols"], you're accessing the key called "symbols" in that dictionary
        symbol = item["symbol"]  # A dictionary as well

        #If the coin is a normal USDT pair and it does not have an underline, add it to the list
        if symbol.endswith("USDT") and "_" not in symbol:  #Only keeps coins that are USDT futures pairs, reject underline because symbols with that are dated contracts which are not funding rate
            symbols.append(symbol) 
    return symbols

def get_funding_rate(symbol):
    url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}"
    visit_the_url = requests.get(url).json()
    rate = float(visit_the_url["lastFundingRate"]) * 100 #The fundind rate will be in % form 
    return float(f"{rate:.4f}") 

def monitor_all_symbols():
    global funding_data_cache
    global Total_number_of_symbols


    ceilling = 0.05
    floor = -0.05

    while True:
        try:
            symbols = get_all_symbols()
            Total_number_of_symbols = len(symbols)
            print(f"Monitoring {len(symbols)} symbols... \n")
            print("--- Checking Funding Rates ---")

            results = []
            for symbol in symbols:
                try:
                    rate = get_funding_rate(symbol)
                except Exception: # without Exception the except catches everything so you can't interrupt the program by doing control C
                    continue

                if rate > ceilling:
                    results.append({"Symbol": symbol, "Funding rate": rate, "Alert": "VERY HIGH"})
                    print (f"ALERT: {symbol} VERY HIGH: {rate:.4f}%")
                elif rate < floor:
                    results.append({"Symbol": symbol, "Funding rate": rate, "Alert": "VERY LOW"})
                    print(f"ALERT: {symbol} VERY LOW: {rate:.4f}%")
                else:
                    results.append({"Symbol": symbol, "Funding rate": rate, "Alert": "OK"})
                    print(f"OK: {symbol} {rate:.4f}%")

                funding_data_cache = results

            print(f"\n✓ Fetching complete! {len(results)} symbols loaded.")
            print("Will fetch again in 60 minutes.\n")

        except Exception as error:
            print ("Monitor crashed...", error)

        time.sleep(3600) #check every hour

@app.route("/")
def index():
    # Return the HTML template
    return render_template("index.html", total_symbols = Total_number_of_symbols)

@app.route("/funding_rate_shown_on_website")
def funding_rate_shown_on_website():
    return jsonify(funding_data_cache)

if __name__ == "__main__":
    threading.Thread(target=monitor_all_symbols, daemon=True).start() # Runs monitor_all_symbols() loop in the background (backend)        # daemon = background thread that automatically stops when the main program stops.
    app.run(debug=False)   # Start the Flask website