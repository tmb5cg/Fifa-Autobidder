import csv
from datetime import datetime
from decimal import Decimal
from time import sleep

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import ui
from selenium.webdriver.support.wait import WebDriverWait

import helpers
from helpers import *


class Autobidder:
    def __init__(self, driver, queue):
        self.driver = driver
        self.queue = queue
        self.playerlist = []
        self.helper = Helper(self.driver)

        # Get input list of target players
        src = "./data/player_list.txt"
        txt = open(src, "r", encoding="utf8")

        for aline in txt:
            values = aline.strip("\n").split(",")
            self.playerlist.append(values)
        txt.close()

        # Clear out old market data
        self.helper.clearOldUserData()

    def start(self):
        self.queue.put("Updating queue from inside autobidder...")
        log_event("Autobidder started")

        src = "./data/player_list.txt"
        txt = open(src, "r", encoding="utf8")


        self.playerlist2 = []
        for aline in txt:
            values = aline.strip("\n").split(",")
            self.playerlist2.append(values)
        txt.close()

        num_players_to_bid_on = len(self.playerlist2)

        bidsallowed, bidstomake_eachplayer = self.helper.getWatchlistTransferlistSize()
        # bidsallowed = 10
        bidstomake_eachplayer = 10

        self.helper.user_num_target_players = num_players_to_bid_on
        self.helper.user_num_bids_each_target = bidstomake_eachplayer
        self.helper.update_autobidder_logs()
        
        for player in self.playerlist2:
            # "Name", "Name on Card", "Rating", "Team", "Nation", "Type", "Position", "Internal ID", "Futbin ID", "Futbin Price", "Futbin LastUpdated", "Actual Market Price", "Buy Percent"
            fullname = player[0]
            cardname = player[1]
            cardoverall = player[2]

            self.helper.go_to_tranfer_market_and_input_parameters(cardname, fullname, cardoverall) 

            sleep(2)
            # Clear max bin
            input = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[6]/div[2]/input")
            input.click()
            sleep(0.3)
            input.send_keys(0)
            sleep(1)

            # Check if we have updated actual price in CSV
            futbinprice = int(player[9])
            marketprice = int(player[11])
            buy_percent = float(player[12])
            price_to_use = 0
            if (marketprice == 0):
                price_to_use = buy_percent * futbinprice
                log_event("Bidding on " + str(player[1]) + " up to FUTBIN price: " + str(futbinprice) + ". Will determine actual market price while searching. Purchase ceiling: " + str(price_to_use))
            else:
                price_to_use = buy_percent * marketprice
                log_event("Bidding on " + str(player[1]) + " up to MARKET price: " + str(marketprice) + ". Purchase ceiling: " + str(price_to_use))

            # Bid on players on current page -- 6 seconds spent in search tab
            self.helper.clickSearch()
            self.helper.bid_on_current_page(cardname, price_to_use, bidstomake_eachplayer, 0, "None")

            log_event("Finished bidding on:" + str(cardname))
            sleep(1)


        # Parse market data to find actual sell price 
        log_event("Parsing market data to find most accurate sell prices...")
        self.helper.get_lowestbin_from_searchdata()
 
        log_event("Going to watchlist. Time for war")
        self.helper.go_to_watchlist()
        self.manageWatchlist()


    def manageWatchlist(self):
        status = 1
        while (status == 1):
            # Make sure we are on watchlist, else break (for debugging)
            page = self.driver.find_element_by_xpath("/html/body/main/section/section/div[1]/h1").text
            if (page.lower() == "transfer targets"):
                self.helper.update_autobidder_logs()
                num_activebids = self.helper.get_num_activebids()
                if (num_activebids != 0):
                    # Evaluate 5 cards closest to expiration, returns "processing" if exception
                    active_bids = self.helper.getAllPlayerInfoWatchlist()
                    if (active_bids != "processing"):
                        firstplayer = active_bids[0]
                        # firstplayer = active_bids[1]
                        # firstplayer = active_bids[2]

                        firstplayer_timeremaining = firstplayer[7]
                        # secondplayer_timeremaining = firstplayer[7]
                        # thirdplayer_timeremaining = firstplayer[7]
                        # fourthplayer_timeremaining = firstplayer[7]
                        # Triple check that first player is not Processing (else will throw exception, redundant but necessary)
                        if (0 < firstplayer_timeremaining):
                            # If method reaches here, everything should be good to go...
                            # Iterate over cards on watchlist
                            for card in active_bids:
                                bidStatus = card[1]
                                if "outbid" in bidStatus:
                                    playername = card[3]
                                    playernumber = card[0]
                                    curbid = card[5]
                                    timeremainingseconds = card[7]
                                    timeremainingmins = timeremainingseconds/60
                                    id = card[8]
                                    sellprice = self.helper.getPlayerSellPrice(id)
                                    stopPrice = self.helper.getPlayerPriceCeiling(id)
                                    # log_event("Player outbid --> " + str(playername))
                                    if (self.helper.user_num_coins >= curbid+100):
                                        if (curbid < stopPrice):
                                            # log_event("Player outbid --> " + str(playername) + " --> proceed to outbid. Current bid of " + str(curbid) + " gives potential profit of " + str(sellprice - curbid) + " coins.")
                                            result = self.helper.makebid_individualplayerWatchlist(playernumber, curbid)
                                            if result == "Failure":
                                                log_event("Error outbidding " + str(playername) + ". Refreshing page")
                                                sleep(1)
                                                self.helper.refreshPageAndGoToWatchlist()
                                            if result == "Success":
                                                log_event("Outbid " + str(playername) + " | CurBid: " + str(curbid) + " | Stop: " + str(stopPrice) + " || Est. Profit: " + str(sellprice - curbid))
                                    else:
                                        # User doesn't have enough coins
                                        log_event("You don't have enough coins to continue bidding")
                                        status = 0
                else:
                    status = 0
                    # self.manageTransferlist()
            else: 
                status = 0
        log_event("No active bids, or not on watch list")
        self.manageTransferlist()

    def manageTransferlist(self):
        page = self.driver.find_element_by_xpath("/html/body/main/section/section/div[1]/h1").text
        if (page.lower() == "transfer targets"):
            log_event("Bidding round finished, will now send players to transfer list and list them!")
            # send won to transfer list
            sleep(3)

            try:
                # # Send won to Transfer list
                self.helper.send_won_players_to_transferlist()
                sleep(2)
                self.helper.clearExpired()
            except:
                log_event("error here line 160 autobidder.py")

            log_event("Sleeping for 2 minutes and heading back to war")
            sleep(60*2)
            self.start()
        else:
            log_event("Weird error, click start Autobidder again")

        # log_event("Sent won players to transfer list!")

        # Make sure we are still on watchlist
        # page = self.driver.find_element_by_xpath("/html/body/main/section/section/div[1]/h1").text
        # if (page.lower() == "transfer targets"):
        #     self.helper.send_won_players_to_transferlist()
        #     log_event("Sent won players to TL")
        #     self.helper.clearExpired()
        #     log_event("Cleared expired")
