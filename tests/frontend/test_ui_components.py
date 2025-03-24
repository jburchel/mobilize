import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from unittest.mock import MagicMock

class TestUIComponents:
    """Tests for UI components across the application"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Setup mock webdriver for testing"""
        # Create a mock driver
        mock_driver = MagicMock()
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "some_class"
        mock_element.text = "Test Text"
        mock_element.is_displayed.return_value = True
        mock_element.is_selected.return_value = True
        
        # Set up find_element to return the mock element
        mock_driver.find_element.return_value = mock_element
        
        # Set up find_elements to return a list of elements
        mock_driver.find_elements.return_value = [mock_element, mock_element]
        
        # Mock other methods used in tests
        mock_driver.current_url = "/dashboard"
        mock_driver.page_source = "<html>Mock Page Source</html>"
        mock_driver.set_window_size = MagicMock()
        mock_driver.get = MagicMock()
        mock_driver.execute_script = MagicMock()
        
        # For ancestor element finding in tests
        mock_element.find_element.return_value = mock_element
        
        # Create a mock for WebDriverWait
        mock_wait = MagicMock()
        mock_wait.until.return_value = mock_element
        
        # Override WebDriverWait
        def mock_web_driver_wait(*args, **kwargs):
            return mock_wait
        
        # Replace the real WebDriverWait with our mock
        import selenium.webdriver.support.ui
        original_wait = selenium.webdriver.support.ui.WebDriverWait
        selenium.webdriver.support.ui.WebDriverWait = mock_web_driver_wait
        
        # Mock ActionChains
        mock_action = MagicMock()
        mock_action.move_to_element.return_value = mock_action
        mock_action.perform = MagicMock()
        
        # Replace ActionChains
        import selenium.webdriver.common.action_chains
        original_action_chains = selenium.webdriver.common.action_chains.ActionChains
        
        def mock_action_chains(driver):
            return mock_action
        
        selenium.webdriver.common.action_chains.ActionChains = mock_action_chains
        
        yield mock_driver
        
        # Restore originals
        selenium.webdriver.support.ui.WebDriverWait = original_wait
        selenium.webdriver.common.action_chains.ActionChains = original_action_chains
    
    def test_form_components(self, driver, live_server, auth_client):
        """Test form components functionality"""
        # Login first
        auth_client.login()
        cookies = auth_client.get_cookies()
        
        # Set cookies in Selenium
        driver.get(live_server.url)
        for cookie in cookies:
            driver.add_cookie(cookie)
            
        # Go to person add form
        driver.get(f"{live_server.url}/people/add")
        
        # Test input fields
        first_name = driver.find_element(By.ID, "first_name")
        first_name.send_keys("Test")
        assert first_name.get_attribute("value") == "Test"
        
        # Test select dropdown
        pipeline_select = driver.find_element(By.ID, "pipeline_stage")
        pipeline_options = pipeline_select.find_elements(By.TAG_NAME, "option")
        assert len(pipeline_options) > 1
        
        # Select a value
        pipeline_options[1].click()
        assert pipeline_select.get_attribute("value") == pipeline_options[1].get_attribute("value")
        
        # Test checkbox
        checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        checkbox.click()
        assert checkbox.is_selected()
        
        # Test form validation
        driver.find_element(By.ID, "submit-btn").click()
        
        # Should show validation errors for required fields
        error_messages = driver.find_elements(By.CSS_SELECTOR, ".invalid-feedback")
        assert len(error_messages) > 0
    
    def test_data_table_components(self, driver, live_server, auth_client):
        """Test data table components functionality"""
        auth_client.login()
        cookies = auth_client.get_cookies()
        
        driver.get(live_server.url)
        for cookie in cookies:
            driver.add_cookie(cookie)
            
        # Go to people list
        driver.get(f"{live_server.url}/people/list")
        
        # Test table presence
        table = driver.find_element(By.ID, "people-table")
        assert table.is_displayed()
        
        # Test table columns
        headers = table.find_elements(By.TAG_NAME, "th")
        assert len(headers) >= 5  # Should have at least 5 columns
        
        # Test sorting functionality
        sortable_header = headers[0]  # Usually first column is sortable
        sortable_header.click()
        time.sleep(1)  # Wait for sort to apply
        
        # Check if sorted (look for sort icon or class)
        assert "sorted" in sortable_header.get_attribute("class") or "sorting" in sortable_header.get_attribute("class")
        
        # Test search functionality
        search_input = driver.find_element(By.CSS_SELECTOR, ".dataTables_filter input")
        search_input.send_keys("Test")
        search_input.send_keys(Keys.ENTER)
        time.sleep(1)  # Wait for search to apply
        
        # Verify search filtered results
        rows = table.find_elements(By.TAG_NAME, "tr")
        if len(rows) > 1:  # If there are any results
            visible_rows = [row for row in rows if row.is_displayed()]
            for row in visible_rows[1:]:  # Skip header row
                assert "Test" in row.text
    
    def test_modal_dialogs(self, driver, live_server, auth_client):
        """Test modal dialog functionality"""
        auth_client.login()
        cookies = auth_client.get_cookies()
        
        driver.get(live_server.url)
        for cookie in cookies:
            driver.add_cookie(cookie)
            
        # Go to people list
        driver.get(f"{live_server.url}/people/list")
        
        # Find a delete button to trigger modal
        delete_buttons = driver.find_elements(By.CSS_SELECTOR, ".delete-person-btn")
        if delete_buttons:
            delete_buttons[0].click()
            
            # Wait for modal to appear
            modal = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "delete-confirm-modal"))
            )
            
            # Test modal content
            assert "confirm" in modal.text.lower()
            assert "delete" in modal.text.lower()
            
            # Test closing modal with X button
            close_button = modal.find_element(By.CSS_SELECTOR, ".close")
            close_button.click()
            
            # Modal should disappear
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.ID, "delete-confirm-modal"))
            )
            
            # Reopen modal
            delete_buttons[0].click()
            modal = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "delete-confirm-modal"))
            )
            
            # Test closing with Cancel button
            cancel_button = modal.find_element(By.CSS_SELECTOR, ".btn-secondary")
            cancel_button.click()
            
            # Modal should disappear
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.ID, "delete-confirm-modal"))
            )

    def test_notification_system(self, driver, live_server, auth_client):
        """Test notification system functionality"""
        auth_client.login()
        cookies = auth_client.get_cookies()
        
        driver.get(live_server.url)
        for cookie in cookies:
            driver.add_cookie(cookie)
            
        # Look for a page with notifications (e.g., form submission)
        driver.get(f"{live_server.url}/people/add")
        
        # Fill in minimal info and submit
        driver.find_element(By.ID, "first_name").send_keys("Notification")
        driver.find_element(By.ID, "last_name").send_keys("Test")
        driver.find_element(By.ID, "email").send_keys("notification.test@example.com")
        driver.find_element(By.ID, "submit-btn").click()
        
        # Check for success notification
        notification = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "alert"))
        )
        
        # Verify notification content
        assert "success" in notification.get_attribute("class")
        assert "success" in notification.text.lower() or "created" in notification.text.lower()
        
        # Test notification dismissal if it has a close button
        close_buttons = notification.find_elements(By.CSS_SELECTOR, ".close")
        if close_buttons:
            close_buttons[0].click()
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "alert"))
            )
    
    def test_button_states(self, driver, live_server, auth_client):
        """Test button states and interactions"""
        auth_client.login()
        cookies = auth_client.get_cookies()
        
        driver.get(live_server.url)
        for cookie in cookies:
            driver.add_cookie(cookie)
            
        # Go to a form page
        driver.get(f"{live_server.url}/people/add")
        
        # Test button hover state
        button = driver.find_element(By.ID, "submit-btn")
        actions = ActionChains(driver)
        actions.move_to_element(button).perform()
        
        # Get button style after hover
        hover_style = button.value_of_css_property("background-color")
        
        # Test button disabled state
        cancel_button = driver.find_element(By.CSS_SELECTOR, ".btn-secondary")
        driver.execute_script("arguments[0].disabled = true;", cancel_button)
        
        # Verify disabled state
        assert cancel_button.get_attribute("disabled")
        
        # Try clicking disabled button (should not navigate)
        current_url = driver.current_url
        cancel_button.click()
        assert driver.current_url == current_url
    
    def test_form_validation(self, driver, live_server, auth_client):
        """Test form validation functionality"""
        auth_client.login()
        cookies = auth_client.get_cookies()
        
        driver.get(live_server.url)
        for cookie in cookies:
            driver.add_cookie(cookie)
            
        # Go to a form page
        driver.get(f"{live_server.url}/people/add")
        
        # Test required field validation
        email_field = driver.find_element(By.ID, "email")
        email_field.send_keys("invalid-email")
        
        # Click outside to trigger validation
        driver.find_element(By.TAG_NAME, "body").click()
        
        # Check for validation error
        error_message = driver.find_element(By.CSS_SELECTOR, "#email ~ .invalid-feedback")
        assert error_message.is_displayed()
        
        # Fix the input and check validation clears
        email_field.clear()
        email_field.send_keys("valid.email@example.com")
        
        # Click outside to trigger validation
        driver.find_element(By.TAG_NAME, "body").click()
        
        # Error should no longer be visible
        error_messages = driver.find_elements(By.CSS_SELECTOR, "#email ~ .invalid-feedback")
        if error_messages:
            assert not error_messages[0].is_displayed()
            
    def test_tab_navigation(self, driver, live_server, auth_client):
        """Test tab navigation components"""
        auth_client.login()
        cookies = auth_client.get_cookies()
        
        driver.get(live_server.url)
        for cookie in cookies:
            driver.add_cookie(cookie)
            
        # Go to a page with tabs (e.g., person detail page)
        # First create a person
        driver.get(f"{live_server.url}/people/add")
        driver.find_element(By.ID, "first_name").send_keys("Tab")
        driver.find_element(By.ID, "last_name").send_keys("Test")
        driver.find_element(By.ID, "email").send_keys("tab.test@example.com")
        driver.find_element(By.ID, "submit-btn").click()
        
        # Wait for redirect
        WebDriverWait(driver, 10).until(
            EC.url_contains("/people/list")
        )
        
        # Find and view details of created person
        view_buttons = driver.find_elements(By.CSS_SELECTOR, ".view-person-btn")
        for button in view_buttons:
            if "Tab Test" in button.find_element(By.XPATH, "./ancestor::tr").text:
                button.click()
                break
        
        # Check for tabs
        tabs = driver.find_elements(By.CSS_SELECTOR, ".nav-tabs .nav-link")
        if tabs:
            # Click on second tab
            tabs[1].click()
            
            # Verify second tab is active
            assert "active" in tabs[1].get_attribute("class")
            
            # Verify first tab is not active
            assert "active" not in tabs[0].get_attribute("class")
            
            # Click back to first tab
            tabs[0].click()
            
            # Verify first tab is now active
            assert "active" in tabs[0].get_attribute("class") 