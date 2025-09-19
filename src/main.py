"""
Main application controller for bank statement processing.

This module orchestrates the entire processing pipeline:
PDF extraction -> AI analysis -> Data validation -> CSV storage
"""

import sys
import warnings
from pathlib import Path
from typing import List, Dict, Any

# Suppress urllib3 OpenSSL warning
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+.*")

from src.config import load_config, get_config, ProcessingConfig
from src.logging_config import setup_logging, get_logger, LoggerMixin
from src.exceptions import (
    StatementProcessingError,
    ConfigurationError,
    PDFProcessingError,
    AIProcessingError,
    StorageError
)
from src.pdf_parser import extract_text_from_pdf, validate_pdf_file
from src.llm_extractor import extract_data_with_llm, test_api_connection
from src.data_processor import (
    get_existing_hashes,
    convert_statement_to_records,
    append_to_csv,
    get_csv_summary,
    validate_csv_structure
)


class StatementProcessor(LoggerMixin):
    """Main application class for processing bank statements."""

    def __init__(self, config: ProcessingConfig):
        """
        Initialize the statement processor.

        Args:
            config: Application configuration
        """
        self.config = config

    def setup_environment(self) -> None:
        """
        Validate environment and API connectivity.

        Raises:
            ConfigurationError: If configuration is invalid
            AIProcessingError: If API connection fails
        """
        self.logger.info("Setting up application environment")

        try:
            # Test API connection
            self.log_operation("Testing API connection")
            if not test_api_connection(self.config.api_key):
                raise AIProcessingError(
                    "API connection test failed",
                    model_name=self.config.model_name,
                    details={"api_key_length": len(self.config.api_key)}
                )

            self.log_operation("API connection successful", model=self.config.model_name)

        except Exception as e:
            if isinstance(e, AIProcessingError):
                raise
            raise ConfigurationError(
                "Failed to validate API configuration",
                details={"model_name": self.config.model_name},
                cause=e
            )


    def get_pdf_files(self) -> List[str]:
        """
        Get list of PDF files in the configured directory.

        Returns:
            List[str]: List of valid PDF file paths
        """
        pdf_directory = Path(self.config.data_dir)

        if not pdf_directory.exists():
            self.log_operation("Creating data directory", path=str(pdf_directory))
            pdf_directory.mkdir(parents=True, exist_ok=True)
            return []

        pdf_files = []
        invalid_files = []

        for file_path in pdf_directory.glob("*.pdf"):
            if validate_pdf_file(str(file_path)):
                pdf_files.append(str(file_path))
            else:
                invalid_files.append(file_path.name)

        if invalid_files:
            self.logger.warning(
                "Found invalid PDF files",
                invalid_count=len(invalid_files),
                invalid_files=invalid_files
            )

        self.log_operation(
            "PDF file discovery completed",
            valid_files=len(pdf_files),
            invalid_files=len(invalid_files),
            directory=str(pdf_directory)
        )

        return sorted(pdf_files)


    def process_single_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process a single PDF file and extract bank statement data.

        Args:
            pdf_path: Path to PDF file

        Returns:
            dict: Processing result with status and data/error info
        """
        filename = Path(pdf_path).name

        self.log_operation("Starting PDF processing", filename=filename, path=pdf_path)

        try:
            # Extract text from PDF
            self.log_operation("Extracting text from PDF", filename=filename)
            raw_text = extract_text_from_pdf(pdf_path)

            if not raw_text or len(raw_text.strip()) < 50:
                raise PDFProcessingError(
                    "Insufficient text extracted from PDF",
                    file_path=pdf_path,
                    details={"text_length": len(raw_text)}
                )

            self.log_operation(
                "Text extraction completed",
                filename=filename,
                text_length=len(raw_text)
            )

            # Process with AI
            self.log_operation("Processing with AI", filename=filename)
            statement_data = extract_data_with_llm(raw_text, self.config.api_key)

            self.log_operation(
                "AI processing completed",
                filename=filename,
                transaction_count=len(statement_data.transactions),
                account_holder=statement_data.account_holder_name,
                bank=statement_data.bank_name,
                period=statement_data.statement_period
            )

            return {
                "status": "success",
                "filename": filename,
                "statement": statement_data
            }

        except Exception as e:
            error_data = {"filename": filename, "path": pdf_path}

            if isinstance(e, StatementProcessingError):
                error_data.update(e.to_dict())
                self.logger.error("PDF processing failed", **error_data)
            else:
                self.log_error("Unexpected error during PDF processing", e, **error_data)

            return {
                "status": "error",
                "filename": filename,
                "error": str(e),
                "error_type": type(e).__name__
            }


def main():
    """
    Main application entry point.
    """
    try:
        # Load configuration and setup logging
        config = load_config()
        setup_logging(config.log_level)
        logger = get_logger(__name__)

        logger.info("🏦 Bank Statement Processor Starting", version="2.0")

        # Create processor instance
        processor = StatementProcessor(config)

        # Setup environment and validate API
        processor.setup_environment()

        # Validate CSV structure
        if not validate_csv_structure(config.output_path):
            logger.warning("Existing CSV has invalid structure, creating backup")
            backup_path = f"{config.output_path}.backup"
            if Path(config.output_path).exists():
                Path(config.output_path).rename(backup_path)

        # Get existing transactions
        existing_hashes = get_existing_hashes(config.output_path)
        logger.info("Existing transactions loaded", count=len(existing_hashes))

        # Get PDF files to process
        pdf_files = processor.get_pdf_files()

        if not pdf_files:
            logger.warning("No PDF files found", directory=config.data_dir)
            print(f"\n📂 No PDF files found in '{config.data_dir}' directory")
            print("Please add PDF bank statements to process.")
            return

        logger.info("Starting batch processing", file_count=len(pdf_files))

        # Process each PDF file
        all_new_records = []
        successful_files = 0
        failed_files = []

        for i, pdf_path in enumerate(pdf_files, 1):
            processor.log_progress(i, len(pdf_files), item=Path(pdf_path).name)

            result = processor.process_single_pdf(pdf_path)

            if result["status"] == "success":
                # Convert to CSV records
                new_records = convert_statement_to_records(
                    result["statement"],
                    result["filename"],
                    existing_hashes
                )

                all_new_records.extend(new_records)
                successful_files += 1

                logger.info(
                    "PDF processed successfully",
                    filename=result["filename"],
                    new_transactions=len(new_records),
                    total_transactions=len(result["statement"].transactions)
                )

            else:
                failed_files.append({
                    "filename": result["filename"],
                    "error": result["error"],
                    "error_type": result.get("error_type", "Unknown")
                })

        # Save new records to CSV
        if all_new_records:
            logger.info("Saving new transactions", count=len(all_new_records))
            try:
                append_to_csv(all_new_records, config.output_path)
                logger.info("Transactions saved successfully", path=config.output_path)
            except Exception as e:
                raise StorageError(
                    "Failed to save transactions to CSV",
                    file_path=config.output_path,
                    operation="append",
                    cause=e
                )
        else:
            logger.info("No new transactions to save")

        # Generate and log summary
        summary_data = {
            "files_processed": successful_files,
            "total_files": len(pdf_files),
            "new_transactions": len(all_new_records),
            "failed_files": len(failed_files)
        }

        logger.info("Processing completed", **summary_data)

        # Print user-friendly summary
        print("\n" + "=" * 50)
        print("📈 PROCESSING SUMMARY")
        print("=" * 50)
        print(f"Files processed successfully: {successful_files}/{len(pdf_files)}")
        print(f"New transactions added: {len(all_new_records)}")

        if failed_files:
            print(f"\n❌ Failed files ({len(failed_files)}):")
            for failed_file in failed_files:
                print(f"  • {failed_file['filename']}: {failed_file['error']}")

        # CSV summary
        try:
            summary = get_csv_summary(config.output_path)
            if "error" not in summary:
                print(f"\n📊 DATABASE SUMMARY:")
                print(f"  Total transactions: {summary['total_transactions']}")
                print(f"  Unique accounts: {summary['unique_accounts']}")
                print(f"  Banks: {', '.join(summary['banks'])}")
                if summary['date_range']['earliest']:
                    print(f"  Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
        except Exception as e:
            logger.warning("Failed to generate CSV summary", error=str(e))

        print(f"\n🎯 Ready for import to Google Sheets: {config.output_path}")

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        print("\n\n⏹️  Processing interrupted by user")
        sys.exit(1)
    except StatementProcessingError as e:
        logger.error("Application error", **e.to_dict())
        print(f"\n❌ Error: {e.message}")
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected fatal error", error=str(e), error_type=type(e).__name__)
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()