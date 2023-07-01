# crypto_manager
A simple web app for managing and trading your cryptos in Kraken exchange

## Installation
1. Clone the repository
2. Install the requirements: `pip install -r requirements.txt`
3. Keys: make sure you have your Kraken API keys. Save them in a file called `keys.yaml` with the following structure:
   ```
   APIKEY: "your_api_key"
   PRIVATEKEY: "your_api_secret, also called private key
   ```
4. You may want to edit file `config.py` to consider more cryptos
5. Run the app: `streamlit run app.py`
