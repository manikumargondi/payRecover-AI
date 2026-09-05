from main import SessionLocal, Transaction

db = SessionLocal()

transactions = [
    Transaction(
        transaction_id="TXN2001",
        customer="Mani",
        amount=1500,
        status="failed",
        reason="insufficient_balance"
    ),
    Transaction(
        transaction_id="TXN2002",
        customer="Rahul",
        amount=2499,
        status="failed",
        reason="card_declined"
    ),
    Transaction(
        transaction_id="TXN2003",
        customer="Priya",
        amount=800,
        status="failed",
        reason="network_error"
    )
]

db.add_all(transactions)
db.commit()

print("3 transactions added successfully!")

print(db.query(Transaction).all())

db.close()