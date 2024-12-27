from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pymongo
import uuid
from datetime import datetime
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("mongourl")
client = pymongo.MongoClient(MONGO_URI)
db = client["twitter_trends"]
collection = db["trends"]

# Selenium setup
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

try:
    # Open Twitter login page
    driver.get("https://x.com/i/flow/login?lang=en")
    print("Opened Twitter login page")
    time.sleep(3)  # Short pause for possible pop-ups

    # Close any pop-up dialogs if they appear
    try:
        popup_close = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(@class, 'r-')][@aria-label='Close']"))
        )
        popup_close.click()
        print("Closed pop-up dialog")
    except:
        pass

    # Enter username
    try:
        username = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.r-30o5oe.r-1dz5y72"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", username)
        username.click()  # Ensure focus
        username.send_keys(os.getenv("twt_username"))
        username.send_keys(Keys.RETURN)
        print("Entered username")
    except Exception as e:
        print(f"Error entering username: {e}")
        driver.save_screenshot("username_error.png")
        raise

    time.sleep(3)

    # Click next or login button
    try:
        next_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
        )
        next_btn.click()
    except:
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
        )
        login_btn.click()
    time.sleep(3)

    # If asked for phone/verification code, handle it
    try:
        verification_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "text"))) 
        verification_input.send_keys(os.getenv("phone_verification_code"))  # or prompt user for code
        verification_input.send_keys(Keys.RETURN)
        time.sleep(5)
    except:
        pass

    try:
        phone_number_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='text']"))
        )
        phone_number_input.send_keys(os.getenv("phone_number"))
        phone_number_input.send_keys(Keys.RETURN)
        print("Entered phone number to verify account")
        time.sleep(30)  # Wait for user to receive and enter OTP
    except:
        pass

    # Enter password
    try:
        password = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.css-175oi2r.r-18u37iz.r-16y2uox.r-1wbh5a2.r-1wzrnnt.r-1udh08x.r-xd6kpl.r-is05cd.r-ttdzmv"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", password)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.css-175oi2r.r-18u37iz.r-16y2uox.r-1wbh5a2.r-1wzrnnt.r-1udh08x.r-xd6kpl.r-is05cd.r-ttdzmv")))
        password.click()  # Ensure focus
        password.send_keys(os.getenv("twt_password"))
        password.send_keys(Keys.RETURN)
        print("Entered password")
    except Exception as e:
        print(f"Error entering password: {e}")
        driver.save_screenshot("password_error.png")
        raise

    time.sleep(10)

    # Locate the "What’s Happening" section for trends
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//section[contains(@aria-labelledby, 'accessible-list')]"))
    )
    trends_section = driver.find_element(By.XPATH, "//section[contains(@aria-labelledby, 'accessible-list')]")
    trends = trends_section.find_elements(By.XPATH, ".//span")[:5]  # Fetch the top 5 trends
    trend_list = [trend.text for trend in trends if trend.text.strip()]  # Remove empty strings
    print("Scraped trends:", trend_list)

    # Generate unique ID and other metadata
    unique_id = str(uuid.uuid4())
    ip_address = requests.get("https://api.ipify.org").text  # Get public IP
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create the trend record
    trend_record = {
        "_id": unique_id,
        "trend1": trend_list[0] if len(trend_list) > 0 else "N/A",
        "trend2": trend_list[1] if len(trend_list) > 1 else "N/A",
        "trend3": trend_list[2] if len(trend_list) > 2 else "N/A",
        "trend4": trend_list[3] if len(trend_list) > 3 else "N/A",
        "trend5": trend_list[4] if len(trend_list) > 4 else "N/A",
        "datetime": current_time,
        "ip_address": ip_address,
    }

    # Insert the record into MongoDB
    collection.insert_one(trend_record)
    print("Scraped data saved to MongoDB successfully!")

except Exception as e:
    print(f"An error occurred: {e}")
    driver.save_screenshot("error_screenshot.png")  # Save a screenshot for debugging

finally:
    # Ensure the browser is still open before attempting to quit
    if driver.service.process:
        driver.quit()