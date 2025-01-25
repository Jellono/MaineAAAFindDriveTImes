# MaineAAAFindDriveTimes
Automated Python script that scrapes the Maine AAA site for driving lesson availability and sends email notifications for new openings.

## Overview
This Python application automates the process of checking for available driving lessons on the Maine AAA website. It runs every 15 minutes, scrapes the site for newly available appointments, and sends email notifications to a predefined group when new slots are found.

## Features
- Scrapes the Maine AAA website for driving lesson availability.
- Sends email notifications for new appointment openings.
- Filters appointments based on day (weekday/weekend) and start time thresholds.
- Logs all actions to a file for real-time monitoring.

## Setup Instructions

### Prerequisites
1. **Python**: Install Python 3.7 or higher.
2. **Google Chrome/Chromium**: Ensure a browser is installed.
3. **ChromeDriver**: Install ChromeDriver and ensure it matches your browser version.
4. **Gmail Account**: Set up Gmail to send email notifications.

### Gmail Setup for Email Notifications
1. Go to [Google Account Security Settings](https://myaccount.google.com/security).
2. Enable **2-Step Verification** on your account.
3. Navigate to **App Passwords** under "Signing in to Google."
4. Generate a new app password:
   - **App**: Select "Mail."
   - **Device**: Choose "Other (Custom name)" (e.g., "AAA Scraper").
5. Copy the app password and use it in the script.

