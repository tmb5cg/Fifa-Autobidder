import helpers
import mainhelpers
import newhelpers

from newhelpers import *
from helpers import *
from mainhelpers import *

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

class Autobidder:
    def __init__(self, driver):
        self.driver = driver
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
                log_event("Bidding on " + str(player[1]) + " up to FUTBIN price: " + str(futbinprice) + ". Will use market price after first pass. Purchase ceiling: " + str(price_to_use))
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
        # find out why james rodriguez was picked for luis rodriguez
        #since GUI is on separate thread and constantly updating, it can parse the txt files to list the number of bids made today, number of players won, numebr sold etc

        # rememebr this is just to get set up on my github, i can get this loosely running albeit ugly in probably 30 minutes ... just do it 
        log_event("Going to watchlist. Time for war.")

    def manageWatchlist(self):
        # evaluate current state. if any player on page is outbid TRY: everything EXCEPT: restart
        # Prepare watchlist for bidding wars, clear out won players etc
        try:
            self.helper.send_won_players_to_transferlist(self.driver)
        except:
            # log_event("Sending players to TL didn't really work")

        try:
            self.helper.clearExpired(self.driver)
            log_event("Cleared expired players")
        except:
            # log_event("Clear expired didn't work for some reason?")

        sleep(1)
        self.manageTransferlist()

        sleep(2)

        try:
            playerdata = getAllPlayerInfoWatchlist(self.driver)
        except:
            print("Playerdata unable to fetch, reloading ManageWatchlist")
            log = "Playerdata unable to fetch, reloading ManageWatchlist"
            log_event(log)
            self.manageWatchlistBidwar()

        firstcard = playerdata[0]
        firstcardTimeRemaining = firstcard[7]

        # If first card is processing, rerun the function
        if (firstcardTimeRemaining < 0):
            log_event("First card is processing, rerunning managewatchlist")
            self.manageWatchlistBidwar()
        else:
            for card in playerdata:
                # [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
                # [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]

                playername = card[3]
                playernumber = card[0]
                bidStatus = card[1]
                curbid = card[5]
                timeremainingseconds = card[7]
                timeremainingmins = timeremainingseconds/60
                id = card[8]

                # Only have it outbid if TimeRemaining is 6 mins or less, ie ~400 seconds
                if ((timeremainingseconds < 300) and (timeremainingseconds > 3)):
                    if "outbid" in bidStatus:

                        # Get players sell price
                        # stopPrice = 0
                        # for data in self.players_futbin_prices:
                        #     if (data[0] == playername):
                        #         stopPrice = data[1]

                        sellprice = 0
                        sellprice = getActualSellprice(id)
                        stopPrice = sellprice*.85
                        log_events("CHECKING IF WE SHOULD OUTBID Player " + str(playername) + " || CurBid: " + str(curbid) + " || Sell price: " + str(sellprice) + " || Stop price: " + str(stopPrice))
                        if curbid < stopPrice:
                            log_events(str(playername) + " || CurBid: " + str(curbid) + " || FutbinPrice: " + str(stopPrice) + " || Will now outbid")
                            result = makebid_individualplayerWatchlist(self.driver, playernumber, curbid)
                            if result == "Failure":
                                print("Bid failure, refreshing page")
                                log = "Bid failure, refreshing page"
                                log_events(log)

                                refreshPageAndGoToWatchlist(self.driver)
                                sleep(4)
                                self.manageWatchlistBidwar()
                            if result == "Success":
                                self.manageWatchlistBidwar() # so we can reload the page status

        self.manageWatchlistBidwar()

