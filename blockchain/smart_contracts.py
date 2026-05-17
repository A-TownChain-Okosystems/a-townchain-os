# blockchain/smart_contracts.py
# ATC Smart Contract Layer

class ATCToken:
    def __init__(self):
        self.balances = {}
        self.total_supply = 1_000_000
    
    def transfer(self, sender, receiver, amount):
        if self.balances.get(sender, 0) >= amount:
            self.balances[sender] -= amount
            self.balances[receiver] = self.balances.get(receiver, 0) + amount
            return True
        return False
