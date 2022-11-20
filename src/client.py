from typing import Optional

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.bcs import Serializer
from aptos_sdk.client import RestClient, FaucetClient
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionArgument,
    TransactionPayload,
)
from aptos_sdk.type_tag import StructTag, TypeTag

import constants
import config
import os


class LiquidSwapClient(RestClient):
    def __init__(self, node_url: str, wallet_path: str = None):
        super().__init__(node_url)

        if wallet_path:
            self.my_account = Account.load(wallet_path)
        elif os.path.exists(config.wallet_path):
            self.my_account = Account.load(config.wallet_path)
        else:
            self.my_account = Account.generate()
            self.my_account.store(config.wallet_path)

    def get_coin_info(self, token: str) -> int:
        token = config.Tokens_Mapping[token]
        data = self.account_resource(
            AccountAddress.from_hex(token.split("::")[0]),
            f"{constants.COIN_INFO}<{token}>",
        )["data"]
        return data["decimals"]

    def convert_to_decimals(self, amount: float, token: str) -> int:
        d = self.get_coin_info(token)
        return int(amount * 10**d)

    def pretty_amount(self, amount: int, token: str) -> float:
        d = self.get_coin_info(token)
        return float(amount / 10**d)

    def calculate_rates(self, from_token: str, to_token: str, amount: float) -> float:
        try:
            token_x = from_token
            token_y = to_token
            type = f"{constants.NETWORKS_MODULES['LiquidityPool']}::LiquidityPool<{config.Tokens_Mapping[token_x]}, {config.Tokens_Mapping[token_y]}, {constants.CURVES}>"
            data = self.account_resource(
                AccountAddress.from_hex(constants.RESOURCES_ACCOUNT),
                f"{constants.NETWORKS_MODULES['LiquidityPool']}::LiquidityPool<{config.Tokens_Mapping[token_x]}, {config.Tokens_Mapping[token_y]}, {constants.CURVES}>",
            )["data"]
            from_token_reserve = self.pretty_amount(
                int(data["coin_x_reserve"]["value"]), token_x
            )
            to_token_reserve = self.pretty_amount(
                int(data["coin_y_reserve"]["value"]), token_y
            )
        except:
            token_x = to_token
            token_y = from_token
            type = f"{constants.NETWORKS_MODULES['LiquidityPool']}::LiquidityPool<{config.Tokens_Mapping[token_x]}, {config.Tokens_Mapping[token_y]}, {constants.CURVES}>"
            data = self.account_resource(
                AccountAddress.from_hex(constants.RESOURCES_ACCOUNT),
                type,
            )["data"]
            to_token_reserve = self.pretty_amount(
                int(data["coin_x_reserve"]["value"]), token_x
            )
            from_token_reserve = self.pretty_amount(
                int(data["coin_y_reserve"]["value"]), token_y
            )

        coinInAfterFees = amount * (constants.FEE_SCALE - constants.FEE_PCT)

        newReservesInSize = from_token_reserve * constants.FEE_SCALE + coinInAfterFees

        return coinInAfterFees * to_token_reserve / newReservesInSize

    def get_token_balance(self, token: str) -> float:
        """get balance of `token`"""
        if self.is_coin_registered(token):
            r = self.account_resource(
                self.my_account.address(),
                f"0x1::coin::CoinStore<{config.Tokens_Mapping[token]}>",
            )["data"]["coin"]["value"]
            return self.pretty_amount(int(r), token)
        else:
            return 0

    def is_coin_registered(self, token: str) -> bool:
        try:
            self.account_resource(
                self.my_account.address(),
                f"0x1::coin::CoinStore<{config.Tokens_Mapping[token]}>",
            )["data"]["coin"]["value"]
            return True
        except:
            return False

    def register(self, token: str) -> str:

        payload = EntryFunction.natural(
            "0x1::managed_coin",
            "register",
            [
                TypeTag(StructTag.from_str(config.Tokens_Mapping[token])),
            ],
            [],
        )
        signed_transaction = self.create_single_signer_bcs_transaction(
            self.my_account, TransactionPayload(payload)
        )

        tx = self.submit_bcs_transaction(signed_transaction)
        rest_client.wait_for_transaction(tx)
        print(f"register coin: {token}, tx: {tx}")
        return tx

    def swap(
        self, from_token: str, to_token: str, from_amount: float, to_amount: float
    ) -> str:

        if not self.is_coin_registered(to_token):
            tx = self.register(to_token)

        payload = EntryFunction.natural(
            constants.NETWORKS_MODULES["Scripts"],
            "swap",
            [
                TypeTag(StructTag.from_str(config.Tokens_Mapping[from_token])),
                TypeTag(StructTag.from_str(config.Tokens_Mapping[to_token])),
                TypeTag(StructTag.from_str(constants.CURVES)),
            ],
            [
                TransactionArgument(
                    self.convert_to_decimals(from_amount, from_token),
                    Serializer.u64,
                ),
                TransactionArgument(
                    self.convert_to_decimals(to_amount, to_token),
                    Serializer.u64,
                ),
            ],
        )
        signed_transaction = self.create_single_signer_bcs_transaction(
            self.my_account, TransactionPayload(payload)
        )
        tx = self.submit_bcs_transaction(signed_transaction)
        rest_client.wait_for_transaction(tx)
        print(f"swap coin tx: {tx}")
        return tx


if __name__ == "__main__":

    rest_client = LiquidSwapClient(config.Node_Url)

    r = rest_client.calculate_rates("APTOS", "USDT", 1)

    print(r)

    r = rest_client.calculate_rates("USDT", "APTOS", 1)

    print(r)

    r = rest_client.get_token_balance("APTOS")

    print(r)

    rest_client.swap("APTOS", "USDT", 0.01, 0.005)
