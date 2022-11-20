from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.bcs import Serializer
from aptos_sdk.client import RestClient
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionArgument,
    TransactionPayload,
)
from aptos_sdk.type_tag import StructTag, TypeTag

from .constants import (
    COIN_INFO,
    NETWORKS_MODULES,
    RESOURCES_ACCOUNT,
    FEE_SCALE,
    FEE_PCT,
    CURVES,
)


class LiquidSwapClient(RestClient):
    def __init__(self, node_url: str, tokens_mapping: dict, wallet_path: str):
        super().__init__(node_url)

        self.tokens_mapping = tokens_mapping

        self.my_account = Account.load(wallet_path)

    def get_coin_info(self, token: str) -> int:
        token = self.tokens_mapping[token]
        data = self.account_resource(
            AccountAddress.from_hex(token.split("::")[0]),
            f"{COIN_INFO}<{token}>",
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
            type = f"{NETWORKS_MODULES['LiquidityPool']}::LiquidityPool<{self.tokens_mapping[token_x]}, {self.tokens_mapping[token_y]}, {CURVES}>"
            data = self.account_resource(
                AccountAddress.from_hex(RESOURCES_ACCOUNT),
                f"{NETWORKS_MODULES['LiquidityPool']}::LiquidityPool<{self.tokens_mapping[token_x]}, {self.tokens_mapping[token_y]}, {CURVES}>",
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
            type = f"{NETWORKS_MODULES['LiquidityPool']}::LiquidityPool<{self.tokens_mapping[token_x]}, {self.tokens_mapping[token_y]}, {CURVES}>"
            data = self.account_resource(
                AccountAddress.from_hex(RESOURCES_ACCOUNT),
                type,
            )["data"]
            to_token_reserve = self.pretty_amount(
                int(data["coin_x_reserve"]["value"]), token_x
            )
            from_token_reserve = self.pretty_amount(
                int(data["coin_y_reserve"]["value"]), token_y
            )

        coinInAfterFees = amount * (FEE_SCALE - FEE_PCT)

        newReservesInSize = from_token_reserve * FEE_SCALE + coinInAfterFees

        return coinInAfterFees * to_token_reserve / newReservesInSize

    def get_token_balance(self, token: str) -> float:
        """get balance of `token`"""
        if self.is_coin_registered(token):
            r = self.account_resource(
                self.my_account.address(),
                f"0x1::coin::CoinStore<{self.tokens_mapping[token]}>",
            )["data"]["coin"]["value"]
            return self.pretty_amount(int(r), token)
        else:
            return 0

    def is_coin_registered(self, token: str) -> bool:
        try:
            self.account_resource(
                self.my_account.address(),
                f"0x1::coin::CoinStore<{self.tokens_mapping[token]}>",
            )["data"]["coin"]["value"]
            return True
        except:
            return False

    def register(self, token: str) -> str:

        payload = EntryFunction.natural(
            "0x1::managed_coin",
            "register",
            [
                TypeTag(StructTag.from_str(self.tokens_mapping[token])),
            ],
            [],
        )
        signed_transaction = self.create_single_signer_bcs_transaction(
            self.my_account, TransactionPayload(payload)
        )

        tx = self.submit_bcs_transaction(signed_transaction)
        self.wait_for_transaction(tx)
        print(f"register coin: {token}, tx: {tx}")
        return tx

    def swap(
        self, from_token: str, to_token: str, from_amount: float, to_amount: float
    ) -> str:

        if not self.is_coin_registered(to_token):
            tx = self.register(to_token)

        payload = EntryFunction.natural(
            NETWORKS_MODULES["Scripts"],
            "swap",
            [
                TypeTag(StructTag.from_str(self.tokens_mapping[from_token])),
                TypeTag(StructTag.from_str(self.tokens_mapping[to_token])),
                TypeTag(StructTag.from_str(CURVES)),
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
        self.wait_for_transaction(tx)
        print(f"swap coin tx: {tx}")
        return tx
