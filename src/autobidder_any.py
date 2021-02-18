import helpers
import mainhelpers

from helpers import *
from mainhelpers import *

from time import sleep
from datetime import datetime
from selenium.webdriver.support import ui
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ChromeOptions, Chrome


class AutobidderAny:
    def __init__(self, driver, searchdata):
        self.driver = driver
        self.searchdata = searchdata
        self.searchdata_ids_prices = []

    def run(self, bidmethod):
        if bidmethod == "GUIfilters":
            print("bid on any player")
            log = "Bidding on any common golds about to expire at lower price than Futbin says"
            log_event(log)


            futbindata = futbinscraper(20)
            self.bid_using_futbinprices(futbindata)

        if bidmethod == "playerlist":
            print("Bidding using input player list from GUI")
            log = "Bidding using input player list from GUI"
            log_event(log)


            self.bid_using_list()

    def testfunc(self):
        price = getActualSellprice(170368)
        print(price)

        price = getActualSellprice(192045)
        print(price)

    def getMostAccuratePricesFromMarket(self):
        clearOldSearchData()
        print("Cleared old search data hopefully, will now get new data")
        log = "Cleared old search data, will now get new data"
        log_event(log)

        sleep(5)
        for player in self.searchdata:
            name = player[1]

            cardname, cardoverall = go_to_tranfer_market_and_input_parameters(self.driver, name)
            id = getPlayerIDFromTargets(cardname, cardoverall)
            if (id == 0):
                id = getPlayerID(cardname, cardoverall)

            addPlayerToTargetList(id, cardname, cardoverall, 0, "fromPriceFunc")

            print("Searching for: " + str(cardname) + " | " + str(id))   

            log = "Searching for: " + str(cardname) + " | " + str(id)
            log_event(log)

            data = [id, cardname, cardoverall]
            self.searchdata_ids_prices.append(data)
            sleep(1)

            futbinprice, lastupdated = get_futbin_price_lastupdated(id)

            futbinprice_plus500 = futbinprice + 500

            sleep(2)

            # enter max bin
            input = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[6]/div[2]/input")
            input.click()
            sleep(1)
            input.send_keys(futbinprice_plus500)

            sleep(1)

            clickSearch(self.driver)

            sleep(2)

            keepsearching = True
            while keepsearching:
                sleep(3)
                # Write playerdata to csv
                players_on_page = getAllPlayerInfo(self.driver)
                try:
                    self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]')
                    # print("Next page button exists")
                    try:
                        # print("Clicking next page, and while loop should restart")
                        sleep(1)
                        self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]').click()
                    except:
                        # print("Found next page element but couldn't click it")
                        # print("Hopefully skipping to next player in list")
                        sleep(5)
                        keepsearching = False
                except:
                    # print("No next page button, hopefully skipping to the next player in list")
                    sleep(5)
                    keepsearching = False

        print("Finished fetching price data for player: " + str(cardname))
        print("Proceeding to aggregate data and find lowest BIN")
        print("We will exclude cards with greater than 57 mins on market")

        log = "Finished fetching price data for player: " + str(cardname) + " Proceeding to aggregate data and find lowest BIN, We will exclude cards with greater than 57 mins on market"
        log_event(log)

        sleep(5)
        newSearchdata_ids_prices = []
        get_lowestbin_from_searchdata()
        for player in self.searchdata_ids_prices:
            ogid = player[0]
            name = player[1]
            overall = player[2]

            id = getPlayerIDFromTargets(name, overall)

            print("OG ID: " + str(ogid) + " || New ID (from targets method): " + str(id))

            marketprice = getActualSellprice(id)
            marketprice = int(marketprice)

            newdata = [id, name, overall, marketprice]
            newSearchdata_ids_prices.append(newdata)
            print("Player: " + str(name) + " || " + str(overall) + " || MARKET PRICE: " + str(marketprice))

            log = "Player: " + str(name) + " || " + str(overall) + " || MARKET PRICE: " + str(marketprice)
            log_event(log)

            self.searchdata_ids_prices = newSearchdata_ids_prices

        # [[178509, 'Olivier Giroud', '79', 900],
        #  [192045, 'Luis Rodríguez', '78', 800]]
        print("Final array of price data: " + str(self.searchdata_ids_prices))


    def bid_using_list(self):
        self.getMostAccuratePricesFromMarket()
        sleep(5)
        num_players_to_bid_on = len(self.searchdata)

        # Remove old market search data
        # clearOldSearchData()

        if (num_players_to_bid_on != 1):
            transferdata = getWatchlistTransferlistSize(self.driver)
            bidsallowed = 50 - transferdata[2]
            bidstomake_eachplayer = round(bidsallowed/num_players_to_bid_on) - 1
        elif (num_players_to_bid_on == 1):
            transferdata = getWatchlistTransferlistSize(self.driver)
            bidsallowed = 50 - transferdata[2]
            bidstomake_eachplayer = bidsallowed
        else:
            print("Your player list is a bit odd")

        print("Number of players to bid on: " + str(num_players_to_bid_on))
        print("Bids to make on each player: " + str(bidstomake_eachplayer))
        log = "Number of players to bid on: " + str(num_players_to_bid_on)
        log2 = "Bids to make on each player: " + str(bidstomake_eachplayer)

        # Log to data logs
        log_event(log)
        log_event(log2)


        for player in self.searchdata:
            name = player[1]

            cardname, cardoverall = go_to_tranfer_market_and_input_parameters(self.driver, name) # 3 to 4 seconds
            playerid = getPlayerIDFromTargets(cardname, cardoverall)

            sleep(2)
            # enter max bin
            input = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[6]/div[2]/input")
            input.click()
            sleep(1)
            input.send_keys(0)
            sleep(1)

            # Check if we have updated actual price in CSV
            futbinprice = getActualSellprice(playerid)
            print("Price found in bid_using_list (should match price printed above): " + str(futbinprice))
            log = "Price found in bid_using_list (should match price printed above): " + str(futbinprice)
            log_event(log)

            if (futbinprice == 0):
                futbinprice, lastupdated = get_futbin_price_lastupdated(playerid)

            addPlayerToTargetList(playerid, cardname, cardoverall, futbinprice, "lastupdated")

            print(str(name) + " playerid " + str(playerid) + " lowest market price " + str(futbinprice) + " name on card " + str(cardname))
            log = str(name) + " playerid " + str(playerid) + " lowest market price " + str(futbinprice) + " name on card " + str(cardname)
            log_event(log)

            # Bid on players on current page -- 6 seconds spent in search tab
            clickSearch(self.driver)
            makebids_currentpage(self.driver, name, futbinprice, bidstomake_eachplayer, 0, "None")
            print("Finished bidding on:" + str(name))
            log = "Finished bidding on:" + str(name)
            log_event(log)

        print("Going to watchlist now")
        log_event("Going to watchlist now")
        # get_lowestbin_from_searchdata()
        sleep(2)
        go_to_watchlist(self.driver)
        self.manageWatchlistBidwar()


    def manageWatchlistBidwar(self):
        sleep(0.3)

        try:
            num_activebids = get_num_activebids(self.driver)
        except:
            self.manageWatchlistBidwar()

        if num_activebids < 5:
            print("Number of active bids less than 5, sending players to TL and managing TL")
            log = "Number of active bids less than 5, sending players to TL and managing TL"
            log_event(log)
            try:
                send_won_players_to_transferlist(self.driver)
            except:
                print("Sending to TL didn't really work, gonna try again")
                log = "Sending to TL didn't really work, gonna try again"
                log_event(log)
            sleep(5)
            try:
                clearExpired(self.driver)
            except:
                print("Clearexpired caused exception, likely no players to clear")
                log = "Clearexpired caused exception, likely no players to clear"
                log_event(log)
                try:
                    clearExpired(self.driver)
                except:
                    print("Clearexpired didn't work for the 2nd time WTF")
                    log = "Clearexpired didn't work for the 2nd time WTF"
                    log_event(log)

            sleep(5)
            print("Getting update sell prices! Going to transfer list now ")
            log = "Getting update sell prices, and now heading to the transfer list"
            log_event(log)
            self.getMostAccuratePricesFromMarket()
            sleep(3)
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
            print("First card is processing, rerunning managewatchlist")
            log = "First card is processing, rerunning managewatchlist"
            log_event(log)
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

                # Only have it outbid if TimeRemaining is 3 mins or less, ie 180 seconds
                if ((timeremainingseconds < 185) and (timeremainingseconds > 3)):
                    if "outbid" in bidStatus:

                        # Get players sell price
                        # stopPrice = 0
                        # for data in self.players_futbin_prices:
                        #     if (data[0] == playername):
                        #         stopPrice = data[1]

                        sellprice = 0
                        sellprice = getActualSellprice(id)

                        stopPrice = sellprice*.85
                        print("CHECKING IF WE SHOULD OUTBID Player " + str(playername) + " || CurBid: " + str(curbid) + " || Sell price: " + str(sellprice) + " || Stop price: " + str(stopPrice))
                        log = "CHECKING IF WE SHOULD OUTBID Player " + str(playername) + " || CurBid: " + str(curbid) + " || Sell price: " + str(sellprice) + " || Stop price: " + str(stopPrice)
                        log_events(log)
                        if curbid < stopPrice:
                            print(str(playername) + " || CurBid: " + str(curbid) + " || FutbinPrice: " + str(stopPrice) + " || Will now outbid")
                            log = str(playername) + " || CurBid: " + str(curbid) + " || FutbinPrice: " + str(stopPrice) + " || Will now outbid"
                            log_events(log)
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


    def manageTransferlist(self):
        go_to_transferlist(self.driver)
        sleep(5)
        players = getAllPlayerInfo(self.driver)
        playerids = []

        clickRelistAll = False
        clickClearExpired = False
        unlistedplayerscount = 0
        expiredplayerscount = 0
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
                expiredplayerscount += 1
            if "won" in bidstatus:
                clickClearExpired = True

        print(playerids)
        if clickClearExpired:
            print("Click clear expired")
            log = "Clearing expired / sold players"
            log_events(log)
            self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[1]/header/button").click()
            sleep(2)

        if clickRelistAll:
            print("Listing " + str(expiredplayerscount) + " expired players for 100 less than expiration price...")
            log = "Listing " + str(expiredplayerscount) + " expired players for 100 less than expiration price..."
            log_events(log)

            for x in range(expiredplayerscount):
                # Players didn't sell, currently selecting first player that didn't sell
                # click player (because if player sells it switches)
                self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div").click()
                # click "Re-list Item"
                self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[1]/button").click()
                sleep(1)
                # drop buy now by 100 (clicking minus button)
                self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/button[1]").click()
                sleep(1)
                # click "List for Transfer"
                self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/button").click()
                sleep(2)

        print("All expired players were relisted!")
        print("Now listing" + str(unlistedplayerscount) + " unlisted players...")

        log = "All expired players were relisted! Now listing" + str(unlistedplayerscount) + " unlisted players..."
        log_events(log)

        sleep(5)

        print(unlistedplayerscount)
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

            currentplayerid = getPlayerIDFromTargets(playername, playerrating)
            if currentplayerid == 0:
                currentplayerid = getPlayerID(playername, playerrating)

            print("Current player ID: " + str(currentplayerid) + " " + playername)
            log = "Current player ID: " + str(currentplayerid) + " " + playername
            log_events(log)
            futbinprice = getActualSellprice(currentplayerid)
            print("Current player lowest sell price: " + str(futbinprice))
            log = "Current player lowest sell price: " + str(futbinprice)
            log_events(log)

            futbinprice = int(futbinprice)

            if (futbinprice == 0):
                # get futbin price and list it for that
                futbinprice, lastupdated = get_futbin_price_lastupdated(currentplayerid)
                print("It appears player " + str(currentplayerid) + " " + playername + " is from an old search. Will list for Futbin price of: " + str(futbinprice))
                log = "It appears player " + str(currentplayerid) + " " + playername + " is from an old search. Will list for Futbin price of: " + str(futbinprice)
                log_events(log)
            else:
                print("Price ID match found, will now list player for " + str(futbinprice))
                log = "Price ID match found, will now list player for " + str(futbinprice)
                log_events(log)

            if futbinprice > 1000:
                buynowprice = futbinprice - 100
                startprice = buynowprice - 100
            elif futbinprice <= 1000:
                buynowprice = futbinprice - 50
                startprice = buynowprice - 50
            else:
                print("Something weird happened")

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
            print("Listed player " + str(currentplayerid) + " for BIN: " + str(buynowprice))
            sleep(5)

        print("Transferlist succesfully handled! Sleeping for 3 minutes and researching TM.")
        log = "Transferlist succesfully handled! Sleeping for 3 minutes and researching TM."
        log_events(log)
        sleep(180)
        self.bid_using_list()


    def bid_using_futbinprices(self, futbindata):
        transferdata = getWatchlistTransferlistSize(self.driver)
        bidsallowed = 50 - transferdata[2]

        go_to_tranfer_market_and_input_parameters_commongolds(self.driver, "Gold", "Common")

        clickSearch(self.driver) # 3 seconds

        # Bid on players on current page -- 6 seconds spent in search tab
        name = "AnyPlayer"
        futbinprice = 0
        bidstomake_eachplayer = bidsallowed

        makebids_currentpage(self.driver, name, futbinprice, bidstomake_eachplayer, 0, futbindata)
        print("Finished bidding on:" + str(name))


    def futbinscraper(self, numpages):
        playerpricedata = []
        #tab_url = "https://www.futbin.com/21/players?page=1&version=gold_nr"

        tab_url = "https://www.futbin.com/21/players?page=1&version=gold_nr"
        browser = self.driver

        browser.execute_script("window.open('');")
        browser.switch_to.window(browser.window_handles[1])
        browser.get(tab_url)
        # print("Current Page Title is : %s" %browser.title)

        # ~ ~ ~ ~ ~ ~ Do Stuff in new tab here ~ ~ ~ ~ ~
        for page in range(2, numpages):
            for i in range(29):
                i+=1
                price = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='repTb']/tbody/tr[" + str(i) + "]/td[5]/span"))).text
                playername = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='repTb']/tbody/tr[" + str(i) + "]/td[1]/div[2]/div[1]/a"))).text
                rating = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='repTb']/tbody/tr[" + str(i) + "]/td[2]/span"))).text

                if "K" in price:
                    price = price.replace("K", "")
                    if "." in price:
                        price = price.replace(".", "")
                        price = int(price)
                        price = price*100
                    else:
                        price = int(price)
                        price = price * 1000

                print(str(playername) + " " + str(price))

                price = int(price)
                playerid = getPlayerID(playername, rating)
                playerprice = [playerid, playername, rating, price]
                playerpricedata.append(playerprice)

            sleep(2)
            browser.get("https://www.futbin.com/21/players?page=" + str(page) + "&version=gold_nr")
            page += 1

        for player in playerpricedata:
            print(player)

        # ~ ~ ~ ~ ~ ~ ~ Close the futbin tab ~ ~ ~ ~ ~
        browser.close()

        # Switch back to the first tab with URL A
        browser.switch_to.window(browser.window_handles[0])
        print("Current Page Title is : %s" %browser.title)

        return playerpricedata
