Setup Instructions:

Install required packages:
    pip install selenium pandas webdriver_manager

Usage Guidelines:

The script creates two output files:

    amazon_products.json
    amazon_products.csv
A log file is created with timestamp for debugging

The script implements:

Login authentication
Category navigation
Product data extraction
Discount calculation
Error handling
Data storage in multiple formats
Rate Limiting:

Includes sleep timers to prevent overloading
Respects Amazon's robots.txt
Implements proper waits for page loads

    Error Handling:
        Catches and logs exceptions
        Graceful failure handling
        Maintains session stability
