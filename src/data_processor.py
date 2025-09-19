"""
Data processing and CSV management module.

This module handles transaction deduplication, hashing, and CSV file operations
for persistent storage of bank statement data.
"""

import pandas as pd
import hashlib
import os
from typing import List, Set, Dict, Any
from src.schemas import Transaction, BankStatement


def create_transaction_hash(account_number: str, transaction: Transaction) -> str:
    """
    Create a stable SHA-256 hash for transaction deduplication.

    Args:
        account_number: Account number for the transaction
        transaction: Transaction object to hash

    Returns:
        str: SHA-256 hash string for the transaction
    """
    # Normalize description for consistent hashing
    normalized_description = transaction.description.lower().strip()

    # Create hash string with all identifying information
    # Handle None values for balance
    balance_str = str(transaction.balance) if transaction.balance is not None else "0.0"

    hash_string = (
        f"{account_number}-{transaction.date}-{normalized_description}-"
        f"{transaction.debit}-{transaction.credit}-{balance_str}"
    )

    # Include reference if available
    if transaction.reference:
        hash_string += f"-{transaction.reference}"

    return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()


def get_existing_hashes(csv_path: str) -> Set[str]:
    """
    Read existing transaction hashes from CSV file.

    Args:
        csv_path: Path to the CSV file

    Returns:
        Set[str]: Set of existing transaction hashes
    """
    try:
        if not os.path.exists(csv_path):
            return set()

        df = pd.read_csv(csv_path)
        if 'transaction_hash' in df.columns:
            return set(df['transaction_hash'].astype(str))
        else:
            return set()

    except (FileNotFoundError, pd.errors.EmptyDataError):
        return set()
    except Exception as e:
        print(f"Warning: Error reading existing CSV file: {e}")
        return set()


def append_to_csv(records: List[Dict[str, Any]], csv_path: str) -> None:
    """
    Append new transaction records to CSV file.

    Args:
        records: List of transaction dictionaries to append
        csv_path: Path to the CSV file

    Raises:
        Exception: If unable to write to CSV file
    """
    if not records:
        return

    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        # Create DataFrame from records
        df = pd.DataFrame(records)

        # Check if file exists and has content
        file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0

        # Write to CSV
        df.to_csv(csv_path, mode='a', header=not file_exists, index=False)

        print(f"Successfully appended {len(records)} records to {csv_path}")

    except Exception as e:
        print(f"Error writing to CSV file {csv_path}: {e}")
        raise


def convert_statement_to_records(
    statement: BankStatement,
    source_filename: str,
    existing_hashes: Set[str]
) -> List[Dict[str, Any]]:
    """
    Convert BankStatement to CSV records, filtering out duplicates.

    Args:
        statement: BankStatement object to convert
        source_filename: Name of source PDF file
        existing_hashes: Set of existing transaction hashes

    Returns:
        List[Dict]: List of new transaction records ready for CSV
    """
    new_records = []

    for transaction in statement.transactions:
        # Create hash for this transaction
        tx_hash = create_transaction_hash(statement.account_number, transaction)

        # Skip if already exists
        if tx_hash in existing_hashes:
            continue

        # Create record dictionary
        record = {
            'transaction_hash': tx_hash,
            'source_file': source_filename,
            'account_holder': statement.account_holder_name,
            'bank_name': statement.bank_name,
            'account_number': statement.account_number,
            'sort_code': statement.sort_code,
            'statement_period': statement.statement_period,
            'transaction_date': transaction.date,
            'description': transaction.description,
            'debit': transaction.debit,
            'credit': transaction.credit,
            'balance': transaction.balance,
            'reference': transaction.reference,
        }

        new_records.append(record)
        existing_hashes.add(tx_hash)  # Update set to prevent duplicates within same batch

    return new_records


def validate_csv_structure(csv_path: str) -> bool:
    """
    Validate that CSV file has the expected column structure.

    Args:
        csv_path: Path to CSV file to validate

    Returns:
        bool: True if structure is valid, False otherwise
    """
    expected_columns = {
        'transaction_hash', 'source_file', 'account_holder', 'bank_name',
        'account_number', 'sort_code', 'statement_period', 'transaction_date',
        'description', 'debit', 'credit', 'balance', 'reference'
    }

    try:
        if not os.path.exists(csv_path):
            return True  # New file is okay

        df = pd.read_csv(csv_path, nrows=0)  # Read only headers
        actual_columns = set(df.columns)

        return expected_columns.issubset(actual_columns)

    except Exception:
        return False


def get_csv_summary(csv_path: str) -> Dict[str, Any]:
    """
    Get summary statistics from the CSV file.

    Args:
        csv_path: Path to CSV file

    Returns:
        Dict: Summary statistics
    """
    try:
        if not os.path.exists(csv_path):
            return {"total_transactions": 0, "unique_accounts": 0, "banks": []}

        df = pd.read_csv(csv_path)

        summary = {
            "total_transactions": len(df),
            "unique_accounts": df['account_number'].nunique() if 'account_number' in df.columns else 0,
            "banks": df['bank_name'].unique().tolist() if 'bank_name' in df.columns else [],
            "date_range": {
                "earliest": df['transaction_date'].min() if 'transaction_date' in df.columns else None,
                "latest": df['transaction_date'].max() if 'transaction_date' in df.columns else None
            }
        }

        return summary

    except Exception as e:
        print(f"Error generating CSV summary: {e}")
        return {"error": str(e)}