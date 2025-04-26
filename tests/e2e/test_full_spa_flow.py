import pytest
from playwright.sync_api import sync_playwright

def test_full_spa_flow():
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page()
        pg.goto('http://localhost:5000')
        # simulate login
        pg.fill('#username','admin'); pg.fill('#password','pass'); pg.click('#login')
        assert pg.url.endswith('/dashboard')
        # check graph
        assert pg.is_visible('canvas')
        br.close()
