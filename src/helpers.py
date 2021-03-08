import csv
import email
import imaplib
import json
import os
import platform
import random
import sys
from csv import reader
from datetime import datetime
from time import sleep

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.common.exceptions import NoSuchElementException        
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import ui
from selenium.webdriver.support.wait import WebDriverWait

class Helper:
    def __init__(self, driver):
        self.driver = driver

        # Global sell and buy ceilings to be captured from UI
        self.sellceiling = .95
        self.priceceiling = .95

        # Current state user variables
        self.user_num_target_players = 0
        self.user_num_bids_each_target = 0
        self.user_requests_made = 0
        self.user_bids_made = 0
        self.user_transferlist_size = 0
        self.user_activebids = 0
        self.user_num_coins = 0        
        self.user_players_won = 0
        self.user_projected_profit = 0
        self.user_actual_profit = 0

        self.user_watchlist_winning = 0
        self.user_watchlist_outbid = 0
        self.user_watchlist_totalsize = 0
        self.user_transferlist_selling = 0
        self.user_transferlist_sold = 0
        self.user_transferlist_totalsize = 0
        self.user_start_coins = 0
        self.user_watchlist_expired = 0

        self.user_sum_of_all_current_bids_on_watchlist = 0

        self.sleeptime_between_rounds = 0

        self.conserve_bids, self.sleep_time, self.botspeed = self.getUserConfig()

    # Action: evaluates transfer list, watchlist size etc
    # Returns: number of cards able to bid on, depending on input list size
    def getWatchlistTransferlistSize(self):
        try:
            # Click Transfer Market tab
            self.sleep_approx(1)
            self.driver.find_element(By.XPATH, '/html/body/main/section/nav/button[3]').click()
            self.sleep_approx(1)

            transferlist_selling = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[2]/span[2]').text
            transferlist_sold = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[3]/span[2]').text
            transferlist_totalsize = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[1]/span[1]').text

            watchlist_winning = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[2]/span[2]').text
            watchlist_outbid = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[3]/span[2]').text
            watchlist_totalsize = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[1]/span[1]').text

            num_coins = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[1]/div[1]/div[1]').text

            self.user_transferlist_selling = int(transferlist_selling)
            self.user_transferlist_sold = int(transferlist_sold)
            self.user_transferlist_totalsize = int(transferlist_totalsize)

            self.user_watchlist_winning = int(watchlist_winning)
            self.user_watchlist_outbid = int(watchlist_outbid)
            self.user_watchlist_totalsize = int(watchlist_totalsize)

            self.user_num_coins = str(num_coins)

            data = [self.user_watchlist_winning, self.user_watchlist_outbid, self.user_watchlist_totalsize, self.user_transferlist_selling, self.user_transferlist_sold, self.user_transferlist_totalsize, num_coins]

            playerlist = self.getPlayerListFromGUI()
            num_players_to_bid_on = len(playerlist)
            self.user_num_target_players = num_players_to_bid_on

            if (num_players_to_bid_on != 1):
                bidsallowed = 50 - int(data[2])
                bidstomake_eachplayer = round(bidsallowed/num_players_to_bid_on) - 1

                self.user_num_bids_each_target = bidstomake_eachplayer
            elif (num_players_to_bid_on == 1):
                bidsallowed = 50 - int(data[2])
                bidstomake_eachplayer = bidsallowed

                self.user_num_bids_each_target = bidstomake_eachplayer
            else:
                bidsallowed = 0
                bidstomake_eachplayer = 0
                log_event("Error fetching watchlist / TList size")

            

            log_event("Bid to make on each player: " + str(bidstomake_eachplayer))
            return bidsallowed, bidstomake_eachplayer
        except:
            log_event("Exception getWatchlistTransferlistSize")
            log_event("Restart bot")
            # self.getWatchlistTransferlistSize()

    # Action: clicks player to search market from dropdwon by evaluating results ie there are many "Rodriguez" cards
    def go_to_tranfer_market_and_input_parameters(self, cardname, fullname, cardoverall):
        try:
            cardname = cardname.lower()
            fullname = fullname.lower()

            # Go to transfer market 
            self.driver.find_element(By.CLASS_NAME, 'icon-transfer').click()
            self.sleep_approx(1)
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'ut-tile-transfer-market'))
            )
            self.sleep_approx(1)
            self.driver.find_element(By.CLASS_NAME, 'ut-tile-transfer-market').click()

            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'ut-player-search-control'))
            )
            wait_for_shield_invisibility(self.driver)

            # Insert player name into search
            self.driver.find_element(By.XPATH, '//div[contains(@class, "ut-player-search-control")]//input').click()
            self.sleep_approx(2)
            self.driver.find_element(By.XPATH, '//div[contains(@class, "ut-player-search-control")]//input').send_keys(cardname)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//ul[contains(@class, "playerResultsList")]/button'))
            )

            # Player list dropdown is visible now, so we must  /html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul
            results_list = self.driver.find_elements_by_xpath('//ul[contains(@class, "playerResultsList")]/button')
            num_results = len(results_list)

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

            # log_event("waiting a sec Should click result number: " + str(result_to_click))
            self.sleep_approx(1)
            self.driver.find_element_by_xpath("/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul/button[" + str(result_to_click) + "]").click()
        except:
            log_event("Exception go_to_transfer_market_and_input_parameters")
            return "error"
            # self.go_to_tranfer_market_and_input_parameters(cardname, fullname, cardoverall)

    # Action: Evaluates current market page, calls makebid_individualplayer to make bids
    # TODO: Make this nonrecursive and any other methods
    def bid_on_current_page(self, name, futbinprice, bids_allowed, bids_made, futbindata):
        keepgoing = True
        while keepgoing:
            # Each page, get user config
            self.conserve_bids, self.sleep_time, self.botspeed = self.getUserConfig()
            status = self.checkState("transfermarket")
            if status:
                futbinprice = int(futbinprice)
                maxbidprice = round(futbinprice * .85)

                self.sleep_approx(2)
                players_on_page = self.getAllPlayerInfo()
                for card in players_on_page:
                    playernumber = card[0]
                    bidStatus = card[1]
                    curbid = card[5]
                    timeremainingseconds = card[7]
                    timeremainingmins = timeremainingseconds/60
                    playerid = card[8]
                    buynow = card[6]

                    if bids_made < bids_allowed+1:
                        if "highest-bid" not in bidStatus:
                            #TODO make this config variable
                            if timeremainingmins < 30:
                                if timeremainingmins > 2:
                                    if curbid <= maxbidprice:
                                        if (self.conserve_bids == 1):
                                            # print("conserve bids is ON - bid .7")
                                            # *.85 and *.9 = .765
                                            bid_to_make = maxbidprice * .9
                                            bid_to_make = round(bid_to_make)
                                        else:
                                            # print("conserve bids is OFF - bid small")
                                            bid_to_make = curbid
                                        
                                        self.makebid_individualplayer(playernumber, bid_to_make)
                                        bids_made += 1
                                        log_event("Bids made on " + str(name) + ": " + str(bids_made) + "/" + str(bids_allowed))

                            else:
                                keepgoing = False
                    else:
                        keepgoing = False

                self.sleep_approx(3)
                log_event("Going to next page")
                try:
                    self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]')
                    self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]').click()
                    self.user_requests_made += 1
                except:
                    log_event("No next page found, returning")
                    keepgoing = False
        log_event("Finished bidding on: " + str(name))

    # Action: Bids on player during initial market search
    def makebid_individualplayer(self, playernumber, bidprice):
        status = self.checkState("transfermarket")
        if status:
            try:
                originalbid = bidprice
                bidprice = bidprice + 50

                page = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[1]/h1").text #page = self.driver.find_elements_by_tag_name("h1.title")

                if page == "TRANSFER TARGETS":
                    playerbutton = "/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li[" + str(playernumber) + "]/div"
                else:
                    playerbutton = "/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(playernumber) + "]/div"

                self.driver.find_element_by_xpath(playerbutton)
                self.sleep_approx(1)
                self.driver.find_element_by_xpath(playerbutton).click()
                self.sleep_approx(1)


                bid_price_box = self.driver.find_element_by_css_selector('input.numericInput.filled')
                bid_price_box.click()
                bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                bid_price_box.send_keys(bidprice)
                self.sleep_approx(1)

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

                self.user_bids_made += 1
                self.update_autobidder_logs()
                self.sleep_approx(3)
            except:
                log_event("Exception makebid_individualplayer")
                log_event("Not going to retry, to avoid infinite loop")
                # self.makebid_individualplayer(playernumber, bidprice)

    # Logs initial starting coins for reference
    def setStartingCoins(self):
        num_coins = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[1]/div[1]/div[1]').text
        num_coins = str(num_coins)
        if "," in num_coins:
            num_coins = num_coins.replace(",", "")

        num_coins = int(num_coins)
        log_event("Starting coins: " + str(num_coins))
        self.user_start_coins = num_coins
        self.update_autobidder_logs()

    # Action: Logs all data on current page of market, to be used later to find accurate buy now
    def getAllPlayerInfo(self):
        status = self.checkState("transfermarket")
        if status:
            try:
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
                        print("Location: TRANSFERLIST || Player Unlisted")
                    else:
                        rating = cardinfo[0]
                        name = cardinfo[2]
                        startprice = cardinfo[16]
                        curbid_or_finalsoldprice = cardinfo[18]
                        buynow = cardinfo[20]
                        time = cardinfo[22]

                        # clean ratings
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
                    # print(full_entry)

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
            except:
                log_event("Exception retrying getAllPlayerInfo")
                self.getAllPlayerInfo()

    # Action: Retrieves player internal ID from name and rating
    def getPlayerID(self, cardname, rating):
        inputoverall = int(rating)
        inputcardname = cardname.lower()
        # First attempts to find ID in user input list
        for player in self.getPlayerListFromGUI():
            p_overall = int(player[2])
            p_cardname = player[1]
            p_cardname = p_cardname.lower()

            diff = p_overall - inputoverall

            pid = int(player[7])
            # print(str(p_overall) + " " + str(p_cardname) + " " + str(pid))

            if (diff == 0):
                if (p_cardname == inputcardname):
                    # print("ID FOUND line 486" + str(p_overall) + " " + str(p_cardname) + " " + str(pid))

                    return pid

        # If not found in small player list, check master list (takes longer)
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

    # Action: Parses market logs from searches to find accurate sell price, and updates player_list.txt - terribly inefficient but it works for now
    def get_lowestbin_from_searchdata(self):
        # Get target players IDs
        playerids = []
        txt = open("./data/player_list.txt", "r", encoding="utf8")
        for aline in txt:
            values2 = aline.strip("\n").split(",")
            # make sure it doesn't read in the blank line at end of file 
            if (len(values2) > 5):
                id = values2[7]
                playerids.append(id)
        txt.close()

        # Find cheapest listing from market data
        id_and_lowest_bin = [] # this will hold (id, lowest bin)
        for playerid in playerids:
            playerid = int(playerid)
            buynowprices = []

            futbin_price = 0
            txt = open("./data/market_logs.txt", "r", encoding="utf8")
            for aline in txt:
                player = aline.strip("\n").split(",")
                if (len(player) > 3):
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
                log_event("ID mismatch -- minimum bin price array was empty")
                log_event("Minimum bin set to 0")
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
            # ignore blank line
            if (len(entry) > 3):
                entryid = int(entry[7])
                entry_futbinprice = int(entry[9])
                new_updated_actual_price = 0
                for x in id_and_lowest_bin:
                    id = int(x[0])
                    price = x[1]
                    diff = entryid - id
                    if (diff == 0):
                        # print("got here")
                        mktprice = int(price)
                        fbinprice = int(entry_futbinprice)
                        diff = mktprice - fbinprice
                        if (diff > 1000):
                            new_updated_actual_price = fbinprice
                            log_event("Market price (" + str(mktprice) + ") seems odd, will use Futbin price (" + str(fbinprice) + ").")
                        else:
                            log_event("Confirmed mkt price seems accurate")
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

    # Returns price ceiling to stop bidding at during bidwars
    def getPlayerPriceCeiling(self, playerid):
        # for player in self.playerlist:
        #     pid = int(player[7])
        #     diff = pid - int(playerid)
        #     if (diff == 0):
        #         futbinprice = int(player[9])
        #         marketprice = int(player[11])
        #         if (diff == 0):
        #             if (marketprice == 0):
        #                 return (futbinprice * self.priceceiling)
        #             else:
        #                 return (marketprice * self.priceceiling)
            
        # Get target players IDs
        txt = open("./data/player_list.txt", "r", encoding="utf8")
        for aline in txt:
            values2 = aline.strip("\n").split(",")
            line_id = int(values2[7])
            inputid = int(playerid)
            diff = line_id - inputid

            futbinprice = int(values2[9])
            marketprice = int(values2[11])
            if (diff == 0):
                if (marketprice == 0):
                    return (futbinprice * .85)
                else:
                    return (marketprice * .85)
        txt.close()

    # Returns price to sell player at
    def getPlayerSellPrice(self, playerid):
        # Get target players IDs
        txt = open("./data/player_list.txt", "r", encoding="utf8")
        for aline in txt:
            values2 = aline.strip("\n").split(",")
            line_id = int(values2[7])
            inputid = int(playerid)
            diff = line_id - inputid

            futbinprice = int(values2[9])
            marketprice = int(values2[11])
            if (diff == 0):
                if (marketprice == 0):
                    return (futbinprice * .95)
                else:
                    return (marketprice * .95)
        txt.close()

        return 0


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Watchlist methods

    # Note - not used, from an older version
    # Action: lists won players on transfer market
    def list_players_for_transfer(self):
        # Get num players to send
        self.sleep_approx(3)

        playersOnPage = self.driver.find_elements_by_tag_name("li.listFUTItem")
        num_players_won_this_round = 0
        for player in playersOnPage:
            bidStatus = player.get_attribute("class")
            bidStatus = str(bidStatus)

            if "won" in bidStatus:
                num_players_won_this_round += 1
                self.user_players_won += 1

        total_spent = 0
        total_projected_sellprice = 0
        total_projected_profit = 0
        count = 1
        for x in range(num_players_won_this_round):
            state = self.checkState("watchlist")
            if (state):
                boughtprice_location = "/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(num_players_won_this_round - x) + "]/div/div[2]/div[2]/span[2]"
                playerrating_location = "/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(num_players_won_this_round - x) + "]/div/div[1]/div[1]/div[4]/div[2]/div[1]"
                playername_location = "/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(num_players_won_this_round - x) + "]/div/div[1]/div[2]"

                boughtprice = self.driver.find_element_by_xpath(boughtprice_location).text
                playerrating = str(self.driver.find_element_by_xpath(playerrating_location).text)
                playername = str(self.driver.find_element_by_xpath(playername_location).text)
                boughtprice = str(boughtprice)

                playerid = self.getPlayerID(playername, playerrating)

                if "," in boughtprice:
                    boughtprice = boughtprice.replace(",", "")
                
                bought_price_int = int(boughtprice)
                total_spent += bought_price_int

                playersellprice = self.getPlayerSellPrice(playerid)
                player_profit = int(playersellprice) - bought_price_int

                total_projected_sellprice += int(playersellprice)
                total_projected_profit += player_profit
                count += 1
        
        log_event("Num players won this round: " + str(num_players_won_this_round))
        log_event("Total investment: " + str(total_spent))
        log_event("Total worth:      " + str(total_projected_sellprice))
        log_event("Projected profit:  " + str(total_projected_profit))
        log_event("Listing them for transfer... ")

        self.user_projected_profit += total_projected_profit
        self.update_autobidder_logs()
        
        players_to_be_listed = True 
        while players_to_be_listed: 
            try:
                playersOnPage = self.driver.find_elements_by_tag_name("li.listFUTItem")
                
                num_players_won = 0
                for player in playersOnPage:
                    bidStatus = player.get_attribute("class")
                    bidStatus = str(bidStatus)

                    if "won" in bidStatus:
                        num_players_won += 1
                        
                if (num_players_won == 0):
                    players_to_be_listed = False
                    return

                # Listing players
                count = 1
                for x in range(num_players_won):
                    self.sleep_approx(1.5)
                    # Click bottom most player
                    playersOnPage[num_players_won - count].click()
                    self.sleep_approx(1.5)

                    list_on_transfermarket_button_location = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[1]/button"
                    startprice_location = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[2]/div[2]/input"
                    buynowprice_location = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/input"
                    listplayer_location = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/button"

                    # Click list for transfer button
                    self.driver.find_element_by_xpath(list_on_transfermarket_button_location).click()
                    self.sleep_approx(1.5)

                    # START PRICE
                    startpricebox = self.driver.find_element_by_xpath(startprice_location)
                    startpricebox.click()
                    startpricebox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                    startpricebox.send_keys(Keys.CONTROL, "a", Keys.DELETE)

                    listprice = int(round(playersellprice, -2))

                    startpricebox.send_keys(listprice)

                    self.sleep_approx(1.5)

                    # BUY NOW
                    buynowbox = self.driver.find_element_by_xpath(buynowprice_location)
                    buynowbox.click()
                    buynowbox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                    buynowbox.send_keys(Keys.CONTROL, "a", Keys.DELETE)

                    buynowprice = listprice
                    buynowbox.send_keys(listprice)
                    self.sleep_approx(1.5)

                    listplayerbutton = self.driver.find_element_by_xpath(listplayer_location).click()
                    self.sleep_approx(1.5)
                    wait_for_shield_invisibility(self.driver)                
                    count += 1
            except:
                log_event("Listing players error, should retry tho")

        log_event("- - - All players listed - - -")

    # Evaluates and detects outbid players on watchlist
    # Returns: ?
    def getAllPlayerInfoWatchlist(self):
        status = self.checkState("watchlist")
        if status:
            try:
                players_on_page = self.driver.find_elements_by_tag_name("li.listFUTItem")
                page = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[1]/h1").text #page = self.driver.find_elements_by_tag_name("h1.title")

                playerdata = []
                playernumber = 1
                sum_of_all_current_bids_on_watchlist = 0
                for card in players_on_page:
                    # Only look at top 5 players
                    if playernumber < 6:
                        bidstatus = card.get_attribute("class")
                        cardinfo = card.text.splitlines()

                        # If user is on transfer list (from old implementation)
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
                                return "processing"
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

                            # If any player is processing, just return 
                            elif "Processing" in time:
                                seconds = -5
                                return "processing"
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
                            sum_of_all_current_bids_on_watchlist += curbid_or_finalsoldprice

                            # clean buy now
                            if "," in buynow:
                                buynow = buynow.replace(",", "")
                            buynow = int(buynow)

                        id = self.getPlayerID(name, rating)
                        if (id == 0):
                            log_event("Error - ID not found in Targets, general id search found for name " + str(name) + " rating" + str(rating))
                        info = [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
                        playerdata.append(info)
                    playernumber += 1
                self.user_sum_of_all_current_bids_on_watchlist = sum_of_all_current_bids_on_watchlist

                return playerdata
            except:
                # If method reaches here, the first card on watchlist likely dissappeared in the middle of parsing
                return "processing"

    # Outbids people on watchlist
    def makebid_individualplayerWatchlist(self, playernumber, bidprice):
        # /html/body/div[4]/section/div/div/button[1]
        # https://i.gyazo.com/317c7fa554d3ab5e8fd6d48dd6337b41.png
        status = self.checkState("watchlist")
        if status:
            try:
                page = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[1]/h1").text #page = self.driver.find_elements_by_tag_name("h1.title")

                self.sleep_approx(1)
                originalbid = bidprice
                bidprice = bidprice + 50

                if page == "TRANSFER TARGETS":
                    playerbutton = "/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li[" + str(playernumber) + "]/div"
                else:
                    playerbutton = "/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(playernumber) + "]/div"

                self.driver.find_element_by_xpath(playerbutton)
                self.driver.find_element_by_xpath(playerbutton).click()
                self.sleep_approx(0.5)

                try:
                    # bid_price_box = self.driver.find_element_by_css_selector('input.numericInput.filled')
                    # bid_price_box.click()
                    # bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                    # bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                    # bid_price_box.send_keys(bidprice)
                    # self.sleep_approx(0.5)

                    # Click make bid method
                    if page == "TRANSFER TARGETS":
                        # Click make bid
                        WebDriverWait(self.driver, 30).until(
                            EC.visibility_of_element_located((By.XPATH, '/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/button[1]'))
                            )
                        self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/button[1]").click()

                        self.sleep_approx(1)
                        # Check if "highest bidder" glitch occurred
                        overbid_glitch = self.check_exists_by_xpath("/html/body/div[4]/section/div/div/button[1]")
                        if overbid_glitch:
                            cancel_btn = self.driver.find_element_by_xpath("/html/body/div[4]/section/div/div/button[1]")
                            cancel_btn.click()
                            self.sleep_approx(1)
                    else:
                        self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/button[1]").click()

                except:
                    log_event("Bid method failed")

                if (page == "TRANSFER TARGETS"):
                    # self.sleep_approx(1)
                    curbidprice_afterbidding = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[1]/div/div[2]/span[2]").text
                    if "," in curbidprice_afterbidding:
                        curbidprice_afterbidding = curbidprice_afterbidding.replace(",", "")
                    curbidprice_afterbidding = int(curbidprice_afterbidding)

                    diff = originalbid - curbidprice_afterbidding

                    if (diff == 0):
                        return "Failure"
                    else:
                        self.user_bids_made += 1
                        self.update_autobidder_logs()
                        return "Success"

                self.sleep_approx(1)
            except:
                log_event("makebid_individualplayerWatchlist error")

    # During bid wars, oftentimes bids will not go through - this refreshes the webapp
    def refreshPageAndGoToWatchlist(self):
        try:
            self.sleep_approx(1)
            self.user_requests_made += 1
            self.driver.refresh()

            wait_for_shield_invisibility(self.driver)


            WebDriverWait(self.driver, 30).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'icon-transfer'))
            )

            wait_for_shield_invisibility(self.driver)


            self.sleep_approx(3)

            log_event("Going back to watchlist")
            self.go_to_watchlist()
        except:
            log_event("Exception retrying refreshPageGoToWatchlist")
            self.refreshPageAndGoToWatchlist()

    # Returns number of active bids. Also stores number won, expired, etc. for display on GUI
    def get_num_activebids(self):
        try:
            players = self.driver.find_elements_by_tag_name("li.listFUTItem")
            playernumber = 1

            activebids_counter = 0
            expired_counter = 0
            won_counter = 0
            for player in players:
                bidStatus = player.get_attribute("class")
                if "highest-bid" in bidStatus:
                    activebids_counter+=1
                elif "outbid" in bidStatus:
                    activebids_counter+=1
                elif "expired" in bidStatus:
                    expired_counter+=1
                elif "won" in bidStatus:
                    won_counter+=1

        
            # self.user_watchlist_expired = expired_counter
            self.user_activebids = activebids_counter
            # self.user_players_won = won_counter
            return activebids_counter
        except:
            # log_event("Exception get_num_active_bids returning 1")
            return 1


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Transferlist methods

    # Action: Logs all data on current page of market, to be used later to find accurate buy now
    def getAllPlayerInfoTransferlist(self):
        status = True
        if status:
            try:
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
                        print("Location: TRANSFERLIST || Player Unlisted")
                    else:
                        rating = cardinfo[0]
                        name = cardinfo[2]
                        startprice = cardinfo[16]
                        curbid_or_finalsoldprice = cardinfo[18]
                        buynow = cardinfo[20]
                        time = cardinfo[22]

                        # clean ratings
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
                    if (id == 0):
                        print("Unknown player on TL, unable to get ID")

                    info = [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
                    playerdata.append(info)

                    now = datetime.now()
                    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                    dt_string = dt_string.split(" ")
                    date = dt_string[0]
                    currenttime = dt_string[1]

                    agg = [date, currenttime, playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]

                    playernumber += 1

                return playerdata
            except:
                log_event("User error checking Transfer List")

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Button clicks

    def clearExpired(self):
        self.sleep_approx(1)
        playersOnPage = self.driver.find_elements_by_tag_name("li.listFUTItem")
        
        num_players_expired = 0
        for player in playersOnPage:
            bidStatus = player.get_attribute("class")
            bidStatus = str(bidStatus)

            if "expired" in bidStatus:
                num_players_expired += 1

        log_event("Num players expired: " + str(num_players_expired))

        if num_players_expired > 0:
            try:
                self.sleep_approx(1)
                self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div/section[4]/header/button').click()
                self.sleep_approx(1)
            except:
                log_event("Clear expired button click did not work, please manually click")

    def clickSearch(self):
        self.sleep_approx(1)
        self.driver.find_element(By.XPATH, '(//*[@class="button-container"]/button)[2]').click()
        self.user_requests_made += 1

    def clickBack(self):
        self.sleep_approx(1)
        self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[1]/button[1]').click()
        self.sleep_approx(1)


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Navigation

    def go_to_transfer_market(self):
        try:
            self.driver.find_element(By.CLASS_NAME, 'icon-transfer').click()

            sleeptime = random.randint(1, 5)

            self.sleep_approx(sleeptime)
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'ut-tile-transfer-market'))
            )
            self.sleep_approx(sleeptime)
            self.driver.find_element(By.CLASS_NAME, 'ut-tile-transfer-market').click()
        except:
            log_event("Exception retrying go_transfer_market")

    def go_to_watchlist(self):
        try:
            self.sleep_approx(0.5)
            self.driver.find_element(By.XPATH, '/html/body/main/section/nav/button[3]').click()
            self.sleep_approx(0.5)
            self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]').click()
            self.sleep_approx(0.5)
        except:
            log_event("Exception retrying go_to_watchlist")
            self.go_to_watchlist()

    def go_to_transferlist(self):
        try:
            self.sleep_approx(5)
            self.driver.find_element(By.XPATH, "/html/body/main/section/nav/button[3]").click()
            self.sleep_approx(5)
            self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div[3]").click()
            self.sleep_approx(1)
        except:
            log_event("Exception retrying go_to_transferlist")
            self.go_to_transferlist()

    def go_to_login_page(self):
        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@class="ut-login-content"]//button'))
        )
        print("Logging in...")

        self.sleep_approx(random.randint(5, 10))
        self.driver.find_element(By.XPATH, '//*[@class="ut-login-content"]//button').click()

        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'email'))
        )


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ General
    # Returns + updates config options from GUI
    def getUserConfig(self):
        # Load Autobidder stats
        userconfig_json = open('./data/config.json')
        json1_str = userconfig_json.read()
        configops = json.loads(json1_str)[0]
        
        config_choices = []
        for key, value in configops.items():
            config_choices.append(value)
        
        conserve_bids = config_choices[0]
        sleep_time = config_choices[1]
        botspeed = config_choices[0]

        sleep_time = int(sleep_time)
        botspeed = float(botspeed)
        conserve_bids = int(conserve_bids)
        self.conserve_bids, self.sleep_time, self.botspeed = conserve_bids, sleep_time, botspeed

        return conserve_bids, sleep_time, botspeed

    # Ensures user is on correct page to avoid infinite loops in try / except
    def checkState(self, desiredPage):
        try:
            page = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[1]/h1").text #page = self.driver.find_elements_by_tag_name("h1.title")
            page = str(page)
            page = page.lower()

            if (desiredPage == "watchlist"):
                if (page == "transfer targets"):
                    return True
                else:
                    log_event("Unexpectedly not on Watchlist, stopping")
                    return False

            elif (desiredPage == "transfermarket"):
                if (page == "search results"):
                    return True
                else:
                    log_event("Unexpectedly not on Transfer Market, stopping")
                    return False
            else:
                log_event("checkState was passed invalid location")
        except:
            log_event("Error checking state")
               
    def check_exists_by_xpath(self, xpath):
        try:
            self.driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True

    def get_futbin_price_lastupdated(self, ID):
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

    # Lists all players on transfer list using futbin prices
    def manageTransferlist(self):

        sleep(3)

        try:
            log_event("Clicked clear expired")
            self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[1]/header/button").click()
        except:
            log_event("")
        gui_ids = []
        user_playerlist = self.getPlayerListFromGUI()
        for player in user_playerlist:
            pid = int(player[7])
            gui_ids.append(pid)

        sleep(5)

        players = self.getAllPlayerInfoTransferlist()

        clickRelistAll = False
        clickClearExpired = False

        unlistedplayerscount = 0
        didnotsellcount = 0
        soldcount = 0
        currentlylistedcount = 0
        for player in players:
            #info = [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
            # print(str(player))
            playerid = int(player[8])
            bidstatus = player[1]
            name = player[3]

            if bidstatus == "listFUTItem":
                unlistedplayerscount += 1
            if playerid not in gui_ids:
                gui_ids.append(playerid)

            if "expired" in bidstatus:
                didnotsellcount += 1
                clickRelistAll = True
                
            if "won" in bidstatus:
                soldcount += 1
                clickClearExpired = True
            if (bidstatus == "listFUTItem has-auction-data"):
                currentlylistedcount += 1

        print("Num players sold: " + str(soldcount))
        print("Num players didn't sell: " + str(didnotsellcount))
        print("Num players unlisted: " + str(unlistedplayerscount))
        print("Num players listed currently: " + str(currentlylistedcount))
        print("Not going to touch unlisted players")

        print("Proceeding to relist with accurate prices...")
        if clickClearExpired:
            log_event("Clicked clear expired")
            self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[1]/header/button").click()
        
        priceData = []
        # id, sellprice
        for id in gui_ids: 
            price = self.getPlayerSellPrice(id)

            if (price == 0):
                price, lastupdated = self.get_futbin_price_lastupdated(id)

            pid_price = [id, price]
            # print(pid_price)
            priceData.append(pid_price)
            sleep(3)
        players_to_relist = True
        total_sell_prices = 0
        while players_to_relist:
            players = self.getAllPlayerInfoTransferlist()
            if (didnotsellcount == 0):
                # print("didnot sell count: " + str(didnotsellcount))
                players_to_relist = False
            else:
                try:
                    for x in range(didnotsellcount-1):
                        # x += 1
                        # will always click play number 1
                        playerbutton = "/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div"
                        startpriceinput = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[2]/div[2]/input"
                        buynowpriceinput = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/input"
                        listfortransfer = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/button"
                        
                        playernamelocation = "/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[2]"
                        playerratinglocation = "/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[1]/div[4]/div[2]/div[1]"

                        playername = self.driver.find_element(By.XPATH, playernamelocation).text
                        playerrating = self.driver.find_element(By.XPATH, playerratinglocation).text
                        currentplayerid = self.getPlayerID(playername, playerrating)

                        # Get sell price
                        for data in priceData:
                            id = data[0]
                            futbinprice = int(data[1])
                            currentplayerid = int(currentplayerid)
                            id = int(id)
                            if currentplayerid == id:
                                # print("Price ID match found, will now list player for " + str(futbinprice))
                                if futbinprice > 1000:
                                    buynowprice = futbinprice
                                    startprice = buynowprice-50
                                elif futbinprice < 1000:
                                    buynowprice = futbinprice
                                    startprice = buynowprice-100
                                else:
                                    log_event("price of player unable to be fetched line 1414 in helpers")

                                # Add sell price to sum
                                total_sell_prices += buynowprice
                                self.user_projected_profit += buynowprice

                                # Click player
                                self.driver.find_element(By.XPATH, playerbutton).click()
                                self.sleep_approx(1)
                                # Click list for transfer
                                self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[1]/button").click()
                                self.sleep_approx(1)

                                buynowBox = self.driver.find_element(By.XPATH, buynowpriceinput)
                                buynowBox.click()
                                self.sleep_approx(1)
                                buynowBox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                                buynowBox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                                buynowBox.send_keys(buynowprice)

                                self.sleep_approx(1)
                                startpriceBox = self.driver.find_element(By.XPATH, startpriceinput)
                                startpriceBox.click()
                                self.sleep_approx(1)
                                startpriceBox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                                startpriceBox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                                startpriceBox.send_keys(startprice)
                                self.sleep_approx(1)

                                # List for transfer!
                                self.driver.find_element(By.XPATH, listfortransfer).click()
                                log_event("Listed player " + str(id) + " for BIN: " + str(buynowprice))
                                self.update_autobidder_logs()
                                self.sleep_approx(3)
                except:
                    log_event("annoying issue with transfer list method")
        log_event("Players relisted! Projected worth: " + str(total_sell_prices))


    # Action: updates GUI with current state variables
    def update_autobidder_logs(self):
        # also update user config vars
        self.conserve_bids, self.sleep_time, self.botspeed = self.getUserConfig()

        try:
            num_coins = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[1]/div[1]/div[1]').text
            num_coins = str(num_coins)
            if "," in num_coins:
                num_coins = num_coins.replace(",", "")

            num_coins = int(num_coins)
            self.user_num_coins = num_coins
            with open('./data/gui_stats.json', 'r') as f:
                json_data = json.load(f)
                # json_data2 = json_data[0] 
                json_data[0]["# of Targets"] = self.user_num_target_players
                json_data[0]['# of Bids to make on each'] = self.user_num_bids_each_target
                json_data[0]['Requests made'] = self.user_requests_made
                json_data[0]['Bids made'] = self.user_bids_made
                json_data[0]['Transfer list size'] = self.user_transferlist_size
                json_data[0]['Active bids'] = self.user_activebids
                json_data[0]['Current coins'] = self.user_num_coins
                json_data[0]['Players won'] = self.user_players_won
                json_data[0]['Projected Profit'] = self.user_projected_profit
                json_data[0]['Actual profit'] = "--"

                json_data[0]['watchlist_winning'] = self.user_watchlist_winning
                json_data[0]['watchlist_outbid'] = self.user_watchlist_outbid
                json_data[0]['watchlist_totalsize'] = self.user_watchlist_totalsize
                json_data[0]['transferlist_selling'] = self.user_transferlist_selling
                json_data[0]['transferlist_sold'] = self.user_transferlist_sold
                json_data[0]['transferlist_totalsize'] = self.user_transferlist_totalsize
                json_data[0]['Starting coins'] = self.user_start_coins


            with open('./data/gui_stats.json', 'w') as f:
                f.write(json.dumps(json_data))
        except:
            print("Err update_autobidder_logs")

    # Action: clears old market search data logs
    def clearOldMarketLogs(self):
        file = open("./data/market_logs.txt", "r+")
        file.truncate(0)
        file.close()

    # Action: sets all previous logs to 0
    def clearOldUserData(self):
        file = open("./data/market_logs.txt", "r+")
        file.truncate(0)
        file.close()

        # Clear GUI logs
        try:
            with open('./data/gui_stats.json', 'r') as f:
                json_data = json.load(f)
                # json_data2 = json_data[0] 
                json_data[0]["# of Targets"] = 0
                json_data[0]['# of Bids to make on each'] = 0

                json_data[0]['Requests made'] = 0
                json_data[0]['Bids made'] = 0
                json_data[0]['Transfer list size'] = 0
                json_data[0]['Active bids'] = 0
                json_data[0]['Current coins'] = 0
                json_data[0]['Players won'] = 0
                json_data[0]['Projected Profit'] = 0
                json_data[0]['Actual profit'] = "--"

                json_data[0]['watchlist_winning'] = 0
                json_data[0]['watchlist_outbid'] = 0
                json_data[0]['watchlist_totalsize'] = 0
                json_data[0]['transferlist_selling'] = 0
                json_data[0]['transferlist_sold'] = 0
                json_data[0]['transferlist_totalsize'] = 0
                json_data[0]['Starting coins'] = 0


            with open('./data/gui_stats.json', 'w') as f:
                f.write(json.dumps(json_data))
        except:
            print("Err update_autobidder_logs")

    def getFutbinDataAndPopulateTable(self, futbin_url):
        browser = self.driver
        driver = self.driver

        tab_url = futbin_url 

        browser.execute_script("window.open('');")
        browser.switch_to.window(browser.window_handles[1])
        browser.get(tab_url)
 
        name = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[8]/div[15]/div/div/div[1]/div[2]/table/tbody/tr[2]/td"))).text
        team = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[8]/div[15]/div/div/div[1]/div[2]/table/tbody/tr[3]/td/a"))).text
        nation = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[8]/div[12]/div[3]/div[1]/div/ul/li[1]/a"))).text
        cardtype = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[8]/div[15]/div/div/div[1]/div[2]/table/tbody/tr[12]/td"))).text
        rating = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[8]/div[13]/div[2]/div/div/div[1]/div/a/div/div[2]"))).text
        cardname = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[8]/div[13]/div[2]/div/div/div[1]/div/a/div/div[3]"))).text
        position = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[8]/div[13]/div[2]/div/div/div[1]/div/a/div/div[4]"))).text

        internals_location = driver.find_element(By.XPATH, "/html/body/div[8]/div[5]/div")
        internal_id = int(internals_location.get_attribute("data-baseid"))
        futbin_id = internals_location.get_attribute("data-id")
        
        # price, lastupdated = get_futbin_price_lastupdated(fifa_id)

        r = requests.get('https://www.futbin.com/21/playerPrices?player={0}'.format(internal_id))

        data = r.json()
        price = data[str(internal_id)]["prices"]["xbox"]["LCPrice"]
        lastupdated = data[str(internal_id)]["prices"]["xbox"]["updated"]

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
        # print("Futbin Price: " + str(price) + " || Last Updated: " + str(lastupdated))
        futbin_id = int(futbin_id)
        market_price = 0
        buy_pct = .85
        agg = [name, cardname, rating, team, nation, cardtype, position, internal_id, futbin_id, price, lastupdated, market_price, buy_pct]
                # columns = ["Name", "Card name", "Rating", "Team", "Nation", "Type", "Position", "Internal ID", "Futbin ID", "Futbin Price", "Futbin LastUpdated", "Actual Market Price"]


        full_entry = ""
        for word in agg:
            word = str(word)
            word_comma = word + ","
            full_entry += word_comma

        # Remove last comma
        full_entry = full_entry[:-1]
        print(full_entry)

        # Add new line to end
        hs = open("./data/player_list.txt", "a", encoding="utf8")
        hs.write(full_entry + "\n")
        hs.close()

        log_event("Added player " + str(cardname))

        # "/html/body/div[8]/div[5]/div" <-- this div has an attribute "data-baseid" which is what we want, also "data-player-resource" which is the same, and finally "data-id" gives internal futbin ID

        # ~ ~ ~ ~ ~ ~ ~ Close the futbin tab ~ ~ ~ ~ ~
        browser.close()

        # Switch back to the first tab with URL A
        browser.switch_to.window(browser.window_handles[0])
        # log_event("Fetched player info")

    def sleep_approx(self, seconds):
        upperbound = (seconds+0.2)*10000
        if (seconds >= 1):
            lowerbound = (seconds-0.2)*10000
        else:
            lowerbound = seconds*10000

        # wait_for_shield_invisibility(self.driver, sleeptime)

        sleeptime = random.randint(lowerbound,upperbound)
        sleeptime = sleeptime/10000
        sleeptime = sleeptime*.8

        if (self.botspeed == 1.25):
            sleeptime = sleeptime*.75
        elif (self.botspeed == 1.5):
            sleeptime = sleeptime*.5
        sleep(sleeptime)
        
    def getPlayerListFromGUI(self):
        playerlist = []
        # Tried to be cheeky and only have this called on initialization, but this made adding / removing to player list in real time impossible
        # Get input list of target players
        src = "./data/player_list.txt"
        txt = open(src, "r", encoding="utf8")

        for aline in txt:
            values = aline.strip("\n").split(",")
            playerlist.append(values)
        txt.close()

        return playerlist


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ NON CLASS METHODS

def getText(driver, xpath):
    result = driver.get_element_by_xpath(xpath).text
    return result

def clickElement(driver, xpath):
    driver.get_element_by_xpath(xpath).click()

def login(driver, user, email_credentials):
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@class="ut-login-content"]//button'))
    )
    # print("Logging in...")

    sleep(random.randint(2, 4))
    driver.find_element(By.XPATH, '//*[@class="ut-login-content"]//button').click()

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, 'email'))
    )


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

    access_code = get_access_code(email_credentials)

    driver.find_element(By.ID, 'oneTimeCode').send_keys(access_code)
    sleep(1)
    driver.find_element(By.ID, 'btnSubmit').click()

    log_event("Logged in successfully!")
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'icon-transfer'))
    )
    sleep(2)

def get_access_code(email_credentials):
    EA_EMAIL = "EA@e.ea.com"
    M = imaplib.IMAP4_SSL("imap.gmail.com")

    try:
        M.login(email_credentials["email"], email_credentials["password"])
    except imaplib.IMAP4.error:
        # print("Login to email failed")
        log_event("Unable to fetch access code from email (see ReadMe for help on this), enter it manually")
        sys.exit(1)

    print("Waiting for access code...")
    sleep(3)
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

    log_event(email_message['Subject'])

    access_code = ''.join(filter(str.isdigit, email_message['Subject']))

    return access_code

def wait_for_shield_invisibility(driver, duration=0.25):
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((By.CLASS_NAME, 'ut-click-shield showing interaction'))
    )
    sleep(.25)

def log_event(event):
    # Update GUI logs
    event = str(event)
    
    # add some randomness
    x = random.randint(1,10000)
    x2 = x/10000
    sleep(x2)

    file_object = open('./data/gui_logs.txt', 'a')
    now = datetime.now()
    dt_string = now.strftime("[%H:%M:%S] ")

    full_log = dt_string + event + "\n"
    print(full_log)
    file_object.write(full_log)
    file_object.close()

def clearOldUserData_nonclass():

    # file = open("./data/gui_logs.txt", "r+")
    # file.truncate(0)
    # file.close()

    file = open("./data/market_logs.txt", "r+")
    file.truncate(0)
    file.close()

    # Clear GUI logs
    try:
        with open('./data/gui_stats.json', 'r') as f:
            json_data = json.load(f)
            # json_data2 = json_data[0] 
            json_data[0]["# of Targets"] = 0
            json_data[0]['# of Bids to make on each'] = 0

            json_data[0]['Requests made'] = 0
            json_data[0]['Bids made'] = 0
            json_data[0]['Transfer list size'] = 0
            json_data[0]['Active bids'] = 0
            json_data[0]['Current coins'] = 0
            json_data[0]['Players won'] = 0
            json_data[0]['Projected Profit'] = 0
            json_data[0]['Actual profit'] = "--"

            json_data[0]['watchlist_winning'] = 0
            json_data[0]['watchlist_outbid'] = 0
            json_data[0]['watchlist_totalsize'] = 0
            json_data[0]['transferlist_selling'] = 0
            json_data[0]['transferlist_sold'] = 0
            json_data[0]['transferlist_totalsize'] = 0
            json_data[0]['Starting coins'] = 0


        with open('./data/gui_stats.json', 'w') as f:
            f.write(json.dumps(json_data))
    except:
        print("Err update_autobidder_logs")