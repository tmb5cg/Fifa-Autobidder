import importlib
import json
import os
import os.path
from os import path
import platform
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import ui
from selenium.webdriver.support.wait import WebDriverWait
import configparser
from datetime import datetime

def clearGUIstats():
    config = configparser.ConfigParser()
    config.read("./data/config.ini")
    user_settings_current_date = str(config.get("Other", "todays_date"))
    print("USER SETTINGS DATE: " + str(user_settings_current_date))

    today = datetime.today().strftime('%Y-%m-%d')
    today_str = str(today)
    print("TODAYS DATE: " + str(today))

    if (user_settings_current_date == today_str):
        print("Dates match - will not clear GUI statistics")
    else:
        print("Dates do not match - clearing GUI stats, setting date to day")

        # Set Date var to current date in file 
        config.read("./data/config.ini")
        config.set("Other","todays_date", today_str)
        with open('./data/config.ini', 'w') as configfile:
            config.write(configfile)

        # Reset GUI stats to 0 since it is new day
        config.read("./data/config.ini")
        val = "0"

        options = config.options("Statistics")
        for stat in options:
            cur_stat = config.set("Statistics", stat, val)

        with open('./data/config.ini', 'w') as configfile:
            config.write(configfile)
        
def checkStartupFiles():
    gui_logs_exists = path.exists("./data/gui_logs.txt")
    if not (gui_logs_exists):
        pathstr = os.path.abspath(__file__)
        pathstr = str(pathstr)

        slash = pathstr[-8]
        pathstr_new = pathstr[:-14]
        pathstr_new = pathstr_new + "data"

        save_path = pathstr_new
        file_name = "gui_logs.txt"

        completeName = os.path.join(save_path, file_name)
        print(completeName)
        file1 = open(completeName, "a+")
        file1.close()

    target_players_exists = path.exists("./data/target_players.txt")
    if not (target_players_exists):
        pathstr = os.path.abspath(__file__)
        pathstr = str(pathstr)

        slash = pathstr[-8]
        pathstr_new = pathstr[:-14]
        pathstr_new = pathstr_new + "data"

        save_path = pathstr_new
        file_name = "targetplayers.txt"

        completeName = os.path.join(save_path, file_name)
        file1 = open(completeName, "w")
        file1.close()

    logs_csv_exists = path.exists("./data/logs.csv")
    if not (logs_csv_exists):
        pathstr = os.path.abspath(__file__)
        pathstr = str(pathstr)

        slash = pathstr[-8]
        pathstr_new = pathstr[:-14]
        pathstr_new = pathstr_new + "data"

        save_path = pathstr_new
        file_name = "logs.csv"

        completeName = os.path.join(save_path, file_name)
        file1 = open(completeName, "w")
        file1.close()


def create_driver():
    system = platform.system()
    print("SYSTEM IS: " + str(system))
    if system == 'Darwin':
        path = 'chrome_mac/chromedriver'
    elif system == 'Linux':
        path = 'chrome_linux/chromedriver'
    elif system == 'Windows':
        path = os.getcwd() + '\chrome_windows\chromedriver.exe'

    options = webdriver.ChromeOptions()

    # For older ChromeDriver under version 79.0.3945.16
    options.add_argument("--ignore-certificate-error")
    options.add_argument("--ignore-ssl-errors")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)


    # For ChromeDriver version 79.0.3945.16 or over
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    # options.add_argument('--start-maximized')
    options.add_argument('--start-fullscreen')
    options.add_argument('--single-process')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--incognito")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("disable-infobars")

    driver = webdriver.Chrome(executable_path=path, options=options)
    driver.maximize_window()

    return driver