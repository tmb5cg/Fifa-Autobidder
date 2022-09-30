import configparser
from datetime import datetime
import json
import os
from os import path
import platform
import random
import re
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException)
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import ui
from selenium.webdriver.support.wait import WebDriverWait
import undetected_chromedriver as uc


def log_event(queue, event, bidroundOver=False):
    """
    Sends log to queue, which GUI handles and writes to txt file for display on GUI.
    The queue objects allows us to talk to the GUI from a separate threads, which is cool.
    This was a big breakthrough in functionality.

    Parameters:
        queue (queue): GUI's queue object
        event (str): Event log to write to data/output.txt
    """
    event = str(event)

    combined = [event, bidroundOver]
    queue.put(combined)


def getFilters(url):
    webapp_options = ['quality', 'rarity',
                      'league', 'club', 'country', 'position']
    futbin_options = ['league', 'nation', 'club', 'version', 'position']

    full_data = ""

    # Opening JSON file
    with open('./data/futbin_decoder.json') as json_file:
        data = json.load(json_file)
        full_data = data

    txt = url
    results = re.findall("[^&?]*?=[^&?]*", txt)

    webapp_filters_output = {}
    if results:
        for i in results:
            temp = i.split("=")

            param = temp[0]
            value = temp[1]
            param = param.strip()
            value = value.strip()

            # Extract valid futbin paramters
            if param in futbin_options:
                try:
                    if (param == "nation"):
                        param = "country"
                    full_data[param]
                    try:
                        output = full_data[param][value]

                        if (param != "version"):
                            webapp_filters_output[param] = output[param]
                        else:
                            webapp_filters_output["quality"] = output['quality']
                            webapp_filters_output["rarity"] = output['rarity']
                    except:
                        continue
                except:
                    continue
    else:
        print("No match")

    total_filters = len(webapp_filters_output)
    return webapp_filters_output


def create_driver():
    system = platform.system()
    # print("SYSTEM IS: " + str(system))
    if system == 'Darwin':
        path = 'chrome_mac/chromedriver'
    elif system == 'Linux':
        path = 'chrome_linux/chromedriver'
    elif system == 'Windows':
        path = os.getcwd() + '\chrome_windows\chromedriver.exe'

    # Shoutout to the dev who created this
    use_undetected_chromedriver = True
    if use_undetected_chromedriver:
        options = uc.ChromeOptions()

        options.add_argument('--profile-directory=Profile 8')
        options.add_argument('--disable-popup-blocking')  # allow for new tab
        # options.add_extension("adblocker/uBlock-Origin.crx")

        driver = uc.Chrome(options=options)
        return driver

    else:
        options = webdriver.ChromeOptions()

        # For older ChromeDriver under version 79.0.3945.16
        options.add_argument("--ignore-certificate-error")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Stop annoying windows logs
        options.add_argument('--disable-logging')
        options.add_argument("--log-level=3")

        driver = webdriver.Chrome(executable_path=path, options=options)

        return driver


def setup_adblock(driver):
    driver.execute_script(
        "alert('Install Adblocker after accepting this prompt. Without Adblocker, FUTBIN fetch will break (way too many advertisements). After 10 seconds, bot will automatically go to Webapp. ');")

    alert_present = True
    while alert_present:
        try:
            alert_present = WebDriverWait(driver, 1).until(
                EC.alert_is_present(), 'Alert is gone')

        except Exception as e:
            # Alert is gone, now install adblock
            alert_present = False
            try:
                driver.get(
                    "https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm?hl=en")
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.XPATH, "/html/body/div[5]/div[2]/div/div/div[2]/div[2]/div/div/div/div")))
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[5]/div[2]/div/div/div[2]/div[2]/div/div/div/div"))).click()

            except Exception as e:
                # print("User broke futbin fetch, self.botRunning false")
                print("Issue installing adblocker, please install manually")
                driver.switch_to.window(driver.window_handles[0])

            driver.switch_to.window(driver.window_handles[0])

    sleep(14)
    # installing = True
    # infiniteCounter = 0
    # while installing:
    #     try:
    #         elements = "/html/body/div[3]/div[2]/div/div/div[2]"
    #         page_content = driver.find_elements(By.XPATH, elements)

    #         for elem in page_content:
    #             text = str(elem.text)
    #             text = text.strip()
    #             # print(text)
    #             lowered = text.lower()
    #             if (text == "Remove from Chrome"):
    #                 installing = False

    #             if (lowered == "remove from chrome"):
    #                 installing = False

    #             if "remove" in lowered:
    #                 installing = False
    #                 break

    #     except:
    #         infiniteCounter += 1
    #         if infiniteCounter > 10:
    #             print("Issue installing adblocker, restart bot")
    #             break

    driver.get("https://www.ea.com/fifa/ultimate-team/web-app/")


def login(queue, driver, user):
    try:
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//*[@class="ut-login-content"]//button'))
        )

        sleep(random.randint(2, 4))
        driver.find_element(
            By.XPATH, '//*[@class="ut-login-content"]//button').click()

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'email'))
        )

        sleep(1)
        driver.find_element(By.ID, 'email').send_keys(user["email"])
        sleep(1)
        driver.find_element(By.ID, 'password').send_keys(user["password"])
        sleep(1)
        driver.find_element(
            By.XPATH, '/html/body/div[1]/div[2]/section/div[1]/form/div[6]/a').click()
        sleep(3)

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div/form/div/section/a[2]'))
        ).click()

        log_event(queue, "Continue login manually")
    except:
        log_event(queue, "Continue login manually")


def clearGUIstats():
    config = configparser.ConfigParser()
    config.read("./data/settings.ini")
    user_settings_current_date = str(config.get("Other", "todays_date"))

    today = datetime.today().strftime('%Y-%m-%d')
    today_str = str(today)

    if (user_settings_current_date != today_str):
        # Set Date var to current date in file
        config.read("./data/settings.ini")
        config.set("Other", "todays_date", today_str)
        with open("./data/settings.ini", 'w') as configfile:
            config.write(configfile)

        # Reset GUI stats to 0 since it is new day
        config.read("./data/settings.ini")
        val = "0"

        options = config.options("Statistics")
        for stat in options:
            cur_stat = config.set("Statistics", stat, val)

        with open("./data/settings.ini", 'w') as configfile:
            config.write(configfile)


def checkStartupFiles():
    gui_logs_exists = os.path.exists("./data/output.txt")
    if not (gui_logs_exists):
        pathstr = os.path.abspath(__file__)
        pathstr = str(pathstr)

        slash = pathstr[-8]
        pathstr_new = pathstr[:-14]
        pathstr_new = pathstr_new + "data"

        save_path = pathstr_new
        file_name = "output.txt"

        completeName = os.path.join(save_path, file_name)
        print(completeName)
        file1 = open(completeName, "a+")
        file1.close()

    target_players_exists = os.path.exists("./data/targetplayers.txt")
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

    logs_csv_exists = os.path.exists("./data/logs.csv")
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
