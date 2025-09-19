"""
Data schemas for bank statement processing.

This module defines the Pydantic models that ensure all extracted data
is properly validated and structured.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Transaction(BaseModel):
    """Represents a single bank transaction."""
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    description: str = Field(..., description="Transaction description")
    debit: Optional[float] = Field(None, description="Debit amount if applicable")
    credit: Optional[float] = Field(None, description="Credit amount if applicable")
    balance: Optional[float] = Field(None, description="Account balance after transaction")
    reference: Optional[str] = Field(None, description="Transaction reference number")


class BankStatement(BaseModel):
    """Represents a complete bank statement with metadata and transactions."""
    account_holder_name: str = Field(..., description="Name of account holder")
    bank_name: str = Field(..., description="Name of the bank")
    account_number: str = Field(..., description="Account number")
    sort_code: str = Field(..., description="Bank sort code")
    statement_period: str = Field(..., description="Statement period (e.g., 'Jan 2024')")
    transactions: List[Transaction] = Field(..., description="List of transactions")