import helpers
from helpers import *
from config import EMAIL_CREDENTIALS, EA_EMAIL

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

import email
import imaplib
import sys
from time import sleep
import random
import requests
import csv
from csv import reader
from datetime import datetime


def getAllPlayerInfo(driver):
    players_on_page = driver.find_elements_by_tag_name("li.listFUTItem")
    page = driver.find_element(By.XPATH, "/html/body/main/section/section/div[1]/h1").text #page = self.driver.find_elements_by_tag_name("h1.title")

    playerdata = []
    playernumber = 1
    for card in players_on_page:
        bidstatus = card.get_attribute("class")
        cardinfo = card.text.splitlines()

        if (len(cardinfo) == 15):
            rating = cardinfo[0]
            name = cardinfo[2]
            startprice = 0
            curbid_or_finalsoldprice = 0
            buynow = 0
            time = 0

            rating = int(rating)
            # print("Location: TRANSFERLIST || Player Unlisted")
        else:
            rating = cardinfo[0]
            name = cardinfo[2]
            startprice = cardinfo[16]
            curbid_or_finalsoldprice = cardinfo[18]
            buynow = cardinfo[20]
            time = cardinfo[22]

            # clean rating
            rating = int(rating)

            # clean timeremaining
            seconds = 0
            if "<5" in time:
                seconds = 5
            elif "<10" in time:
                seconds = 10
            elif "<15" in time:
                seconds = 15
            elif "<30" in time:
                seconds = 30
            elif "1 Minute" in time:
                seconds = 60
            elif "Minutes" in time:
                time = time[:-8]
                time = int(time)
                time = 60*time
                seconds = time
            elif "Expired" in time:
                seconds = -5
            elif "Processing" in time:
                seconds = -5
            else:
                seconds = 60*65

            time = int(seconds)

            # clean startprice
            if "," in startprice:
                startprice = startprice.replace(",", "")

            startprice = int(startprice)

            # clean current bid or finalsoldprice
            if "---" in curbid_or_finalsoldprice:
                curbid_or_finalsoldprice = startprice-50
            elif "," in curbid_or_finalsoldprice:
                curbid_or_finalsoldprice = curbid_or_finalsoldprice.replace(",", "")

            curbid_or_finalsoldprice = int(curbid_or_finalsoldprice)

            # clean buy now
            if "," in buynow:
                buynow = buynow.replace(",", "")
            buynow = int(buynow)

        id = getPlayerIDFromTargets(name, rating)
#        print("player id from targets" + str(id))
        if (id == 0):
            id = getPlayerID(name, rating)
            print("ID not found in Targets, general id search found " + str(id))

        info = [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
        playerdata.append(info)

        # datetime object containing current date and time
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        dt_string = dt_string.split(" ")
        date = dt_string[0]
        currenttime = dt_string[1]

        with open(r'marketsearchdata.csv', 'a') as f:
            info = [date, currenttime, playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]

            writer = csv.writer(f)
            writer.writerow(info)
            # row[6] = buynow
            # row[7] = time
            # row[8] = id

        playernumber += 1

    return playerdata


def getAllPlayerInfoWatchlist(driver):
    players_on_page = driver.find_elements_by_tag_name("li.listFUTItem")
    page = driver.find_element(By.XPATH, "/html/body/main/section/section/div[1]/h1").text #page = self.driver.find_elements_by_tag_name("h1.title")

    playerdata = []
    playernumber = 1
    for card in players_on_page:
        # Only look at top 4 players
        if playernumber < 4:
            bidstatus = card.get_attribute("class")
            cardinfo = card.text.splitlines()

            if (len(cardinfo) == 15):
                rating = cardinfo[0]
                name = cardinfo[2]
                startprice = 0
                curbid_or_finalsoldprice = 0
                buynow = 0
                time = 0

                rating = int(rating)
                # print("Location: TRANSFERLIST || Player Unlisted")
            else:
                rating = cardinfo[0]
                name = cardinfo[2]
                startprice = cardinfo[16]
                curbid_or_finalsoldprice = cardinfo[18]
                buynow = cardinfo[20]
                time = cardinfo[22]

                # clean rating
                rating = int(rating)

                # clean timeremaining
                seconds = 0
                if "<5" in time:
                    seconds = 5
                elif "<10" in time:
                    seconds = 10
                elif "<15" in time:
                    seconds = 15
                elif "<30" in time:
                    seconds = 30
                elif "1 Minute" in time:
                    seconds = 60
                elif "Minutes" in time:
                    time = time[:-8]
                    time = int(time)
                    time = 60*time
                    seconds = time
                elif "Expired" in time:
                    seconds = -5
                elif "Processing" in time:
                    seconds = -5
                else:
                    print("weird, assume it is >1 hour")
                    seconds = 60*65

                time = int(seconds)

                # clean startprice
                if "," in startprice:
                    startprice = startprice.replace(",", "")

                startprice = int(startprice)

                # clean current bid or finalsoldprice
                if "---" in curbid_or_finalsoldprice:
                    curbid_or_finalsoldprice = startprice-50
                elif "," in curbid_or_finalsoldprice:
                    curbid_or_finalsoldprice = curbid_or_finalsoldprice.replace(",", "")

                curbid_or_finalsoldprice = int(curbid_or_finalsoldprice)

                # clean buy now
                if "," in buynow:
                    buynow = buynow.replace(",", "")
                buynow = int(buynow)

            id = getPlayerIDFromTargets(name, rating)
    #        print("player id from targets" + str(id))
            if (id == 0):
                id = getPlayerID(name, rating)
                print("ID not found in Targets, general id search found " + str(id))
            info = [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
            playerdata.append(info)
            playernumber += 1

    return playerdata


def makebids_currentpage(driver, name, futbinprice, bids_allowed, bids_made, futbindata):
    futbinprice = int(futbinprice)
    maxbidprice = round(futbinprice * .85)

    sleep(2)
    players_on_page = getAllPlayerInfo(driver)
    for card in players_on_page:
        # [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
        playernumber = card[0]
        bidStatus = card[1]
        curbid = card[5]
        timeremainingseconds = card[7]
        timeremainingmins = timeremainingseconds/60
        playerid = card[8]
        buynow = card[6]

        if (name == "AnyPlayer"):
            if bids_made < bids_allowed+1:
                for p in futbindata:
                    id = p[0]
                    id = int(id)
                    playerid = int(playerid)
                    diff = id - playerid

                    if (diff == 0):
                        price = p[3]
                        price = int(price)
                        # Bid on player if price is 300 less than futbin price
                        maxbidprice = price

                if curbid < 1300:
                    futbinprice = maxbidprice
                    # Make sure futbin price is at least 700 coins
                    if 700 < futbinprice:
                        # Check to see if we can make 300 or more coins
                        delta = futbinprice - curbid
                        buynow = int(buynow)
                        delta2 = buynow - curbid
                        # Check function isGoodSBCFodder ie bundes german etc
                        if (delta > 250) and (delta < 700) and (delta2 > 800):
                            print("Player " + str(card[3]) + " || " + str(card[2]) + " || Current bid: " + str(curbid) + " || Futbin Price: " + str(futbinprice) + " (Updated: idk mins ago) || DELTA: " + str(delta))
                            print("Bids made on " + str(name) + ": " + str(bids_made) + "/" + str(bids_allowed))
                            makebid_individualplayer(driver, playernumber, curbid)
                            bids_made += 1
        else:
            if bids_made < bids_allowed+1:
                if "highest-bid" not in bidStatus:
                    if timeremainingmins < 40:
                        if curbid <= maxbidprice:
                            makebid_individualplayer(driver, playernumber, curbid)
                            bids_made += 1
                            print("Bids made on " + str(name) + ": " + str(bids_made) + "/" + str(bids_allowed))

                    else:
                        print("Time remaining exceeded 40 minutes, RETURN")
                        return "Finished"
            else:
                print("Final Number of bids made on " + str(name) + ": " + str(bids_made) + "/" + str(bids_allowed))
                return "Finished"

    sleeptime = random.randint(3000, 5000)
    sleep(sleeptime/1000)
    print("Going to next page")
    driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]')
    driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]').click()

    makebids_currentpage(driver, name, futbinprice, bids_allowed, bids_made, futbindata)


def makebid_individualplayer(driver, playernumber, bidprice):
    originalbid = bidprice
    bidprice = bidprice + 50

    page = driver.find_element(By.XPATH, "/html/body/main/section/section/div[1]/h1").text #page = self.driver.find_elements_by_tag_name("h1.title")

    if page == "TRANSFER TARGETS":
        playerbutton = "/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li[" + str(playernumber) + "]/div"
    else:
        playerbutton = "/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(playernumber) + "]/div"

    driver.find_element_by_xpath(playerbutton)
    sleep(1)
    driver.find_element_by_xpath(playerbutton).click()
    sleep(1)


    bid_price_box = driver.find_element_by_css_selector('input.numericInput.filled')
    bid_price_box.click()
    bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
    bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
    bid_price_box.send_keys(bidprice)
    sleep(1)

    # Click make bid method
    if page == "TRANSFER TARGETS":
        driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/button[1]").click()
    else:
        driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/button[1]").click()


    if (page == "TRANSFER TARGETS"):
        curbidprice_afterbidding = driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[1]/div/div[2]/span[2]").text
        if "," in curbidprice_afterbidding:
            curbidprice_afterbidding = curbidprice_afterbidding.replace(",", "")
        curbidprice_afterbidding = int(curbidprice_afterbidding)

        diff = originalbid - curbidprice_afterbidding

        if (diff == 0):
            print("Bid did not go through! Will now return 0 and hopefully refresh. Original bid:" + str(originalbid) + "Current bid after bidding: " + str(curbidprice_afterbidding))
            return "Failure"
        else:
            print("Bid succesfully went through!")

    sleeptime = random.randint(3000, 5000)
    sleep(sleeptime/1000)


def makebid_individualplayerWatchlist(driver, playernumber, bidprice):
    originalbid = bidprice
    bidprice = bidprice + 50

    page = driver.find_element(By.XPATH, "/html/body/main/section/section/div[1]/h1").text #page = self.driver.find_elements_by_tag_name("h1.title")

    if page == "TRANSFER TARGETS":
        playerbutton = "/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li[" + str(playernumber) + "]/div"
    else:
        playerbutton = "/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(playernumber) + "]/div"

    driver.find_element_by_xpath(playerbutton)
    sleep(1)
    driver.find_element_by_xpath(playerbutton).click()
    sleep(1)

    sleep(1)

    try:
        bid_price_box = driver.find_element_by_css_selector('input.numericInput.filled')
        bid_price_box.click()
        bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        bid_price_box.send_keys(bidprice)
        sleep(1)

        # Click make bid method
        if page == "TRANSFER TARGETS":
            driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/button[1]").click()
        else:
            driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/button[1]").click()

    except:
        print("Bid method failed")

    if (page == "TRANSFER TARGETS"):
        sleep(1)
        curbidprice_afterbidding = driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[1]/div/div[2]/span[2]").text
        if "," in curbidprice_afterbidding:
            curbidprice_afterbidding = curbidprice_afterbidding.replace(",", "")
        curbidprice_afterbidding = int(curbidprice_afterbidding)

        diff = originalbid - curbidprice_afterbidding

        if (diff == 0):
            print("Bid did not go through! Will now return 0 and hopefully refresh. Original bid:" + str(originalbid) + "Current bid after bidding: " + str(curbidprice_afterbidding))
            return "Failure"
        else:
            print("Bid succesfully went through!")
            return "Success"
    sleep(1)


def go_to_tranfer_market_and_input_parameters(driver, playername):
    go_to_transfer_market(driver)

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'ut-player-search-control'))
    )
    wait_for_shield_invisibility(driver)

    # Insert player name into search
    driver.find_element(By.XPATH, '//div[contains(@class, "ut-player-search-control")]//input').click()
    sleep(random.randint(1,2))
    driver.find_element(By.XPATH, '//div[contains(@class, "ut-player-search-control")]//input').send_keys(playername)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//ul[contains(@class, "playerResultsList")]/button'))
    )

    sleep(1)

    fullplayername = driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul/button[1]/span[1]').text
    fullplayeroverall = driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul/button[1]/span[2]').text

    # Click player name (top result)
    driver.find_element(By.XPATH, '//ul[contains(@class, "playerResultsList")]/button').click()

    sleep(1)

    return fullplayername, fullplayeroverall


def go_to_tranfer_market_and_input_parameters_commongolds(driver, type, rarity):
    go_to_transfer_market(driver)

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'ut-player-search-control'))
    )
    wait_for_shield_invisibility(driver)

    sleep(2)

    # Click quality filter
    driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[2]/div/div').click()

    sleep(random.randint(3,7))

    if type == "Gold":
        # Click GOLD
        driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[2]/div/ul/li[4]').click()
    elif type == "Silver":
        # Click SILVER
        driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[2]/div/ul/li[3]').click()
    elif type == "Special":
        # Click SPECIAL
        driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[2]/div/ul/li[5]').click()

    sleep(2)

    # RARITY
    # Click rarity filter
    driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[3]/div/div').click()

    sleep(2)
    if rarity == "Common":
        driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[3]/div/ul/li[2]').click()
    elif rarity == "Rare":
        driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[3]/div/ul/li[3]').click()
    elif rarity == "TOTW":
        driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[3]/div/ul/li[4]').click()

    print("Sleeping for 20 seconds and will bid on any player")
    sleep(20)


def send_won_players_to_transferlist(driver):
    sleep(2.5)
    playersOnPage = driver.find_elements_by_tag_name("li.listFUTItem")

    playernumber = 1
    for player in playersOnPage:
        bidStatus = player.get_attribute("class")
        bidStatus = str(bidStatus)

        if "won" in bidStatus:
            # playerbutton = /html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div
            #playerbutton = "/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li[" + str(playernumber) + "]/div"

            # Click player
            player.click()

            sleep(1)

            # Send to transfer list
            driver.find_element_by_xpath("/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[3]/button[8]").click()
            send_won_players_to_transferlist(driver)
#        playernumber += 1


def refreshPageAndGoToWatchlist(driver):
    driver.refresh()

    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'icon-transfer'))
    )

    sleep(3)

    print("Refreshpage: going to watchlist")
    go_to_watchlist(driver)
    sleep(2)


# ~ ~ ~ ~ ~ Login Helpers ~ ~ ~


def login(driver, user):
    go_to_login_page(driver)

    sleep(1)
    driver.find_element(By.ID, 'email').send_keys(user["email"])
    sleep(1)
    driver.find_element(By.ID, 'password').send_keys(user["password"])
    sleep(1)
    driver.find_element(By.ID, 'btnLogin').click()
    sleep(1)


    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, 'btnSendCode'))
    ).click()

    access_code = get_access_code()

    driver.find_element(By.ID, 'oneTimeCode').send_keys(access_code)
    sleep(1)
    driver.find_element(By.ID, 'btnSubmit').click()

    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'icon-transfer'))
    )
    sleep(2)


def get_access_code():
    M = imaplib.IMAP4_SSL("imap.gmail.com")

    try:
        M.login(EMAIL_CREDENTIALS["email"], EMAIL_CREDENTIALS["password"])
    except imaplib.IMAP4.error:
        print("Login to email failed")
        sys.exit(1)

    print("Waiting for access code...")
    sleep(10)
    message_numbers_list = []
    message_numbers = []

    while not message_numbers_list:
        M.select()
        status, message_numbers = M.search(None, f'FROM "{EA_EMAIL}" UNSEEN')
        message_numbers_list = message_numbers[0].split()

    message_number = message_numbers[0].split()[0]
    _, msg = M.fetch(message_number, '(RFC822)')
    raw_email = msg[0][1].decode('utf-8')

    email_message = email.message_from_string(raw_email)

    print(email_message['Subject'])

    access_code = ''.join(filter(str.isdigit, email_message['Subject']))

    return access_code
