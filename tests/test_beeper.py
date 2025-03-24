import json
from membase.chain.beeper import BeeperClient
from web3 import Web3
from web3.constants import ADDRESS_ZERO

import os

NATIVE_TOKEN = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'

BNB_CHAIN_SETTINGS = {
    "RPC": "https://bsc-testnet-rpc.publicnode.com",
    "ChainId": 97,
    "PancakeV3Factory": "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
    "PancakeV3SwapRouter": "0x1b81D678ffb9C0263b24A97847620C99d213eB14",
    "PancakeV3PoolDeployer": "0x41ff9AA7e16B8B1a8a8dc4f0eFacd93D02d071c9",
    "PostionManage" : "0x427bF5b37357632377eCbEC9de3626C71A5396c1",
    "Beeper" : "0x1CbcD3d13C9d73a2bD40D6737294ccd21D1607c1",
    "BeeperUtil" : "0x04ad17C42D38fe20d754D8b32C2aA01d02c7b32F",
}

deployer = Web3.to_checksum_address("0x1D8534E663F27AB422E50F532CA3193b7ac6e996")
with open("./out/0x1D8534E663F27AB422E50F532CA3193b7ac6e996") as d:
    deployprivkey = d.readline()

BEEPER_TOKEN =  Web3.to_checksum_address('0x238950013FA29A3575EB7a3D99C00304047a77b5')


wallet = "0x373C8E4947Ed9F939E5D25615607f11D5CcCe136"
with open("./out/0x373C8E4947Ed9F939E5D25615607f11D5CcCe136") as d:
    privkey = d.readline()


app_id = "cm5lt8cxs022d4bbclcvh1kn8"
bp = BeeperClient(BNB_CHAIN_SETTINGS, wallet, privkey) 

twitter_id = 11945844
twitter_account = "0x373C8E4947Ed9F939E5D25615607f11D5CcCe136"
wbnb = Web3.to_checksum_address("0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd")
received = Web3.to_checksum_address("0x1D8534E663F27AB422E50F532CA3193b7ac6e996")

#bp.deploy(wallet, privkey)
#bp.set_admin(wallet, privkey, deployer)
#to = bp.deploy_token(deployer, deployprivkey, twitter_account, twitter_id)
tin = Web3.to_checksum_address("0x4c51bA950B2D3F8d75e82a6B9c878d9573aCBF66")
to = Web3.to_checksum_address("0x8ED141836ea27Df805c17024c4e0f48F587d2448")

#wallet_id = "ipi97ecw4m7igwsev9ps2445"
#wallet_address = "0xaA4E39fb1AFd4df87D19BC16FA0819336fB8e5c0"
#wallet_id = deployprivkey
#wallet_address = deployer

#txn = bp.transfer_asset(wallet_address, wallet_id, deployer, "", 300000)
#print(f"{txn}")

#beeper_token = "0x238950013FA29A3575EB7a3D99C00304047a77b5"

#usdt_token = "0xd308dd50e00dafe6a6a77dd7c3e79c17f37de1ee"

to = Web3.to_checksum_address("0x2e6b3f12408d5441e56c3C20848A57fd53a78931")

def test_swap_token():    
    #dbp = BeeperClient(BNB_CHAIN_SETTINGS, deployer, deployprivkey)
    #tx, to, supply = dbp.deploy_token(twitter_account, twitter_id)
    #print(f"deployed token: {to}")   

    paddr = bp.get_token_pool(to, 10000)
    print(f"pool addr: {paddr}")

    # token->token
    bp.make_trade("", to, 2306184959924)

   
    # token-> bnb 
    amount = bp.get_balance(wallet, to)
    print(f"has balance: {amount}")
    bp.make_trade(to, "", int(amount/10)) 
    # wbnb -> token 
    bp.make_trade(wbnb, to, 400000)
    # token -> wbnb 
    bp.make_trade(to, wbnb, int(amount/10)) 

def test_transfer():

    # transfer bnb
    print(f"==== transfer bnb")
    val = bp.get_balance(received, "")
    print(f"before {val}")
    bp.transfer_asset(received, "", 1000)
    val = bp.get_balance(received, "")
    print(f"{val}")

    # transfer token
    print(f"==== transfer token")
    val = bp.get_balance(received, to)
    print(f"before {val}")
    bp.transfer_asset(received, to, 2000)
    val = bp.get_balance(received, to)
    print(f"{val}")


    # claim reward
    print(f"==== claim reward")
    val = bp.get_balance(wallet, to)
    print(f"before {val}")
    bp.claim_reward(to)
    val = bp.get_balance(wallet, to) 
    print(f"{val}")

try:
    #test_swap_token()
    test_transfer()
except Exception as e:
    print(e)