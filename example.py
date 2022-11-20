from liquidswap_sdk.client import LiquidSwapClient

# Your setting
from config import node_url, tokens_mapping, wallet_path, slippage


if __name__ == "__main__":

    liquidswap_client = LiquidSwapClient(node_url, tokens_mapping, wallet_path)

    usdt_out = liquidswap_client.calculate_rates("APTOS", "USDT", 1)

    print(f"swap 1 APT to {usdt_out} USDT")

    liquidswap_client.swap("APTOS", "USDT", 1, usdt_out)

    apt_out = liquidswap_client.calculate_rates("USDT", "APTOS", usdt_out / 2)

    print(f"swap {usdt_out/2} USDT to {apt_out} APT")

    # Need the slippage here to prevent `ERR_COIN_OUT_NUM_LESS_THAN_EXPECTED_MINIMUM`
    liquidswap_client.swap("USDT", "APTOS", usdt_out / 2, apt_out * (1 - slippage))

    usdt_remaining = liquidswap_client.get_token_balance("USDT")
    apt_remaining = liquidswap_client.get_token_balance("APTOS")

    print(f"apt_remaining: {apt_remaining}, usdt_remaining: {usdt_remaining}")
