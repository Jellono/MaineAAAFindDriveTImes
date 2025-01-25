"""
Maine AAA Driving Lesson Availability Scraper
=============================================

This Python application automates the process of checking for available driving lessons
on the Maine AAA website. It runs every 15 minutes to scrape the site for newly available
appointments and sends email notifications to a predefined group when new slots are found.

Features:
- Scrapes the Maine AAA website for available driving lessons.
- Sends email notifications to a specified list of recipients when new appointments are detected.
- Filters appointments based on user-defined time thresholds for weekdays and weekends.
- Logs all activity to a file for real-time monitoring.

Setup Instructions:
1. Configure the placeholders for your Gmail account, email recipients, and the AAA login credentials.
2. Install the required dependencies (see README for details).
3. Run the script using Python.
4. Optionally, configure the script to run in the background (e.g., using `screen` or `nohup`).

Note:
- This script uses Selenium for web scraping and requires Chrome/Chromium and ChromeDriver installed.
- Use responsibly and ensure compliance with the website's terms of service.
"""

import logging
import sys
from datetime import datetime
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import traceback

# Configurable Variables
RUN_INTERVAL_MINUTES = 15  # Time interval (in minutes) between script runs
WEEKDAY_START_TIME = "04:30 PM"  # Start time cutoff for weekdays
WEEKEND_START_TIME = "09:00 AM"  # Start time cutoff for weekends
SMTP_SERVER = "smtp.gmail.com"  # SMTP server for sending emails
SMTP_PORT = 587  # SMTP port for sending emails
SENDER_EMAIL = "your_email@gmail.com"  # Your Gmail address (used to send emails)
SENDER_PASSWORD = "your_app_password"  # App password generated in Gmail settings
RECIPIENT_EMAILS = ["recipient1@example.com", "recipient2@example.com"]  # List of recipient email addresses
LOGIN_LINK = "https://example.com/login"  # URL of the Maine AAA login page

# Logging Configuration
log_file = "app.log"  # Log file to store all logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="a"),  # Append logs to a file
        logging.StreamHandler(sys.stdout),       # Output logs to the console
    ]
)

# Function to compare two times
def is_time_greater_or_equal(time1, time2):
    """
    Compare two times to determine if time1 is greater than or equal to time2.

    Args:
        time1 (str): First time in 12-hour format (e.g., "03:15 PM").
        time2 (str): Second time in 12-hour format (e.g., "03:00 PM").

    Returns:
        bool: True if time1 >= time2, otherwise False.
    """
    time1_dt = datetime.strptime(time1, "%I:%M %p")
    time2_dt = datetime.strptime(time2, "%I:%M %p")
    return time1_dt >= time2_dt

# Function to convert 24-hour time to 12-hour time with AM/PM
def convert_24hr_to_12hr(time_str):
    """
    Convert a 24-hour formatted time string to a 12-hour formatted time string with AM/PM.

    Args:
        time_str (str): Time in 24-hour format (e.g., "1530").

    Returns:
        str: Time in 12-hour format with AM/PM (e.g., "3:30 PM").
    """
    hours = int(time_str[:2])
    minutes = time_str[2:]
    period = "AM" if hours < 12 else "PM"
    hours = hours if 1 <= hours <= 12 else hours - 12 if hours > 12 else 12
    return f"{hours}:{minutes} {period}"

# Email Function
def send_email(appointments):
    """
    Send an email with the list of available appointments.

    Args:
        appointments (list): List of available appointment strings.
    """
    subject = "Driving Lesson Openings Available"
    body = "Here are the available appointments:\n\n" + "\n".join(appointments)
    body += f"\n\nYou can log in here:\n{LOGIN_LINK}"
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = ", ".join(RECIPIENT_EMAILS)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
        logging.info(f"Email sent successfully to {', '.join(RECIPIENT_EMAILS)}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# Database Initialization
def initialize_database():
    """
    Initialize the SQLite database for storing appointment data.

    Returns:
        sqlite3.Connection: Database connection object.
    """
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_string TEXT UNIQUE,
            start_time_12hr TEXT,
            end_time_12hr TEXT,
            instructor TEXT,
            sent_email INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

# Scraper Function
def run_scraper():
    """
    Main scraper function to log in, retrieve appointment data, and send email notifications.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run browser in headless mode (no GUI)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Use the Service class for ChromeDriver
    service = Service("/usr/bin/chromedriver")  # Path to the ChromeDriver binary
    driver = webdriver.Chrome(service=service, options=chrome_options)

    conn = initialize_database()
    cursor = conn.cursor()

    try:
        logging.info(f"Opening login page: {LOGIN_LINK}")
        driver.get(LOGIN_LINK)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys("your_username")
        driver.find_element(By.ID, "password").send_keys("your_password")
        driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]").click()
        logging.info("Login completed.")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "div_QuickLinks")))
        driver.find_element(By.XPATH, "//a[contains(text(), 'Schedule my drive')]").click()
        logging.info("Navigated to 'Schedule My Drive' page.")

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "btnSelectAppt")))
        date_elements = driver.find_elements(By.XPATH, "//a[@id='btnSelectAppt']")
        appointments_to_send = []

        for element in date_elements:
            appointment_string = element.get_attribute("data-appointmentdatelongstring")
            start_time = convert_24hr_to_12hr(element.get_attribute("data-starttime"))
            end_time = convert_24hr_to_12hr(element.get_attribute("data-endtime"))
            instructor = element.get_attribute("data-instructor")
            
            day_of_week = appointment_string.split(",")[0].strip()
            start_time_limit = WEEKEND_START_TIME if day_of_week in ["Sat", "Sun"] else WEEKDAY_START_TIME
            if not is_time_greater_or_equal(start_time, start_time_limit):
                continue
            
            cursor.execute("SELECT sent_email FROM appointments WHERE appointment_string = ?", (appointment_string,))
            if cursor.fetchone():
                continue
            
            appointments_to_send.append(f"{appointment_string} | Instructor: {instructor}")
            cursor.execute("""
                INSERT OR IGNORE INTO appointments (
                    appointment_string, start_time_12hr, end_time_12hr, instructor, sent_email
                ) VALUES (?, ?, ?, ?, 1)
            """, (appointment_string, start_time, end_time, instructor))
            conn.commit()

        if appointments_to_send:
            send_email(appointments_to_send)
        else:
            logging.info("No new appointments to email.")
    except Exception as e:
        logging.error(f"Error in scraper: {e}")
        logging.error(traceback.format_exc())
    finally:
        driver.quit()
        conn.close()

# Main Loop with Error Handling
while True:
    try:
        logging.info("Starting the scraper...")
        run_scraper()
        logging.info(f"Scraper completed. Sleeping for {RUN_INTERVAL_MINUTES} minutes...")
        time.sleep(RUN_INTERVAL_MINUTES * 60)
    except Exception as e:
        logging.error(f"Application crashed: {e}")
        logging.error(traceback.format_exc())
