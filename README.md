# liquidswap-sdk-python


## Installation
https://pypi.org/project/liquidswap-sdk/

`pip install liquidswap-sdk`

## Functions

### import
```python
from liquidswap_sdk.client import LiquidSwapClient
```

### new a client
```python
liquidswap_client = LiquidSwapClient(node_url, tokens_mapping, wallet_path)
```

### get the output amount from given input amount
```python
liquidswap_client.calculate_rates("APTOS", "USDT", 1)
```

### swap token
```python
liquidswap_client.swap("APTOS", "USDT", 1, usdt_out)
```

### get token balance
```python
liquidswap_client.get_token_balance("APTOS")
```

### register token
```python
liquidswap_client.register("USDT")
```

## How to use

1. create your [config](config.py)

2. add token addresses you want to trade to `tokens_mapping`

3. make sure there is some APT in your wallet of `wallet_path`

4. make yout own script! (check: [example](example.py))

5. if you are ready to `mainnt`, change the `node_url` to `https://fullnode.mainnet.aptoslabs.com/v1`


## WIP:

- [x] convert_to_decimals
- [x] calculate_rates
- [x] swap
- [x] create pypl package


