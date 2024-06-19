# Membership Card Configuration and PDF Generation Service

This Django application, named `membership`, provides configurations for generating and printing membership cards. It includes the `MembershipCardConfig` class for configuration settings and the `PDFGenerationService` class for generating membership cards in PDF format.

## Table of Contents

- [Configuration](#configuration)
  - [Module Name](#module-name)
  - [Default Configuration](#default-configuration)
  - [MembershipCardConfig Class](#membershipcardconfig-class)
    - [Card Print Configuration](#card-print-configuration)
    - [WKHTML Command Options for Printing](#wkhtml-command-options-for-printing)
    - [Template Selection Based on OS](#template-selection-based-on-os)
    - [Terms and Conditions](#terms-and-conditions)
- [PDFGenerationService Class](#pdfgenerationservice-class)
  - [Methods](#methods)
    - [generate_pdf](#generate_pdf)
    - [get_insuree_photo](#get_insuree_photo)
    - [generate_eligibility_html](#generate_eligibility_html)
- [Helper Functions](#helper-functions)
  - [generate_conditions_html](#generate_conditions_html)
  - [send_email](#send_email)

## Configuration

### Module Name

```python
MODULE_NAME = 'membership'
## WKHTML Command Options for Printing

The `wkhtml_cmd_options_for_printing` dictionary contains options for configuring the `wkhtmltopdf` command used in generating PDFs. Below are the options available:

```python
wkhtml_cmd_options_for_printing = {
    "orientation": "Portrait",
    "page-size": "A4",
    "no-outline": None,
    "encoding": "UTF-8",
    "enable-local-file-access": True,
    "margin-top": "0",
    "margin-bottom": "0",
    "disable-smart-shrinking": False,
    "quiet": True,
}

### wkhtml_cmd_options_for_printing

Options for configuring the PDF generation with `wkhtmltopdf`:

- **orientation**: Portrait
- **page-size**: A4
- **no-outline**: None
- **encoding**: UTF-8
- **enable-local-file-access**: True
- **margin-top**: 0
- **margin-bottom**: 0
- **disable-smart-shrinking**: False
- **quiet**: True

These options control various aspects of the PDF output, such as page orientation, size, encoding, margins, and verbosity.


### get_template_by_os

This method determines and returns an appropriate HTML template filename based on the operating system (`OS`) of the server where the application is running.

```python
def get_template_by_os():
    import platform
    system = platform.system()
    if system == "Windows":
        template_name = "card_template_osx.html"  # Template for Windows (Not tested)
    elif system == "Darwin":
        template_name = "card_template_linux.html"  # Template for macOS (Darwin)
    elif system == "Linux":
        template_name = "card_template_linux.html"  # Template for Linux
    else:
        return None  # Return None if the OS is not recognized

    return template_name
```
