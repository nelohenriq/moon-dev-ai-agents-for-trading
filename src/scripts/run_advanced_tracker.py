from src.agents.advanced_wallet_tracker import AdvancedWalletTracker
import asyncio
from termcolor import cprint

WHALE_WALLETS = [
    '888DUdR3P4fYa4Es5AVvJhoqwQGhFV56NotdHt2gz3e1',
    '8MeAg93NcLXJAhhUfdVoDaShRXFLey8vKof2ph7w6M9E',
    'GnjUARqXzrCecVG6fwZ3bc322TZN435tR8Erjz4oKDM7'
    # Add more whale wallets here
]

async def main():
    tracker = AdvancedWalletTracker(
        target_wallets=WHALE_WALLETS,
        min_usd_value=1000  # Track trades worth $1000+
    )
    
    while True:
        try:
            await tracker.track_and_notify()
            await asyncio.sleep(15)  # Check every 15 seconds
        except Exception as e:
            cprint(f"🚨 Error: {str(e)}", "red")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
