import src.mainhelpers
from src.mainhelpers import *

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

from time import sleep
import random
import requests
import csv
from csv import reader

import src.helpers
from src.helpers import *


def wait_for_shield_invisibility(driver, duration=0.25):
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((By.CLASS_NAME, 'ut-click-shield showing interaction'))
    )
    sleep(duration)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Getter methods ~ ~ ~ ~

def addPlayerToTargetList(playerid, cardname, cardoverall, futbinprice, lastupdated):
    with open(r'targetplayers.csv', 'a') as f:
        info = [playerid, cardname, cardoverall, futbinprice, lastupdated]

        writer = csv.writer(f)
        writer.writerow(info)


def getActualSellprice(id):
    with open('targetplayers_currentprices.csv', 'r') as read_obj:
        csv_reader = reader(read_obj)

        for player in csv_reader:
            playerid = player[0]
            price = player[1]

            diff = int(id) - int(playerid)

            print("inputID = " + str(id) + " || Cur ID in CSV: " + str(playerid) + " || DIFF = " + str(diff))
            if (diff == 0):
                price = int(price)
                return price
        return 0


def get_lowestbin_from_searchdata():
    #info = [date, time, playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]

    pricedata = []
    with open('marketsearchdata.csv', 'r') as read_obj:
        csv_reader = reader(read_obj)

        playerids = []
        for player in csv_reader:
            #name = player[5]
            id = player[10]
            #overall = player[4]
            if id not in playerids:
                if (id != 0):
                    playerids.append(id)

    for id in playerids:
        buynowprices = []
        with open('marketsearchdata.csv', 'r') as read_obj:
            # info = [date, currenttime, playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]

            csv_reader = reader(read_obj)
            for player in csv_reader:
                playername = player[5]
                marketid = player[10]
                overall = player[4]
                timeremainingSeconds = player[9]
                timeremainingSeconds = int(timeremainingSeconds)
                timeremainingMinutes = int(timeremainingSeconds/60)

                # ID match, ID not Zero (exclude IFs), less than 57 mins (exclude undercuts)
                if (id == marketid) and (id != 0) and (timeremainingMinutes < 58):
                    buynowprice = player[8]
                    buynowprice = int(buynowprice)
                    buynowprices.append(buynowprice)

            minimumbin = min(buynowprices)
            playername = getPlayerCardName(id)
            print(str(playername) + " min buy now: " + str(minimumbin))
            data = [id, minimumbin, playername]
            pricedata.append(data)

    with open(r'targetplayers_currentprices.csv', 'w') as f:
        writer = csv.writer(f)
        for row in pricedata:
            writer.writerow(row)

    print("Add a function that opens marketsearchdata as W to clear it for next run")


def clearOldSearchData():
    file = open("marketsearchdata.csv", "r+")
    file.truncate(0)
    file.close()


def getPlayerID(cardname, rating):
    with open('players2.csv', 'r') as read_obj:
        csv_reader = reader(read_obj)

        for player in csv_reader:
            card = player[0]
            firstname = player[1]
            lastname = player[2]
            playerrating = player[3]
            id = player[4]

            diff = int(rating) - int(playerrating)

            fullname = firstname + " " + lastname
            id = int(id)
            if (diff == 0):
                if (cardname == card):
                    # print("Found " + str(id))
                    return id
                if ((cardname == firstname) or (cardname == lastname)):
                    # print("Found " + str(id))
                    return id
                if (fullname == cardname):
                    return id
        return 0


# def getPlayerIDFast(cardname, rating):
#     # cardname on market is Rodriguez so it looks up rodriguez 78 and there's another guy w that last name and overall
#     # maybe have it use the ID from intitial search
#     #info = [playerid, cardname, cardoverall, futbinprice, lastupdated]
#     with open('targetplayers.csv', 'r') as read_obj:
#         csv_reader = reader(read_obj)
#
#         for player in csv_reader:
#             card = player[1]
#             playerrating = player[2]
#             id = player[0]
#
#             diff = int(rating) - int(playerrating)
#
#             id = int(id)
#             if (diff == 0):
#                 if (cardname == card):
#                     # print("Found " + str(id))
#                     return id
#         return 0

def getPlayerIDFromTargets(inputcardname, inputrating):
    # cardname on market is Rodriguez so it looks up rodriguez 78 and there's another guy w that last name and overall
    # maybe have it use the ID from intitial search
    #info = [playerid, cardname, cardoverall, futbinprice, lastupdated]
    with open('targetplayers.csv', 'r') as read_obj:
        csv_reader = reader(read_obj)

        for player in csv_reader:
            card = player[1]
            playerrating = player[2]
            id = player[0]

            # print("CARD in CSV:  " + str(card))
            # print("RTING in CSV: " + str(playerrating))
            # print("CARD input:   " + str(inputcardname))
            # print("RTING input:  " + str(inputrating))
            playerrating = int(playerrating)
            rating = int(inputrating)

            lastname = inputcardname
            ratingDiff = playerrating - rating
            if (ratingDiff == 0):
                if (lastname in card):
                    id = int(id)
                    return id

        print("ID from targets function still doesnt work")
        return 0


def getPlayerCardName(playerid):
    with open('players2.csv', 'r') as read_obj:
        csv_reader = reader(read_obj)
        for player in csv_reader:
            card = player[0]
            firstname = player[1]
            lastname = player[2]
            playerrating = player[3]
            id = player[4]

            id = int(id)
            playerid = int(playerid)
            diff = id - playerid
            if (diff == 0):
                if (card == ""):
                    return lastname
                else:
                    return card
        return "Not found"


def get_watchlist_size(driver):
    sleep(1.5)
    driver.find_element(By.XPATH, '/html/body/main/section/nav/button[3]').click()
    sleep(1.5)

    # driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]').click()
    # sleep(2)
    watchlist_size = driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[1]/span[1]').text
    watchlist_size = int(watchlist_size)
    sleep(1)
    return watchlist_size


def get_num_activebids(driver):
    players = driver.find_elements_by_tag_name("li.listFUTItem")

    playernumber = 1

    count = 0
    for player in players:
        bidStatus = player.get_attribute("class")
        if "highest-bid" in bidStatus:
            count+=1
        elif "outbid" in bidStatus:
            count+=1

    return count


def get_num_won(driver):
    players = driver.find_elements_by_tag_name("li.listFUTItem")

    playernumber = 1

    count = 0
    for player in players:
        bidStatus = player.get_attribute("class")
        if "won" in bidStatus:
            count+=1
    return count


def get_num_lost(driver):
    players = driver.find_elements_by_tag_name("li.listFUTItem")

    playernumber = 1

    count = 0
    for player in players:
        bidStatus = player.get_attribute("class")
        if "expired" in bidStatus:
            count+=1
    return count


def getWatchlistTransferlistSize(driver):
    sleep(3)
    driver.find_element(By.XPATH, '/html/body/main/section/nav/button[3]').click()
    sleep(3)

    transferlist_selling = driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[2]/span[2]').text
    transferlist_sold = driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[3]/span[2]').text
    transferlist_totalsize = driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[1]/span[1]').text

    watchlist_winning = driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[2]/span[2]').text
    watchlist_outbid = driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[3]/span[2]').text
    watchlist_totalsize = driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[1]/span[1]').text

    transferlist_selling = int(transferlist_selling)
    transferlist_sold = int(transferlist_sold)
    transferlist_totalsize = int(transferlist_totalsize)

    watchlist_winning = int(watchlist_winning)
    watchlist_outbid = int(watchlist_outbid)
    watchlist_totalsize = int(watchlist_totalsize)

    data = [watchlist_winning, watchlist_outbid, watchlist_totalsize, transferlist_selling, transferlist_sold, transferlist_totalsize]
    return data


def get_futbin_price_lastupdated(ID):
    r = requests.get('https://www.futbin.com/21/playerPrices?player={0}'.format(ID))
    # r = requests.get('https://www.futbin.com/20/playerGraph?type=daily_graph&year=20&player={0}'.format(ID))
    data = r.json()

    price = data[str(ID)]["prices"]["xbox"]["LCPrice"]
    lastupdated = data[str(ID)]["prices"]["xbox"]["updated"]

    # 18 mins ago
    # 48 mins ago
    # 1 hour ago
    # 2 hours ago
    if (lastupdated == "Never"):
        return 0, 100
    elif ("mins ago" in lastupdated):
        lastupdated = lastupdated[:-9]
        lastupdated = int(lastupdated)
    elif("hour ago" in lastupdated):
        lastupdated = lastupdated[:-9]
        lastupdated = int(lastupdated) * 60
    elif("hours ago" in lastupdated):
        lastupdated = lastupdated[:-10]
        lastupdated = int(lastupdated) * 60
    elif("seconds" in lastupdated):
        lastupdated = 1
    elif("second" in lastupdated):
        lastupdated = 1
    else:
        return 0, 100

    price = price.replace(",", "")
    price = int(price)

    # MINUTES
    lastupdated = int(lastupdated)
    #print("Futbin Price: " + str(price) + " || Last Updated: " + str(lastupdated))
    return price, lastupdated

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Navigation Methods ~ ~ ~ ~


def go_to_transfer_market(driver):
    driver.find_element(By.CLASS_NAME, 'icon-transfer').click()

    sleeptime = random.randint(1, 5)

    sleep(sleeptime)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'ut-tile-transfer-market'))
    )
    sleep(sleeptime)
    driver.find_element(By.CLASS_NAME, 'ut-tile-transfer-market').click()


def go_to_watchlist(driver):
    sleep(1.5)
    driver.find_element(By.XPATH, '/html/body/main/section/nav/button[3]').click()
    sleep(1.5)
    driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]').click()
    sleep(2)


def go_to_transferlist(driver):
    sleep(20)
    driver.find_element(By.XPATH, "/html/body/main/section/nav/button[3]").click()
    sleep(10)
    driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div[3]").click()
    sleep(10)


def go_to_login_page(driver):
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@class="ut-login-content"]//button'))
    )
    print("Logging in...")

    sleep(random.randint(5, 10))
    driver.find_element(By.XPATH, '//*[@class="ut-login-content"]//button').click()

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, 'email'))
    )


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Button Clicks ~ ~ ~ ~


def clearExpired(driver):
    sleep(1)
    driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div/section[4]/header/button').click()
    sleep(1)


def clickSearch(driver):
    sleep(1)
    driver.find_element(By.XPATH, '(//*[@class="button-container"]/button)[2]').click()


def clickBack(driver):
    sleep(1)
    driver.find_element(By.XPATH, '/html/body/main/section/section/div[1]/button[1]').click()
    sleep(1)
