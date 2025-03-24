import os
import json
import pkgutil
import time
import logging
from web3 import Web3
from hashlib import sha256
import requests
from web3.middleware import SignAndSendRawMiddlewareBuilder
from web3.middleware import ExtraDataToPOAMiddleware
from web3.constants import ADDRESS_ZERO 
from web3.contract.contract import ContractFunction

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from web3.types import (
    Nonce,
    TxParams,
    TxReceipt,
    Wei,
)

from .util import (
    _create_wallet,
)


logger = logging.getLogger(__name__)

from membase.chain.evm import BaseClient

class BeeperClient(BaseClient):
    def __init__(self, config: dict, wallet_address: str, private_key: str, privy_app_id: str = None):
        ep = config["RPC"]
        super().__init__(
            wallet_address=wallet_address,
            private_key=private_key,
            ep=ep
        )

    
        self.config = config
        
        max_approval_hex = f"0x{64 * 'f'}"
        self.max_approval_int = int(max_approval_hex, 16)
        max_approval_check_hex = f"0x{15 * '0'}{49 * 'f'}"
        self.max_approval_check_int = int(max_approval_check_hex, 16)    

        self.router_address = Web3.to_checksum_address(self.config["PancakeV3SwapRouter"])
        router_abi = pkgutil.get_data('membase.chain', 'solc/pancake_swaprouter_v3.abi').decode()
        self.router = self.w3.eth.contract(address=self.router_address, abi=router_abi)

        self.privy_app_id = ""
        if privy_app_id and privy_app_id != "": 
            self.privy_app_id = privy_app_id
            app_secret = os.getenv('PRIVY_APP_SECRET')
            if not app_secret or app_secret == "":
                print("please set privy app secret env 'PRIVY_APP_SECRET'")
                exit(1)

    def deploy(self, wallet_address: str, private_key: str):
        wbnb = self.router.functions.WETH9().call()
        swapRouter = Web3.to_checksum_address(self.config["PancakeV3SwapRouter"])
        uniswapV3Factory =  Web3.to_checksum_address(self.config["PancakeV3Factory"])
        positionManager =  Web3.to_checksum_address(self.config["PostionManage"])

        wallet_address = Web3.to_checksum_address(wallet_address)
        # todo: another account here
        beeperEOA = Web3.to_checksum_address(wallet_address)
        contract_json = json.loads(pkgutil.get_data('membase.chain', 'solc/Beeper.sol/Beeper.json').decode())

        current_nonce = self.w3.eth.get_transaction_count(wallet_address)
        Beeper = self.w3.eth.contract(abi=contract_json['abi'], bytecode=contract_json['bytecode']['object'])
        transaction = Beeper.constructor(wbnb, uniswapV3Factory, positionManager, swapRouter, beeperEOA).build_transaction({
            "from": wallet_address,
            "nonce": current_nonce,
            "gas": 10_000_000,
            "gasPrice": self.w3.eth.gas_price,
        })

        signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        beeper_address = tx_receipt.contractAddress
        if tx_receipt['status'] == 0:
            print("Transaction failed")
            self._display_cause(tx_hash)
            exit(1)
        else:
            print(f'Transaction succeeded: {tx_hash.hex()}')

        print(f"Beeper address: {beeper_address}")

        beeper = self.w3.eth.contract(address=beeper_address, abi=contract_json['abi'])

        contract_json = json.loads(pkgutil.get_data('membase.chain', 'solc/LpLockerv2.sol/LpLockerv2.json').decode())

        current_nonce = current_nonce + 1
        LockerFactory = self.w3.eth.contract(abi=contract_json['abi'], bytecode=contract_json['bytecode']['object'])
        transaction = LockerFactory.constructor(beeper_address, positionManager, beeperEOA, 60).build_transaction({
            "from": wallet_address,
            "nonce": current_nonce,
            "gas": 10_000_000,
            "gasPrice": self.w3.eth.gas_price,
        })
        signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt['status'] == 0:
            print("Transaction failed")
            self._display_cause(tx_hash)
            exit(1)
        else:
            print(f'Transaction succeeded: {tx_hash.hex()}')

        locker_address = tx_receipt.contractAddress
        print(f"Locker address: {locker_address}")

        current_nonce = current_nonce + 1
        update_tx = beeper.functions.updateLiquidityLocker(locker_address).build_transaction({
            "from": wallet_address,
            "nonce": current_nonce,
            "gas": 10_000_000,
            "gasPrice": self.w3.eth.gas_price,
        })
        signed_tx = self.w3.eth.account.sign_transaction(update_tx, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt['status'] == 0:
            print("Transaction failed")
            self._display_cause(tx_hash)
            exit(1)
        else:
            print(f'Transaction succeeded: {tx_hash.hex()}')

        current_nonce = current_nonce + 1
        contract_json = json.loads(pkgutil.get_data('membase.chain', 'solc/Util.sol/Util.json').decode())
        util = self.w3.eth.contract(abi=contract_json['abi'], bytecode=contract_json['bytecode']['object'])
        transaction = util.constructor(beeper_address, wbnb).build_transaction({
            "from": wallet_address,
            "nonce": current_nonce,
            "gas": 10_000_000,
            "gasPrice": self.w3.eth.gas_price,
        })

        signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        util_address = tx_receipt.contractAddress
        if tx_receipt['status'] == 0:
            print("Transaction failed")
            self._display_cause(tx_hash)
            exit(1)
        else:
            print(f'Transaction succeeded: {tx_hash.hex()}')

        print(f"Util address: {util_address}")

        current_nonce = current_nonce + 1
        transaction = beeper.functions.toggleAllowedPairedToken(wbnb, True).build_transaction({
            "from": wallet_address,
            "nonce": current_nonce,
            "gas": 10_000_000,
            "gasPrice": self.w3.eth.gas_price,
        })
        signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt['status'] == 0:
            print("Transaction failed")
            self._display_cause(tx_hash)
            exit(1)
        else:
            print(f'Transaction succeeded: {tx_hash.hex()}')
        
        self.config["Beeper"] = beeper_address
        self.config["BeeperUtil"] = util_address
    
    # by owner, add deployer_admin to call deploy_token
    def set_admin(self, 
                    wallet_address: str, 
                    private_key: str, 
                    deployer_admin: str,                                           
                    ):
        beeper_address = Web3.to_checksum_address(self.config["Beeper"])
        deployer_admin = Web3.to_checksum_address(deployer_admin)
        contract_json = json.loads(pkgutil.get_data('membase.chain', 'solc/Beeper.sol/Beeper.json').decode())
        Beeper = self.w3.eth.contract(address=beeper_address, abi=contract_json['abi'])
        transaction = Beeper.functions.setAdmin(deployer_admin, True).build_transaction({
            "from": wallet_address,
            "nonce": self.w3.eth.get_transaction_count(wallet_address),
            "gas": 10_000_000,
            "gasPrice": self.w3.eth.gas_price,
            #"value": self.w3.to_wei(10000, 'gwei'),
        })
        signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt['status'] == 0:
            print("Transaction failed")
            self._display_cause(tx_hash)
        else:
            print(f'Transaction succeeded: {tx_hash.hex()}')

    # by owner or deployer admin
    def deploy_token(self, 
                    twitter_eth_account: str,
                    twitter_id: int, 
                    image: str = 'https://twitter.com/',
                    token_name : str = 'Beeper',
                    token_symbol:  str = 'Power by Beeper',
                    token_supply: int = 10000000000 * 10**18,
                    initial_tick: int = -207400, 
                    fee: int = 10000, #1%; 500:0.05%; 2500:0.25%
                    buyfee: int = 10000,                                               
                    ) -> str:
        
        beeper_address = Web3.to_checksum_address(self.config["Beeper"])
        util_address = Web3.to_checksum_address(self.config["BeeperUtil"])
        wbnb = self.router.functions.WETH9().call()
        
        # risky, use envion
        if self.wallet_address == "":
            raise Exception(f"No admin wallet address")
        if self.private_key== "":
            raise Exception(f"No admin private key")
            
        private_key = self.wallet_address
        wallet_address = self.private_key

        tweetHash = sha256(str(twitter_id).encode('utf-8')).hexdigest() 
        twitter_eth_account = Web3.to_checksum_address(twitter_eth_account)
        contract_json = json.loads(pkgutil.get_data('membase.chain', 'solc/Util.sol/Util.json').decode())
        util = self.w3.eth.contract(address=util_address, abi=contract_json['abi'])
        
        try:
            generated_salt, token_address = util.functions.generateSalt(twitter_eth_account, twitter_id, token_name, token_symbol, image, tweetHash, token_supply, wbnb).call()
            print(f"Salt: {generated_salt.hex()} {token_address}")
        except Exception as e:
            raise e

        pool_config =[initial_tick,  wbnb,  buyfee]
        contract_json = json.loads(pkgutil.get_data('membase.chain', 'solc/Beeper.sol/Beeper.json').decode())
        beeper = self.w3.eth.contract(address=beeper_address, abi=contract_json['abi'])

        return self.build_and_send_tx(
                beeper.functions.deployToken(
                    token_name, 
                    token_symbol, 
                    token_supply, 
                    fee, 
                    generated_salt, 
                    twitter_eth_account, 
                    twitter_id, 
                    image, 
                    tweetHash, 
                    pool_config
                ),
                self.get_tx_params(gas=8_000_000),
            ), token_address, token_supply

    # by user
    def claim_reward(self,
                    token_address: str,                                           
                    ):
        beeper_address = Web3.to_checksum_address(self.config["Beeper"])
        token_address = Web3.to_checksum_address(token_address)
        contract_json = json.loads(pkgutil.get_data('membase.chain', 'solc/Beeper.sol/Beeper.json').decode())
        Beeper = self.w3.eth.contract(address=beeper_address, abi=contract_json['abi'])

        return self.build_and_send_tx(
                Beeper.functions.claimRewards(token_address),
                self.get_tx_params(),
            )

    def make_trade(self, 
                    input_token :str, 
                    output_token :str,
                    amount: int = 1000000, 
                    fee: int = 10000 # deploy same setting
                    ):
            """
            :param input_token: "" means native.
            :param output_token: "" means native.
            """
            if input_token == "" :
                # buy token
                return self._native_to_token(output_token, amount, fee
                )
            elif output_token == "":
                # sell token
                return self._token_to_native(input_token, amount, fee
                )
            else:
                return self._token_to_token(input_token,output_token, amount, fee)
            
    def _native_to_token(self, 
                  token_address :str, 
                  amount: int = 1000000, 
                  fee: int = 10000 # deploy same setting
                  ):
        token_address = Web3.to_checksum_address(token_address)

        pfees = [10000, 2500, 500, 100]
        for pfee in pfees:
            paddr = self.get_token_pool(token_address, pfee)
            if paddr != ADDRESS_ZERO:
                print(f"pool addr at: {paddr} {pfee}")
                fee = pfee
                break
        
        return self.build_and_send_tx(
            self.router.functions.exactInputSingle(
                {
                    "tokenIn": self.router.functions.WETH9().call(),
                    "tokenOut": token_address,
                    "fee": fee,
                    "recipient": self.wallet_address,
                    "deadline": int(time.time()) + 3600,
                    "amountIn": amount,
                    "amountOutMinimum": 0,
                    "sqrtPriceLimitX96": 0,
                }
            ),
            self.get_tx_params(value=amount),
        )

    def _token_to_native(self,
                  token_address :str, 
                  amount: int = 1000000, 
                  fee: int = 10000 # deploy same setting
                  ):
        token_address = Web3.to_checksum_address(token_address)

        pfees = [10000, 2500, 500, 100]
        for pfee in pfees:
            paddr = self.get_token_pool(token_address, pfee)
            if paddr != ADDRESS_ZERO:
                print(f"pool addr at: {paddr} {pfee}")
                fee = pfee
                break

        self.check_appraval(token_address, self.router_address)

        print(f"Seller: {amount} {token_address} to bnb...")

        swap_data = self.router.encode_abi(
            "exactInputSingle",
            args=[
                (
                    token_address,
                    self.router.functions.WETH9().call(),
                    fee,
                    ADDRESS_ZERO,
                    int(time.time()) + 3600,
                    amount,
                    0,
                    0,
                )
            ],
        )
        unwrap_data = self.router.encode_abi(
            "unwrapWETH9", args=[0, self.wallet_address]
        )

        # Multicall
        return self.build_and_send_tx(
            self.router.functions.multicall([swap_data, unwrap_data]),
            self.get_tx_params(),
        )
    
    def _token_to_token(self, 
                  input_token :str,
                  output_token :str, 
                  amount: int = 1000000, 
                  fee: int = 10000
                  ):
        input_token = Web3.to_checksum_address(input_token)
        output_token = Web3.to_checksum_address(output_token)


        wbnb_address = Web3.to_checksum_address(self.router.functions.WETH9().call())
        if input_token != wbnb_address and output_token != wbnb_address:
            return self._token_to_token_via_hop(input_token, output_token, amount, fee)

        self.check_appraval(input_token, self.router_address)
        
        return self.build_and_send_tx(
            self.router.functions.exactInputSingle(
                {
                    "tokenIn": input_token,
                    "tokenOut": output_token,
                    "fee": fee,
                    "recipient": self.wallet_address,
                    "deadline": int(time.time()) + 3600,
                    "amountIn": amount,
                    "amountOutMinimum": 0,
                    "sqrtPriceLimitX96": 0,
                }
            ),
            self.get_tx_params(),
        )
    
    def _token_to_token_via_hop(self,
                  input_token :str,
                  output_token :str, 
                  amount: int = 1000000, 
                  fee: int = 10000
                  ):
        input_token = Web3.to_checksum_address(input_token)
        output_token = Web3.to_checksum_address(output_token)

        self.check_appraval(input_token, self.router_address)

        wbnb_address = self.router.functions.WETH9().call()

        tokens = [input_token, wbnb_address, output_token]
        #fees = [fee, fee]
        fees = []
        # pancake fee: 100, 500, 2500, 10000        
        pfees = [10000, 2500, 500, 100]
        for fee in pfees:
            paddr = self.get_token_pool(input_token, fee)
            if paddr != ADDRESS_ZERO:
                print(f"pool addr at: {paddr} {fee}")
                fees.append(fee)
                break
        if len(fees) != 1:
            raise Exception(f"No pair for input token or not paired with wbnb")

        for fee in pfees:
            paddr = self.get_token_pool(output_token, fee)
            if paddr != ADDRESS_ZERO:
                print(f"pool addr at: {paddr} {fee}")
                fees.append(fee)
                break
        if len(fees) != 2:
            raise Exception(f"No pair for output token or not paired with wbnb")            

        path = self._encode_path(tokens, fees)

        return self.build_and_send_tx(
            self.router.functions.exactInput(
                {
                    "path": path,
                    "recipient": self.wallet_address,
                    "deadline": int(time.time()) + 3600,
                    "amountIn": amount,
                    "amountOutMinimum": 0,
                }
            ),
            self.get_tx_params(),
        )


    def get_token_pool(self, 
                token_address :str,
                fee: int = 10000,
                ) -> str:
        token_address = Web3.to_checksum_address(token_address)
        wbnb_address = self.router.functions.WETH9().call()

        factory_address =  Web3.to_checksum_address(self.config["PancakeV3Factory"])
        factory_abi = pkgutil.get_data('membase.chain', 'solc/pancake_factory_v3.abi').decode()
        factory = self.w3.eth.contract(address=factory_address, abi=factory_abi)
        
        return factory.functions.getPool(token_address, wbnb_address, fee).call()

    def _encode_path(
        self,
        tokens: list[str],
        fees: list,
        exact_output: bool = False,
    ) -> bytes:
        """Encode the routing tokens to be suitable to use with Quoter and SwapRouter.

        For example if we would like to route the swap from token1 -> token3 through 2 pools:
        * pool1: token1/token2
        * pool2: token2/token3

        then encoded path would have this format: `token1 - pool1's fee - token2 - pool2's - token3`,
        in which each token address length is 20 bytes and fee length is 3 bytes

        `Read more <https://github.com/Uniswap/v3-periphery/blob/22a7ead071fff53f00d9ddc13434f285f4ed5c7d/contracts/libraries/Path.sol>`__.

        :param tokens: List of token addresses how to route the trade
        :param fees: List of trading fees of the pools in the route
        :param exact_output: Whether the encoded path be used for exactOutput quote or swap
        """
        assert len(fees) == len(tokens) - 1
        if exact_output:
            tokens.reverse()
            fees.reverse()

        encoded = b""
        for index, token in enumerate(tokens):
            encoded += bytes.fromhex(token[2:])
            if token != tokens[-1]:
                encoded += int.to_bytes(fees[index], 3, "big")

        return encoded

    def create_wallet(self):
        return _create_wallet(self.privy_app_id)