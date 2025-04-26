import pytest
from playwright.sync_api import sync_playwright

def test_spa_auth_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('http://localhost:5000/')
        assert page.text_content('h1') == 'EngineProject Dashboard (Auth)'
        browser.close()
