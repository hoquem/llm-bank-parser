# Bank Statement Processor

Intelligent PDF bank statement processing pipeline that extracts transaction data and creates a comprehensive CSV file for Google Sheets import.

## Features

- ✅ Processes PDF bank statements from any bank
- ✅ AI-powered data extraction using Google Gemini
- ✅ Automatic duplicate detection and prevention
- ✅ Comprehensive transaction data including references
- ✅ Ready-to-import CSV format for Google Sheets
- ✅ Batch processing of multiple statements

## Quick Start

1. **Setup Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API Key**
   ```bash
   cp .env.template .env
   # Edit .env and add your Google API key
   ```

3. **Add PDF Statements**
   ```bash
   # Place your PDF bank statements in the data/ folder
   cp your_statements.pdf data/
   ```

4. **Run Processing**
   ```bash
   python -m src.main
   ```

5. **Import to Google Sheets**
   - Open Google Sheets
   - File → Import → Upload → Select `output/comprehensive_data.csv`

## Output Format

The CSV file contains these columns:
- `transaction_hash` - Unique identifier for deduplication
- `source_file` - Original PDF filename
- `account_holder` - Account holder name
- `bank_name` - Bank name
- `account_number` - Account number
- `sort_code` - Bank sort code
- `statement_period` - Statement period
- `transaction_date` - Transaction date (YYYY-MM-DD)
- `description` - Transaction description
- `debit` - Debit amount (if applicable)
- `credit` - Credit amount (if applicable)
- `balance` - Account balance after transaction
- `reference` - Transaction reference number (if available)

## Getting Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

## Directory Structure

```
statement-processor/
├── data/                # Place PDF files here
├── output/              # CSV output location
├── src/                 # Source code
├── venv/                # Virtual environment
├── .env                 # API configuration
└── requirements.txt     # Dependencies
```

## Supported Banks

The AI model can process statements from any bank, including:
- HSBC, Barclays, Santander, Lloyds
- Monzo, Starling, Revolut
- And many others

## Re-running

You can safely re-run the processor with new PDFs. Existing transactions are automatically detected and skipped using hash-based deduplication.