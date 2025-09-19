"""
Main application controller for bank statement processing.

This module orchestrates the entire processing pipeline:
PDF extraction -> AI analysis -> Data validation -> CSV storage
"""

import os
import sys
import warnings
from pathlib import Path
from dotenv import load_dotenv
from typing import List

# Suppress urllib3 OpenSSL warning
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+.*")

from src.pdf_parser import extract_text_from_pdf, validate_pdf_file
from src.llm_extractor import extract_data_with_llm, test_api_connection
from src.data_processor import (
    get_existing_hashes,
    convert_statement_to_records,
    append_to_csv,
    get_csv_summary,
    validate_csv_structure
)


def setup_environment() -> str:
    """
    Load environment variables and validate API key.

    Returns:
        str: Google API key

    Raises:
        ValueError: If API key is not found or invalid
    """
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in .env file. "
            "Please create a .env file with your Google API key."
        )

    # Test API connection
    print("Testing API connection...")
    if not test_api_connection(api_key):
        raise ValueError("Invalid Google API key or connection failed")

    print("✓ API connection successful")
    return api_key


def get_pdf_files(directory: str) -> List[str]:
    """
    Get list of PDF files in the specified directory.

    Args:
        directory: Directory to scan for PDF files

    Returns:
        List[str]: List of PDF file paths
    """
    pdf_directory = Path(directory)

    if not pdf_directory.exists():
        print(f"Creating directory: {pdf_directory}")
        pdf_directory.mkdir(parents=True, exist_ok=True)
        return []

    pdf_files = []
    for file_path in pdf_directory.glob("*.pdf"):
        if validate_pdf_file(str(file_path)):
            pdf_files.append(str(file_path))
        else:
            print(f"⚠️  Skipping invalid PDF: {file_path.name}")

    return sorted(pdf_files)


def process_single_pdf(pdf_path: str, api_key: str) -> dict:
    """
    Process a single PDF file and extract bank statement data.

    Args:
        pdf_path: Path to PDF file
        api_key: Google API key

    Returns:
        dict: Processing result with status and data/error info
    """
    filename = os.path.basename(pdf_path)
    print(f"\n📄 Processing: {filename}")

    try:
        # Extract text from PDF
        print("  Extracting text...")
        raw_text = extract_text_from_pdf(pdf_path)

        if not raw_text or len(raw_text.strip()) < 50:
            return {
                "status": "error",
                "filename": filename,
                "error": "Insufficient text extracted from PDF"
            }

        print(f"  Extracted {len(raw_text)} characters")

        # Process with AI
        print("  Processing with AI...")
        statement_data = extract_data_with_llm(raw_text, api_key)

        print(f"  ✓ Extracted {len(statement_data.transactions)} transactions")
        print(f"    Account: {statement_data.account_holder_name}")
        print(f"    Bank: {statement_data.bank_name}")
        print(f"    Period: {statement_data.statement_period}")

        return {
            "status": "success",
            "filename": filename,
            "statement": statement_data
        }

    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        print(f"  ❌ {error_msg}")
        return {
            "status": "error",
            "filename": filename,
            "error": error_msg
        }


def main():
    """
    Main application entry point.
    """
    print("🏦 Bank Statement Processor")
    print("=" * 50)

    try:
        # Setup environment and API
        api_key = setup_environment()

        # Configuration
        pdf_directory = "data"
        output_csv = "output/comprehensive_data.csv"

        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)

        # Validate CSV structure
        if not validate_csv_structure(output_csv):
            print("⚠️  Existing CSV has invalid structure. Creating backup...")
            backup_path = f"{output_csv}.backup"
            if os.path.exists(output_csv):
                os.rename(output_csv, backup_path)

        # Get existing transactions
        existing_hashes = get_existing_hashes(output_csv)
        print(f"\n📊 Found {len(existing_hashes)} existing transactions in database")

        # Get PDF files to process
        pdf_files = get_pdf_files(pdf_directory)

        if not pdf_files:
            print(f"\n📂 No PDF files found in '{pdf_directory}' directory")
            print("Please add PDF bank statements to process.")
            return

        print(f"\n🔍 Found {len(pdf_files)} PDF files to process")

        # Process each PDF file
        all_new_records = []
        successful_files = 0
        failed_files = []

        for pdf_path in pdf_files:
            result = process_single_pdf(pdf_path, api_key)

            if result["status"] == "success":
                # Convert to CSV records
                new_records = convert_statement_to_records(
                    result["statement"],
                    result["filename"],
                    existing_hashes
                )

                all_new_records.extend(new_records)
                successful_files += 1

                if new_records:
                    print(f"  ➕ {len(new_records)} new transactions")
                else:
                    print("  ℹ️  No new transactions (all duplicates)")

            else:
                failed_files.append(f"{result['filename']}: {result['error']}")

        # Save new records to CSV
        if all_new_records:
            print(f"\n💾 Saving {len(all_new_records)} new transactions to CSV...")
            append_to_csv(all_new_records, output_csv)
            print(f"✓ Data saved to: {output_csv}")
        else:
            print("\n💾 No new transactions to save")

        # Print summary
        print("\n" + "=" * 50)
        print("📈 PROCESSING SUMMARY")
        print("=" * 50)
        print(f"Files processed successfully: {successful_files}/{len(pdf_files)}")
        print(f"New transactions added: {len(all_new_records)}")

        if failed_files:
            print(f"\n❌ Failed files ({len(failed_files)}):")
            for error in failed_files:
                print(f"  • {error}")

        # CSV summary
        summary = get_csv_summary(output_csv)
        if "error" not in summary:
            print(f"\n📊 DATABASE SUMMARY:")
            print(f"  Total transactions: {summary['total_transactions']}")
            print(f"  Unique accounts: {summary['unique_accounts']}")
            print(f"  Banks: {', '.join(summary['banks'])}")
            if summary['date_range']['earliest']:
                print(f"  Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")

        print(f"\n🎯 Ready for import to Google Sheets: {output_csv}")

    except KeyboardInterrupt:
        print("\n\n⏹️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()