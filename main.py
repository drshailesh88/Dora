#!/usr/bin/env python3
"""
Dora - DocAssist Medical Knowledge Platform

Run with:
    python main.py query "What is the treatment for diabetes?"
    python main.py ingest ./medical_books/
    python main.py serve
"""

from src.cli import app

if __name__ == "__main__":
    app()
