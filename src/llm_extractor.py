"""
AI-powered data extraction module.

This module handles communication with Google Gemini AI to extract
structured bank statement data from raw text.
"""

from google import genai
import json
import re
from typing import Optional
from src.schemas import BankStatement


def build_prompt(text: str) -> str:
    """
    Build a detailed prompt for the LLM to extract bank statement data.

    Args:
        text: Raw text extracted from PDF

    Returns:
        str: Formatted prompt for the AI model
    """
    return f"""You are an expert financial data extraction assistant. Your task is to extract structured information from bank statement text and return it as valid JSON.

CRITICAL REQUIREMENTS:
1. Extract ALL transactions found in the statement
2. Use YYYY-MM-DD format for all dates
3. For amounts: use positive numbers for both debits and credits
4. Include reference numbers when available
5. Return ONLY valid JSON, no markdown formatting

JSON STRUCTURE REQUIRED:
{{
    "account_holder_name": "Full name of account holder",
    "bank_name": "Bank name (e.g., HSBC, Barclays, Santander)",
    "account_number": "Account number",
    "sort_code": "Sort code (XX-XX-XX format)",
    "statement_period": "Statement period (e.g., 'January 2024')",
    "transactions": [
        {{
            "date": "YYYY-MM-DD",
            "description": "Transaction description",
            "debit": 123.45 or null,
            "credit": 67.89 or null,
            "balance": 1234.56,
            "reference": "Reference number or null"
        }}
    ]
}}

IMPORTANT NOTES:
- If amount is a debit/withdrawal, put value in "debit" field and null in "credit"
- If amount is a credit/deposit, put value in "credit" field and null in "debit"
- Balance should always be the running balance after the transaction
- Extract reference numbers when visible (sometimes called "Reference", "Ref", or similar)
- For descriptions, clean up but keep essential information
- If you cannot determine a field clearly, use reasonable defaults or null

Here is the bank statement text to process:
---
{text}
---

Return only the JSON response:"""


def extract_data_with_llm(text: str, api_key: str) -> BankStatement:
    """
    Send text to the LLM and parse response into BankStatement object.

    Args:
        text: Raw text from PDF
        api_key: Google API key for Gemini

    Returns:
        BankStatement: Validated bank statement data

    Raises:
        ValueError: If API key is invalid
        json.JSONDecodeError: If LLM response is not valid JSON
        Exception: If data validation fails
    """
    if not api_key:
        raise ValueError("Google API key is required")

    # Configure the API with new SDK
    client = genai.Client(api_key=api_key)

    # Build and send prompt
    prompt = build_prompt(text)

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )

        if not response.text:
            raise Exception("Empty response from AI model")

        # Clean up the response to extract JSON
        json_text = _clean_json_response(response.text)

        # Parse JSON
        data = json.loads(json_text)

        # Validate and return as BankStatement
        return BankStatement(**data)

    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response as JSON: {e}")
        print(f"Raw response: {response.text[:500]}...")
        raise
    except Exception as e:
        print(f"Error during AI extraction: {e}")
        raise


def _clean_json_response(response_text: str) -> str:
    """
    Clean AI response to extract pure JSON.

    Args:
        response_text: Raw response from AI model

    Returns:
        str: Cleaned JSON string
    """
    # Remove markdown code blocks
    text = response_text.strip()
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    # Find JSON boundaries
    start_idx = text.find('{')
    end_idx = text.rfind('}')

    if start_idx == -1 or end_idx == -1:
        raise ValueError("No valid JSON found in response")

    return text[start_idx:end_idx + 1]


def test_api_connection(api_key: str) -> bool:
    """
    Test if the API key works with a simple request.

    Args:
        api_key: Google API key to test

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents="Say 'API connection successful'"
        )
        return "successful" in response.text.lower()
    except Exception:
        return False