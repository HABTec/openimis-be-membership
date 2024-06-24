# Membership Card Configuration and PDF Generation Service

This Django application, named `membership`, provides configurations for generating and printing membership cards. It includes the `MembershipCardConfig` class for configuration settings and the `PDFGenerationService` class for generating membership cards in PDF format.


# Requirements
```
Install the wkhtmltopdf static binary.

This requires libfontconfig (on Ubuntu: sudo aptitude install libfontconfig).



Installation
Run pip install django-wkhtmltopdf.

Add 'wkhtmltopdf' to INSTALLED_APPS in your settings.py.

By default it will execute the first wkhtmltopdf command found on your PATH.

If you can’t add wkhtmltopdf to your PATH, you can set WKHTMLTOPDF_CMD to a specific executable:

e.g. in settings.py:
```
## Table of Contents

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

# Usages
## Available Mutations
- GeneratePdfSlip.Field()

Client Side
```
const query = `
    mutation {
      generatePdfSlip(insureeUuid: "${insureeUuid}") {
        base64Pdf
      }
    }
`;
```
Sample Usage
```
const insureeUuid = "your-insuree-uuid";  // Replace with the actual UUID of the insuree
const query = `
    mutation {
      generatePdfSlip(insureeUuid: "${insureeUuid}") {
        base64Pdf
      }
    }
`;

// Example of how to use the mutation with a GraphQL client
fetch('/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ query }),
})
  .then(response => response.json())
  .then(data => {
    const base64Pdf = data.data.generatePdfSlip.base64Pdf;
    console.log(base64Pdf);
  })
  .catch(error => {
    console.error('Error:', error);
  });

```

### Testing when DEBUG is True 

```
python
if settings.DEBUG:
    urlpatterns += [
        path('membership-card/test', index, name='index'),
    ]
```
