import datetime
import hashlib
import json
import time
import threading
from typing import Optional
import uuid

from web3 import Web3

from membase.chain.beeper import BeeperClient
from membase.memory.memory import Message
from membase.memory.multi_memory import MultiMemory


class TraderClient(BeeperClient):
    def __init__(self, config: dict, wallet_address: str, private_key: str, token_address: str, membase_id: Optional[str] = None):
        super().__init__(config, wallet_address, private_key)

        self.token_address = Web3.to_checksum_address(token_address)
        self.paired_token_address = self.get_wrapped_token()
        pool_address, fee = self.get_token_pool(token_address)
        if not pool_address:
            raise Exception(f"No pool for token {token_address}")
        self.pool_address = pool_address
        self.fee = fee
        if membase_id:
            self.membase_id = membase_id
        else:
            self.membase_id = "trader"

        self.local_id = uuid.uuid5(uuid.NAMESPACE_URL, self.wallet_address + self.token_address)
        self.memory = MultiMemory(
            membase_account=self.wallet_address,
            default_conversation_id=self.local_id,
            auto_upload_to_hub=True,
        )

        self.trade_prefix = f"tx_{self.local_id}"
        self.liquidity_prefix = f"liquidity_{self.local_id}"

        self.memory.load_from_hub(self.trade_prefix)
        self.memory.load_from_hub(self.liquidity_prefix)
        
        self.trade_memory = self.memory.get_memory(self.trade_prefix)
        self.liquidity_memory = self.memory.get_memory(self.liquidity_prefix)


        self.wallet_history = []

        self.init_info = self.get_wallet_info()
        self.token_info = self.get_token_info()
        self.get_liquidity_info()
        
        # Start monitoring in background
        self._monitor_thread = None
        self.start_monitoring()

    def __del__(self):
        """Clean up monitoring thread when object is destroyed"""
        if hasattr(self, '_monitor_thread') and self._monitor_thread is not None:
            self._monitor_thread = None

    def get_token_info(self):
        decimals = self.get_token_decimals(self.token_address)
        total_supply = self.get_token_supply(self.token_address)

        # todo: add holders
        return {
            "token_address": self.token_address,
            "token_decimals": decimals,
            "token_total_supply": total_supply,
            "native_token_decimals": 18,
            "native_token_name": "BNB",
            "swap_fee_tier": str(self.fee/10000) + "%",
            "transaction_fee": "~" + str(1_000_000_000_000_000) + " native token"
        }

    def get_liquidity_info(self):
        token_balance = self.get_balance(self.pool_address, self.token_address)
        paired_token_balance = self.get_balance(self.pool_address, self.paired_token_address)
        token_price = self.get_raw_price(self.token_address, self.paired_token_address, self.fee)

        # in liquidity pool
        liquidity_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "token_reserve": token_balance,
            "native_reserve": paired_token_balance,
            "token_price": token_price,
        }

        liquidity_memory = self.memory.get_memory(self.liquidity_prefix)
        res = liquidity_memory.get(recent_n=1)
        if len(res) > 0:
            info = json.loads(res[0].content)
            if info['token_reserve'] == token_balance and info['native_reserve'] == paired_token_balance and info['token_price'] == token_price:
                #print(f"duplicate liquidity info: {liquidity_info}")
                return
            
        msg = Message(
            name=self.membase_id,
            role="user",
            content=json.dumps(liquidity_info),
        )
        liquidity_memory.add(msg)

    def get_wallet_info(self):
        token_balance = self.get_balance(self.wallet_address, self.token_address)
        balance = self.get_balance(self.wallet_address, "")
        price = self.get_raw_price(self.token_address, self.paired_token_address, self.fee)
        token_value = token_balance * price
        total_value = token_value + balance

        wallet_info = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "native_balance": balance,
            "token_balance": token_balance,
            "total_value": total_value,
        }
        #check duplicate with previous one
        if len(self.wallet_history) > 0:
            if self.wallet_history[-1]['native_balance'] == balance and self.wallet_history[-1]['token_balance'] == token_balance and self.wallet_history[-1]['total_value'] == total_value:
                #print(f"duplicate wallet info: {wallet_info}")
                return

        self.wallet_history.append(wallet_info)

    def get_info(self, recent_n: int = 8):
        # token info
        token_info = {
            "desc": "Token information including its contract address, decimals, total supply, and fee for trading",
            "infos": self.token_info,
        }
        # user owned info
        wallet_infos = {
            "desc": "User wallet information including native balance, token balance, and total portfolio value (token_balance * token_price + native_balance). User can buy and sell tokens using balances in the wallet.",
            "infos": self.wallet_history[-recent_n:],
        }
        # liquidity pool info
        liquidity_infos = self.liquidity_memory.get(recent_n=recent_n)
        infos = []
        for info in liquidity_infos:
            content = json.loads(info.content)
            infos.append(content)

        liquidity_infos = {
            "pool desc": "A liquidity pool is a pairing of tokens in a smart contract that is used for swapping on decentralized exchanges (DEXs).",
            "desc": "Liquidity pool information including native reserve, token reserve, and token price.",
            "infos": infos,
        }

        infos = []
        trade_infos = self.trade_memory.get(recent_n=recent_n)
        for info in trade_infos:
            content = json.loads(info.content)
            infos.append(content)
        trade_infos = {
            "desc": "Trade history including type, tx_hash, gas_fee(cost of the transaction), token_delta(change of token balance), native_delta(change of native balance)",
            "infos": infos,
        }
        
        info = {
            "token_info": token_info,
            "wallet_infos": wallet_infos,
            "liquidity_infos": liquidity_infos,
            "trade_infos": trade_infos,
        }
        return info

    def buy(self, amount: int, reason: str = ""):
        before_balance = self.get_balance(self.wallet_address, self.token_address)
        before_native_balance = self.get_balance(self.wallet_address, "")

        try:
            tx = self.make_trade("", self.token_address, amount, self.fee)
            tx_receipt = self.get_tx_info(tx)
            gasfee = tx_receipt['gasUsed']*tx_receipt['effectiveGasPrice']

            after_balance = self.get_balance(self.wallet_address, self.token_address)
            while after_balance == before_balance:
                time.sleep(1)
                after_balance = self.get_balance(self.wallet_address, self.token_address)

            after_native_balance = self.get_balance(self.wallet_address, "")

            token_delta = after_balance - before_balance
            native_delta = after_native_balance + gasfee - before_native_balance
            native_delta_with_fee = native_delta - gasfee

            # trader's real price
            strike_price = native_delta / token_delta
            if strike_price < 0:
                strike_price = -strike_price
        
            trade_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "buy",
                "tx_hash": tx,
                "gas_fee": gasfee,
                "token_delta": token_delta,
                "native_delta_without_fee": native_delta,
                "native_delta": native_delta_with_fee,
                "strike_price": strike_price,
                "reason": reason,
            }
            msg = Message(
                name=self.membase_id,
                role="user",
                content=json.dumps(trade_info),
            )

            self.trade_memory.add(msg)
        except Exception as e:
            print(f"Error in buying: {str(e)}")
            trade_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "buy",
                "tx_status": str(e),
                "reason": reason,
            }
        return trade_info

    def sell(self, amount: int, reason: str = ""):
        before_balance = self.get_balance(self.wallet_address, self.token_address)
        before_native_balance = self.get_balance(self.wallet_address, "")

        try:
            tx = self.make_trade(self.token_address, "", amount, self.fee)
            tx_receipt = self.get_tx_info(tx)
            gasfee = tx_receipt['gasUsed']*tx_receipt['effectiveGasPrice']

            after_balance = self.get_balance(self.wallet_address, self.token_address)
            while after_balance == before_balance:
                time.sleep(1)
                after_balance = self.get_balance(self.wallet_address, self.token_address)

            after_native_balance = self.get_balance(self.wallet_address, "")

            token_delta = after_balance - before_balance
            native_delta = after_native_balance + gasfee - before_native_balance
            native_delta_with_fee = native_delta - gasfee

            # trader's real price
            strike_price = native_delta / token_delta
            if strike_price < 0:
                strike_price = -strike_price

            trade_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "sell",
                "tx_hash": tx,
                "gas_fee": gasfee,
                "token_delta": token_delta,
                "native_delta_without_fee": native_delta,
                "native_delta": native_delta_with_fee,
                "strike_price": strike_price,
                "reason": reason,
            }
            msg = Message(
                name=self.membase_id,
                role="user",
                content=json.dumps(trade_info),
            )
            self.trade_memory.add(msg)
        except Exception as e:
            print(f"Error in selling: {str(e)}")
            trade_info = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "sell",
                "tx_status": str(e),
                "reason": reason,
            }
        return trade_info
    
    def start_monitoring(self, interval: int = 60):
        """
        Start a background process to monitor wallet and liquidity info every minute
        Args:
            interval: Time interval in seconds between each check (default: 60 seconds)
        """
        def _periodic_monitor():
            while True:
                try:
                    self.get_wallet_info()
                    self.get_liquidity_info()
                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in monitoring: {str(e)}")
                    time.sleep(interval)  # Continue monitoring even if there's an error

        self._monitor_thread = threading.Thread(target=_periodic_monitor, daemon=True)
        self._monitor_thread.start()
        return self._monitor_thread
