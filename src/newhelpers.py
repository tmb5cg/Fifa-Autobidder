from config import EMAIL_CREDENTIALS, EA_EMAIL
import helpers 
from helpers import log_event, wait_for_shield_invisibility
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

class Helper:
    def __init__(self, driver):
        self.driver = driver
        self.playerlist = []

        # Get input list of target players
        src = "./data/player_list.txt"
        txt = open(src, "r", encoding="utf8")

        for aline in txt:
            values = aline.strip("\n").split(",")
            self.playerlist.append(values)
        txt.close()

    # Action: evaluates transfer list, watchlist size etc
    # Returns: number of cards able to bid on, depending on input list size
    def getWatchlistTransferlistSize(self):

        sleep(1)
        self.driver.find_element(By.XPATH, '/html/body/main/section/nav/button[3]').click()
        sleep(1)

        transferlist_selling = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[2]/span[2]').text
        transferlist_sold = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[3]/span[2]').text
        transferlist_totalsize = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[1]/span[1]').text

        watchlist_winning = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[2]/span[2]').text
        watchlist_outbid = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[3]/span[2]').text
        watchlist_totalsize = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[1]/span[1]').text

        num_coins = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[1]/div[1]/div[1]').text

        transferlist_selling = int(transferlist_selling)
        transferlist_sold = int(transferlist_sold)
        transferlist_totalsize = int(transferlist_totalsize)

        watchlist_winning = int(watchlist_winning)
        watchlist_outbid = int(watchlist_outbid)
        watchlist_totalsize = int(watchlist_totalsize)

        data = [watchlist_winning, watchlist_outbid, watchlist_totalsize, transferlist_selling, transferlist_sold, transferlist_totalsize, num_coins]

        # Log data for display in GUI - remove old data first
        file = open("./data/user_stats.txt", "r+")
        file.truncate(0)
        file.close()

        full_entry = ""
        for word in data:
            word = str(word)
            word_comma = word + ","
            full_entry += word_comma

        # Remove last comma
        full_entry = full_entry[:-1]
        log_event("Current state: " + str(full_entry))

        # Add new line to end
        hs = open("./data/user_stats.txt", "a", encoding="utf8")
        hs.write(full_entry + "\n")
        hs.close()

        num_players_to_bid_on = len(self.playerlist)

        if (num_players_to_bid_on != 1):
            bidsallowed = 50 - data[2]
            bidstomake_eachplayer = round(bidsallowed/num_players_to_bid_on) - 1
        elif (num_players_to_bid_on == 1):
            bidsallowed = 50 - data[2]
            bidstomake_eachplayer = bidsallowed
        else:
            bidsallowed = 0
            bidstomake_eachplayer = 0
            log_event("Error fetching watchlist / TList size")

        

        log_event("Bid to make on each player: " + str(bidstomake_eachplayer))
        return bidsallowed, bidstomake_eachplayer

    # Action: clicks player to search market from dropdwon by evaluating results ie there are many "Rodriguez" cards
    def go_to_tranfer_market_and_input_parameters(self, cardname, fullname, cardoverall):
        cardname = cardname.lower()
        fullname = fullname.lower()

        # Go to transfer market 
        self.driver.find_element(By.CLASS_NAME, 'icon-transfer').click()
        sleep(1)
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'ut-tile-transfer-market'))
        )
        sleep(1)
        self.driver.find_element(By.CLASS_NAME, 'ut-tile-transfer-market').click()

        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'ut-player-search-control'))
        )
        wait_for_shield_invisibility(self.driver)

        # Insert player name into search
        self.driver.find_element(By.XPATH, '//div[contains(@class, "ut-player-search-control")]//input').click()
        sleep(random.randint(1,2))
        self.driver.find_element(By.XPATH, '//div[contains(@class, "ut-player-search-control")]//input').send_keys(cardname)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//ul[contains(@class, "playerResultsList")]/button'))
        )

        # Player list dropdown is visible now, so we must  /html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul
        results_list = self.driver.find_elements_by_xpath('//ul[contains(@class, "playerResultsList")]/button')
        num_results = len(results_list)
        # log_event("NUMBER OF RESULTS FOR ANGEL " + str(num_results))
        # log_event("should be 5")

        result_to_click = 1
        for x in range(num_results):
            x+=1
            playername = self.driver.find_element_by_xpath("/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul/button[" + str(x) + "]/span[1]").text
            playeroverall = self.driver.find_element_by_xpath("/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul/button[" + str(x) + "]/span[2]").text

            playername = str(playername)
            playername = playername.lower()

            playeroverall = int(playeroverall)
            target_overall = int(cardoverall)

            diff = playeroverall - target_overall

            if (diff == 0):
                if (playername == cardname):
                    result_to_click = x
                if (playername == fullname):
                    result_to_click = x

        log_event("waiting a sec Should click result number: " + str(result_to_click))
        sleep(1)
        self.driver.find_element_by_xpath("/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul/button[" + str(result_to_click) + "]").click()

    # Action: Evaluates current market page, calls makebid_individualplayer to make bids
    def bid_on_current_page(self, name, futbinprice, bids_allowed, bids_made, futbindata):
        futbinprice = int(futbinprice)
        maxbidprice = round(futbinprice * .85)

        sleep(2)
        players_on_page = self.getAllPlayerInfo()
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
                                log_event("Player " + str(card[3]) + " || " + str(card[2]) + " || Current bid: " + str(curbid) + " || Futbin Price: " + str(futbinprice) + " (Updated: idk mins ago) || DELTA: " + str(delta))
                                log_event("Bids made on " + str(name) + ": " + str(bids_made) + "/" + str(bids_allowed))
                                makebid_individualplayer(playernumber, curbid)
                                bids_made += 1
            else:
                if bids_made < bids_allowed+1:
                    if "highest-bid" not in bidStatus:
                        if timeremainingmins < 40:
                            if timeremainingmins > 3:
                                if curbid <= maxbidprice:
                                    self.makebid_individualplayer(playernumber, curbid)
                                    bids_made += 1
                                    log_event("Bids made on " + str(name) + ": " + str(bids_made) + "/" + str(bids_allowed))

                        else:
                            log_event("Time remaining of players on page exceeded 40 minutes, RETURN")
                            return "Finished"
                else:
                    log_event("Final Number of bids made on " + str(name) + ": " + str(bids_made) + "/" + str(bids_allowed))
                    return "Finished"

        sleeptime = random.randint(3000, 5000)
        sleep(sleeptime/1000)
        log_event("Going to next page")
        self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]')
        self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]').click()

        self.bid_on_current_page(name, futbinprice, bids_allowed, bids_made, futbindata)

    # Action: Bids on player
    def makebid_individualplayer(self, playernumber, bidprice):
        originalbid = bidprice
        bidprice = bidprice + 50

        page = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[1]/h1").text #page = self.driver.find_elements_by_tag_name("h1.title")

        if page == "TRANSFER TARGETS":
            playerbutton = "/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li[" + str(playernumber) + "]/div"
        else:
            playerbutton = "/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(playernumber) + "]/div"

        self.driver.find_element_by_xpath(playerbutton)
        sleep(1)
        self.driver.find_element_by_xpath(playerbutton).click()
        sleep(1)


        bid_price_box = self.driver.find_element_by_css_selector('input.numericInput.filled')
        bid_price_box.click()
        bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        bid_price_box.send_keys(bidprice)
        sleep(1)

        # Click make bid method
        if page == "TRANSFER TARGETS":
            self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/button[1]").click()
        else:
            self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/button[1]").click()


        if (page == "TRANSFER TARGETS"):
            curbidprice_afterbidding = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[1]/div/div[2]/span[2]").text
            if "," in curbidprice_afterbidding:
                curbidprice_afterbidding = curbidprice_afterbidding.replace(",", "")
            curbidprice_afterbidding = int(curbidprice_afterbidding)

            diff = originalbid - curbidprice_afterbidding

            if (diff == 0):
                log_event("Bid did not go through! Will now return 0 and hopefully refresh. Original bid:" + str(originalbid) + "Current bid after bidding: " + str(curbidprice_afterbidding))
                return "Failure"
            else:
                log_event("Bid succesfully went through!")

        sleeptime = random.randint(3000, 5000)
        sleep(sleeptime/1000)

    # Action: Logs all data on current page of market
    def getAllPlayerInfo(self):
        players_on_page = self.driver.find_elements_by_tag_name("li.listFUTItem")
        page = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[1]/h1").text #page = self.driver.find_elements_by_tag_name("h1.title")

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

            id = self.getPlayerID(name, rating)
            # if (id == 0):
            #     id = getPlayerID(name, rating)
            #     print("ID not found in Targets, general id search found " + str(id))

            info = [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
            playerdata.append(info)

            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            dt_string = dt_string.split(" ")
            date = dt_string[0]
            currenttime = dt_string[1]

            agg = [date, currenttime, playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]

            full_entry = ""
            for word in agg:
                word = str(word)
                word_comma = word + ","
                full_entry += word_comma

            # Remove last comma
            full_entry = full_entry[:-1]
            print(full_entry)

            # Add new line to end
            hs = open("./data/market_logs.txt", "a", encoding="utf8")
            hs.write(full_entry + "\n")
            hs.close()

            # with open(r'./marketsearchdata.csv', 'a', encoding="utf8") as f:
            #     info = [date, currenttime, playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]

            #     writer = csv.writer(f)
            #     writer.writerow(info)
            #     # row[6] = buynow
            #     # row[7] = time
            #     # row[8] = id

            playernumber += 1

        return playerdata

    # Action: Retrieves player internal ID from name and rating
    def getPlayerID(self, cardname, rating):
        with open('./data/players_database.csv', 'r', encoding="utf8") as read_obj:
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

            # If not found, raise error
            log_event("Player ID not found for: " + str(cardname) + " " + str(rating))
            return 0

    # Action: Parses market logs from searches to find accurate sell price, and updates player_list.txt
    def get_lowestbin_from_searchdata(self):
        #info = [date, time, playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]

        # Get target players IDs
        playerids = []
        txt = open("./data/player_list.txt", "r", encoding="utf8")
        for aline in txt:
            values2 = aline.strip("\n").split(",")
            id = values2[7]
            playerids.append(id)
        txt.close()

        # Find cheapest listing from market data
        id_and_lowest_bin = [] # this will hold (id, lowest bin)
        for playerid in playerids:
            playerid = int(playerid)
            buynowprices = []

            txt = open("./data/market_logs.txt", "r", encoding="utf8")
            for aline in txt:
                player = aline.strip("\n").split(",")
                playername = player[5]
                marketid = int(player[10])
                overall = player[4]
                timeremainingSeconds = player[9]
                timeremainingSeconds = int(timeremainingSeconds)
                timeremainingMinutes = int(timeremainingSeconds/60)

                # print(marketid)
                # ID match, ID not Zero (exclude IFs), less than 57 mins (exclude undercuts)
                if (playerid == marketid) and (playerid != 0) and (timeremainingMinutes < 58):
                    buynowprice = player[8]
                    buynowprice = int(buynowprice)
                    buynowprices.append(buynowprice)

            try:
                minimumbin = min(buynowprices)
            except:
                # log_event("ID mismatch -- minimum bin price array was empty")
                minimumbin = 0
            playername = self.getPlayerCardName(playerid)

            log_event(str(playername) + " min buy now from market data: " + str(minimumbin))
            # Now we have player ID, and their lowest bin -- update it on GUI
            data = [playerid, minimumbin]
            id_and_lowest_bin.append(data)

        # agg = [name, cardname, rating, team, nation, cardtype, position, internal_id, futbin_id, price, lastupdated]
        # columns = ["Name", "Card name", "Rating", "Team", "Nation", "Type", "Position", "Internal ID", "Futbin ID", "Futbin Price", "Futbin LastUpdated", "Actual Market Price"]

        txt = open("./data/player_list.txt", "r", encoding="utf8")

        playerlist = []
        for aline in txt:
            values2 = aline.strip("\n").split(",")
            playerlist.append(values2)

        # Now that playerlist is saved in temp memory, clear the old user input list
        hs = open("./data/player_list.txt", "r+", encoding="utf8")
        hs.truncate(0)
        hs.close()

        # This is a terribly inefficient way of updating the GUI's playerlist with the market price. Its a first draft 
        for entry in playerlist:
            entryid = int(entry[7])
            new_updated_actual_price = 0
            for x in id_and_lowest_bin:
                id = int(x[0])
                price = x[1]
                diff = entryid - id
                if (diff == 0):
                    # print("got here")
                    new_updated_actual_price = price

            # print(new_updated_actual_price)
            full_entry = ""
            count = 0
            for word in entry:
                if (count == 11):
                    word = new_updated_actual_price
                word = str(word)
                word_comma = word + ","
                full_entry += word_comma
                count+=1

            # Remove last comma
            full_entry = full_entry[:-1]

            # Add new line to end
            hs = open("./data/player_list.txt", "a", encoding="utf8")
            hs.write(full_entry + "\n")
            hs.close()

    # Action: clears old market search data logs
    def clearOldSearchData():
        hs = open("./data/market_logs.txt", "r+", encoding="utf8")
        hs.truncate(0)
        hs.close()

    # Returns: player card name based on ID
    def getPlayerCardName(self, playerid):
        with open('./data/players_database.csv', 'r', encoding="utf8") as read_obj:
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

    # Action: sends won players to transfer list 
    def send_won_players_to_transferlist(self):
        sleep(1)
        playersOnPage = self.driver.find_elements_by_tag_name("li.listFUTItem")

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
                self.driver.find_element_by_xpath("/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[3]/button[8]").click()
                self.send_won_players_to_transferlist()

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
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Button clicks

    def clearExpired(self):
        sleep(1)
        self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div/section[4]/header/button').click()
        sleep(1)

    def clickSearch(self):
        sleep(1)
        self.driver.find_element(By.XPATH, '(//*[@class="button-container"]/button)[2]').click()

    def clickBack(self):
        sleep(1)
        self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[1]/button[1]').click()
        sleep(1)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Navigation


def go_to_transfer_market(self):
    self.driver.find_element(By.CLASS_NAME, 'icon-transfer').click()

    sleeptime = random.randint(1, 5)

    sleep(sleeptime)
    WebDriverWait(self.driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'ut-tile-transfer-market'))
    )
    sleep(sleeptime)
    self.driver.find_element(By.CLASS_NAME, 'ut-tile-transfer-market').click()


def go_to_watchlist(self):
    sleep(1.5)
    self.driver.find_element(By.XPATH, '/html/body/main/section/nav/button[3]').click()
    sleep(1.5)
    self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]').click()
    sleep(2)


def go_to_transferlist(self):
    sleep(20)
    self.driver.find_element(By.XPATH, "/html/body/main/section/nav/button[3]").click()
    sleep(10)
    self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div[3]").click()
    sleep(10)


def go_to_login_page(self):
    WebDriverWait(self.driver, 15).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@class="ut-login-content"]//button'))
    )
    print("Logging in...")

    sleep(random.randint(5, 10))
    self.driver.find_element(By.XPATH, '//*[@class="ut-login-content"]//button').click()

    WebDriverWait(self.driver, 10).until(
        EC.visibility_of_element_located((By.ID, 'email'))
    )
