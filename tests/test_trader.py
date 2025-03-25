from web3 import Web3

from membase.chain.trader import TraderClient


BNB_CHAIN_SETTINGS = {
    "RPC": "https://bsc-testnet-rpc.publicnode.com",
    "ChainId": 97,
    "PancakeV3Factory": "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
    "PancakeV3SwapRouter": "0x1b81D678ffb9C0263b24A97847620C99d213eB14",
    "PancakeV3PoolDeployer": "0x41ff9AA7e16B8B1a8a8dc4f0eFacd93D02d071c9",
    "PancakeV3Quoter": "0xbC203d7f83677c7ed3F7acEc959963E7F4ECC5C2",
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


def test_trade():
    to = Web3.to_checksum_address("0x2e6b3f12408d5441e56c3C20848A57fd53a78931")
    bp = TraderClient(BNB_CHAIN_SETTINGS, deployer, deployprivkey, to)
    amount = 2306184959924
    bp.buy(amount)
    bp.sell(amount/2)

    bp.get_liquidity_info()
    bp.get_wallet_info()
    # format info
    print(bp.get_info())

test_trade()