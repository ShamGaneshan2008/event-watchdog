from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import sqlite3
import time

URL = "https://programmer100.pythonanywhere.com/"

# Connect to database
connection = sqlite3.connect("temperature.db")
cursor = connection.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS temperature (
    date TEXT,
    value TEXT
)
""")
connection.commit()

def scrape():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # run without opening browser

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get(URL)
    time.sleep(3)  # wait for JS to load

    temp = driver.find_element(By.ID, "displaytimer").text
    driver.quit()
    return temp

def store(temp):
    time_now = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
    cursor.execute(
        "INSERT INTO temperature VALUES (?, ?)",
        (time_now, temp)
    )
    connection.commit()

if __name__ == "__main__":
    temperature = scrape()
    print("Temperature:", temperature)
    store(temperature)
