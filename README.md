# crypto_manager
A simple web app for managing and trading your cryptos in Kraken exchange

## Running app
1. Clone the repository
2. Install the requirements: `pip install -r requirements.txt`
3. Keys: make sure you have your Kraken API keys. Save them in a file called `keys.yaml`, at the same level as README.md file, with the following structure:
   ```
   APIKEY: "your_api_key"
   PRIVATEKEY: "your_api_secret, also called private key
   ```
4. You may want to edit file `config.py` to consider more cryptos
5. Run the app: navigate to folder and run `streamlit run ./app.py`


## Backtesting strategies
1. Edit `trading/config.yaml` file
2. Run `trading/main.py` file
