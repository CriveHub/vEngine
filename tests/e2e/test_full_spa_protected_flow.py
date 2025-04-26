import pytest
from playwright.sync_api import sync_playwright

def test_full_spa_protected_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('http://localhost:5000/login')
        page.fill('#username','admin'); page.fill('#password','pass'); page.click('#submit')
        assert page.url.endswith('/dashboard')
        assert page.locator('.chart').count() > 0
        browser.close()
