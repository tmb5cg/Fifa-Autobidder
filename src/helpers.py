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

import pandas as pd
import requests
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        TimeoutException, WebDriverException)
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import ui
from selenium.webdriver.support.wait import WebDriverWait


class Helper:
    def __init__(self, driver, queue):
        self.driver = driver
        self.queue = queue

        with open('./data/gui_stats.json', 'r') as f:
            json_data = json.load(f)

            self.user_num_target_players = json_data[0]["# of Targets"]
            self.user_num_bids_each_target = json_data[0]['# of Bids to make on each']
            self.user_requests_made = json_data[0]['Requests made']
            self.user_bids_made = json_data[0]['Bids made']
            self.user_transferlist_size = json_data[0]['Transfer list size']
            self.user_activebids = json_data[0]['Active bids']
            self.user_num_coins = json_data[0]['Current coins']
            self.user_players_won = json_data[0]['Players won']
            self.user_projected_profit = json_data[0]['Projected Profit']
            self.user_actual_profit = json_data[0]['Actual profit']

            self.user_watchlist_winning = json_data[0]['watchlist_winning']
            self.user_watchlist_outbid = json_data[0]['watchlist_outbid']
            self.user_watchlist_totalsize = json_data[0]['watchlist_totalsize']

            self.user_transferlist_selling = json_data[0]['transferlist_selling']
            self.user_transferlist_sold = json_data[0]['transferlist_sold']
            self.user_transferlist_totalsize = json_data[0]['transferlist_totalsize']

            self.user_start_coins = json_data[0]['Starting coins']
            self.user_watchlist_expired = 0

            self.transferlistInfiniteLoopCounter = 0

        with open('./data/gui_stats.json', 'w') as f:
            f.write(json.dumps(json_data))

        self.user_sum_of_all_current_bids_on_watchlist = 0
        self.sleeptime_between_rounds = 0
        self.conserve_bids, self.sleep_time, self.botspeed, self.bidexpiration_ceiling, self.buyceiling, self.sellceiling = self.getUserConfig()
        self.p_ids_and_prices = {}

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Main methods

    def go_to_tranfer_market_and_input_parameters(self, cardname, fullname, cardoverall):
        """
        Clicks player to search market from dropdown by evaluating results 
        ie there are many "Rodriguez" cards, this chooses the correct one
        by checking the player's rating

        Parameters:
            cardname (str): Player's name on card
            fullname (str): Player's full name from database
            cardoverall (int): Player's card overall

        Returns:
            if exception, returns str saying error 
        """
        try:
            cardname = cardname.lower()
            fullname = fullname.lower()

            # Go to transfer market
            self.driver.find_element(By.CLASS_NAME, 'icon-transfer').click()
            self.sleep_approx(1)
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, 'ut-tile-transfer-market'))
            )
            self.sleep_approx(1)
            self.driver.find_element(
                By.CLASS_NAME, 'ut-tile-transfer-market').click()

            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, 'ut-player-search-control'))
            )
            wait_for_shield_invisibility(self.driver)

            # Insert player name into search
            self.driver.find_element(
                By.XPATH, '//div[contains(@class, "ut-player-search-control")]//input').click()
            self.sleep_approx(2)
            self.driver.find_element(
                By.XPATH, '//div[contains(@class, "ut-player-search-control")]//input').send_keys(cardname)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//ul[contains(@class, "playerResultsList")]/button'))
            )

            # Player list dropdown is visible now, so we must  /html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul
            results_list = self.driver.find_elements_by_xpath(
                '//ul[contains(@class, "playerResultsList")]/button')
            num_results = len(results_list)

            result_to_click = 1
            for x in range(num_results):
                x += 1
                playername = self.driver.find_element_by_xpath(
                    "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul/button[" + str(x) + "]/span[1]").text
                playeroverall = self.driver.find_element_by_xpath(
                    "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul/button[" + str(x) + "]/span[2]").text

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

            # log_event(self.queue, "waiting a sec Should click result number: " + str(result_to_click))
            self.sleep_approx(1)
            self.driver.find_element_by_xpath(
                "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/ul/button[" + str(result_to_click) + "]").click()
        except:
            log_event(
                self.queue, "Exception go_to_transfer_market_and_input_parameters")
            return "error"
            # self.go_to_tranfer_market_and_input_parameters(cardname, fullname, cardoverall)

    def search_market_gather_players(self, name, max_price_to_pay, bids_allowed, bids_made, futbindata, min_bid, max_bid):
        """
        While on transfer market, evaluates current market page, calls makebid_individualplayer if players should be bid on (i.e. if underpriced)

        Location:
            transfer market

        Parameters:
            name (str): Player's cardname (for added security check).
            max_price_to_pay (float): Max price to pay for player.
            bids_allowed (int): Number of bids allowed to make on the player.
            bids_made (int): Number of bids made on player.
            futbindata (none): old variable from previous build, unused (whenever I remove stuff, stuff breaks).
            min_bid (float): Min bid set at search, used to fix poorly built search method.
            max_bid (float): Max bid set at search, used to fix poorly built search method.

        Returns:
            bids_made (int): Number of bids made on player in this search round.
        """
        if (int(max_bid) < 400):
            max_bid = 400
        # Ensure bid box is visible, then clear previous params
        self.sleep_approx(2)
        input = self.driver.find_element(
            By.XPATH, "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[6]/div[2]/input")
        self.driver.execute_script("arguments[0].scrollIntoView(true);", input)
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[6]/div[2]/input"))).click()
        self.sleep_approx(1)
        input.send_keys(0)
        self.sleep_approx(1)

        clear = "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[1]/button"
        maxbidbox = self.driver.find_element(
            By.XPATH, "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[3]/div[2]/input")
        minbidbox = self.driver.find_element(
            By.XPATH, "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[2]/div[2]/input")

        # CLEAR RESULTS BOX
        self.driver.find_element(By.XPATH, clear).click()
        self.sleep_approx(1)

        # insert max_bid here
        maxbidbox.click()
        self.sleep_approx(1)
        maxbidbox.send_keys(max_bid)
        self.sleep_approx(1)

        # insert min_bid here
        minbidbox.click()
        self.sleep_approx(1)
        minbidbox.send_keys(min_bid)
        self.sleep_approx(1)

        # search the pages, and bid on players under bid price
        self.clickSearch()
        sleep(3)

        keepgoing = True
        while keepgoing:
            # Each page, get user config
            self.getUserConfig()
            status = self.checkState("transfermarket")
            if status:
                max_price_to_pay = int(max_price_to_pay)
                self.sleep_approx(4)

                # TODO understand why some eligible players fail to receive bids...
                players_on_page = self.getAllPlayerInfo()
                for card in players_on_page:
                    playernumber = card[0]
                    bidStatus = card[1]
                    curbid = card[5]
                    timeremainingseconds = card[7]
                    timeremainingmins = timeremainingseconds/60
                    playerid = card[8]
                    buynow = card[6]

                    if bids_made < bids_allowed-1:
                        if "highest-bid" not in bidStatus:
                            stopbidTime = int(self.bidexpiration_ceiling)
                            if timeremainingmins < stopbidTime:
                                if timeremainingmins >= 2:
                                    # Check if bid to make falls under ceiling
                                    if (curbid < 1000):
                                        curbidprice_afterbidding = curbid+50
                                    else:
                                        curbidprice_afterbidding = curbid+100
                                    if curbidprice_afterbidding < max_price_to_pay:
                                        if ((curbid*2)<self.user_num_coins):
                                            self.makebid_individualplayer(
                                                playernumber, max_price_to_pay)
                                            self.sleep_approx(2)
                                            bids_made += 1
                                            log_event(self.queue, "Bids made on " + str(name) +
                                                    ": " + str(bids_made) + "/" + str(bids_allowed))
                                        else:
                                            log_event(self.queue, "not enough coins")
                            else:
                                keepgoing = False
                    else:
                        keepgoing = False

                self.sleep_approx(3)
                log_event(self.queue, "Going to next page")
                try:
                    self.driver.find_element_by_xpath(
                        '/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]')
                    self.driver.find_element_by_xpath(
                        '/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]').click()
                    self.user_requests_made += 1
                except:
                    log_event(self.queue, "No next page found, returning")
                    keepgoing = False
        self.clickBack()
        self.sleep_approx(1)
        return bids_made

    def makebid_individualplayer(self, playernumber, max_price_to_pay):
        """
        Makes a bid on a player. Only called when player has been evaluated and 
        we're sure they're underpriced - this method just does the actual bid action.

        Location:
            transfer market

        Parameters:
            playernumber (int): The index/location of the player on the page (ie player in row 7 of 24 results), 
            max_price_to_pay (float): Max price to pay for the player, used to triple check we don't 
                                      bid over this price if the player somehow slipped through the other checks

        Returns:
            none
        """
        status = self.checkState("transfermarket")
        if status:
            # Click player
            playerbutton = "/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(
                playernumber) + "]/div"
            self.driver.find_element_by_xpath(playerbutton)
            self.sleep_approx(1)
            self.driver.find_element_by_xpath(playerbutton).click()
            self.sleep_approx(1)

            # If conserve bids is on, bid at (user_buy_ceiling * .7)*max price to pay
            if (self.conserve_bids == 1):
                bid_to_make = round(int(max_price_to_pay*.7), -2)
                bid_price_box = self.driver.find_element_by_css_selector(
                    'input.numericInput.filled')
                bid_price_box.click()
                self.sleep_approx(1)
                bid_price_box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                self.sleep_approx(1)

                # Enter bid price of (0.85)*(0.8) * marketprice
                bid_price_box.send_keys(bid_to_make)
                self.sleep_approx(1)

                # Click make bid button #TODO read input price and check for max bid error
                self.driver.find_element(
                    By.XPATH, "/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/button[1]").click()
            else:
                # Not in conserve mode - Don't enter price - just click make bid
                self.driver.find_element(
                    By.XPATH, "/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/button[1]").click()

            self.user_bids_made += 1
            self.update_autobidder_logs()
            self.sleep_approx(1)

    def setStartingCoins(self):
        """
        Stores user's coins (as class variable) on bot startup - only called once on inits

        Location:
            homepage

        Parameters:
            none

        Returns:
            none
        """
        num_coins = self.driver.find_element(
            By.XPATH, '/html/body/main/section/section/div[1]/div[1]/div[1]').text
        num_coins = str(num_coins)
        if "," in num_coins:
            num_coins = num_coins.replace(",", "")

        num_coins = int(num_coins)
        log_event(self.queue, "Starting coins: " + str(num_coins))
        self.user_start_coins = num_coins
        self.update_autobidder_logs()

    def getAllPlayerInfo(self):
        """
        Parses all players on current page of market.
        Saves info to data/market_logs.txt, to be used when
        parsing the market data to find the player's actual
        sell price

        Location:
            transfer market

        Parameters:
            none

        Returns:
            playerdata (list): info for all players on page such as:
                date
                currenttime
                playernumber (int): index/location on page
                bidstatus (int): outbid, bid on / not bid on, highest bidder etc
                rating
                name
                startprice
                curbid_or_finalsoldprice (int): if --- (player has no bid), set to min bid
                buynow
                time_remaining
                id
                #TODO add details here
        """
        status = self.checkState("transfermarket")
        if status:
            try:
                players_on_page = self.driver.find_elements_by_tag_name(
                    "li.listFUTItem")
                # page = self.driver.find_elements_by_tag_name("h1.title")
                page = self.driver.find_element(
                    By.XPATH, "/html/body/main/section/section/div[1]/h1").text

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
                            curbid_or_finalsoldprice = curbid_or_finalsoldprice.replace(
                                ",", "")

                        curbid_or_finalsoldprice = int(
                            curbid_or_finalsoldprice)

                        # clean buy now
                        if "," in buynow:
                            buynow = buynow.replace(",", "")
                        buynow = int(buynow)

                    id = self.getPlayerID(name, rating)

                    info = [playernumber, bidstatus, rating, name,
                            startprice, curbid_or_finalsoldprice, buynow, time, id]
                    playerdata.append(info)

                    now = datetime.now()
                    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                    dt_string = dt_string.split(" ")
                    date = dt_string[0]
                    currenttime = dt_string[1]

                    agg = [date, currenttime, playernumber, bidstatus, rating,
                           name, startprice, curbid_or_finalsoldprice, buynow, time, id]

                    full_entry = ""
                    for word in agg:
                        word = str(word)
                        word_comma = word + ","
                        full_entry += word_comma

                    full_entry = full_entry[:-1]

                    # Add new line to end
                    hs = open("./data/market_logs.txt", "a", encoding="utf8")
                    hs.write(full_entry + "\n")
                    hs.close()

                    playernumber += 1

                return playerdata
            except:
                log_event(self.queue, "Exception getAllPlayerInfo")

    def get_lowestbin_from_searchdata(self):
        """
        Parses market logs from searches to find accurate sell price (based on buy now prices), and updates player_list.txt.
        Terribly inefficient but it works for now

        In the event only prices found are 10,000, the price is rejected and we continue to use Futbin as truth.
        Also excludes players expiring 55+ mins, if some crazy undercut is found.

        Location:
            anywhere!

        Parameters:
            none

        Returns:
            none, just updates player_list.txt

        """
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
        id_and_lowest_bin = []  # this will hold (id, lowest bin)
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
                    if (playerid == marketid) and (playerid != 0) and (timeremainingMinutes < 55):
                        buynowprice = player[8]
                        buynowprice = int(buynowprice)
                        if (buynowprice != 10000):
                            buynowprices.append(buynowprice)

            try:
                minimumbin = min(buynowprices)
            except:
                log_event(
                    self.queue, "ID mismatch -- minimum bin price array was empty")
                log_event(self.queue, "Minimum bin set to 0")
                minimumbin = 0
            playername = self.getPlayerCardName(playerid)

            log_event(self.queue, str(playername) +
                      " min buy now from market data: " + str(minimumbin))

            # Now we have player ID, and their lowest bin -- update it on GUI
            data = [playerid, minimumbin]
            id_and_lowest_bin.append(data)

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
                            log_event(self.queue, "Market price (" + str(mktprice) +
                                      ") seems odd, will use Futbin price (" + str(fbinprice) + ").")
                        else:
                            log_event(
                                self.queue, "Confirmed mkt price seems accurate")
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
                    count += 1

                # Remove last comma
                full_entry = full_entry[:-1]

                # Add new line to end
                hs = open("./data/player_list.txt", "a", encoding="utf8")
                hs.write(full_entry + "\n")
                hs.close()

    def getPlayerCardName(self, playerid):
        """
        Returns player card name, based on ID

        Location:
            anywhere!

        Parameters:
            playerid (int): Player's internal ID

        Returns:
            cardname (str): Player's cardname
        """
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

    def getPlayerPriceCeiling(self, playerid):
        """
        Returns price ceiling to stop bidding at during bidwars.

        Location:
            anywhere
        Parameters:
            playerid (int): The player's ID.

        Returns:
            marketprice * user_buyceiling_percent (float)
        """
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
                    return (futbinprice * self.buyceiling)
                else:
                    return (marketprice * self.buyceiling)
        txt.close()

        # If player isn't found, return 0
        return 0

    def getPlayerSellPrice(self, playerid):
        """
        Returns price to sell player at, for listing players/when calculating profit.

        Location:
            anywhere

        Parameters:
            playerid (int): The player's ID.

        Returns:
            marketprice * user_buyceiling_percent (float)
        """
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
                    return (futbinprice * self.sellceiling)
                else:
                    return (marketprice * self.sellceiling)
        txt.close()

        # If not found, return 0
        return 0

    def getWatchlistTransferlistSize(self):
        """
        Gets and stores users transfer list, watchlist size etc.
        For use in calculating available bids to make

        Parameters:
            none

        Returns:
            bidsallowed (int): number of bids able to make (max 50)
            bidstomake_eachplayers (int): number of bids to make on each, depending on input list size
        """

        # Click Transfer Market tab
        self.sleep_approx(1)
        self.driver.find_element(
            By.XPATH, '/html/body/main/section/nav/button[3]').click()
        self.sleep_approx(1)

        transferlist_selling = self.driver.find_element(
            By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[2]/span[2]').text
        transferlist_sold = self.driver.find_element(
            By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[3]/span[2]').text
        transferlist_totalsize = self.driver.find_element(
            By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[1]/span[1]').text

        watchlist_winning = self.driver.find_element(
            By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[2]/span[2]').text
        watchlist_outbid = self.driver.find_element(
            By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[3]/span[2]').text
        watchlist_totalsize = self.driver.find_element(
            By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]/div[2]/div/div[1]/span[1]').text

        num_coins = self.driver.find_element(
            By.XPATH, '/html/body/main/section/section/div[1]/div[1]/div[1]').text

        self.user_transferlist_selling = int(transferlist_selling)
        self.user_transferlist_sold = int(transferlist_sold)
        self.user_transferlist_totalsize = int(transferlist_totalsize)

        self.user_watchlist_winning = int(watchlist_winning)
        self.user_watchlist_outbid = int(watchlist_outbid)
        self.user_watchlist_totalsize = int(watchlist_totalsize)

        self.user_num_coins = str(num_coins)

        data = [self.user_watchlist_winning, self.user_watchlist_outbid, self.user_watchlist_totalsize,
                self.user_transferlist_selling, self.user_transferlist_sold, self.user_transferlist_totalsize, num_coins]

        playerlist = self.getPlayerListFromGUI()
        num_players_to_bid_on = len(playerlist)
        self.user_num_target_players = num_players_to_bid_on

        if (num_players_to_bid_on != 1):
            bidsallowed = 50 - int(data[2])
            bidstomake_eachplayer = round(
                bidsallowed/num_players_to_bid_on) - 1

            self.user_num_bids_each_target = bidstomake_eachplayer
        elif (num_players_to_bid_on == 1):
            bidsallowed = 50 - int(data[2])
            bidstomake_eachplayer = bidsallowed

            self.user_num_bids_each_target = bidstomake_eachplayer
        else:
            bidsallowed = 0
            bidstomake_eachplayer = 0
            log_event(self.queue, "Error fetching watchlist / TList size")

        log_event(self.queue, "Bid to make on each player: " +
                  str(bidstomake_eachplayer))
        return bidsallowed, bidstomake_eachplayer

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Watchlist methods

    def getWatchlistSummary(self):
        """
        Analyzes all relevant info on watchlist - num players won, expired, currently active. 
        Stores values in user var's for display on GUI.

        Location: 
            watchlist

        Returns:
            num_players_won (int): The number of players won.
        """
        players = self.getAllPlayerInfoWatchlistFull()

        # [ playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id ]
        num_players_won = 0
        num_players_expired = 0

        wonplayers_sellprice_total = 0
        wonplayers_boughtprice_total = 0
        for p in players:
            p_bidstatus = p[1]
            p_id = p[8]
            p_boughtprice = p[5]
            p_sellprice = self.getPlayerSellPrice(p_id)

            if "won" in p_bidstatus:
                num_players_won += 1
                wonplayers_sellprice_total += p_sellprice
                wonplayers_boughtprice_total += p_boughtprice
            if "expired" in p_bidstatus:
                num_players_expired += 1

        # TODO if num players lost deviates from players won, notify other autobidder is likely on player
        projectedprofit = wonplayers_sellprice_total - wonplayers_boughtprice_total
        self.user_players_won += num_players_won
        # self.user_projected_profit += projectedprofit

        log_event(self.queue, "Players won: " + str(num_players_won))
        log_event(self.queue, "Players lost: " + str(num_players_expired))
        log_event(self.queue, "Total investment:   " +
                  str(wonplayers_boughtprice_total))
        log_event(self.queue, "Total proj. return: " +
                  str(wonplayers_sellprice_total))
        log_event(self.queue, "Projected Profit:   " + str(projectedprofit))

        return num_players_won

    def getAllPlayerInfoWatchlist(self):
        """
        Method returns info for 5 players closest to expiration.
        If any player is Processing, method returns string "Processing".

        Location: 
            watchlist

        Returns:
           playerdata (list): [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
        """
        status = self.checkState("watchlist")
        if status:
            try:
                players_on_page = self.driver.find_elements_by_tag_name(
                    "li.listFUTItem")
                # page = self.driver.find_elements_by_tag_name("h1.title")
                page = self.driver.find_element(
                    By.XPATH, "/html/body/main/section/section/div[1]/h1").text

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
                                curbid_or_finalsoldprice = curbid_or_finalsoldprice.replace(
                                    ",", "")

                            curbid_or_finalsoldprice = int(
                                curbid_or_finalsoldprice)
                            sum_of_all_current_bids_on_watchlist += curbid_or_finalsoldprice

                            # clean buy now
                            if "," in buynow:
                                buynow = buynow.replace(",", "")
                            buynow = int(buynow)

                        id = self.getPlayerID(name, rating)
                        if (id == 0):
                            log_event(self.queue, "Error - ID not found in Targets, general id search found for name " + str(
                                name) + " rating" + str(rating))
                        info = [playernumber, bidstatus, rating, name,
                                startprice, curbid_or_finalsoldprice, buynow, time, id]
                        playerdata.append(info)
                    playernumber += 1
                self.user_sum_of_all_current_bids_on_watchlist = sum_of_all_current_bids_on_watchlist

                return playerdata
            except:
                # If method reaches here, the first card on watchlist likely dissappeared in the middle of parsing
                return "processing"

    def getAllPlayerInfoWatchlistFull(self):
        """
        Method returns info for ALL players on watchlist (not just top 6)
        If any player is Processing, method returns string "Processing".

        Location: 
            watchlist

        Returns:
           playerdata (list): [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
        """
        status = self.checkState("watchlist")
        if status:
            try:
                players_on_page = self.driver.find_elements_by_tag_name(
                    "li.listFUTItem")
                # page = self.driver.find_elements_by_tag_name("h1.title")
                page = self.driver.find_element(
                    By.XPATH, "/html/body/main/section/section/div[1]/h1").text

                playerdata = []
                playernumber = 1
                sum_of_all_current_bids_on_watchlist = 0
                for card in players_on_page:
                    # Only look at top 5 players
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
                            curbid_or_finalsoldprice = curbid_or_finalsoldprice.replace(
                                ",", "")

                        curbid_or_finalsoldprice = int(
                            curbid_or_finalsoldprice)
                        sum_of_all_current_bids_on_watchlist += curbid_or_finalsoldprice

                        # clean buy now
                        if "," in buynow:
                            buynow = buynow.replace(",", "")
                        buynow = int(buynow)

                        id = self.getPlayerID(name, rating)
                        if (id == 0):
                            log_event(self.queue, "Error - ID not found in Targets, general id search found for name " + str(
                                name) + " rating" + str(rating))
                        info = [playernumber, bidstatus, rating, name,
                                startprice, curbid_or_finalsoldprice, buynow, time, id]
                        playerdata.append(info)
                    playernumber += 1
                self.user_sum_of_all_current_bids_on_watchlist = sum_of_all_current_bids_on_watchlist

                return playerdata
            except:
                # If method reaches here, the first card on watchlist likely dissappeared in the middle of parsing
                return "processing"

    def makebid_individualplayerWatchlist(self, playernumber, bidprice):
        """
        Outbids player on watchlist

        Location:
            watchlist
        Parameters:
            playernumber (int): index/location/row of player to outbid.
            bidprice (int): price to bid, if applicable

        Returns:
            ComplexNumber: A complex number which contains the sum.
        """
        # /html/body/div[4]/section/div/div/button[1]
        # https://i.gyazo.com/317c7fa554d3ab5e8fd6d48dd6337b41.png
        status = self.checkState("watchlist")
        if status:
            try:
                # page = self.driver.find_elements_by_tag_name("h1.title")
                page = self.driver.find_element(
                    By.XPATH, "/html/body/main/section/section/div[1]/h1").text

                self.sleep_approx(1)
                originalbid = bidprice

                playerbutton = "/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li[" + str(
                    playernumber) + "]/div"

                self.driver.find_element_by_xpath(playerbutton)
                self.driver.find_element_by_xpath(playerbutton).click()
                self.sleep_approx(0.5)

                try:
                    # Click make bid
                    WebDriverWait(self.driver, 30).until(
                        EC.visibility_of_element_located(
                            (By.XPATH, '/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/button[1]'))
                    )
                    self.driver.find_element(
                        By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/button[1]").click()

                    self.sleep_approx(1)
                    # Check if "highest bidder" glitch occurred
                    overbid_glitch = self.check_exists_by_xpath(
                        "/html/body/div[4]/section/div/div/button[1]")
                    if overbid_glitch:
                        cancel_btn = self.driver.find_element_by_xpath(
                            "/html/body/div[4]/section/div/div/button[1]")
                        cancel_btn.click()
                        self.sleep_approx(1)
                except:
                    log_event(self.queue, "Bid method failed")

                if (page == "TRANSFER TARGETS"):
                    # self.sleep_approx(1)
                    curbidprice_afterbidding = self.driver.find_element(
                        By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[1]/div/div[2]/span[2]").text
                    if "," in curbidprice_afterbidding:
                        curbidprice_afterbidding = curbidprice_afterbidding.replace(
                            ",", "")
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
                log_event(self.queue, "makebid_individualplayerWatchlist error")

    def refreshPageAndGoToWatchlist(self):
        """
        Refreshes web app and goes back to  watchlist.
        Used during bid wars, when "Bid Status not Updated" error occurs.

        """
        try:
            self.sleep_approx(1)
            self.user_requests_made += 1
            self.driver.refresh()

            wait_for_shield_invisibility(self.driver)

            WebDriverWait(self.driver, 30).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, 'icon-transfer'))
            )

            wait_for_shield_invisibility(self.driver)

            self.sleep_approx(3)

            log_event(self.queue, "Going back to watchlist")
            self.go_to_watchlist()
        except:
            log_event(self.queue, "Exception retrying refreshPageGoToWatchlist")
            # TODO could be dangerous when stuck in infinite loop
            self.refreshPageAndGoToWatchlist()

    def get_num_activebids(self):
        """
        Returns number of active bids. Also stores number won, expired, etc. for display on GUI

        Location: 
            watchlist

        Returns:
            activebids_counter (int): number of active bids.
        """
        try:
            players = self.driver.find_elements_by_tag_name("li.listFUTItem")
            playernumber = 1

            activebids_counter = 0
            expired_counter = 0
            won_counter = 0
            for player in players:
                bidStatus = player.get_attribute("class")
                if "highest-bid" in bidStatus:
                    activebids_counter += 1
                elif "outbid" in bidStatus:
                    activebids_counter += 1
                elif "expired" in bidStatus:
                    expired_counter += 1
                elif "won" in bidStatus:
                    won_counter += 1

            self.user_activebids = activebids_counter
            return activebids_counter
        except:
            return 1

    def send_won_players_to_transferlist(self):
        """
        Sends won players to the transfer list

        Location: 
            watchlist

        """
        sleep(5)
        playerswon = self.getWatchlistSummary()
        self.clearExpired()

        try:
            players_to_send_to_transferlist = True
            while players_to_send_to_transferlist:
                # Check if topmost player exists that should be listed
                topmost_player_location = "/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div"
                p_exists = self.check_exists_by_xpath(topmost_player_location)
                if (p_exists == False):
                    players_to_send_to_transferlist = False
                # Send each to transfer list
                else:
                    self.sleep_approx(1)
                    sendtotransferlist_location = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[3]/button[8]"
                    self.driver.find_element(
                        By.XPATH, topmost_player_location).click()
                    self.sleep_approx(1)
                    self.driver.find_element(
                        By.XPATH, sendtotransferlist_location).click()
                    self.sleep_approx(1)
        except:
            log_event(self.queue, "Error sending won p to TL")

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Transferlist methods

    def getTransferListSummary(self):
        """
        Analyzes all relevant info on TL - value of players, num players etc.
        Opens Futbin tab via chromedriver to fetch price, to avoid Futbin blocking user IP by overdoing their API.
        Returns dict of all their prices + all relevant info.

        # TODO switch back to json call so no interrupt while running in background
        Stores dictionairy as class object.

        Location:
            transfer list

        Returns:
            intel = a list consisting of the following, where "p" means "player":
                p_ids_and_prices,
                num_p_sold,
                num_p_expired,
                num_p_unlisted,
                num_p_listed,
                sold_p_value,
                expired_p_value,
                unlisted_p_value,
                listed_p_value
        """
        p_ids_and_prices = {}
        players = self.getAllPlayerInfoTransferlist()

        # Get IDs of all players
        log_event(self.queue, "Gathering player prices... ")
        for p in players:
            p_bidstatus = p[1]
            p_id = p[8]
            # removed Filter for unlisted / expired players
            if p_id not in p_ids_and_prices:
                p_sellprice = self.getPlayerSellPrice(p_id)
                # If sell price returns 0, need to fetch from Futbin
                if p_sellprice == 0:
                    p_sellprice = self.getFutbinPrice_opentab(p_id)
                    self.sleep_approx(5)  # Delay iteration to not anger futbin
                # Add player ID and price to dict
                p_ids_and_prices[p_id] = p_sellprice

        for p_id in p_ids_and_prices:
            p_price = p_ids_and_prices[p_id]
            p_name = self.getPlayerCardName(p_id)
            log_event(self.queue, str(p_name) + " - #" +
                      str(p_id) + " Price " + str(p_price))

        num_p_sold = 0
        num_p_expired = 0
        num_p_unlisted = 0
        num_p_listed = 0

        sold_p_value = 0
        expired_p_value = 0
        unlisted_p_value = 0
        listed_p_value = 0

        for p in players:
            p_bidstatus = p[1]
            p_id = p[8]
            p_soldprice = p[5]  # is 0 if unlisted
            p_sellprice = int(p_ids_and_prices[p_id])

            if "won" in p_bidstatus:
                num_p_sold += 1
                sold_p_value += p_soldprice
            if "expired" in p_bidstatus:
                num_p_expired += 1
                expired_p_value += p_sellprice
            if (p_bidstatus == "listFUTItem"):
                num_p_unlisted += 1
                unlisted_p_value += p_sellprice
            if (p_bidstatus == "listFUTItem has-auction-data"):
                num_p_listed += 1
                listed_p_value += p_sellprice

        log_event(self.queue, "Players sold:     " + str(num_p_sold))
        log_event(self.queue, "Players expired:  " + str(num_p_expired))
        log_event(self.queue, "Players listed: " + str(num_p_listed))
        log_event(self.queue, "Players unlisted: " + str(num_p_unlisted))
        log_event(self.queue, " - - - ")
        log_event(self.queue, "Sold players value:     " + str(sold_p_value))
        log_event(self.queue, "Expired players value:  " +
                  str(expired_p_value))
        log_event(self.queue, "Unlisted players value: " +
                  str(unlisted_p_value))
        log_event(self.queue, "Listed players value:   " + str(listed_p_value))

        # TODO subtract bought price
        self.user_players_won += int(num_p_unlisted)
        self.p_ids_and_prices = p_ids_and_prices
        intel = [p_ids_and_prices, num_p_sold, num_p_expired, num_p_unlisted,
                 num_p_listed, sold_p_value, expired_p_value, unlisted_p_value, listed_p_value]
        return intel

    def getTransferListSummaryWithoutPrices(self):
        """
        (same as above, but doesn't fetch futbin prices)
        Analyzes all relevant info on TL - value of players, num players etc.
        Returns dict of all their prices + all relevant info
        # TODO switch back to json call so no interrupt while running in background
        Stores dictionairy as class object.

        Location:
            transfer list

        Returns:
            num_p_sold = number of players sold.
            num_p_expired = number of players expired.
            num_p_unlisted = number of players unlisted.
            num_p_listed = number of players currently listed.
        """
        players = self.getAllPlayerInfoTransferlist()

        num_p_sold = 0
        num_p_expired = 0
        num_p_unlisted = 0
        num_p_listed = 0
        sold_p_value = 0

        for p in players:
            p_bidstatus = p[1]
            p_id = p[8]
            p_soldprice = p[5]  # is 0 if unlisted

            if "won" in p_bidstatus:
                num_p_sold += 1
                sold_p_value += p_soldprice
            if "expired" in p_bidstatus:
                num_p_expired += 1
            if (p_bidstatus == "listFUTItem"):
                num_p_unlisted += 1
            if (p_bidstatus == "listFUTItem has-auction-data"):
                num_p_listed += 1

        # TODO subtract bought price
        return num_p_sold, num_p_expired, num_p_unlisted, num_p_listed
 
    def getAllPlayerInfoTransferlist(self):
        """
        Logs all player data on transfer list, to be used later to find accurate buy now.
        TODO can be combined with other getInfo methods.

        Location:
            transfer list

        Returns:
            agg (list) where each item contains:
                date, 
                currenttime, 
                playernumber, 
                bidstatus, 
                rating, 
                name, 
                startprice, 
                curbid_or_finalsoldprice, 
                buynow, 
                time, 
                id
        """
        status = True
        if status:
            try:
                players_on_page = self.driver.find_elements_by_tag_name(
                    "li.listFUTItem")
                # page = self.driver.find_elements_by_tag_name("h1.title")
                page = self.driver.find_element(
                    By.XPATH, "/html/body/main/section/section/div[1]/h1").text

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
                            curbid_or_finalsoldprice = curbid_or_finalsoldprice.replace(
                                ",", "")

                        curbid_or_finalsoldprice = int(
                            curbid_or_finalsoldprice)

                        # clean buy now
                        if "," in buynow:
                            buynow = buynow.replace(",", "")
                        buynow = int(buynow)

                    id = self.getPlayerID(name, rating)
                    if (id == 0):
                        print("Unknown player on TL, unable to get ID")

                    info = [playernumber, bidstatus, rating, name,
                            startprice, curbid_or_finalsoldprice, buynow, time, id]
                    playerdata.append(info)

                    now = datetime.now()
                    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                    dt_string = dt_string.split(" ")
                    date = dt_string[0]
                    currenttime = dt_string[1]

                    agg = [date, currenttime, playernumber, bidstatus, rating,
                           name, startprice, curbid_or_finalsoldprice, buynow, time, id]

                    playernumber += 1

                return playerdata
            except:
                log_event(self.queue, "User error checking Transfer List")

    def relist_expired_players(self, p_ids_and_prices):
        """
        Relists expired players on transfer list.
        I still don't love my transfer listing method, this is probably the 3rd version...

        Location:
            transfer list

        Parameters:
            p_ids_and_prices (dict): Dictionary of prices returned by getTransferListSummary.

        """
        # TODO make this user configurable, like when I had Ronaldo on my transfer list
        players_to_list = True
        try:
            while players_to_list:
                # Check if topmost player exists that should be listed
                topmost_player_location_unlisted = "/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div"
                p_exists = self.check_exists_by_xpath(
                    topmost_player_location_unlisted)
                if (p_exists == False):
                    players_to_list = False
                else:
                    # Click topmost player
                    self.sleep_approx(2)
                    self.clickButton(topmost_player_location_unlisted)
                    self.sleep_approx(1)

                    # Click list for transfer
                    listfortransfer_location = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[1]/button"
                    self.clickButton(listfortransfer_location)
                    self.sleep_approx(1)

                    # Get player sell price
                    playerrating = int(self.getText(
                        "/html/body/main/section/section/div[2]/div/div/section/div/div/div[1]/div/div[2]/div/div/div[1]/div/div[7]/div[2]/div[1]"))
                    playercardname = self.getText(
                        "/html/body/main/section/section/div[2]/div/div/section/div/div/div[1]/div/div[2]/div/div/div[1]/div/div[4]")
                    playerid = self.getPlayerID(playercardname, playerrating)
                    sellprice = p_ids_and_prices[playerid]

                    startprice_loc = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[2]/div[2]/input"
                    buynow_loc = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/input"
                    listplayer_loc = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/button"

                    # Make sure text boxes are visible
                    self.scrollIntoView(listplayer_loc)
                    self.send_keys_and_sleep(buynow_loc, sellprice)
                    self.send_keys_and_sleep(startprice_loc, sellprice-100)

                    # Final step - list player on market
                    self.clickButton(listplayer_loc)
        except:
            log_event(self.queue, " error 204, should be ok tho")

    def list_unlisted_players(self, p_ids_and_prices):
        """
        Lists unlisted players on transfer list.

        Location:
            transfer list

        Parameters:
            p_ids_and_prices (dict): Dictionairy of prices returned by getTransferListSummary.
        """
        players_to_list = True
        try:
            while players_to_list:
                # Check if topmost player exists that should be listed
                topmost_player_location_unlisted = "/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div"
                p_exists = self.check_exists_by_xpath(
                    topmost_player_location_unlisted)
                if (p_exists == False):
                    players_to_list = False
                else:
                    # Click topmost player
                    self.sleep_approx(2)
                    self.clickButton(topmost_player_location_unlisted)
                    self.sleep_approx(1)

                    # Get bought price (to log profit)
                    bought_player = self.check_exists_by_xpath(
                        "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[1]/div[2]/div/span[2]")
                    bought_price = 0
                    if bought_player:
                        playercardname = self.getText(
                            "/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div/div[1]/div[2]")

                        bought_price = self.getText(
                            "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[1]/div[2]/div/span[2]")

                        # Detect if player was packed
                        if (len(str(bought_price)) != 0):
                            if "," in bought_price:
                                bought_price = int(
                                    bought_price.replace(",", ""))
                        else:
                            bought_price = 0

                    # Click list for transfer
                    listfortransfer_location = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[1]/button"
                    self.clickButton(listfortransfer_location)
                    self.sleep_approx(1)

                    # Get player sell price
                    playerrating = int(self.getText(
                        "/html/body/main/section/section/div[2]/div/div/section/div/div/div[1]/div/div[2]/div/div/div[1]/div/div[7]/div[2]/div[1]"))
                        
                    playercardname = self.getText(
                        "/html/body/main/section/section/div[2]/div/div/section/div/div/div[1]/div/div[2]/div/div/div[1]/div/div[4]")
                    playerid = self.getPlayerID(playercardname, playerrating)
                    sellprice = int(p_ids_and_prices[playerid])
                    log_event(self.queue, "Sell price to use for " +
                              str(playercardname) + ": " + str(sellprice))

                    # Log profit (only if player wasn't packed)
                    bought_price = int(bought_price)
                    if (bought_price != 0):
                        # Sell price * .95 to account for EA tax
                        potential_profit = (sellprice*0.95) - bought_price
                        log_event(self.queue, "Sell price " + str(playercardname) +
                                  ": " + str(sellprice) + " Bought: " + str(bought_price))
                        log_event(self.queue, "Sell price * .95 " +
                                  str(playercardname) + ": " + str(sellprice*.95))
                        self.user_projected_profit += potential_profit
                        self.update_autobidder_logs()

                    startprice_loc = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[2]/div[2]/input"
                    buynow_loc = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/input"
                    listplayer_loc = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/button"

                    # Make sure text boxes are visible
                    self.scrollIntoView(listplayer_loc)
                    self.send_keys_and_sleep(buynow_loc, sellprice)
                    self.send_keys_and_sleep(startprice_loc, sellprice-100)

                    # Final step - list player on market
                    self.clickButton(listplayer_loc)
        except Exception as e:
            log_event(self.queue, " err 203, should be ok tho ")
            log_event(self.queue, e)


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Button clicks / getters

    def findElement_and_wait(self, xpath):
        """
        Finds element and waits for visibility.

        Location:
            anywhere

        Parameters:
            xpath (str): The object's XPATH.

        Returns:
            none
        """
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

    def scrollIntoView(self, button_xpath):
        """
        Finds element and scrolls into view (necessary if on small screen).

        Location:
            anywhere

        Parameters:
            xpath (str): The object's XPATH.

        Returns:
            none
        """

        button = self.driver.find_element(By.XPATH, button_xpath)
        self.driver.execute_script(
            "arguments[0].scrollIntoView(true);", button)
        # WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, button_xpath)))

    def clickButton(self, xpath):
        """
        Clicks button via XPATH.

        Location:
            anywhere

        Parameters:
            xpath (str): The object's XPATH.
        """
        WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, xpath))).click()
        self.sleep_approx(1)

    def send_keys_and_sleep(self, xpath, price):
        """
        Clicks textbox and sends key value.

        Location:
            anywhere

        Parameters:
            xpath (str): The object's XPATH.
            price (str): The string to enter (typically price).

        Returns:
            none
        """
        self.sleep_approx(1)
        textbox = self.driver.find_element(By.XPATH, xpath)
        textbox.click()
        self.sleep_approx(0.5)
        textbox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        price = int(round(price, -2))
        textbox.send_keys(price)
        self.sleep_approx(1)

    def getText(self, xpath):
        """
        Retrieves text of web object.

        Location:
            anywhere

        Parameters:
            xpath (str): The object's XPATH.

        Returns:
            text (str): text at given XPATH.
        """
        text = self.driver.find_element(By.XPATH, xpath).text
        return text

    def clearSold(self):
        """
        Clicks 'clear sold' button.

        Location:
            transfer list
        """
        try:
            self.sleep_approx(1)
            self.driver.find_element(
                By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[1]/header/button").click()
            self.sleep_approx(1)
        except:
            log_event(self.queue, "No sold players to clear")
            self.sleep_approx(1)

    def clearExpired(self):
        """
        Clicks 'clear expired' button.

        Location:
            watch list
        """
        self.sleep_approx(1)
        playersOnPage = self.driver.find_elements_by_tag_name("li.listFUTItem")

        num_players_expired = 0
        for player in playersOnPage:
            bidStatus = player.get_attribute("class")
            bidStatus = str(bidStatus)

            if "expired" in bidStatus:
                num_players_expired += 1

        if num_players_expired > 0:
            clearExpired = self.driver.find_element(
                By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[4]/header/button")
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", clearExpired)
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[4]/header/button"))).click()
            self.sleep_approx(1)
            log_event(self.queue, "Cleared expired")
            self.sleep_approx(1)

    def clickSearch(self):
        """
        Clicks 'Search' button.

        Location:
            transfer market search page
        """
        self.sleep_approx(1)
        self.driver.find_element(
            By.XPATH, '(//*[@class="button-container"]/button)[2]').click()
        self.user_requests_made += 1

    def clickBack(self):
        """
        Clicks 'back' button.

        Location:
            transfer market
        """
        self.sleep_approx(1)
        self.driver.find_element(
            By.XPATH, '/html/body/main/section/section/div[1]/button[1]').click()
        self.sleep_approx(1)


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Navigation

    def go_to_transfer_market(self):
        """
        Clicks Transfer Market button on sidebar.

        Location:
            anywhere
        """
        try:
            self.driver.find_element(By.CLASS_NAME, 'icon-transfer').click()

            sleeptime = random.randint(1, 5)

            self.sleep_approx(sleeptime)
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, 'ut-tile-transfer-market'))
            )
            self.sleep_approx(sleeptime)
            self.driver.find_element(
                By.CLASS_NAME, 'ut-tile-transfer-market').click()
        except:
            log_event(self.queue, "Exception retrying go_transfer_market")

    def go_to_watchlist(self):
        """
        Clicks Watchlist button on sidebar.

        Location:
            anywhere
        """
        try:
            self.sleep_approx(0.5)
            self.driver.find_element(
                By.XPATH, '/html/body/main/section/nav/button[3]').click()
            self.sleep_approx(0.5)
            self.driver.find_element(
                By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]').click()
            self.sleep_approx(0.5)
        except:
            log_event(self.queue, "Bot broke - go_to_watchlist method")

    def go_to_transferlist(self):
        """
        Clicks Transer List grid button on Transfer Market.

        Location:
            transfer market
        """
        if self.transferlistInfiniteLoopCounter < 5:
        
        
            try:
                self.sleep_approx(2)
                self.driver.find_element(
                    By.XPATH, "/html/body/main/section/nav/button[3]").click()
                self.sleep_approx(2)
                print("click transfer list button")
                self.driver.find_element(
                    By.XPATH, "/html/body/main/section/section/div[2]/div/div/div[3]").click()
                self.sleep_approx(1)
            except:
                self.transferlistInfiniteLoopCounter+=1
                log_event(self.queue, "Exception retrying go_to_transferlist")
                self.go_to_transferlist()
        else:
            log_event(self.queue, "infinite loop detected")


    def go_to_login_page(self):
        """
        Clicks login button on login page.

        Location:
            login page
        """
        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//*[@class="ut-login-content"]//button'))
        )
        print("Logging in...")

        self.sleep_approx(random.randint(5, 10))
        self.driver.find_element(
            By.XPATH, '//*[@class="ut-login-content"]//button').click()

        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'email'))
        )


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ General

    def getUserConfig(self):
        """
        Fetches user config variables from config.json.
        Also updates config options on GUI if they changed on backend.

        Location:
            anywhere
        """

        # Load Autobidder stats
        userconfig_json = open('./data/config.json')
        json1_str = userconfig_json.read()
        configops = json.loads(json1_str)[0]

        config_choices = []
        for key, value in configops.items():
            config_choices.append(value)

        conserve_bids = config_choices[0]
        sleep_time = config_choices[1]
        botspeed = config_choices[2]
        bidexpiration_ceiling = config_choices[3]
        buyceiling = config_choices[4]
        sellceiling = config_choices[5]

        sleep_time = int(sleep_time)
        botspeed = float(botspeed)
        conserve_bids = int(conserve_bids)
        bidexpiration_ceiling = int(bidexpiration_ceiling)
        buyceiling = float(buyceiling/100)
        sellceiling = float(sellceiling/100)

        if (buyceiling > 1):
            log_event(self.queue, "buy ceiling greater than 1: " +
                      str(buyceiling))
            log_event(self.queue, "setting it to .85: ")
            buyceiling = 0.85

        if (sellceiling > 1):
            log_event(self.queue, "sell ceiling greater than 1: " +
                      str(sellceiling))
            log_event(self.queue, "setting it to .95 ")
            sellceiling = 0.95

        self.conserve_bids = conserve_bids
        self.sleep_time = sleep_time
        self.botspeed = botspeed
        self.bidexpiration_ceiling = bidexpiration_ceiling
        self.buyceiling = buyceiling
        self.sellceiling = sellceiling

        # Return values but this really shouldn't be used - only used on initialization
        return conserve_bids, sleep_time, botspeed, bidexpiration_ceiling, buyceiling, sellceiling

    def checkState(self, desiredPage):
        """
        Checks if user is on desired page of web app, to avoid infinite loops on user intervention.

        Location:
            anywhere

        Parameters:
            desiredPage (str): watchlist, transfermaket, or transferlist

        Returns:
            True or False
        """
        try:
            # page = self.driver.find_elements_by_tag_name("h1.title")
            page = self.driver.find_element(
                By.XPATH, "/html/body/main/section/section/div[1]/h1").text
            page = str(page)
            page = page.lower()

            if (desiredPage == "watchlist"):
                if (page == "transfer targets"):
                    return True
                else:
                    log_event(
                        self.queue, "Unexpectedly not on Watchlist, stopping")
                    return False

            elif (desiredPage == "transfermarket"):
                if (page == "search results"):
                    return True
                else:
                    log_event(
                        self.queue, "Unexpectedly not on Transfer Market, stopping")
                    return False

            elif (desiredPage == "transferlist"):
                if (page == "transfer list"):
                    return True
                else:
                    log_event(
                        self.queue, "Unexpectedly not on Transfer list, stopping")
                    return False
            else:
                log_event(self.queue, "checkState was passed invalid location")
        except:
            log_event(self.queue, "Error checking state")

    def check_exists_by_xpath(self, xpath):
        """
        Checks if element exists by XPATH.
        I think this method is unused. 

        Location:
            anywhere

        Parameters:
            xpath (str): XPATH of web object.

        Returns:
            True or False
        """
        try:
            self.driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True

    def get_futbin_price_lastupdated(self, ID):
        """
        Fetches player price and updated via Futbin API endpoint.
        No longer used as often IP banned while debugging.

        TODO make Playstation price an option.

        Location:
            anywhere
        Parameters:
            ID (int): Player's internal ID.
        Returns:
            futbinprice (int): Player's price on Xbox.
            lastupdated (str): Seconds since player price was last updated on Futbin.
        """
        r = requests.get(
            'https://www.futbin.com/22/playerPrices?player={0}'.format(ID))
        # r = requests.get('https://www.futbin.com/20/playerGraph?type=daily_graph&year=20&player={0}'.format(ID))
        data = r.json()

        price = data[str(ID)]["prices"]["xbox"]["LCPrice"]
        lastupdated = data[str(ID)]["prices"]["xbox"]["updated"]

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
        return price, lastupdated

    def update_autobidder_logs(self):
        """
        Updates GUI with current user config vars.
        Wanted more control over how many reads/writes the bot makes, so made this a separate method.

        Location:
            anywhere
        """
        # also update user config vars
        self.getUserConfig()

        try:
            num_coins = self.driver.find_element(
                By.XPATH, '/html/body/main/section/section/div[1]/div[1]/div[1]').text
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

    def clearOldMarketLogs(self):
        """
        Clears market logs in data/market_logs.txt in preparation for next search run.

        Location:
            transfer market
        """
        file = open("./data/market_logs.txt", "r+")
        file.truncate(0)
        file.close()

    def clearOldUserData(self):
        """
        Sets frontend GUI metrics to 0.
        Since bot doesn't know when it is exited, user vars will remain from previous session.

        Location:
            anywhere
        """
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
        """
        Fetches futbin data and updates data/player_list.txt.
        Opens new tab (kinda annoying)

        Location:
            anywhere
        """
        browser = self.driver
        driver = self.driver

        tab_url = futbin_url

        browser.execute_script("window.open('');")
        browser.switch_to.window(browser.window_handles[1])
        browser.get(tab_url)

        name = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, "/html/body/div[8]/div[15]/div/div/div[1]/div[2]/table/tbody/tr[2]/td"))).text
        team = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, "/html/body/div[8]/div[15]/div/div/div[1]/div[2]/table/tbody/tr[3]/td/a"))).text
        nation = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, "/html/body/div[8]/div[12]/div[3]/div[1]/div/ul/li[1]/a"))).text
        cardtype = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, "/html/body/div[8]/div[15]/div/div/div[1]/div[2]/table/tbody/tr[12]/td"))).text
        rating = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, "/html/body/div[8]/div[13]/div[2]/div/div/div[1]/div/a/div/div[2]"))).text
        cardname = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, "/html/body/div[8]/div[13]/div[2]/div/div/div[1]/div/a/div/div[3]"))).text
        position = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, "/html/body/div[8]/div[13]/div[2]/div/div/div[1]/div/a/div/div[4]"))).text

        internals_location = driver.find_element(
            By.XPATH, "/html/body/div[8]/div[5]/div")
        internal_id = int(internals_location.get_attribute("data-baseid"))
        futbin_id = internals_location.get_attribute("data-id")

        # price, lastupdated = get_futbin_price_lastupdated(fifa_id)

        r = requests.get(
            'https://www.futbin.com/22/playerPrices?player={0}'.format(internal_id))

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
        futbin_id = int(futbin_id)
        market_price = 0
        buy_pct = .85
        agg = [name, cardname, rating, team, nation, cardtype, position,
               internal_id, futbin_id, price, lastupdated, market_price, buy_pct]

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

        log_event(self.queue, "Added player " + str(cardname))

        # ~ ~ ~ ~ ~ ~ ~ Close the futbin tab ~ ~ ~ ~ ~
        browser.close()

        # Switch back to the first tab with URL A
        browser.switch_to.window(browser.window_handles[0])
        # log_event(self.queue, "Fetched player info")

    def sleep_approx(self, seconds):
        """
        Randomizes sleep to avoid detection.
        """
        upperbound = (seconds+0.2)*10000
        if (seconds >= 1):
            lowerbound = (seconds-0.2)*10000
        else:
            lowerbound = seconds*10000

        sleeptime = random.randint(lowerbound, upperbound)
        sleeptime = sleeptime/10000
        sleeptime = sleeptime*.8

        if (self.botspeed == 1.25):
            sleeptime = sleeptime*.75
        elif (self.botspeed == 1.5):
            sleeptime = sleeptime*.5
        sleep(sleeptime)

    def getPlayerListFromGUI(self):
        """
        Retrieves player list from GUI.

        Returns:
            playerlist (list)
        """
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

    def getPlayerID(self, cardname, rating):
        """
        Retrieves player internal ID from card name and rating

        Location:
            anywhere!

        Parameters:
            cardname (str): Player's cardname
            rating (int): Player's rating

        Returns:
            id (int): Internal database ID to be used to identify players since there are lots of identical last names. 
            Returns 0 if player ID not found. Current database is from game's initial release, so in-forms, UCL, etc will return 0
        """
        inputoverall = int(rating)
        inputcardname = cardname.lower()

        # First attempts to find ID in user input list
        for player in self.getPlayerListFromGUI():
            p_overall = int(player[2])
            p_cardname = player[1]
            p_cardname = p_cardname.lower()

            diff = p_overall - inputoverall

            pid = int(player[7])

            if (diff == 0):
                if (p_cardname == inputcardname):
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
                        return id
                    if ((cardname == firstname) or (cardname == lastname)):
                        return id
                    if (fullname == cardname):
                        return id

            # If not found, raise error
            log_event(self.queue, "Player ID not found for: " +
                      str(cardname) + " " + str(rating))
            return 0

    def getFutbinID(self, internalid):
        """
        Returns futbin ID via internal EA id (there are two separate databases!).

        Parameters:
            internalid (int): Players internal EA id.

        Returns:
            futbinid (int): Players futbin ID.
        """
        internalid = int(internalid)
        mydict = pd.read_csv('./data/fut_bin21_players.csv',
                             header=None, index_col=0, squeeze=True).to_dict()
        futbinid = mydict[internalid]
        return futbinid

    def getFutbinPrice_opentab(self, internalid):
        """
        Fetches futbin price by opening a new tab (to avoid IP ban)

        Parameters:
            internalid (int): Player's internal EA id.

        Returns:
            price (int): Player's futbin price.
        """
        browser = self.driver
        driver = self.driver

        futbinid = self.getFutbinID(internalid)
        futbin_url = "https://www.futbin.com/22/player/" + str(futbinid)

        tab_url = futbin_url

        browser.execute_script("window.open('');")
        browser.switch_to.window(browser.window_handles[1])
        browser.get(tab_url)

        price = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.XPATH, "/html/body/div[8]/div[13]/div[2]/div/div/div[2]/div[3]/div/div[3]/span/span"))).text
        price = price.replace(",", "")
        price = int(price)

        # ~ ~ ~ ~ ~ ~ ~ Close the futbin tab ~ ~ ~ ~ ~
        browser.close()

        # Switch back to the first tab with URL A
        browser.switch_to.window(browser.window_handles[0])

        return price

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ NON CLASS METHODS


def getText(driver, xpath):
    result = driver.get_element_by_xpath(xpath).text
    return result


def clickElement(driver, xpath):
    driver.get_element_by_xpath(xpath).click()


def login(queue, driver, user, email_credentials):
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located(
            (By.XPATH, '//*[@class="ut-login-content"]//button'))
    )
    # print("Logging in...")

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
    driver.find_element(By.ID, 'btnLogin').click()
    sleep(3)

    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(
            (By.XPATH, '/html/body/div[2]/form/div[2]/div/div/div/div[2]/a[1]'))
    ).click()

    access_code = get_access_code(queue, email_credentials)

    driver.find_element(By.ID, 'oneTimeCode').send_keys(access_code)
    sleep(1)
    driver.find_element(By.ID, 'btnSubmit').click()

    log_event(queue, "Logged in successfully!")
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'icon-transfer'))
    )
    sleep(2)


def get_access_code(queue, email_credentials):

    EA_EMAIL = "EA@e.ea.com"
    M = imaplib.IMAP4_SSL("imap.gmail.com")

    try:
        M.login(email_credentials["email"], email_credentials["password"])
    except imaplib.IMAP4.error:
        # print("Login to email failed")
        log_event(
            queue, "Unable to fetch access code from email (see ReadMe for help on this), enter it manually")
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

    log_event(queue, email_message['Subject'])

    access_code = ''.join(filter(str.isdigit, email_message['Subject']))

    return access_code


def wait_for_shield_invisibility(driver, duration=0.25):
    """
    Detects loading circle and waits for it to dissappear. 
    """
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located(
            (By.CLASS_NAME, 'ut-click-shield showing interaction'))
    )
    sleep(.25)


def log_event(queue, event):
    """
    Sends log to queue, which GUI handles and writes to txt file for display on GUI.
    The queue objects allows us to talk to the GUI from a separate threads, which is cool.
    This was a big breakthrough in functionality.

    Parameters:
        queue (queue): GUI's queue object
        event (str): Event log to write to data/gui_logs.txt
    """
    event = str(event)
    queue.put(event)


def clearOldUserData_nonclass():
    """
    Clears old user data, non class method.
    Same as other method but used in debugging if we don't have an active Helper object.
    """
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


def getFutbinDataAndPopulateTable(driver, queue, futbin_url):
    """
    Fetches futbin info - same as identical class method, but this is non class.
    Can't remember which one is currently used. 
    The reason is bc of threading.
    """
    browser = driver
    driver = driver

    tab_url = futbin_url

    browser.execute_script("window.open('');")
    browser.switch_to.window(browser.window_handles[1])
    browser.get(tab_url)

    name = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH, "/html/body/div[8]/div[15]/div/div/div[1]/div[2]/table/tbody/tr[2]/td"))).text
    team = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH, "/html/body/div[8]/div[15]/div/div/div[1]/div[2]/table/tbody/tr[3]/td/a"))).text
    nation = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH, "/html/body/div[8]/div[12]/div[3]/div[1]/div/ul/li[1]/a"))).text
    cardtype = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH, "/html/body/div[8]/div[15]/div/div/div[1]/div[2]/table/tbody/tr[12]/td"))).text
    rating = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH, "/html/body/div[8]/div[13]/div[2]/div/div/div[1]/div/a/div/div[2]"))).text
    cardname = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH, "/html/body/div[8]/div[13]/div[2]/div/div/div[1]/div/a/div/div[3]"))).text
    position = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH, "/html/body/div[8]/div[13]/div[2]/div/div/div[1]/div/a/div/div[4]"))).text

    internals_location = driver.find_element(
        By.XPATH, "/html/body/div[8]/div[5]/div")
    internal_id = int(internals_location.get_attribute("data-baseid"))
    futbin_id = internals_location.get_attribute("data-id")

    # price, lastupdated = get_futbin_price_lastupdated(fifa_id)

    r = requests.get(
        'https://www.futbin.com/22/playerPrices?player={0}'.format(internal_id))

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
    futbin_id = int(futbin_id)
    market_price = 0
    buy_pct = .85
    agg = [name, cardname, rating, team, nation, cardtype, position,
           internal_id, futbin_id, price, lastupdated, market_price, buy_pct]

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

    log_event(queue, "Added player " + str(cardname))

    # ~ ~ ~ ~ ~ ~ ~ Close the futbin tab ~ ~ ~ ~ ~
    browser.close()

    # Switch back to the first tab with URL A
    browser.switch_to.window(browser.window_handles[0])
    # log_event(self.queue, "Fetched player info")


def getUserConfigNonClass():
    """
    Fetches user config variables from config.json. (same as other method just nonclass, for use on GUI)
    Also updates config options on GUI if they changed on backend.

    Location:
        anywhere
    """

    # Load Autobidder stats
    userconfig_json = open('./data/config.json')
    json1_str = userconfig_json.read()
    configops = json.loads(json1_str)[0]

    config_choices = []
    for key, value in configops.items():
        config_choices.append(value)

    conserve_bids = config_choices[0]
    sleep_time = config_choices[1]
    botspeed = config_choices[2]
    bidexpiration_ceiling = config_choices[3]
    buyceiling = config_choices[4]
    sellceiling = config_choices[5]

    sleep_time = int(sleep_time)
    botspeed = float(botspeed)
    conserve_bids = int(conserve_bids)
    bidexpiration_ceiling = int(bidexpiration_ceiling)
    buyceiling = float(buyceiling/100)
    sellceiling = float(sellceiling/100)

    if (buyceiling > 1):
        buyceiling = 0.85

    if (sellceiling > 1):
        sellceiling = 1

    # Return values but this really shouldn't be used - only used on initialization
    return conserve_bids, sleep_time, botspeed, bidexpiration_ceiling, buyceiling, sellceiling