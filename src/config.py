from selenium import webdriver
import platform
import os
from selenium.webdriver.support import ui
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ChromeOptions, Chrome

def create_driver():
    system = platform.system()

    if system == 'Darwin':
        path = 'chrome_mac/chromedriver'
    elif system == 'Linux':
        path = 'chrome_linux/chromedriver'
    elif system == 'Windows':
        path = os.getcwd() + '\chrome_windows\chromedriver.exe'

    option = webdriver.ChromeOptions()


    # Removes navigator.webdriver flag

    # For older ChromeDriver under version 79.0.3945.16
    option.add_argument("--ignore-certificate-error")
    option.add_argument("--ignore-ssl-errors")
    option.add_experimental_option("excludeSwitches", ["enable-automation"])
    option.add_experimental_option('useAutomationExtension', False)

    # For ChromeDriver version 79.0.3945.16 or over
    option.add_argument('--disable-blink-features=AutomationControlled')

    # driver = webdriver.Chrome(
    #     executable_path=path,
    #     options=option
    # )

    driver = webdriver.Chrome(executable_path=path, options=option)
    driver.maximize_window()

    return driver


URL = "https://www.ea.com/fifa/ultimate-team/web-app/"

EA_EMAIL = "EA@e.ea.com"

txt = open("./data/logins.txt", "r")
counter = 0
credentials = []
for aline in txt:
    counter += 1
    line = aline.strip("\n")
    credentials.append(str(line))
txt.close()

USER = {
    "email": credentials[0],
    "password": credentials[1],
}

EMAIL_CREDENTIALS = {
    "email": credentials[2],
    "password": credentials[3],
}
