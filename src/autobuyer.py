# import helpers
# import mainhelpers
import helpers

from helpers import *
# from helpers import *
# from mainhelpers import *

import csv
from time import sleep
from decimal import Decimal
from datetime import datetime
from selenium.webdriver.support import ui
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ChromeOptions, Chrome

class Autobuyer:
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

    def start(self):
        self.queue.put("Updating queue from inside autobidder...")
        log_event("Autobidder started")

        num_players_to_bid_on = len(self.playerlist)

        # bidsallowed, bidstomake_eachplayer = self.helper.getWatchlistTransferlistSize()
        bidsallowed = 10
        bidstomake_eachplayer = 5
        
        for player in self.playerlist:
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
            clickSearch(self.driver)
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
        # Make sure we are on watchlist, else break
         
        page = self.driver.find_element_by_xpath("/html/body/main/section/section/div[1]/h1").text
        if (page.lower() == "transfer targets"):
            # log_event("User not on transfer targets page, breaking here -- double check this is correct header")

            try:
                num_activebids = self.helper.get_num_activebids()
                log_event("Num active bids: " + str(num_activebids))
            except:
                log_event("Num_active bids method at beginning of watchlist manager didn't work, recalling method")
                self.helper.manageWatchlist()

            if (num_activebids != 0):
                try:
                    # Returns 5 closest to expiration
                    active_bids = self.helper.getAllPlayerInfoWatchlist()
                    firstplayer = active_bids[0]
                    firstplayer_timeremaining = firstplayer[7]

                    # If first player is not Processing
                    if (firstplayer_timeremaining > 0):
                        print("first player is NOT processing")
                        # self.manageWatchlist()
                    # else:
                        for card in active_bids:
                            bidStatus = card[1]
                            if "outbid" in bidStatus:
                                print("card is outbid")
                                playername = card[3]
                                playernumber = card[0]
                                curbid = card[5]
                                timeremainingseconds = card[7]
                                timeremainingmins = timeremainingseconds/60
                                id = card[8]

                                sellprice = self.helper.getPlayerSellPrice(id)
                                stopPrice = self.helper.getPlayerPriceCeiling(id)

                                log_event("Checking if we should outbid " + str(playername) + " || Stop bidding at: " + str(stopPrice) + " || CurBid: " + str(curbid))
                                if (curbid < stopPrice):
                                    result = self.helper.makebid_individualplayerWatchlist(playernumber, curbid)
                                    if result == "Failure":
                                        log_event("Error making bid on " + str(playername) + ". Refreshing page!")
                                        self.helper.refreshPageAndGoToWatchlist()
                                        sleep(4)
                                        # self.manageWatchlist()
                                    if result == "Success":
                                        log_event("Successfully outbid " + str(playername) + " || Stop price: " + str(stopPrice) + " || CurBid: " + str(curbid))
                                        # self.manageWatchlist()  
                            # log_event("Sleeping for 5 seconds and checking bids again")       
                            sleep(3)   
                        self.manageWatchlist()
                except:
                    self.manageWatchlist()
            else:
                # No active bids, time to clear expired and send everything to TL
                log_event("FINISHED BIDDING WARS... now need to expired and send to TL")
                sleep(10)
                self.helper.clearExpired()
                log_event("Cleared expired players")
                self.manageTransferlist()
        else:
            log_event("User is not on Watchlist, breaking method here")
            self.manageTransferlist()

    def manageTransferlist(self):
        log_event("inside transferlist method now")