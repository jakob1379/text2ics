"""
Allows the package to be run as a script.
Example: python -m text2ics tests/data/ferry_mail.txt --api-key "your-key"
"""

from .cli import app

app()
