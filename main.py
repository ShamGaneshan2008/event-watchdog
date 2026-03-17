import smtplib
import ssl
import os
import time
import sqlite3
import logging

import requests
import selectorlib

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────

# URL of the webpage to scrape tour information
URL = "http://programmer100.pythonanywhere.com/tours/"
SCRAPE_INTERVAL = 2   # seconds between checks

# Email credentials loaded from environment variables (never hardcode these)
EMAIL_USERNAME = os.environ.get("EMAIL_USERNAME")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

# Fallback to user input if environment variables are not set
if not EMAIL_USERNAME:
    EMAIL_USERNAME = input("Enter your email: ")

if not EMAIL_PASSWORD:
    import getpass
    EMAIL_PASSWORD = getpass.getpass("Enter your app password: ")

if not EMAIL_RECEIVER:
    EMAIL_RECEIVER = input("Enter receiver email (or press Enter to use same): ")
    if not EMAIL_RECEIVER:
        EMAIL_RECEIVER = EMAIL_USERNAME

# Validation
if not EMAIL_USERNAME or not EMAIL_PASSWORD:
    print("Email credentials are required!")
    exit()


# ── Event scraper ──────────────────────────────────────────────────────────────
class Event:

    def scrape(self, url):
        """Download HTML source code from the given URL"""
        try:
            response = requests.get(url, timeout=10)  # Send HTTP GET request
            response.raise_for_status()
            source = response.text                    # Get HTML content as text
            return source                             # Return page source
        except requests.RequestException as e:
            log.error("Failed to fetch page: %s", e)
            return None

    def extract(self, source):
        """Extract tour details from HTML using selectorlib"""
        if source is None:
            return None
        try:
            extractor = selectorlib.Extractor.from_yaml_file("extract.yaml")  # Load selectors
            value = extractor.extract(source).get("tours")                     # Extract tour data
            return value                                                        # Return extracted value
        except Exception as e:
            log.error("Extraction failed: %s", e)
            return None


# ── Email sender ───────────────────────────────────────────────────────────────
class Email:

    def send(self, message):              # FIX: added self parameter
        """Send email notification using Gmail SMTP"""
        host = "smtp.gmail.com"           # Gmail SMTP server
        port = 465                        # SSL port
        context = ssl.create_default_context()  # Create SSL context

        try:
            # Connect securely to Gmail server and send mail
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                server.sendmail(EMAIL_USERNAME, EMAIL_RECEIVER, message)
            log.info("Email was sent!")   # Confirmation message
        except smtplib.SMTPException as e:
            log.error("Email failed: %s", e)


# ── Database ───────────────────────────────────────────────────────────────────
class Database:

    def __init__(self, db_path="Sham.db"):
        # Connect to SQLite database
        self.connection = sqlite3.connect(db_path)
        self._ensure_table()

    def _ensure_table(self):
        """Create the events table if it doesn't already exist."""
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                band TEXT,
                city TEXT,
                date TEXT
            )
        """)
        self.connection.commit()

    def _parse(self, extracted):
        """Parse a comma-separated event string into [band, city, date]."""
        parts = [item.strip() for item in extracted.split(",")]  # Remove extra spaces
        if len(parts) != 3:
            raise ValueError(f"Unexpected event format: {extracted!r}")
        return parts  # [band, city, date]

    def store(self, extracted):
        """Store new event details into the database"""
        row = self._parse(extracted)             # Parse extracted string
        cursor = self.connection.cursor()        # Create database cursor
        cursor.execute("INSERT INTO events VALUES(?,?,?)", row)  # Insert record
        self.connection.commit()                 # Save changes
        log.info("Stored new event: %s", row)

    def read(self, extracted):
        """Check if event already exists in the database"""
        band, city, date = self._parse(extracted)   # Unpack values
        cursor = self.connection.cursor()            # Create cursor
        # Select matching event from database
        cursor.execute(
            "SELECT * FROM events WHERE band=? AND city=? AND date=?",
            (band, city, date),
        )
        rows = cursor.fetchall()                 # Fetch all matching rows
        return rows                              # Return rows

    def close(self):
        """Close the database connection cleanly."""
        self.connection.close()


# ── Main loop ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Run the scraper continuously
    log.info("Tour scraper started. Checking every %ds.", SCRAPE_INTERVAL)

    event    = Event()
    database = Database()    # FIX: create once outside the loop
    email    = Email()

    try:
        while True:
            scraped   = event.scrape(URL)           # Get webpage HTML
            extracted = event.extract(scraped)      # Extract tour data
            log.info("Extracted: %s", extracted)    # Print extracted data

            # If a new tour is found
            if extracted and extracted != "No upcoming tours":
                row = database.read(extracted)      # Check if event exists
                if not row:                         # If event is new
                    database.store(extracted)       # Store in database

                    # Improved email format
                    email.send(f"Subject: New Event Alert\n\nNew event found:\n{extracted}")

            time.sleep(SCRAPE_INTERVAL)             # Wait before next check

    except KeyboardInterrupt:
        log.info("Scraper stopped by user.")
    finally:
        database.close()     # FIX: always close the DB on exit


# Step	Action
# 1	    Scrape website
# 2	    Extract event info
# 3	    Read DB → check if event already exists
# 4	    If not found → Insert into DB
# 5	    Send email
# 6	    Repeat