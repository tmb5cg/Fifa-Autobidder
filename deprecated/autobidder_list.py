import helpers
import mainhelpers
from helpers import *
from mainhelpers import *

from time import sleep

class AutobidderPlayerlist:
    def __init__(self, driver, searchdata):
        self.driver = driver
        self.searchdata = searchdata
        self.players_futbin_prices = []

    def run(self):
        print("autobidder_list run function is working")
        self.bid_using_list(self.searchdata)

    def bid_using_list(self, playerdata):
        self.playerdata = playerdata
        print(playerdata)
        num_players_to_bid_on = len(playerdata)

        transferdata = getWatchlistTransferlistSize(self.driver)
        bidsallowed = 50 - transferdata[2]
        bidstomake_eachplayer = round(bidsallowed/num_players_to_bid_on) - 1

        print("Number of players to bid on: " + str(num_players_to_bid_on))
        print("Bids to make on each player: " + str(bidstomake_eachplayer))

        for player in playerdata:
            name = player[1]
            # bidstomake_eachplayer = 4

            cardname, cardoverall = go_to_tranfer_market_and_input_parameters(self.driver, name) # 3 to 4 seconds
            playerid = getPlayerID(cardname, cardoverall)
            futbinprice, lastupdated = get_futbin_price_lastupdated(playerid)
            playernameoncard = getPlayerCardName(playerid)
            data = [playernameoncard, futbinprice]
            self.players_futbin_prices.append(data)
            print(str(name) + " playerid " + str(playerid) + " futbin price " + str(futbinprice) + " name on card " + str(playernameoncard))

            clickSearch(self.driver) # 3 seconds

            # Bid on players on current page -- 6 seconds spent in search tab
            makebids_currentpage(self.driver, name, futbinprice, bidstomake_eachplayer, 0, "None")
            print("Finished bidding on:" + str(name))

        print("Should go to watch list now, sleeping 5 secs")
        sleep(2)
        go_to_watchlist(self.driver)
        self.manageWatchlistBidwar()


    def manageWatchlistBidwar(self):
        sleep(3)

        # Make it only watch the 3 most recent players to minimize wasted bids?
        self.number_of_bids = 0
        num_activebids = get_num_activebids(self.driver)
        num_expired = get_num_lost(self.driver)
        num_won = get_num_won(self.driver)
        total_watch_list = num_activebids + num_expired + num_won
        self.num_watchlist = total_watch_list
        self.bids_available = 48 - self.num_watchlist

        if num_expired > 0:
            clearExpired(self.driver)
            print("Cleared expired")
            sleep(1.5)

        if num_won > 0:
            send_won_players_to_transferlist(self.driver)

        if num_activebids == 0:
            print("Number of active bids less than 15, researching")
            self.manageTransferlist(self.playerdata)

        sleep(2)

        playerdata = getAllPlayerInfo(self.driver)
        for card in playerdata:
            # [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
            playername = card[3]
            playernumber = card[0]
            bidStatus = card[1]
            curbid = card[5]
            timeremainingseconds = card[7]
            timeremainingmins = timeremainingseconds/60

            # Only have it outbid if TimeRemaining is 3 mins or less, ie 180 seconds
            if timeremainingseconds < 185:
                if "outbid" in bidStatus:
                    print("Player " + str(playername) + " outbid!")

                    # Get players sell price
                    stopPrice = 0
                    for data in self.players_futbin_prices:
                        if (data[0] == playername):
                            stopPrice = data[1]

                    if curbid < stopPrice:
                        print(str(playername) + " || CurBid: " + str(curbid) + " || FutbinPrice: " + str(stopPrice) + " || Will now outbid")
                        result = makebid_individualplayer(self.driver, playernumber, curbid)
                        if result == "Failure":
                            print("failure bidding!!!!!! refreshing page ... ")
                            refreshPageAndGoToWatchlist(self.driver)
                            sleep(4)
                            self.manageWatchlistBidwar()

                elif "won" in bidStatus:
                    print("Won player! player: " + str(playernumber))
                elif "expired" in bidStatus:
                    print("Player " + str(playernumber) + " expired")

        self.manageWatchlistBidwar()


    def manageTransferlist(self, playerdata):
        go_to_transferlist(self.driver)
        players = getAllPlayerInfo(self.driver)
        playerids = []

        clickRelistAll = False
        clickClearExpired = False
        unlistedplayerscount = 0
        for player in players:
            #info = [playernumber, bidstatus, rating, name, startprice, curbid_or_finalsoldprice, buynow, time, id]
            print(player)
            playerid = player[8]
            bidstatus = player[1]
            name = player[3]

            if bidstatus == "listFUTItem":
                unlistedplayerscount += 1
            if playerid not in playerids:
                playerids.append(playerid)

            if "expired" in bidstatus:
                clickRelistAll = True
            if "won" in bidstatus:
                clickClearExpired = True

        print(playerids)
        if clickRelistAll:
            print("Click relist all")
            self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[2]/header/button").click()
            # click yes to prompt about relisting
            sleep(2)
            self.driver.find_element(By.XPATH, "/html/body/div[4]/section/div/div/button[2]").click()
            sleep(2)
        if clickClearExpired:
            print("Click clear expired")
            self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[1]/header/button").click()

        # Get player prices
        priceData = []
        for id in playerids:
            futbinprice, lastupdated = get_futbin_price_lastupdated(id)
            futbinprice = int(futbinprice)
            data = [id, futbinprice]
            priceData.append(data)
            print("Retrieved player price ID: " + str(id) + " || Price: " + str(futbinprice))
            sleep(8)

        # List players now that all others are relisted + cleared expired
        # players = getAllPlayerInfo(self.driver)

        for x in range(unlistedplayerscount):
            # x += 1
            # will always click play number 1
            playerbutton = "/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div"

            startpriceinput = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[2]/div[2]/input"
            buynowpriceinput = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/input"
            listfortransfer = "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/button"

            playernamelocation = "/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div/div[1]/div[2]"
            playerratinglocation = "/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div/div[1]/div[1]/div[4]/div[2]/div[1]"

            playername = self.driver.find_element(By.XPATH, playernamelocation).text
            playerrating = self.driver.find_element(By.XPATH, playerratinglocation).text

            currentplayerid = getPlayerID(playername, playerrating)

            # Get sell price
            for data in priceData:
                id = data[0]
                futbinprice = data[1]
                if currentplayerid == id:
                    print("Price ID match found, will now list player for " + str(futbinprice))
                    if futbinprice > 1000:
                        buynowprice = futbinprice - 100
                        startprice = buynowprice - 100
                    elif futbinprice < 1000:
                        buynowprice = futbinprice - 50
                        startprice = buynowprice - 50
                    else:
                        print("Wtf")

                    # Click player
                    self.driver.find_element(By.XPATH, playerbutton).click()
                    sleep(1)
                    # Click list for transfer
                    self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[1]/button").click()
                    sleep(1)

                    buynowBox = self.driver.find_element(By.XPATH, buynowpriceinput)
                    buynowBox.click()
                    sleep(1)
                    buynowBox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                    buynowBox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                    buynowBox.send_keys(buynowprice)

                    sleep(1)
                    startpriceBox = self.driver.find_element(By.XPATH, startpriceinput)
                    startpriceBox.click()
                    sleep(1)
                    startpriceBox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                    startpriceBox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                    startpriceBox.send_keys(startprice)
                    sleep(1)

                    # List for transfer!
                    self.driver.find_element(By.XPATH, listfortransfer).click()
                    print("Listed player " + str(id) + " for BIN: " + str(buynowprice))
                    sleep(5)

            print("Transferlist succesfully handled! Sleeping for 3 minutes and researching TM.")
            sleep(180)
            self.bid_using_list(self.playerdata)
