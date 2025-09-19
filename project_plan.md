Project: Intelligent Statement Processing Pipeline
Objective: To create a Python application that automatically extracts, structures, and stores transaction data from PDF bank statements from various banks into a single, de-normalized CSV file.

Lead Architect: Mahmudul Hoque

Milestone 0: Project Setup & Configuration
Goal: Prepare a clean, organized, and reproducible development environment.

Tasks:

Create the Project Directory Structure:

statement-processor/
├── data/                # Input PDFs will go here
├── output/              # The final CSV will be saved here
├── src/                 # All our Python source code
│   ├── __init__.py
│   ├── pdf_parser.py
│   ├── schemas.py
│   ├── llm_extractor.py
│   ├── data_processor.py
│   └── main.py
├── tests/               # For future unit tests
├── .env                 # To store API keys securely
├── .gitignore           # To exclude unnecessary files
└── requirements.txt     # To manage project dependencies
Set Up the Python Environment:

From the statement-processor directory, run:

Bash

python3 -m venv venv
source venv/bin/activate
Create the requirements.txt file:

Add the following dependencies to the file:

pandas
PyMuPDF
google-generativeai
pydantic
python-dotenv
Install them by running: pip install -r requirements.txt

Create the .env file:

This file will store your secret API key. Add the following line:

GOOGLE_API_KEY="YOUR_API_KEY_HERE"
Milestone 1: Define the Data Schema
Goal: Create a rigid data structure using Pydantic. This ensures all data we process is clean and validated.

File: src/schemas.py

Tasks:

Implement the Pydantic Models:

This code defines the shape of our final JSON output.

Python

from pydantic import BaseModel, Field
from typing import List, Optional

class Transaction(BaseModel):
    date: str
    description: str
    debit: Optional[float] = None
    credit: Optional[float] = None
    balance: float
    reference: Optional[str] = None

class BankStatement(BaseModel):
    account_holder_name: str
    bank_name: str
    account_number: str
    sort_code: str
    statement_period: str
    transactions: List[Transaction]
Milestone 2: Core PDF Text Extraction
Goal: Create a reliable function to extract all raw text from a PDF file.

File: src/pdf_parser.py

Tasks:

Implement the extract_text_from_pdf function:

This module will use PyMuPDF (fitz) as it's highly effective for digital PDFs.

Python

import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts all text from a given PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""
Milestone 3: AI-Powered Information Extraction
Goal: Implement the logic to communicate with the LLM and parse its response into our Pydantic schema.

File: src/llm_extractor.py

Tasks:

Implement the Prompt Builder and Extractor Function:

This is the core AI logic of the application.

Python

import google.generativeai as genai
import json
from src.schemas import BankStatement

def build_prompt(text: str) -> str:
    """Builds the prompt for the LLM with the provided text."""
    # The detailed prompt from our previous discussion goes here
    return f"""
    You are an expert financial data extraction assistant... (rest of prompt) ...

    Here is the bank statement text to process:
    ---
    {text}
    ---
    """

def extract_data_with_llm(text: str, api_key: str) -> BankStatement:
    """Sends text to the LLM and parses the response into a BankStatement object."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    prompt = build_prompt(text)
    response = model.generate_content(prompt)

    # Clean up the response to get pure JSON
    json_response = response.text.strip().replace("```json", "").replace("```", "")

    try:
        data = json.loads(json_response)
        return BankStatement(**data)
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Failed to parse LLM response: {e}")
        raise
Milestone 4: Data Processing and Storage
Goal: Implement hashing for deduplication and the logic for writing data to our master CSV file.

File: src/data_processor.py

Tasks:

Implement Hashing, Deduplication, and CSV Writing:

Python

import pandas as pd
import hashlib
from typing import List, Set
from src.schemas import Transaction, BankStatement

def create_transaction_hash(account_number: str, transaction: Transaction) -> str:
    """Creates a stable SHA-256 hash for a transaction."""
    hash_string = (
        f"{account_number}-{transaction.date}-{transaction.description.lower().strip()}-"
        f"{transaction.debit}-{transaction.credit}-{transaction.balance}"
    )
    return hashlib.sha256(hash_string.encode()).hexdigest()

def get_existing_hashes(csv_path: str) -> Set[str]:
    """Reads a CSV and returns a set of all existing transaction hashes."""
    try:
        df = pd.read_csv(csv_path)
        return set(df['transaction_hash'])
    except FileNotFoundError:
        return set()

def append_to_csv(records: List[dict], csv_path: str):
    """Appends a list of new records to the CSV file."""
    df = pd.DataFrame(records)
    is_new_file = not pd.io.common.file_exists(csv_path)
    df.to_csv(csv_path, mode='a', header=is_new_file, index=False)
Milestone 5: Main Controller
Goal: Create the main entry point that ties all the modules together into a runnable application.

File: src/main.py

Tasks:

Implement the Main Orchestration Logic:

Python

import os
from dotenv import load_dotenv
from src.pdf_parser import extract_text_from_pdf
from src.llm_extractor import extract_data_with_llm
from src.data_processor import (
    create_transaction_hash,
    get_existing_hashes,
    append_to_csv,
)

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")

    pdf_directory = "data"
    output_csv = "output/comprehensive_data.csv"

    existing_hashes = get_existing_hashes(output_csv)
    print(f"Found {len(existing_hashes)} existing transactions.")

    new_records = []
    for filename in os.listdir(pdf_directory):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_directory, filename)
            print(f"Processing {pdf_path}...")

            raw_text = extract_text_from_pdf(pdf_path)
            if not raw_text:
                continue

            try:
                statement_data = extract_data_with_llm(raw_text, api_key)
            except Exception as e:
                print(f"  Skipping file due to LLM extraction error: {e}")
                continue

            for tx in statement_data.transactions:
                tx_hash = create_transaction_hash(statement_data.account_number, tx)
                if tx_hash not in existing_hashes:
                    new_records.append({
                        'transaction_hash': tx_hash,
                        'source_file': filename,
                        'account_holder': statement_data.account_holder_name,
                        'bank_name': statement_data.bank_name,
                        'account_no': statement_data.account_number,
                        'sort_code': statement_data.sort_code,
                        'transaction_date': tx.date,
                        'description': tx.description,
                        'debit': tx.debit,
                        'credit': tx.credit,
                        'balance': tx.balance,
                        'reference': tx.reference,
                    })
                    existing_hashes.add(tx_hash)

    if new_records:
        append_to_csv(new_records, output_csv)
        print(f"Successfully added {len(new_records)} new transactions.")
    else:
        print("No new transactions to add.")

if __name__ == "__main__":
    main()
Next 3 Steps: Project Kickoff
Review the Plan: Read through this entire document to ensure you understand all the steps and how the modules connect.

Execute Milestone 0: Create the full directory structure and set up your environment by running the pip install -r requirements.txt command.

Begin Milestone 1: Start coding the schemas.py file. Getting the data structures right is the most important first step.