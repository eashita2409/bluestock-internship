import time
import sys
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1080})
        
        print("Navigating to Streamlit app...")
        page.goto("http://localhost:8501")
        
        # Wait for Streamlit to load
        page.wait_for_selector("[data-testid='stAppViewContainer']", timeout=30000)
        # Give it an extra moment to render charts
        time.sleep(5)
        
        print("Screenshotting Page 1: Executive Overview")
        page.screenshot(path="docs/dashboard_screenshots/1_executive_overview.png", full_page=True)
        
        # Streamlit radio buttons in sidebar
        print("Switching to Page 2: Performance Analytics")
        # Click the radio button label
        page.click("text='2. Performance Analytics'")
        time.sleep(5) # wait for render
        page.screenshot(path="docs/dashboard_screenshots/2_performance_analytics.png", full_page=True)
        
        print("Switching to Page 3: Portfolio & Allocation")
        page.click("text='3. Portfolio & Allocation'")
        time.sleep(5)
        page.screenshot(path="docs/dashboard_screenshots/3_portfolio_allocation.png", full_page=True)
        
        print("Switching to Page 4: Risk Analytics")
        page.click("text='4. Risk Analytics'")
        time.sleep(5)
        page.screenshot(path="docs/dashboard_screenshots/4_risk_analytics.png", full_page=True)
        
        print("Screenshots captured successfully.")
        browser.close()

if __name__ == "__main__":
    run()
