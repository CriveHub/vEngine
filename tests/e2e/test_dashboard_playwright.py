import pytest
from playwright.sync_api import sync_playwright

def test_dashboard_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:5000/")
        assert "Dashboard" in page.title()
        browser.close()
