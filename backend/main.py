from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker


# =========================
# DATABASE
# =========================

DATABASE_URL = "sqlite:///./payrecover.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    customer = Column(String)
    amount = Column(Float)
    status = Column(String)
    reason = Column(String)


Base.metadata.create_all(bind=engine)


# =========================
# FASTAPI
# =========================

app = FastAPI()


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# HOME
# =========================

@app.get("/")
def home():
    return {
        "message": "PayRecover AI is running"
    }


# =========================
# PAYMENT MODEL
# =========================


class Payment(BaseModel):
    transaction_id: str = Field(..., min_length=1, max_length=100)
    customer: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    status: Literal["failed", "recovered"]
    reason: str = Field(..., min_length=1, max_length=100)


# =========================
# ADD PAYMENT
# =========================

@app.post("/payment")
def create_payment(payment: Payment):

    db = SessionLocal()

    try:
        # Check if transaction already exists
        existing_payment = (
            db.query(Transaction)
            .filter(
                Transaction.transaction_id == payment.transaction_id
            )
            .first()
        )

        if existing_payment:
            raise HTTPException(
                status_code=400,
                detail="Transaction already exists"
            )

        transaction = Transaction(
            transaction_id=payment.transaction_id,
            customer=payment.customer,
            amount=payment.amount,
            status=payment.status,
            reason=payment.reason
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return {
            "message": "Payment saved successfully",
            "transaction_id": transaction.transaction_id
        }

    finally:
        db.close()


# =========================
# GET ALL PAYMENTS
# =========================

@app.get("/payments")
def get_payments():

    db = SessionLocal()

    try:
        transactions = db.query(Transaction).all()

        result = []

        for transaction in transactions:
            result.append({
                "transaction_id": transaction.transaction_id,
                "customer": transaction.customer,
                "amount": transaction.amount,
                "status": transaction.status,
                "reason": transaction.reason
            })

        return result

    finally:
        db.close()


# =========================
# AI PAYMENT ANALYSIS
# =========================

@app.post("/analyze-payment")
def analyze_payment(payment: Payment):

    if payment.reason == "insufficient_balance":

        recommendation = (
            "Ask customer to add sufficient balance and retry."
        )

        priority = "high"

        customer_message = (
            f"Hi {payment.customer}, your payment of "
            f"₹{payment.amount:.0f} could not be completed because "
            "of insufficient balance. Please add sufficient balance "
            "and try again."
        )

    elif payment.reason == "bank_timeout":

        recommendation = (
            "Ask customer to retry the payment after a short time."
        )

        priority = "medium"

        customer_message = (
            f"Hi {payment.customer}, your payment of "
            f"₹{payment.amount:.0f} could not be completed because "
            "of a temporary bank issue. Please try again after "
            "a short time."
        )

    elif payment.reason == "card_declined":

        recommendation = (
            "Ask customer to try another card or payment method."
        )

        priority = "high"

        customer_message = (
            f"Hi {payment.customer}, your payment of "
            f"₹{payment.amount:.0f} was declined by your card. "
            "Please try another card or payment method."
        )

    elif payment.reason == "network_error":

        recommendation = (
            "Ask customer to retry the payment."
        )

        priority = "low"

        customer_message = (
            f"Hi {payment.customer}, your payment of "
            f"₹{payment.amount:.0f} could not be completed because "
            "of a network issue. Please try again."
        )

    else:

        recommendation = (
            "Review the payment manually."
        )

        priority = "low"

        customer_message = (
            f"Hi {payment.customer}, we could not complete your "
            f"payment of ₹{payment.amount:.0f}. Please try again "
            "or contact support."
        )

    return {
        "transaction_id": payment.transaction_id,
        "status": payment.status,
        "recommendation": recommendation,
        "priority": priority,
        "customer_message": customer_message
    }


# =========================
# RECOVER PAYMENT
# =========================

@app.put("/payments/{transaction_id}/recover")
def recover_payment(transaction_id: str):

    db = SessionLocal()

    try:

        payment = (
            db.query(Transaction)
            .filter(
                Transaction.transaction_id == transaction_id
            )
            .first()
        )

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail="Payment not found"
            )

        if payment.status == "recovered":
            return {
                "message": "Payment is already recovered",
                "transaction_id": payment.transaction_id,
                "status": payment.status
            }

        payment.status = "recovered"

        db.commit()
        db.refresh(payment)

        return {
            "message": "Payment recovered successfully",
            "transaction_id": payment.transaction_id,
            "status": payment.status
        }

    finally:
        db.close()

# =========================
# DELETE PAYMENT
# =========================

@app.delete("/payments/{transaction_id}")
def delete_payment(transaction_id: str):

    db = SessionLocal()

    try:
        payment = (
            db.query(Transaction)
            .filter(
                Transaction.transaction_id == transaction_id
            )
            .first()
        )

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail="Payment not found"
            )

        db.delete(payment)
        db.commit()

        return {
            "message": "Payment deleted successfully",
            "transaction_id": transaction_id
        }

    finally:
        db.close()