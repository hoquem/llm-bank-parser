# LLM Bank Parser

> **Universal bank statement parser using LLMs - works with any PDF format**

Stop writing custom parsers for every bank. This tool uses AI to extract transaction data from **any** bank statement PDF and outputs clean CSV data ready for Google Sheets.

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Powered by Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini-orange.svg)](https://ai.google.dev/)

## Why This Exists

**The Problem:** Traditional bank statement parsing requires writing custom code for each bank format. When banks update their PDFs, everything breaks.

**The Solution:** Use LLMs to understand document structure naturally. One prompt works for all banks.

- 🔄 **Before:** 500+ lines of regex code per bank
- ⚡ **After:** 30 minutes of prompt engineering for all banks
- 📈 **Results:** 95% success rate across 8 different banks

## Quick Demo

```bash
# Add PDF statements to data/ folder
cp bank_statements/*.pdf data/

# Run the processor
python -m src.main

# Output: Clean CSV ready for Google Sheets
✓ Processed 22 PDFs from 8 banks in under 2 minutes
✓ Extracted 302 transactions with 95% success rate
```

## How It Works

```
📄 PDF Files → 🔍 Extract Text → 🤖 LLM Processing → 📊 CSV Output
```

1. **Extract Text:** Uses PyPDF2 to get raw text from PDFs
2. **LLM Magic:** Google Gemini understands the document structure and extracts transactions
3. **Clean Output:** Validates data and exports to CSV with deduplication

## Installation

```bash
# 1. Clone repository
git clone https://github.com/hoquem/llm-bank-parser.git
cd llm-bank-parser

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
cp .env.example .env
# Edit .env and add: GOOGLE_API_KEY=your_api_key_here

# 4. Add PDF statements to data/ folder
cp your_statements/*.pdf data/

# 5. Run
python -m src.main
```

## Supported Banks

Works with **any bank PDF format**. Tested with:
- HSBC, Barclays, Monzo, Starling Bank
- Nationwide, first direct, Mettle
- And more...

## Get API Key

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Create a free account
3. Generate API key
4. Add to `.env` file

## Output

Creates `output/transactions.csv` with columns:
- Date, Description, Debit, Credit, Balance
- Account holder, Bank name, Sort code
- Transaction hash (for deduplication)

Perfect for Google Sheets import and financial analysis.

## Requirements

- Python 3.9+
- Google Gemini API key (free tier available)
- PDF bank statements

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas needed:
- [ ] More bank format testing
- [ ] Additional output formats
- [ ] Performance improvements
- [ ] Test coverage

## License

MIT License - use freely for personal or commercial projects.

---

**💡 Pro Tip:** This tool saves developers 20+ hours per bank format. Use it to focus on building features, not parsing PDFs.

**🔗 Read the story:** [Medium article](https://medium.com/@mahmudulhoque/stop-writing-bank-statement-parsers-use-llms-instead-50902360a604) explaining why LLMs beat regex for document processing.