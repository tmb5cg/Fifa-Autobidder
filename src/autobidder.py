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
        self.helper = Helper(self.driver, self.queue)

    def initializeBot(self):
        # On initializatin of bot object, clear old variables etc
        log_event(self.queue, "first time starting")
        self.helper.clearOldUserData()
        self.helper.setStartingCoins()
        sleep(3)
        self.start()

    def start(self):
        log_event(self.queue, "Autobidder started")

        # Clear market logs from previous run
        self.helper.clearOldMarketLogs()

        # Get player list
        self.playerlist2 = self.helper.getPlayerListFromGUI()

        bidsallowed, bidstomake_eachplayer = self.helper.getWatchlistTransferlistSize()
        # bidstomake_eachplayer = 10
        # log_event(self.queue, "Bids to make on each player hard set to 10")

        self.helper.user_num_target_players = len(self.playerlist2)
        self.helper.user_num_bids_each_target = bidstomake_eachplayer
        self.helper.update_autobidder_logs()

        continue_running = True
        for player in self.playerlist2:
            # "Name", "Name on Card", "Rating", "Team", "Nation", "Type", "Position", "Internal ID", "Futbin ID", "Futbin Price", "Futbin LastUpdated", "Actual Market Price", "Buy Percent"
            fullname = player[0]
            cardname = player[1]
            cardoverall = player[2]

            status = self.helper.go_to_tranfer_market_and_input_parameters(cardname, fullname, cardoverall)
            if (status == "error"):
                continue_running = False
                break

            sleep(2)
            # Clear max bin
            input = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[6]/div[2]/input")

            self.driver.execute_script("arguments[0].scrollIntoView(true);", input)
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[6]/div[2]/input"))).click()
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
                log_event(self.queue, "Bidding on " + str(player[1]) + " up to FUTBIN price: " + str(futbinprice) + ". Will determine actual market price while searching. Purchase ceiling: " + str(price_to_use))
            else:
                price_to_use = buy_percent * marketprice
                log_event(self.queue, "Bidding on " + str(player[1]) + " up to MARKET price: " + str(marketprice) + ". Purchase ceiling: " + str(price_to_use))

            # Bid on players on current page -- 6 seconds spent in search tab
            self.helper.clickSearch()
            sleep(2)
            self.helper.bid_on_current_page(cardname, price_to_use, bidstomake_eachplayer, 0, "None")
            sleep(1)

        if (continue_running):
            # Parse market data to find actual sell price 
            log_event(self.queue, "Parsing market data to find most accurate sell prices...")
            self.helper.get_lowestbin_from_searchdata()
    
            log_event(self.queue, "Going to watchlist. Time for war")
            self.helper.go_to_watchlist()
            self.manageWatchlist()
        else:
            log_event(self.queue, "Error, bot stopped!")


    def manageWatchlist(self):
        continue_running = True
        status = 1
        while (status == 1):
            # 1. Make sure we are on watchlist, else break (for debugging)
            page = self.driver.find_element_by_xpath("/html/body/main/section/section/div[1]/h1").text
            if (page.lower() == "transfer targets"):
                # 2. Ensure active bids exist
                # self.helper.update_autobidder_logs()
                num_activebids = self.helper.get_num_activebids()
                if (num_activebids != 0):
                    # Evaluate 5 cards closest to expiration, returns "processing" if exception
                    active_bids = self.helper.getAllPlayerInfoWatchlist()
                    # If any players are processing, bot will not bid
                    if (active_bids != "processing"):
                        firstplayer = active_bids[0]
                        firstplayer_timeremaining = firstplayer[7]
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
                                    # log_event(self.queue, "Player outbid --> " + str(playername))
                                    if (self.helper.user_num_coins >= curbid+100):
                                        if (curbid < stopPrice):
                                            # log_event(self.queue, "Player outbid --> " + str(playername) + " --> proceed to outbid. Current bid of " + str(curbid) + " gives potential profit of " + str(sellprice - curbid) + " coins.")
                                            result = self.helper.makebid_individualplayerWatchlist(playernumber, curbid)
                                            if result == "Failure":
                                                log_event(self.queue, "Error outbidding " + str(playername) + ". Refreshing page")
                                                self.helper.refreshPageAndGoToWatchlist()
                                            if result == "Success":
                                                if (curbid <= 950):
                                                    bidlog = curbid + 50
                                                else:
                                                    bidlog  = curbid + 100
                                                log_event(self.queue, "Outbid " + str(playername) + " | CurBid: " + str(bidlog) + " | Stop: " + str(stopPrice) + " | Est. Prof: " + str(sellprice - curbid))
                                    else:
                                        # User doesn't have enough coins
                                        log_event(self.queue, "You don't have enough coins to continue bidding")
                                        status = 0
                else:
                    status = 0
                    # self.manageTransferlist()
            else: 
                log_event(self.queue, "Unexpected page, stopping bot")
                continue_running = False
                status = 0

        if continue_running:
            log_event(self.queue, "No more active bids")
            log_event(self.queue, "Proceeding to list won players")
            self.finishWatchlist()
        else:
            log_event(self.queue, "Error, bot stopped!")

    # Lists won players for transfer, from watchlist
    def finishWatchlist(self):
        page = self.driver.find_element_by_xpath("/html/body/main/section/section/div[1]/h1").text
        if (page.lower() == "transfer targets"):
            # send won to transfer list
            sleep(3)

            try:
                # # Send won to Transfer list
                self.helper.list_players_for_transfer()
                sleep(2)
                self.helper.clearExpired()
            except:
                log_event(self.queue, "error here line 160 autobidder.py")

            conserve_bids, sleep_time, botspeed = self.helper.getUserConfig()
            sleepmins = int(sleep_time)/60
            sleep_time = int(sleep_time)
            log_event(self.queue, "Sleeping for " + str(sleepmins) + " minutes and heading back to war")
            if (sleep_time < 180):
                log_event(self.queue, "Sleep is less than 180 seconds, not recommended")
                log_event(self.queue, "Forcing 180 sec sleep")
                sleep(180)
            else:
                sleep(sleep_time)
            self.checkTransferlist()
        else:
            log_event(self.queue, "Weird error, click start Autobidder again")

    def checkTransferlist(self):
        log_event(self.queue, "Finished sleeping")
        
        self.helper.go_to_transferlist()

        log_event(self.queue, "went to transfer list")
        sleep(5)

        # CAPTCHA:
        # /html/body/div[4]/section/header/h1
        # that is header of msg ^^
        # OK bnutton: /html/body/div[4]/section/div/div/button

        self.helper.manageTransferlist()

        log_event(self.queue, "Proceeding to restart")
        sleep(3)
        self.start()


