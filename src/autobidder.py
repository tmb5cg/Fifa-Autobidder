import csv
import email
import imaplib
import json
from platform import platform
import random
import sys
from csv import reader
from datetime import datetime
from datetime import date

from decimal import Decimal
from time import sleep


import gspread
from oauth2client.service_account import ServiceAccountCredentials

import requests
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException, TimeoutException, WebDriverException)
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import ui
from selenium.webdriver.support.wait import WebDriverWait

import configparser

class AutobidderTest:
    def __init__(self, driver, queue, GUI_OPTIONS_MENU):
        self.driver = driver
        self.queue = queue
        self.GUI_OPTIONS = GUI_OPTIONS_MENU
        self.playerlist = []
        self.players = []

        # Get user config statistics, and GUI labels
        self.config = configparser.ConfigParser()
        self.config.read("./data/config.ini")

        # Load in frontend statistics on bot init
        self.user_players_won = int(self.config.get("Statistics", "players_won"))
        self.user_watchlist_outbid = int(self.config.get("Statistics", "players_lost"))
        self.user_transferlist_sold  = int(self.config.get("Statistics", "players_sold"))
        self.user_transferlist_relisted = int(self.config.get("Statistics", "players_relisted"))
        self.user_num_coins = int(self.config.get("Statistics", "current_coins"))
        self.user_projected_profit = int(float(self.config.get("Statistics", "projected_profit")))
        self.total_cycles = int(self.config.get("Statistics", "total_cycles"))
        self.user_requests_made = int(self.config.get("Statistics", "requests_made"))
        self.user_bids_made = int(self.config.get("Statistics", "bids_made"))
        self.user_transferlist_selling = int(self.config.get("Statistics", "current_selling"))

        # Assign frontend user config settings to memory on init
        self.undercut_market_on_list, self.sleep_time, self.num_cycles, self.expiration_cutoff_mins, self.margin, self.undercut_market_on_relist, self.futbin_max_price, self.platform = self.getUserConfig()

        # Session variables assigned on init
        self.bids_made_this_round = 0
        self.requests_made_this_round = 0
        self.bidround_number = 0
        self.players_sold_this_round = 0
        self.players_expired_this_round = 0
        self.players_won_this_round = 0
        self.players_lost_this_round = 0
        self.projected_profit_this_round = 0
        self.profit_per_player_this_round = 0
        self.start_time = 0
        self.end_time = 0
        self.LAST_UPDATED_CUTOFF = 80
        self.user_blank_bids_softban_count = 0
        self.popup_text = ""
        self.transferlistInfiniteLoopCounter = 0
        self.botRunning = True

        # Ensure push_to_google is False otherwise will break, this is from my personal version with cloud logging
        self.PUSH_TO_GOOGLE = False
        self.USE_FUTBIN_API = False
        
        # Other global stuff to help user intervention
        self.original_window = self.driver.window_handles[0]
        self.current_tab_viewing = ""
        self.current_tab_num = 0
        
        
        # ENTER FUTBIN URL BELOW
        # your URL must start with https://www.futbin.com/22/players?page=1 exactly
        # everything after ?page=1, you can add whatever futbin filters you like
        self.url = "https://www.futbin.com/22/players?page=1&position=CM&xbox_price=0-1500&version=gold_nr"
        

    # This is the main function
    def test(self):
        devmode = False

        if devmode:
            self.getFutbinList(self.url)
            # self.installAdblock()

        else:
            self.driver.switch_to.window(self.driver.window_handles[0])

            state = self.checkState()
            self.update_autobidder_logs()

            if state == "transfer targets":
                self.listPlayers()

            elif state == "transfer list":
                expiredplayers, players_sold, players_currently_listed, players_unlisted  = self.getTransferlistInfo()
                self.listExpired()

            elif state == "search the transfer market":

                for x in range(int(self.num_cycles)):
                    newstate = self.checkState()
                    if newstate == "search the transfer market":
                        if self.botRunning:
                            self.bidround_number = x
                            self.getFutbinList(self.url)
                            if (self.botRunning):
                                self.sleep_approx(3)
                                self.clickSearch()
                                self.bid()
                                self.total_cycles += 1 
                                self.update_autobidder_logs()
                                
                                # only sleep if is last bid round
                                if ( x+1 < (int(self.num_cycles))):
                                    if self.botRunning:
                                        log_event(self.queue, "Sleeping for " + str(self.sleep_time))
                                        self.sleep_approx(int(self.sleep_time))
                self.update_autobidder_logs()
                log_event(self.queue, "- - - - FINISHED ALL BID ROUNDS - - - ")

            elif state == "search results":
                self.bid()
            
            else:
                log_event(self.queue, "User error: user not on the 'Search the Transfer Market' page ")
                log_event(self.queue, "Read the instructions on the GitHub repo")

            # self.update_autobidder_logs()
            log_event(self.queue, "at main function end, popup text was: " + str(self.popup_text))

            if self.popup_text == "Connect to a network in order to use the app.":
                log_event(self.queue,"network connection lost detected -- insert function ehre to click OK and start over")
                eventData = ["00000000000000", 0, 0, "error", "error", "NetworkConnectionLost"]
                self.log_event(self.queue, "STOPPED at master end of Test main functio - no internet", eventData)

            elif self.popup_text == "Unable to authenticate with the FUT servers. You will now be logged out of the application.":
                print("Captcha -- insert function ehre to click OK and start over")
                eventData = ["00000000000000", 0, 0, "error", "error", "UnableToAuthenticate"]
                self.log_event(self.queue, "STOPPED at master end of Test main function -- unable to authenticate (doesn't auto mean captcha) ", eventData)    
            else:
                eventData = ["00000000000000", 0, 0, "error", "error", "GeneralUserInterventionOrBotBroke"]
                self.log_event(self.queue, "STOPPED at master end of Test main function", eventData)
                

    def bid(self):
        self.wait_for_visibility("/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[1]")
        players_to_use = self.getTargetListIDS()
        
        num_eligible = 0
        keepgoing = True
        no_manual_user_intervention = True
        redPopupVisible = False
        watchlistFullPopup = False
        infinitecounter = 0

        # zero out 
        self.bids_made_this_round = 0
        self.requests_made_this_round = 0

        self.players_sold_this_round = 0
        self.players_expired_this_round = 0
        self.players_won_this_round = 0
        self.players_lost_this_round = 0
        self.projected_profit_this_round = 0
        self.profit_per_player_this_round = 0
        self.start_time = datetime.now()
        self.end_time = 0
        self.user_blank_bids_softban_count = 0
        self.popup_text = ""
        self.hasExceededTimeCutoff = False

        reversePage = False
        while keepgoing and self.botRunning: # and no_manual_user_intervention and not redPopupVisible:
            # try:
                wait_for_shield_invisibility(self.driver)
                if (redPopupVisible):
                    if (self.popup_text == "Item removed from Transfer Targets"):
                        log_event(self.queue,"Red popup (all good): failed bid - item removed from transfer targets - all good")

                        self.popup_text = ""
                        redPopupVisible = False

                    elif (self.popup_text == "Bid status changed, auction data will be updated."):
                        log_event(self.queue, "Red popup (all good): bid status changed, auction data will be upddated")

                        self.popup_text = ""
                        redPopupVisible = False
                        self.goNextPage() # go to next page bc of weird error
            
                    elif (self.popup_text == "Item added to Transfer Targets"):
                        print("Red popup (or white popup) (all good): item added to transfer targets lol wtf ")

                        self.popup_text = ""
                        redPopupVisible = False

                    elif (self.popup_text == "Cannot remove this item from your Transfer Targets."):
                        log_event(self.queue, "Red popup (all good): can't remove item from transfer targets popup, gonna continue")

                        self.popup_text = ""
                        redPopupVisible = False

                    elif (self.popup_text == "Unable to authenticate with the FUT servers. You will now be logged out of the application."):
                        eventData = ["00000000000000", 0, 0, "error", "error", "UnableToAuthenticatePopup"]
                        self.log_event(self.queue, "STOPPED - unable to authenticate popup (this time is it in red pop up func, but i think its actually a popup window/box", eventData)

                        # kill bot
                        keepgoing = False
                        self.botRunning = False
        
                    elif (self.popup_text == "Too many actions have been taken, and use of this feature has been temporarily disabled."):
                        keepgoing = False
                        self.botRunning = False
                        eventData = ["00000000000000", 0, 0, "error", "error", "TooManyActions"]
                        log_event(self.queue, "too many actions taken - this shouldve logged to google sheets that user is softbanned. NOW assume not using bot - go to transfer list and watchlist functions, ideally have a softban fixer method ")
                        self.log_event(self.queue, "STOPPED - SOFTBAN - too many actions taken red popup! add method that fixes this", eventData)
            
                    else:
                        log_event(self.queue,"OTHER POPUP MESSAGE DETECTED, stopping bot")
                        log_event(self.queue,self.popup_text)
                        print("check if it is network connection issue")
                        keepgoing = False
                        self.botRunning = False

                elif (watchlistFullPopup):
                    self.popupText = self.getText("/html/body/div[4]/section/div/p")
                    if (self.popupText == "You are already the highest bidder. Are you sure you want to bid?"):
                        # click cancel
                        log_event(self.queue,"PopupBox You are highest bidder box appeared")
                        self.clickButton("/html/body/div[4]/section/div/div/button[1]")
                        self.sleep_approx(5)

                    elif (self.popupText == "Your Transfer Targets list is full. Please try again later, or clear items from your Watched and Active list."):
                        log_event(self.queue,"PopupBox Watchlist is full popup - clicked OK")
                        self.clickButton("/html/body/div[4]/section/div/div/button")
                        keepgoing = False

                    elif (self.popupText == "Connect to a network in order to use the app."):
                        eventData = ["00000000000000", 0, 0, "error", "error", "InternetConnectionLost"]
                        self.log_event(self.queue, "PopupBox STOPPED - u connect to network popup", eventData)
                        keepgoing = False
                        self.botRunning = False
        
                    elif (self.popupText == "You cannot unwatch an item you are bidding on."):
                        log_event(self.queue, "PopupBox Can't unwatch item bidding on ")
                        self.clickButton("/html/body/div[4]/section/div/div/button")
                        self.popup_text = ""
        
                    elif (self.popupText == "Your bid must be higher than the current bid"):
                        log_event(self.queue, "PopupBox your bid must be higher than current bid ")
                        self.clickButton("/html/body/div[4]/section/div/div/button")
                        self.popup_text = ""

                    elif (self.popupText == "Unable to authenticate with the FUT servers. You will now be logged out of the application."):
                        log_event(self.queue, "STOPPED - PopupBox BAD - unable to authenticate (detected in popup function, not redpopup) should click OK")
                        # self.popup_text == ""
                        keepgoing = False
                        self.botRunning = False
                    else:
                        log_event(self.queue,"STopping bot, Weird popup message is not any of above - should get text")
                        log_event(self.queue,self.popupText)
                        keepgoing = False
                        self.botRunning = False
        
                    # self.clickButton("/html/body/div[4]/section/div/div/button")
                elif self.requests_made_this_round > 50:
                    log_event(self.queue, "Made over 50 requests, stopping, keepgoing = False")
                    keepgoing = False
                elif (self.user_num_coins < 1000):
                    log_event(self.queue, "Coins too low, keepgoing = False")
                    keepgoing = False
                elif (no_manual_user_intervention):
                    players = self.getAllPlayerInfo2() # Re-load player list and cycle through them
                    num_eligible = 0
                    refresh = False
                    for p in players:
                        # print(p)
                        if refresh == False:
                            id = int(p[16])
                            if (id in players_to_use):
                                if ("expired" not in p[2]) and ("highest-bid" not in p[2]) and ("selected" not in p[2]):
                                    if p[8] > 10: # time is greater than 10 secs
                                        if p[8] < int(self.expiration_cutoff_mins * 60): # time is less than 3 mins
                                            pid = p[16]
                                            curbid = int(p[6])
                                            position = p[1]
                                            rating = p[3]

                                            sell_quickily_price = self.getSellPrice(pid)

                                            if (sell_quickily_price > 1000):
                                                breakevenprice = self.round_nearest(0.95 * sell_quickily_price, 100)
                                            else:
                                                breakevenprice = self.round_nearest(0.95*sell_quickily_price)

                                            if (curbid > 1000):
                                                bidprice = curbid + 100
                                            else:
                                                bidprice = curbid+50
                                            
                                            margin = int(self.margin)
                                            idealbid = self.round_nearest(breakevenprice-margin)
                                            if ((breakevenprice - margin) >= bidprice):
                                                idealbid = self.round_nearest(breakevenprice-margin)
                                                if ((sell_quickily_price *0.95) - idealbid) >= margin:

                                                    # ID = p[0]
                                                    nation = self.getText("/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(p[0]) + "]/div/div[1]/div[1]/div[8]/div[1]/span[2]")
                                                    league = self.getText("/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(p[0]) + "]/div/div[1]/div[1]/div[8]/div[2]/span[2]")
                                                    team = self.getText("/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(p[0]) + "]/div/div[1]/div[1]/div[8]/div[3]/span[2]")

                                                    eventData = [pid, p[4], curbid, idealbid, sell_quickily_price, (sell_quickily_price*.95), ((sell_quickily_price*.95) - idealbid), nation, league, team, position, rating]
                                                    
                                                    bidSuccesful = self.makebid_individualplayer2(p[0],idealbid)
                                                    if (bidSuccesful == True):
                                                        self.log_event(self.queue,"BID " + str(self.bids_made_this_round + 1) + ": " + str(p[4]) + " - CurBid: " + str(curbid) + " -> Bid to make: " + str(idealbid) + " -> Sell price " + str(sell_quickily_price) + " -> Minus EA tax: " + str(sell_quickily_price *.95) + "-> Est. Profit: " + str( (sell_quickily_price*.95) - idealbid), eventData)
                                                    
                                                    if self.user_blank_bids_softban_count > 15:
                                                        log_event(self.queue, "im guessing this is a softban but red popup didn't show")
                                                        self.botRunning = False
                                                    
                                                    num_eligible+=1
                                                    refresh = True
                                        else:
                                            # START REVERSING PAGE
                                            self.hasExceededTimeCutoff = True
                                            refresh = True

                    # Go to next page if no eligible players
                    if (num_eligible == 0) and (self.hasExceededTimeCutoff == False):
                        self.goNextPage()
                    
                    watchlistFullPopup = self.check_exists_by_xpath("/html/body/div[4]/section/div/div/button")
                    no_manual_user_intervention = self.checkState("transfermarket")
                    redPopupVisible = self.check_exists_by_xpath("/html/body/div[5]/div")
                    if redPopupVisible:
                        self.popup_text = str(self.getText("/html/body/div[5]/div"))
                    page = self.checkState("transfermarket")
                    if page == False:
                        self.botRunning = False
                        log_event(self.queue,"bot running set to false")
                    
                    if self.hasExceededTimeCutoff:
                        log_event(self.queue, "Time cutoff exceeded - researching")
                        self.clickBack()
                        self.hasExceededTimeCutoff = False
                        self.sleep_approx(5)
                        self.clickSearch()
                        self.sleep_approx(5)

            # except Exception as e:
            #     print(e)
            #     # print("EXCEPTION " + str(infinitecounter))
            #     infinitecounter +=1
            #     if infinitecounter > 4:
            #         log_event(self.queue, "Infinite exception counter greater than 10 in bid method - stopped bot")
            #         # print("infinite  counter over 10, break now")
            #         keepgoing = False
            #         self.botRunning = False
            #         break

        if (self.botRunning):
            log_event(self.queue,"Total Bids made: " + str(self.bids_made_this_round) + " Requests: " + str(self.requests_made_this_round))
            log_event(self.queue,"Margin: " + str(self.margin))
            self.sleep_approx(3)
            self.listExpired()
        else:
            log_event(self.queue,"self.botrunning was false, hopefully user intervention")

    def listExpired(self):
        wait_for_shield_invisibility(self.driver) # add this method to helpersv2
        self.go_to_transferlist() # note this is using old helper object
        wait_for_shield_invisibility(self.driver)

        self.sleep_approx(5)
        wait_for_player_shield_invisibility(self.driver)
        expiredplayers, players_sold, players_currently_listed, players_unlisted = self.getTransferlistInfo()
        log_event(self.queue,"Players sold: " + str(players_sold))
        log_event(self.queue,"Players expired: " + str(expiredplayers))
        log_event(self.queue,"Players currently listed: " + str(players_currently_listed))
        log_event(self.queue,"Players unlisted: " + str(players_unlisted))

        #  FIRST Clear sold - first time
        if players_sold > 0:
            try:
                self.clearSold()
                self.user_transferlist_sold += players_sold
                self.players_sold_this_round += players_sold
                self.update_autobidder_logs()
                players_sold = 0 # reassign players_sold
            except Exception as e:
                print(e)
                log_event(self.queue,"clear sold error")

        wait_for_shield_invisibility(self.driver)
        expiredplayers, players_sold, players_currently_listed, players_unlisted = self.getTransferlistInfo()

        exception_counter = 0
        # SECOND start listing expired players, which can get complicated by sold
        if (expiredplayers > 0):
            wait_for_player_shield_invisibility(self.driver)
            player_exists = self.check_exists_by_xpath("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]")
            if (player_exists):
                self.scrollIntoView("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]")
                self.clickButton("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]")
                wait_for_player_shield_invisibility(self.driver)

                status = True
                while status:
                    status = self.check_exists_by_xpath("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]")                
                    try:
                        # self.wait_for_visibility("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]")
                        # wait_for_shield_invisibility(self.driver)
                        self.clickButton('/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div') # click player
                        # wait_for_player_shield_invisibility(self.driver)
                        wait_for_shield_invisibility(self.driver)
                        self.clickButton("/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[1]/button") # click re-list
                        wait_for_shield_invisibility(self.driver)
                        # wait_for_player_shield_invisibility(self.driver)
                        if int(self.undercut_market_on_relist) == 0:
                            print ("undercut market is 0, not gonna subtract")
                        elif int(self.undercut_market_on_relist) == 1:
                            self.clickButton("/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/button[1]") # click minus button
                        elif int(self.undercut_market_on_relist) == 2:
                            self.clickButton("/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/button[1]") # click minus button
                            self.sleep_approx(0.1)
                            self.clickButton("/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/button[1]") # click minus button

                        wait_for_shield_invisibility(self.driver)
                        # wait_for_player_shield_invisibility(self.driver)

                        rating = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[1]/div[5]/div[2]/div[1]")
                        position = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[1]/div[5]/div[2]/div[2]")
                        name = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[2]")
                        pace = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[3]/ul/li[1]/span[2]")
                        shooting = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[3]/ul/li[2]/span[2]")
                        passing = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[3]/ul/li[3]/span[2]")
                        dribbling = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[3]/ul/li[4]/span[2]")
                        defending = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[3]/ul/li[5]/span[2]")
                        physical = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[3]/ul/li[6]/span[2]")

                        nation = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[1]/div[8]/div[1]/span[2]")
                        league = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[1]/div[8]/div[2]/span[2]")
                        team = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[2]/ul/li[1]/div/div[1]/div[1]/div[8]/div[3]/span[2]")

                        player_data = [rating, pace, shooting, passing, dribbling, defending, physical]

                        unique_player_id = ""
                        for x in player_data:
                            x = str(x)
                            unique_player_id += x

                        self.scrollIntoView("/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/button")
                        relist_price = int(self.getInputBoxText("/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/input"))
                        self.clickButton("/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/button") # List player
                        
                        text = "RELIST PID: " + str(unique_player_id) + " NAME: " + str(name) + " RELISTPRICE: " + str(relist_price) + " POSITION: " + str(position)
                        eventData = [unique_player_id, name, relist_price, position, rating, nation, league, team]
                        self.log_event(self.queue, text, eventData)
                        
                        self.user_transferlist_relisted += 1 # this is actually the number of players that expired
                        self.players_expired_this_round += 1
                        self.user_projected_profit -= (0.95*50)
                        self.update_autobidder_logs()
                        # self.sleep_approx(3)
                    except Exception as e:
                        print(e)
                        exception_counter += 1
                        if exception_counter > 5:
                            status = False

        self.sleep_approx(3)
        expiredplayers, players_sold, players_currently_listed, players_unlisted = self.getTransferlistInfo()

        #  THIRD Clear sold - last time
        if players_sold > 0:
            try:
                self.clearSold()
                self.user_transferlist_sold += players_sold
                self.players_sold_this_round += players_sold
                self.update_autobidder_logs()
            except:
                log_event(self.queue,"clear sold error")
 
        self.sleep_approx(3)
        log_event(self.queue,"Going to watchlist")

        # INSERT CHECK FOR POPUP HERE 
        print("CHECK FOR POOPUP HERE")
        self.go_to_watchlist()
        self.listPlayers()
    
    def listPlayers(self):
        self.sleep_approx(5)

        projected_profit = 0
        status = True
        exception_counter = 0

        players_won = 0
        players_expired = 0
        while status:
            try:
                # every 10 seconds, check if bid is currently active and expiring etc
                activeBid = self.check_exists_by_xpath("/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li")
                wait_for_shield_invisibility(self.driver)
                self.sleep_approx(10)

                if activeBid == False:
                    self.sleep_approx(10)
                    print("active bid is gone - just finished sleeping 10 seconds, gonna clear expired")
                    self.clearExpired()

                    self.sleep_approx(2)
                    players_won, players_expired = self.getWatchlistInfo()
                    
                    unlistedPlayers = True
                    counter = 0
                    while unlistedPlayers:
                        try:
                            wait_for_shield_invisibility(self.driver)
                            wait_for_player_shield_invisibility(self.driver)
                            pid = self.getPIDWatchlist(1)
                            playerPrice = int(self.getSellPrice(pid))
                            boughtprice = self.getText("/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[1]/div[2]/div/span[2]")
                            rating = int(self.getText("/html/body/main/section/section/div[2]/div/div/section/div/div/div[1]/div/div[2]/div/div/div[1]/div/div[7]/div[2]/div[1]"))
                            position = self.getText("/html/body/main/section/section/div[2]/div/div/section/div/div/div[1]/div/div[2]/div/div/div[1]/div/div[7]/div[2]/div[2]")

                            if "," in boughtprice:
                                boughtprice = boughtprice.replace(",", "")
                            boughtprice = int(boughtprice)
                            
                            if playerPrice == 0:
                                print("player id not found in list func, setting player price equal to boughprice plus margin")
                                playerPrice = boughtprice + int(self.margin)
    
                            if (self.undercut_market_on_list == 1):
                                if playerPrice > 1000:
                                    playerPrice = playerPrice - 100
                                else:
                                    playerPrice = playerPrice - 50

                            est_profit = ((playerPrice)*.95) - boughtprice

                            startBid = 0
                            if playerPrice > 1000:
                                startBid = playerPrice - 100
                            else:
                                startBid = playerPrice - 50

                            wait_for_shield_invisibility(self.driver)
                            self.wait_for_visibility("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]")
                            playerName = str(self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div/div[1]/div[2]"))

                            playerNation = str(self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div/div[1]/div[1]/div[8]/div[1]/span[2]"))
                            playerLeague = str(self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div/div[1]/div[1]/div[8]/div[2]/span[2]"))
                            playerTeam = str(self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[1]/div/div[1]/div[1]/div[8]/div[3]/span[2]"))

                            self.clickButton('/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[1]/button') # Show player listing 
                            self.send_keys_and_more('/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[2]/div[2]/input', startBid) # Start bid
                            self.send_keys_and_more('/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/div[3]/div[2]/input', playerPrice) # Buy now
                            self.clickButton('/html/body/main/section/section/div[2]/div/div/section/div/div/div[2]/div[2]/div[2]/button') # List player
                            projected_profit += est_profit
                            self.user_projected_profit += est_profit
                            self.user_players_won += 1
                            self.update_autobidder_logs()
                            counter+=1
                            
                            eventData = [pid, boughtprice, playerPrice, playerName, playerNation, playerLeague, playerTeam, rating, position]
                            if self.undercut_market_on_list == 1:
                                self.log_event(self.queue,"LIST NAME " + str(playerName) + " | Bought for: " + str(boughtprice) + " | Sell for (UNDERCUT): " + str(playerPrice) + " | PROF: " + str(est_profit), eventData)
                            else:
                                self.log_event(self.queue,"LIST NAME " + str(playerName) + " | Bought for: " + str(boughtprice) + " | Sell for: " + str(playerPrice) + " | PROF: " + str(est_profit), eventData)
                            
                            self.sleep_approx(0.5)
                            wait_for_shield_invisibility(self.driver)
                        except Exception as e:
                            unlistedPlayers = False
                            status = False

            except Exception as e:
                log_event(self.queue,"error in listing players: ")
                print(e)
                exception_counter += 1
                if exception_counter > 3:
                    log_event(self.queue,"exception counter greater than 3, kill. setting botRunning to False ")
                    status = False
                    self.botRunning = False
        
        if (self.botRunning):
            try:
                profit_per_player = projected_profit / players_won
            except:
                profit_per_player = 0
            log_event(self.queue, "- - - - STATISTICS ROUND " + str(self.bidround_number + 1) + "- - -")
            log_event(self.queue, "Bids Made: " + str(self.bids_made_this_round) + " | Requests Made: " + str(self.requests_made_this_round))
            log_event(self.queue,"Players won: " + str(players_won) + " | Lost: " + str(players_expired))
            log_event(self.queue,"Projected profit: " + str(projected_profit) + " | Prof per player: " + str(profit_per_player))
            log_event(self.queue, " - - - - - - - - - - - -")

            self.players_won_this_round = players_won
            self.players_lost_this_round = players_expired
            self.projected_profit_this_round = projected_profit
            self.profit_per_player_this_round = profit_per_player

            page = self.checkState("watchlist")
            if page:
                # self.clearExpired()
                self.sleep_approx(5)
                log_event(self.queue,"Finished bidround " + str(self.bidround_number))
                self.end_time = datetime.now()
                # dt_string = now.strftime("[%I:%M:%S %p] ")
                self.write_to_table()
                self.go_to_transfer_market()
            else:
                log_event(self.queue,"not on watchlist, end of listPlayers func, setting bot running to false")
                self.botRunning = False
       
# HELPER METHODS ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def changeUserSettingFromAutobidder(self, new_value, option_to_change="margin"):
        # expiration_cutoff_mins
        # margin
        # undercut_market_on_list
        # undercut_market_on_relist

        self.config.read("./data/config.ini")
        count = 0
        options = self.config.options("Settings")

        new_value = int(new_value)

        # iterate over option memory objects in GUI OPTIONS list
        for option in self.GUI_OPTIONS:
            # Get option name in config.ini file
            option_name = options[count]

            option_dropdown_memory_object_name = str(option)
            current_choice = option.get()

            # print("Option memory object, talking to it from Autobidder: " + str(option_dropdown_memory_object_name) + " curVal (on GUI): " + str(current_choice))

            # Set user option to passed option
            if option_dropdown_memory_object_name == option_to_change:
                option.set(new_value)
           
            count+=1

    def checkForPopup(self):
        popup = self.check_exists_by_xpath("/html/body/div[4]/section/div/div/button")
        if popup:
            self.popup_text = self.getText("/html/body/div[4]/section/div/div/button")
            log_event(self.queue, "popup exists - text is: " + str(self.popup_text))

        else:
            return False

    def goNextPage(self):
        try:
            self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]')
            self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]').click()
            self.sleep_approx(0.5)
            self.wait_for_visibility("/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[1]")
            self.requests_made_this_round += 1
            self.user_requests_made += 1
        except:
            log_event(self.queue,"NEXTPAGE ERROR - hitting back and restarting search")
            self.hasExceededTimeCutoff = True

    def fetch_player_data(self):
        self.wait_for_visibility("/html/body/div[9]/div[2]/div[5]/div[4]/table/tbody")
        tbody = self.driver.find_element_by_xpath("/html/body/div[9]/div[2]/div[5]/div[4]/table/tbody")
        stats = tbody.find_elements(By.XPATH, './tr')
        
        players = []
        index = 1
        for row in stats:
            test = row.text
            # print(test)
            card_details = test.split("\n")
            stats = card_details[1].strip("\n").split(" ")
            # print("Card details: " + str(card_details))
            # print("\n")
            # print("Stats: " + str(stats))

            name = card_details[0].strip("\n")
            rating = stats[0]
            position = stats[1]
            price = stats[3]
            pace = stats[9]
            shooting = stats[10]
            passing = stats[11]
            dribbling = stats[12]
            defense = stats[13]
            physical = stats[14]
            
            if "K" in price:
                price = price.replace("K", "")
                price = float(price)
                price = int(price*1000)
                price = str(price)
            player_data = [rating, pace, shooting, passing, dribbling, defense, physical]

            unique_player_id = ""
            for x in player_data:
                x = str(x)
                unique_player_id += x

            player = [index, name, rating, position, price, pace,shooting,passing,dribbling, defense,physical, unique_player_id]

            players.append(player)
            full_entry = ""
            for word in player:
                word = str(word)
                word_comma = word + ","
                full_entry += word_comma

            full_entry = full_entry[:-1]

            # Add new line to end
            hs = open("./data/targetplayers.txt", "a", encoding="utf8")
            hs.write(full_entry + "\n")
            hs.close()
            index+=1

    def check_for_results(self):
        tbody = self.driver.find_element_by_xpath("/html/body/div[9]/div[2]/div[5]/div[4]/table/tbody")
        stats = tbody.find_elements(By.XPATH, './tr')
        
        for row in stats:
            test = row.text
            if test == "No Results":
                return False
        return True

    def getFutbinList(self, url):
        test = True
        # https://www.futbin.com/22/players?page=1&position=CM&xbox_price=0-1500&version=gold_nr
        try:
            log_event(self.queue, "Fetching futbin prices (new version)... ")
            self.clearOldPlayerlist() # clears targetplayers.txt
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.get(url)

            sleep(7)
            self.driver.execute_script("return window.stop")

            len_url = len(url)
            first = url[:39]
            second = url[40:len_url]

            self.sleep_approx(3)
            self.enable_xbox_prices()
            self.sleep_approx(3)

            # Iterate over page results
            keepgoing = True
            counter = 1
            while keepgoing:
                results = self.check_for_results()

                if results:
                    self.fetch_player_data()

                    counter += 1
                    new_url = first + str(counter) + second
                    self.driver.get(new_url)
                    self.sleep_approx(6)
                    self.driver.execute_script("return window.stop")
                else:
                    log_event(self.queue, "No results box, should close out the tab now")
                    keepgoing = False
            # log_event(self.queue, "Finished exit from while loop")

            # ~ ~ ~ ~ ~ ~ ~ Close the futbin tab ~ ~ ~ ~ ~
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        except:
            log_event(self.queue, "Error fetching futbin")
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.botRunning = False
        
        log_event(self.queue,"Finished fetching futbin prices, hopefully it worked - check targetplayers.txt")

    def enable_xbox_prices(self):                                                                       
        myElem = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/header/nav/div/div/ul[2]/li[4]/div/span')))
        menu = self.driver.find_element_by_xpath("/html/body/header/nav/div/div/ul[2]/li[4]/div/span")
        hidden_submenu_ps = self.driver.find_element_by_xpath("/html/body/header/nav/div/div/ul[2]/li[4]/div/ul/li[1]/a")
        hidden_submenu_xbox = self.driver.find_element_by_xpath("/html/body/header/nav/div/div/ul[2]/li[4]/div/ul/li[2]/a")
        hidden_submenu_pc = self.driver.find_element_by_xpath("/html/body/header/nav/div/div/ul[2]/li[4]/div/ul/li[3]/a")

        user_submenu_choice = ""

        if (self.platform == "Xbox"):
            user_submenu_choice = hidden_submenu_xbox
        elif (self.platform == "Playstation"):
            user_submenu_choice = hidden_submenu_ps
        elif (self.platform == "PC"):
            user_submenu_choice = hidden_submenu_pc

        actions = ActionChains(self.driver)
        actions.move_to_element(menu)
        self.sleep_approx(1)
        actions.click(user_submenu_choice)
        actions.perform()

    def installAdblock(self):
        try:
            log_event(self.queue, "Install Adblock to make FutBin search work properly")
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.get("https://chrome.google.com/webstore/detail/adblock-%E2%80%94-best-ad-blocker/gighmmpiobklfepjocnamgkkbiglidom")
            self.wait_for_visibility("/html/body/div[3]/div[2]/div/div/div[2]/div[2]/div/div/div")
            self.clickButton("/html/body/div[3]/div[2]/div/div/div[2]/div[2]/div/div/div")
            
            # check if button says add to chrome
            # self.wait_for_visibility("/html/body/div[3]/div[2]/div/div/div[2]/div[2]/div")
            # text = str(self.getText("/html/body/div[3]/div[2]/div/div/div[2]/div[2]/div"))
            # if text == "Add to Chrome":
            #     self.clickButton("/html/body/div[3]/div[2]/div/div/div[2]/div[2]/div/div/div/div")
                
            #     # try click accept
            #     # WebDriverWait(self.driver, 10).until(EC.alert_is_present())
            #     # self.driver.switch_to.alert.accept()
            #     self.sleep_approx(2)
            #     test = self.driver.find_element_by_css_selector("body")
            #     test.send_keys(Keys.LEFT)
            #     test.send_keys(Keys.ENTER)
        except Exception as e:
            # print("User broke futbin fetch, self.botRunning false")
            print(e)
            log_event(self.queue,"Failed at installing adblock")
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.botRunning = False
            
        self.driver.switch_to.window(self.driver.window_handles[0])


    def checkState(self, desiredPage=""):
        """
        Checks if user is on desired page of web app, to avoid infinite loops on user intervention.

        Location:
            anywhere

        Parameters:
            desiredPage (str): watchlist, transfermaket, or transferlist

        Returns:
            True or False
        """
        infiniteloopcounter = 0
        try:
            wait_for_shield_invisibility(self.driver)

            page = self.driver.find_element(
                By.XPATH, "/html/body/main/section/section/div[1]/h1").text
            page = str(page)
            page = page.lower()

            if desiredPage == "":
                return page
            elif (desiredPage == "watchlist"):
                if (page == "transfer targets"):
                    return True
                else:
                    return False

            elif (desiredPage == "transfermarket"):
                if (page == "search results"):
                    return True
                else:
                    return False

            elif (desiredPage == "transferlist"):
                if (page == "transfer list"):
                    return True
                else:
                    return False
            else:
                log_event(self.queue, " was passed invalid location")
        except:
            infiniteloopcounter +=1 
            if infiniteloopcounter > 5:
                log_event(self.queue, "Error checking state")
            else:
                self.checkState()
            
    def clearExpired(self):
        """
        Clicks 'clear expired' button.

        Location:
            watch list
        """
        self.sleep_approx(1)
        all_players_expired_pretty_list_for_google = []
        try:
            playersOnPage = self.driver.find_elements(By.TAG_NAME, "li.listFUTItem")

            num_players_expired = 0
            for player in playersOnPage:
                try:
                    bidStatus = player.get_attribute("class")
                    bidStatus = str(bidStatus)
                    if "expired" in bidStatus:
                        num_players_expired += 1

                        cardinfo = player.text.splitlines()
                        # print(cardinfo)

                        rating, name, startprice, curbid_or_finalsoldprice, buynow, time = cardinfo[0], cardinfo[2], cardinfo[16], cardinfo[18], cardinfo[20], cardinfo[22]

                        if "," in curbid_or_finalsoldprice:
                            curbid_or_finalsoldprice = curbid_or_finalsoldprice.replace(",", "")
                        curbid_or_finalsoldprice = int(curbid_or_finalsoldprice)

                        position = cardinfo[1]
                        pace = int(cardinfo[4])
                        shooting = int(cardinfo[6])
                        passing = int(cardinfo[8])
                        dribbling = int(cardinfo[10])
                        defending = int(cardinfo[12])
                        physical = int(cardinfo[14])
                        rating = int(rating)

                        playerNation = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[4]/ul/li[" + str(num_players_expired) + "]/div/div[1]/div[1]/div[8]/div[1]/span[2]")
                        playerLeague = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[4]/ul/li[" + str(num_players_expired) + "]/div/div[1]/div[1]/div[8]/div[2]/span[2]")
                        playerTeam = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[4]/ul/li[" + str(num_players_expired) + "]/div/div[1]/div[1]/div[8]/div[3]/span[2]")


                        player_data = [rating, pace, shooting, passing, dribbling, defending, physical]

                        unique_player_id = ""
                        for x in player_data:
                            x = str(x)
                            unique_player_id += x

                        text = "LOST PID: " + str(unique_player_id) + " NAME: " + str(name) + " SOLDPRICE: " + str(curbid_or_finalsoldprice) + " POSITION: " + str(position)
                        eventData = [unique_player_id, curbid_or_finalsoldprice, rating, name, position, playerNation, playerLeague, playerTeam]
                        # self.log_event(self.queue, text, eventData)
                        pretty_log = self.log_eventv2(self.queue, text, eventData)
                        log_event(self.queue,text)
                        all_players_expired_pretty_list_for_google.append(pretty_log)
                except Exception as e:
                    # self.errorCounter +=1
                    print(e)
                    # eventData = ["00000000000000", 0, 0, "error", "error"]
                    # self.log_event(self.queue, "error6", eventData)
                    # self.errorCounter +=1

            if num_players_expired > 0:
                clearExpired = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[4]/header/button")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", clearExpired)
                WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[4]/header/button"))).click()
                self.sleep_approx(1)
                log_event(self.queue, "Cleared expired")
                self.sleep_approx(1)
        except Exception as e:
            try:
                print(e)
                clearExpired = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[4]/header/button")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", clearExpired)
                WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/main/section/section/div[2]/div/div/div/section[4]/header/button"))).click()
                self.sleep_approx(1)
                log_event(self.queue, "Cleared expired")
                self.sleep_approx(1)
            except:
                print("check for popup here network connection lost ")
                exists = self.check_exists_by_xpath("/html/body/div[4]/section")
                if exists:
                    self.popup_text = self.getText("/html/body/div[4]/section/div/p")
        if len(all_players_expired_pretty_list_for_google) > 0:
            print("looks good, going to push the array to google now")
            # self.pushGoogle(all_players_expired_pretty_list_for_google)

    def clickBack(self):
            exists = self.check_exists_by_xpath("/html/body/main/section/section/div[1]/button[1]")
            if exists:
                self.clickButton("/html/body/main/section/section/div[1]/button[1]")

    def clearSold(self):
        """
        Clicks 'clear sold' button.

        Location:
            transfer list
        """
        self.sleep_approx(1)
        playersOnPage = self.driver.find_elements(By.TAG_NAME, "li.listFUTItem")

        num_players_sold = 0
        all_event_data = []
        for player in playersOnPage:
            bidStatus = player.get_attribute("class")
            bidStatus = str(bidStatus)
            
            if "won" in bidStatus:
                num_players_sold += 1
                nation = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li[" + str(num_players_sold) + "]/div/div[1]/div[1]/div[8]/div[1]/span[2]")
                league = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li[" + str(num_players_sold) + "]/div/div[1]/div[1]/div[8]/div[2]/span[2]")
                team = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[1]/ul/li[" + str(num_players_sold) + "]/div/div[1]/div[1]/div[8]/div[3]/span[2]")
                cardinfo = player.text.splitlines()
                # print(cardinfo)

                rating, name, startprice, curbid_or_finalsoldprice, buynow, time = cardinfo[0], cardinfo[2], cardinfo[16], cardinfo[18], cardinfo[20], cardinfo[22]
                curbid_or_finalsoldprice = curbid_or_finalsoldprice
                if "," in curbid_or_finalsoldprice:
                    curbid_or_finalsoldprice = curbid_or_finalsoldprice.replace(",", "")
                curbid_or_finalsoldprice = int(curbid_or_finalsoldprice)
                # buynow = int(buynow)
                position = cardinfo[1]
                pace = int(cardinfo[4])
                shooting = int(cardinfo[6])
                passing = int(cardinfo[8])
                dribbling = int(cardinfo[10])
                defending = int(cardinfo[12])
                physical = int(cardinfo[14])
                rating = int(rating)

                player_data = [rating, pace, shooting, passing, dribbling, defending, physical]

                unique_player_id = ""
                for x in player_data:
                    x = str(x)
                    unique_player_id += x
                
                # sold price
                # log_event(self.queue, "")
                text = "SOLD PID: " + str(unique_player_id) + " NAME: " + str(name) + " SOLDPRICE: " + str(curbid_or_finalsoldprice) + " POSITION: " + str(position)
                eventData = [unique_player_id, name, curbid_or_finalsoldprice, position, rating, nation, league, team]
                packaged = [text, eventData]
                all_event_data.append(packaged)


        # clear sold here
        try:
            self.scrollIntoView("/html/body/main/section/section/div[2]/div/div/div/section[1]/header/button")
            self.sleep_approx(1)
            wait_for_shield_invisibility(self.driver)

            self.clickButton("/html/body/main/section/section/div[2]/div/div/div/section[1]/header/button")
        except Exception as e:
            print("new clear sold method broke error msg is: ")
            print(e)
            print("retrying click clear sold - maybe add WAIT FOR PLAYER SHIELD INVISIBILTIY befoer clickbutton")

            self.scrollIntoView("/html/body/main/section/section/div[2]/div/div/div/section[1]/header/button")
            self.sleep_approx(1)
            wait_for_shield_invisibility(self.driver)

            self.clickButton("/html/body/main/section/section/div[2]/div/div/div/section[1]/header/button")

        # log the events
        batch_rows_to_append_google = []
        for event in all_event_data:
            text = event[0]
            eventData = event[1]

            rowCleaned = self.log_eventv2(self.queue, text, eventData)
            log_event(self.queue, event) # only doing this so it prints
            batch_rows_to_append_google.append(rowCleaned)


        # batch send all rows to gsheets
        # self.pushGoogle(batch_rows_to_append_google)

    def sleep_approx(self, seconds):
        """
        Randomizes sleep to avoid detection.
        """
        upperbound = (seconds+0.2)*10000
        if (seconds >= 1):
            lowerbound = (seconds-0.2)*10000
        else:
            lowerbound = seconds*10000

        lowerbound = int(lowerbound)
        upperbound = int(upperbound)

        sleeptime = random.randint(lowerbound, upperbound)
        sleeptime = sleeptime/10000
        sleeptime = sleeptime*.8

        sleep(sleeptime)

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


    def go_to_transfer_market(self):
        """
        Clicks Transfer Market button on sidebar.

        Location:
            anywhere
        """
        try:
            self.driver.find_element(By.CLASS_NAME, 'icon-transfer').click()

            sleeptime = random.randint(1, 5)

            selling = str(self.getText("/html/body/main/section/section/div[2]/div/div/div[3]/div[2]/div/div[2]/span[2]"))
            self.user_transferlist_selling = selling

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
            self.sleep_approx(5)
            self.clickButton('/html/body/main/section/nav/button[3]')
            self.sleep_approx(5)
            self.clickButton('/html/body/main/section/section/div[2]/div/div/div[4]')
            # self.driver.find_element(
            #     By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[4]').click()
            self.sleep_approx(5)
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
                print("Went to transfer list")
                self.driver.find_element(
                    By.XPATH, "/html/body/main/section/section/div[2]/div/div/div[3]").click()
                self.sleep_approx(1)
            except:
                self.transferlistInfiniteLoopCounter+=1
                log_event(self.queue, "Exception retrying go_to_transferlist")
                self.go_to_transferlist()
        else:
            log_event(self.queue, "infinite loop detected")


    def clickSearch(self):
        """
        Clicks 'Search' button.

        Location:
            transfer market search page
        """

        #         self.clickButton("/html/body/main/section/section/div[2]/div/div[2]/div/div[2]/button[2]")

        self.sleep_approx(1)
        self.driver.find_element(
            By.XPATH, '(//*[@class="button-container"]/button)[2]').click()
        self.user_requests_made += 1
        
    def clickButton(self, xpath):
        """
        Clicks button via XPATH.

        Location:
            anywhere

        Parameters:
            xpath (str): The object's XPATH.
        """
        self.sleep_approx(0.5)
        WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, xpath))).click()
        self.sleep_approx(1)

    def clearOldPlayerlist(self):
        """

        Location:
            transfer market
        """
        file = open("./data/targetplayers.txt", "r+")
        file.truncate(0)
        file.close()

    def wait_for_visibility(self, xpath, duration=0.25):
        """
        Detects loading circle and waits for it to dissappear. 
        """
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, xpath))
        )

    def getTargetListIDS(self):
        players = []
        txt = open("./data/targetplayers.txt", "r", encoding="utf8")
        dataset = []
        for aline in txt:
            player = aline.strip("\n").split(",")
            player_id = int(player[11])
            dataset.append(player_id)

        return dataset

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

        item = self.driver.find_element(By.XPATH, xpath)
        text2 = item.text

        if len(text2) == 0:
            # print("using special text method")
            text = item.get_attribute("innerHTML")
            return text
        else:
            return text2

    def getAllPlayerInfo2(self):
        """
        Parses all players on current page of market.
        Saves info to data/market_logs.txt, to be used when
        parsing the market data to find the player's actual
        sell price

        """
        sleep(3)
        status = self.checkState("transfermarket")
        if status:
            players_on_page = self.driver.find_elements(By.TAG_NAME, "li.listFUTItem")

            playerdata = []
            playernumber = 1
            for card in players_on_page:
                bidstatus = card.get_attribute("class")
                cardinfo = card.text.splitlines()
                # print(cardinfo)

                rating, name, startprice, curbid_or_finalsoldprice, buynow, time = cardinfo[0], cardinfo[2], cardinfo[16], cardinfo[18], cardinfo[20], cardinfo[22]
                position = cardinfo[1]
                pace = int(cardinfo[4])
                shooting = int(cardinfo[6])
                passing = int(cardinfo[8])
                dribbling = int(cardinfo[10])
                defending = int(cardinfo[12])
                physical = int(cardinfo[14])
                rating = int(rating)

                # clean timeremaining
                seconds = 0
                if "<" in time:
                    if "<5" in time:
                        seconds = 5
                    elif "<10" in time:
                        seconds = 10
                    elif "<15" in time:
                        seconds = 15
                    elif "<30" in time:
                        seconds = 30
                    elif "Minute" in time:
                        seconds = 60
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

                if "," in startprice:
                    startprice = startprice.replace(",", "")
                startprice = int(startprice)
                
                if "," in buynow:
                    buynow = buynow.replace(",", "")
                buynow = int(buynow)
            
                # clean current bid or finalsoldprice
                if "---" in curbid_or_finalsoldprice:
                    if startprice < 1000:
                        curbid_or_finalsoldprice = startprice - 50
                    else:
                        curbid_or_finalsoldprice = startprice - 100
                elif "," in curbid_or_finalsoldprice:
                    curbid_or_finalsoldprice = curbid_or_finalsoldprice.replace(",", "")
                curbid_or_finalsoldprice = int(curbid_or_finalsoldprice)

                player_data = [rating, pace, shooting, passing, dribbling, defending, physical]
                unique_player_id = ""

                for x in player_data:
                    x = str(x)
                    unique_player_id += x

                id = 0
                info = [playernumber, position, bidstatus, rating, name,
                        startprice, curbid_or_finalsoldprice, buynow, time, id, pace, shooting, passing, dribbling, defending, physical, unique_player_id]
                        # time and id are wrong
                playerdata.append(info)
                playernumber += 1

            return playerdata
            # except:
            #     log_event(self.queue, "Exception getAllPlayerInfo")

    def getPlayerBidstatus(self, playernumber):
        status = self.checkState("transfermarket")
        if status:
            loc = "/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(playernumber) + "]"
            player = self.driver.find_element(By.XPATH, loc)
            status = str(player.get_attribute("class"))
            # print(status)
            return status

    def makebid_individualplayer2(self, playernumber, bid_to_make):
        status = self.checkState("transfermarket")
        if status:
            # Click player
            playerbutton = "/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[" + str(playernumber) + "]/div"
            self.clickButton(playerbutton)

            # get current bid before bidding
            self.wait_for_visibility("/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[1]/div/div[2]/span[2]")
            makebidbutton = self.driver.find_element(By.XPATH, "/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/button[1]")
            original_currentbid = self.getText("/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[1]/div/div[2]/span[2]")
            self.send_keys_and_more("/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/div/input", bid_to_make)

            after_currentbid = self.getText("/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[1]/div/div[2]/span[2]")

            if (original_currentbid == after_currentbid):
                # get number in text box
                bidinputbox = self.driver.find_element_by_xpath("/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/div/input")
                bidinput = str(bidinputbox.get_attribute("value"))

                if "," in bidinput:
                    bidinput = bidinput.replace(",", "")
                bidinput = int(bidinput)

                if bidinput == bid_to_make:
                    makebidbutton.click()

                    # CHECK IF BID WENT THROUGH
                    self.sleep_approx(3)
                    wait_for_shield_invisibility(self.driver)
                    watchlistFullPopup = self.check_exists_by_xpath("/html/body/div[4]/section/div/div/button")
                    if watchlistFullPopup == False:

                        status = self.getPlayerBidstatus(playernumber)

                        if "outbid" in status:
                            # print("BID NO WORK CLICKing UNWATCH ")
                            self.sleep_approx(1.5)
                            self.wait_for_visibility("/html/body/main/section/section/div[2]/div/div/section[1]/div/ul/li[1]")
                            try:
                                # unwatch button:
                                self.clickButton("/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[1]/div/div[3]/button")
                                self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]')
                                self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]').click()
                                self.requests_made_this_round += 1
                                self.user_requests_made += 1
                            except:
                                print("exception clicking unwatch lolol")                  
                        
                        elif "highest-bid" in status:
                            self.user_bids_made += 1
                            self.bids_made_this_round +=1
                            self.update_autobidder_logs()
                            return True
                        elif "expired" in status:
                            print("p expired")
                        else:
                            print("Status wasn't updated in time")
                            print("status was: " + str(status))
                            # self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]')
                            # self.driver.find_element_by_xpath('/html/body/main/section/section/div[2]/div/div/section[1]/div/div/button[2]').click()
                            # self.botRunning = False
                            self.requests_made_this_round += 1
                            self.user_requests_made += 1
                            self.user_blank_bids_softban_count += 1
                            return False
                    else:
                        return False
                else:
                    print("Avoided bid error")
                    return False # returns true bc only return false if softban
            else:
                print("Avoided bid error")
                return False

        else:
            return False

    def verifySearch(self):
        try:
            cardtype = "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[2]/div/div/span" # gold
            rarity = "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[3]/div/div/span" # common
            league = "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[1]/div[7]/div/div/span" # Serie A TIM (ITA 1)

            cardtype = self.getText(cardtype)
            cardtype = str(cardtype)
            cardtype = cardtype.lower()

            rarity = self.getText(rarity)
            rarity = str(rarity)
            rarity = rarity.lower()

            league = self.getText(league)
            league = str(league)
            league = league.lower()

            minbin = "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[5]/div[2]/input"
            maxbin = "/html/body/main/section/section/div[2]/div/div[2]/div/div[1]/div[2]/div[6]/div[2]/input"

            minbin = self.getInputBoxText(minbin)
            maxbin = self.getInputBoxText(maxbin)
            if (cardtype == "gold"):
                print("gold yes")
                if (rarity == "common"):
                    print("rarity common")
                    if(league == "serie a tim (ita 1)"):
                        print("league yes")
                        print("all good")
                        if (minbin == 9900) and (maxbin == 10000):
                            print("all perfect")
                            return True
            return False
        except:
            return False
           
    def getInputBoxText(self, xpath):
        inputbox = self.driver.find_element_by_xpath(xpath)
        bidinput = str(inputbox.get_attribute("value"))

        if "," in bidinput:
            bidinput = bidinput.replace(",", "")
        bidinput = int(bidinput)
        return bidinput

    def send_keys_and_more(self, xpath, price):
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
        self.sleep_approx(.25)
        self.wait_for_visibility(xpath)
        textbox = self.driver.find_element(By.XPATH, xpath)
        textbox.click()
        self.sleep_approx(0.25)
        textbox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        textbox.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        price = str(price)
        textbox.send_keys(price)
        # self.sleep_approx(.2)
        # # click + button then - button 
        # self.clickButton("/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/div/button[2]")
        # self.sleep_approx(.2)
        # self.clickButton("/html/body/main/section/section/div[2]/div/div/section[2]/div/div/div[2]/div[2]/div/button[1]")
        # self.sleep_approx(.2)

    def getSellPrice(self, pid):
        pid = int(pid)
        futbindata = self.getTargetList()

        for x in futbindata:
            thatid = int(x[11])
            if (thatid == pid):
                price = str(x[4])
                if "K" in price:
                    # print("k found in price")
                    price = price.replace("K", "")
                    price = float(price)
                    price = int(price*1000)
                price = int(price)

                # if (price > 1000):
                #     price = price - 100
                # else:
                #     price = price - 50
                return int(price)
        print("no id found lol input" + str(pid))
        
        return 0

    def getPlayerInfoFromID(self, pid):
        # 4,Suso,82,RW,750,
        pid = int(pid)
        futbindata = self.getTargetList()

        for x in futbindata:
            thatid = int(x[11])
            if (thatid == pid):
                name = str(x[1])
                rating = str(x[2])
                position = str(x[3])
                price = str(x[4])

                
                return name, rating, position, price
        print("no id found lol input" + str(pid))
        
        return "unknown", 0, "unknown", 900

    def round_nearest(self, x,num=50):
        return int(round(float(x)/num)*num)

    def getUserConfig(self):
        """
        Fetches user config variables from config.json.
        Also updates config options on GUI if they changed on backend.

        Location:
            anywhere
        """
        self.config.read("./data/config.ini")


        # SETTINGS START
        self.sleep_time = int(self.config.get("Settings", "sleep_time"))
        self.num_cycles = int(self.config.get("Settings", "num_cycles"))
        self.expiration_cutoff_mins = int(self.config.get("Settings", "expiration_cutoff_mins"))
        self.margin = int(self.config.get("Settings", "margin"))

        self.undercut_market_on_list = int(self.config.get("Settings", "undercut_market_on_list"))
        self.undercut_market_on_relist = int(self.config.get("Settings", "undercut_market_on_relist"))

        self.futbin_max_price = int(self.config.get("Settings", "futbin_max_price"))
        self.platform = str(self.config.get("Settings", "platform"))


        # Return values but this really shouldn't be used - only used on initialization
        return self.undercut_market_on_list, self.sleep_time, self.num_cycles, self.expiration_cutoff_mins, self.margin, self.undercut_market_on_relist, self.futbin_max_price, self.platform

    def update_autobidder_logs(self):
        """
        Updates GUI with current user config vars.
        Wanted more control over how many reads/writes the bot makes, so made this a separate method.

        Location:
            anywhere
        """
        #                self.config.set("Settings", option_name, str(choice))
           #     self.config.write(open("./data/config.ini", "w"))
        # also update user config vars
        self.getUserConfig()
        self.config.read("./data/config.ini")

        try:
            num_coins = self.driver.find_element(By.XPATH, '/html/body/main/section/section/div[1]/div[1]/div[1]').text
            num_coins = str(num_coins)
            if "," in num_coins:
                num_coins = num_coins.replace(",", "")

            num_coins = int(num_coins)
            self.user_num_coins = num_coins

            self.config.set("Statistics", "players_won", str(self.user_players_won))
            self.config.set("Statistics", "players_lost", str(self.user_watchlist_outbid))
            self.config.set("Statistics", "players_sold", str(self.user_transferlist_sold))
            self.config.set("Statistics", "players_relisted", str(self.user_transferlist_relisted))
            self.config.set("Statistics", "current_coins", str(self.user_num_coins))
            self.config.set("Statistics", "projected_profit", str(self.user_projected_profit))
            self.config.set("Statistics", "total_cycles", str(self.total_cycles))
            self.config.set("Statistics", "requests_made", str(self.user_requests_made))
            self.config.set("Statistics", "bids_made", str(self.user_bids_made))
            self.config.set("Statistics", "current_selling", str(self.user_transferlist_selling))
            # self.config.write(open("./data/config.ini", "w"))
            with open('./data/config.ini', 'w') as configfile:
                self.config.write(configfile)

        except Exception as e:
            print("PIZA")
            print("Err hhhhhhupdate_autobidder_logs: " + str(e))

    def getTargetList(self):
        players = []
        txt = open("./data/targetplayers.txt", "r", encoding="utf8")
        for aline in txt:
            player = aline.strip("\n").split(",")
            players.append(player)
        return players

    def getPIDWatchlist(self, playernumber):

        # position = "/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(playernumber) + "]/div/div[1]/div[1]/div[5]/div[2]/div[2]"
        rating = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(playernumber) + "]/div/div[1]/div[1]/div[5]/div[2]/div[1]")
        pace = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(playernumber) + "]/div/div[1]/div[3]/ul/li[1]/span[2]")
        shooting = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(playernumber) + "]/div/div[1]/div[3]/ul/li[2]/span[2]")
        passing = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(playernumber) + "]/div/div[1]/div[3]/ul/li[3]/span[2]")
        dribbling = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(playernumber) + "]/div/div[1]/div[3]/ul/li[4]/span[2]")
        defending = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(playernumber) + "]/div/div[1]/div[3]/ul/li[5]/span[2]")
        physical = self.getText("/html/body/main/section/section/div[2]/div/div/div/section[3]/ul/li[" + str(playernumber) + "]/div/div[1]/div[3]/ul/li[6]/span[2]")

        player_data = [rating, pace, shooting, passing, dribbling, defending, physical]
        unique_player_id = ""

        for x in player_data:
            x = str(x)
            unique_player_id += x
        
        return unique_player_id

    def getWatchlistInfo(self):
        infiniteloopcounter = 0
        page = self.checkState("watchlist")
        if page:
            try:
                players_on_page = self.driver.find_elements(By.TAG_NAME, "li.listFUTItem")
            
                playerdata = []
                playernumber = 1
                players_won = 0
                players_expired = 0

                for card in players_on_page:
                    # Only look at top 5 players
                    bidstatus = card.get_attribute("class")
                    cardinfo = card.text.splitlines()
                    # print(cardinfo)

                    rating = cardinfo[0]
                    name = cardinfo[2]
                    startprice = cardinfo[16]
                    curbid_or_finalsoldprice = cardinfo[18]
                    buynow = cardinfo[20]
                    time = cardinfo[22]

                    if "won" in bidstatus:
                        players_won += 1
                    if "expired" in bidstatus:
                        players_expired += 1

                # self.user_players_won += players_won
                self.user_watchlist_outbid += players_expired

                log_event(self.queue, "Players won: " + str(players_won) + " expired: " + str(players_expired))
                self.update_autobidder_logs()
                return players_won, players_expired
            except:
                infiniteloopcounter += 1
                if infiniteloopcounter < 5:

                    self.getWatchlistInfo()
                else:
                    print("infinite loop counter on getWatchlistInfo exceeded 5, setting botRunning to false ")
                    self.botRunning = False
        else:
            self.botRunning = False
            print("setting bot running to false bc getWatchlistInfo failed")
            return 0, 0
 
    def getTransferlistInfo(self):
        state = self.checkState("transferlist")
        if state:
            infiniteloopcounter = 0
            try:
                players_on_page = self.driver.find_elements(By.TAG_NAME, "li.listFUTItem")
            
                playerdata = []
                playernumber = 1

                players_sold = 0
                players_currently_listed = 0
                players_unlisted = 0
                players_expired = 0

                for card in players_on_page:
                    bidstatus = str(card.get_attribute("class"))
                    cardinfo = card.text.splitlines()

                    if ("won" in bidstatus):
                        players_sold += 1
                    elif (bidstatus == "listFUTItem has-auction-data"):
                        players_currently_listed +=1
                    elif (bidstatus == "listFUTItem"):
                        players_unlisted +=1
                    elif ("expired" in bidstatus):
                        players_expired +=1

                return players_expired, players_sold, players_currently_listed, players_unlisted
            except:
                infiniteloopcounter += 1
                print("err getTLsum")
                if infiniteloopcounter < 5:
                    # self.sleep_approx(2)
                    return self.getTransferlistInfo()
                else:
                    print("infinite loop counter on getTransferlistInfo exceeded 5")
        else:
            log_event(self.queue, "Not on transfer list, botrunning false")
            self.botRunning = False

    def write_to_table(self):
        bidround_number = self.total_cycles
        now = datetime.now()
        dt_string = now.strftime("[%I:%M:%S %p]")

        # add try except here
        try:
            time_elapsed = self.end_time - self.start_time
            total_seconds = time_elapsed.total_seconds()
            mins = int(total_seconds/60)
            seconds = int(total_seconds - (60*mins))

            time_pretty = str(mins) + ":" + str(seconds)

            agg = [dt_string, time_pretty, bidround_number, self.players_won_this_round, self.players_lost_this_round, self.bids_made_this_round, self.requests_made_this_round, self.margin, self.players_sold_this_round, self.players_expired_this_round, int(self.projected_profit_this_round), int(self.profit_per_player_this_round)]
            self.log_event(self.queue, "BIDROUNDOVER woohoo", agg)
            full_entry = ""
            for word in agg:
                word = str(word)
                word_comma = word + ","
                full_entry += word_comma

            full_entry = full_entry[:-1]

            # send entry to queue object to update GUI
            log_event(self.queue, full_entry, "bidround")

            # Add new line to end
            hs = open("./data/bid_rounds.txt", "a", encoding="utf8")
            hs.write(full_entry + "\n")
            hs.close()
        except:
            log_event(self.queue, "Short term finished")

    def log_eventv2(self, queue, event, eventData=""):
        """
        Special logging method for when writing to new file
        """
        event = str(event)
        # log_event(queue, event)

        if (len(eventData)) > 1:
            split = event.split(" ")
            event_action = split[0]

            today = date.today()
            now = datetime.now()

            # General
            date2 = str(today.strftime("%m/%d/%Y"))
            time = now.strftime("%I:%M:%S %p")
            coins = self.user_num_coins

            # player specific
            player_id = 0
            player_name = ""
            unique_id = ""
            rating = ""
            position = ""
            player_nation = ""
            player_league = ""
            player_team = ""

            action = ""
            location = ""

            # ACTION DETAILS
            bid_action = 0
            sold_action = 0
            relist_action = 0
            list_action = 0
            lost_action = 0
            
            # BID
            curbid = ""
            bid_made = ""
            sell_price = ""
            sell_price_minus_tax = ""
            est_profit = ""

            # SOLD
            sold_price_won = ""

            # RELIST
            relist_price = ""

            # LIST
            boughtprice = ""
            list_price = ""

            # LOST
            sold_price_outbid = ""

            # SUMMARY
            time_elapsed = ""
            won = ""
            lost = ""
            bids = ""
            requests = ""
            margin = ""
            sold = ""
            relisted = ""
            profit = ""
            profit_per_player = ""
            url = self.url

            if event_action == "SUMMARY":
                action = "SUMMARY"
                location = "none"
                time_elapsed = ""
                won = ""
                lost = ""
                bids = ""
                requests = ""
                margin = ""
                sold = ""
                relisted = ""
                profit = ""
                profit_per_player = ""

            elif event_action == "BID":
                # eventData = [pid, name, curbid, idealbid, sell_quickily_price, (sell_quickily_price*.95), ((sell_quickily_price*.95) - idealbid), nation, league, team, rating, position]]
                # eventData = [pid, p[4], curbid, idealbid, sell_quickily_price, (sell_quickily_price*.95), ((sell_quickily_price*.95) - idealbid), nation, league, team, position, rating]

                player_id = eventData[0]
                player_name, rating, position, price = self.getPlayerInfoFromID(eventData[0])
                player_id = eventData[0]
                player_name = str(eventData[1])
                rating = int(rating)
                position = position
                action = "BID"
                location = "transfer market"
                player_nation = eventData[7]
                player_league = eventData[8]
                player_team = eventData[9]
                # rating = eventData[10]
                # position = eventData[11]

                # unique ones
                curbid = eventData[2]
                bid_made = eventData[3]
                sell_price = eventData[4]
                sell_price_minus_tax = eventData[5]
                est_profit = eventData[6]
                bid_action = 1
                
            elif event_action == "LOST":
                # eventData = [unique_player_id, curbid_or_finalsoldprice, rating, name, position]	
                # eventData = [unique_player_id, curbid_or_finalsoldprice, rating, name, position, playerNation, playerLeague, playerTeam]

                player_id = eventData[0]
                if (player_name != "unknown"):
                    player_id = eventData[0]
                    player_name = eventData[3]
                    rating = int(eventData[2])
                    position = eventData[4]
                    action = "LOST"
                    location = "watchlist"

                    player_nation = eventData[5]
                    player_league = eventData[6]
                    player_team = eventData[7]

                # UNIQUES
                sold_price_outbid = eventData[1]
                lost_action = 1

            elif event_action == "SOLD":
                # [unique_player_id, name, curbid_or_finalsoldprice, position, rating]
                # [unique_player_id, name, curbid_or_finalsoldprice, position, rating, nation, league, team]

                player_id = eventData[0]
                player_name = eventData[1]
                position = eventData[3]
                rating = int(eventData[4])
                player_id = eventData[0]
                player_name = player_name
                rating = rating
                position = position
                action = "SOLD"
                location = "transfer list"
                rating = int(rating)
                player_nation = eventData[5]
                player_league = eventData[6]
                player_team = eventData[7]

                # UNIQUES
                sold_price_won = eventData[2]
                sold_action = 1

            elif event_action == "RELIST":
                # eventData = [unique_player_id, name, relist_price, position, rating]
                # eventData = [unique_player_id, name, relist_price, position, rating, nation, league, team]

                player_id = eventData[0]
                player_name = eventData[1]
                position = eventData[3]
                rating = int(eventData[4])
                player_id = eventData[0]
                player_name = player_name
                rating = rating
                position = position
                action = "RELIST"
                location = "transfer list"

                player_nation = eventData[5]
                player_league = eventData[6]
                player_team = eventData[7]
                
                # UNIQUES 
                relist_price = eventData[2]
                relist_action = 1

            elif event_action == "LIST":
                # eventData = [pid, boughtprice, playerPrice, playerName, playerNation, playerLeague, playerTeam]
                player_id = eventData[0]
                player_name, rating, position, price = self.getPlayerInfoFromID(eventData[0])
                
                player_id = eventData[0]
                player_name = eventData[3] # player_name
                rating = int(rating)
                position = position
                action = "LIST"
                location = "watchlist"

                player_nation = eventData[4]
                player_league = eventData[5]
                player_team = eventData[6]

                # UNIQUES
                boughtprice = eventData[1]
                list_price = eventData[2]
                list_action = 1

            elif event_action == "BIDROUNDOVER":
                time_elapsed = eventData[1]
                won = eventData[3]
                lost = eventData[4]
                bids = eventData[5]
                requests = eventData[6]
                margin = eventData[7]
                sold = eventData[8]
                relisted = eventData[9]
                profit = eventData[10]
                profit_per_player = eventData[11]
                action = "SUMMARY"
                location = "SUMMARY"

            elif event_action == "STOPPED":
                # ["00000000000000", 0, 0, "error", "error", LOCATION]
                reason = eventData[5]
                action = "STOPPED"
                location = str(reason)
                player_id = ""


            if (event_action != "BIDROUNDOVER"):
                if (event_action != "SOFTBAN"):
                    if (event_action != "STOPPED"):
                        # convert player id to int
                        try:
                            pid = str(player_id)
                            unique_id = player_name + "_" + str(rating) + "_" + str(position) + "_" + pid
                            player_id = int(player_id)
                        except:
                            print("casting player ID to int didn't work")
    
            new_datetime = date2 + " " + time
            final = [date2,time,new_datetime,coins,player_id,player_name,unique_id,rating,position,player_nation,player_league,player_team,action,location,bid_action, sold_action, relist_action, list_action, lost_action, curbid,bid_made,sell_price,sell_price_minus_tax,est_profit,sold_price_won,relist_price,boughtprice,list_price,sold_price_outbid,time_elapsed,won,lost,bids,requests,margin,sold,relisted,profit,profit_per_player,url]

            with open(r'./data/logs.csv', 'a', encoding="utf8") as f:
                writer = csv.writer(f)
                writer.writerow(final)
        
            if self.PUSH_TO_GOOGLE:
                self.pushGoogle(final)

            return final

    def log_event2(self, event, msg_type = ''):
        event = str(event)

        combined = [event, msg_type]
        self.queue.put(combined)
        
    def log_event(self, queue, event, eventData=""):
        """
        Special logging method for when writing to new file
        """
        event = str(event)
        log_event(queue, event)

        if (len(eventData)) > 1:
            split = event.split(" ")
            event_action = split[0]

            today = date.today()
            now = datetime.now()

            # General
            date2 = str(today.strftime("%m/%d/%Y"))
            time = now.strftime("%I:%M:%S %p")
            coins = self.user_num_coins

            # player specific
            player_id = 0
            player_name = ""
            unique_id = ""
            rating = ""
            position = ""
            player_nation = ""
            player_league = ""
            player_team = ""

            action = ""
            location = ""

            # ACTION DETAILS
            bid_action = 0
            sold_action = 0
            relist_action = 0
            list_action = 0
            lost_action = 0
            
            # BID
            curbid = ""
            bid_made = ""
            sell_price = ""
            sell_price_minus_tax = ""
            est_profit = ""

            # SOLD
            sold_price_won = ""

            # RELIST
            relist_price = ""

            # LIST
            boughtprice = ""
            list_price = ""

            # LOST
            sold_price_outbid = ""

            # SUMMARY
            time_elapsed = ""
            won = ""
            lost = ""
            bids = ""
            requests = ""
            margin = ""
            sold = ""
            relisted = ""
            profit = ""
            profit_per_player = ""
            url = self.url

            if event_action == "SUMMARY":
                action = "SUMMARY"
                location = "none"
                time_elapsed = ""
                won = ""
                lost = ""
                bids = ""
                requests = ""
                margin = ""
                sold = ""
                relisted = ""
                profit = ""
                profit_per_player = ""

            elif event_action == "BID":
                # eventData = [pid, name, curbid, idealbid, sell_quickily_price, (sell_quickily_price*.95), ((sell_quickily_price*.95) - idealbid), nation, league, team, rating, position]]
                # eventData = [pid, p[4], curbid, idealbid, sell_quickily_price, (sell_quickily_price*.95), ((sell_quickily_price*.95) - idealbid), nation, league, team, position, rating]

                player_id = eventData[0]
                player_name, rating, position, price = self.getPlayerInfoFromID(eventData[0])
                player_id = eventData[0]
                player_name = str(eventData[1])
                rating = int(rating)
                position = position
                action = "BID"
                location = "transfer market"
                player_nation = eventData[7]
                player_league = eventData[8]
                player_team = eventData[9]
                # rating = eventData[10]
                # position = eventData[11]

                # unique ones
                curbid = eventData[2]
                bid_made = eventData[3]
                sell_price = eventData[4]
                sell_price_minus_tax = eventData[5]
                est_profit = eventData[6]
                bid_action = 1
                
            elif event_action == "LOST":
                # eventData = [unique_player_id, curbid_or_finalsoldprice, rating, name, position]	
                # eventData = [unique_player_id, curbid_or_finalsoldprice, rating, name, position, playerNation, playerLeague, playerTeam]

                player_id = eventData[0]
                if (player_name != "unknown"):
                    player_id = eventData[0]
                    player_name = eventData[3]
                    rating = int(eventData[2])
                    position = eventData[4]
                    action = "LOST"
                    location = "watchlist"

                    player_nation = eventData[5]
                    player_league = eventData[6]
                    player_team = eventData[7]

                # UNIQUES
                sold_price_outbid = eventData[1]
                lost_action = 1

            elif event_action == "SOLD":
                # [unique_player_id, name, curbid_or_finalsoldprice, position, rating]
                # [unique_player_id, name, curbid_or_finalsoldprice, position, rating, nation, league, team]

                player_id = eventData[0]
                player_name = eventData[1]
                position = eventData[3]
                rating = int(eventData[4])
                player_id = eventData[0]
                player_name = player_name
                rating = rating
                position = position
                action = "SOLD"
                location = "transfer list"
                rating = int(rating)
                player_nation = eventData[5]
                player_league = eventData[6]
                player_team = eventData[7]

                # UNIQUES
                sold_price_won = eventData[2]
                sold_action = 1

            elif event_action == "RELIST":
                # eventData = [unique_player_id, name, relist_price, position, rating]
                # eventData = [unique_player_id, name, relist_price, position, rating, nation, league, team]

                player_id = eventData[0]
                player_name = eventData[1]
                position = eventData[3]
                rating = int(eventData[4])
                player_id = eventData[0]
                player_name = player_name
                rating = rating
                position = position
                action = "RELIST"
                location = "transfer list"

                player_nation = eventData[5]
                player_league = eventData[6]
                player_team = eventData[7]
                
                # UNIQUES 
                relist_price = eventData[2]
                relist_action = 1

            elif event_action == "LIST":
                # eventData = [pid, boughtprice, playerPrice, playerName, playerNation, playerLeague, playerTeam]
                # [pid, boughtprice, playerPrice, playerName, playerNation, playerLeague, playerTeam, rating, position]
                player_id = eventData[0]
                player_name, rating, position, price = self.getPlayerInfoFromID(eventData[0])

                rating = eventData[7]
                position = eventData[8]
                
                player_id = eventData[0]
                player_name = eventData[3] # player_name
                rating = int(rating)
                # position = position
                action = "LIST"
                location = "watchlist"

                player_nation = eventData[4]
                player_league = eventData[5]
                player_team = eventData[6]

                # UNIQUES
                boughtprice = eventData[1]
                list_price = eventData[2]
                list_action = 1

            elif event_action == "BIDROUNDOVER":
                time_elapsed = eventData[1]
                won = eventData[3]
                lost = eventData[4]
                bids = eventData[5]
                requests = eventData[6]
                margin = eventData[7]
                sold = eventData[8]
                relisted = eventData[9]
                profit = eventData[10]
                profit_per_player = eventData[11]
                action = "SUMMARY"
                location = "SUMMARY"

            elif event_action == "STOPPED":
                # ["00000000000000", 0, 0, "error", "error", LOCATION]
                reason = eventData[5]
                action = "STOPPED"
                location = str(reason)
                player_id = ""


            if (event_action != "BIDROUNDOVER"):
                if (event_action != "SOFTBAN"):
                    if (event_action != "STOPPED"):
                        # convert player id to int
                        try:
                            pid = str(player_id)
                            unique_id = player_name + "_" + str(rating) + "_" + str(position) + "_" + pid
                            player_id = int(player_id)
                        except:
                            print("casting player ID to int didn't work")
    
            new_datetime = date2 + " " + time
            
            final = [date2,time,new_datetime,coins,player_id,player_name,unique_id,rating,position,player_nation,player_league,player_team,action,location,bid_action, sold_action, relist_action, list_action, lost_action, curbid,bid_made,sell_price,sell_price_minus_tax,est_profit,sold_price_won,relist_price,boughtprice,list_price,sold_price_outbid,time_elapsed,won,lost,bids,requests,margin,sold,relisted,profit,profit_per_player,url]

            with open(r'./data/logs.csv', 'a', encoding="utf8") as f:
                writer = csv.writer(f)
                writer.writerow(final)
        
            if self.PUSH_TO_GOOGLE:
                self.pushGoogle(final)


    # never got this working, and is probably what got me banned ha
    def fixSoftban(self):
        windows_open = self.driver.window_handles

        for x in windows_open:
            self.log_event2(x)

        print(len(windows_open))

        # open 3 windows with url
        # url = "https://www.ea.com/fifa/ultimate-team/web-app/"
        # self.driver.execute_script("window.open('');")
        # self.driver.switch_to.window(self.driver.window_handles[1])
        # self.driver.get(url)
        self.openNewWebapp()
        self.openNewWebapp()
        self.openNewWebapp()

        # self.driver.close()

        # switch to original broken tab
        sleep(5)
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.driver.close()

        # for x in range(self.current_tab_num)
        # cur window is now web app 1 of 3

        # 1st webapp tab opened normally
        # switched to 2nd webapp, without logign in it said we're having errors, I clicked ok
        # switched to 3rd webapp, it logged in but immediately said can't authenticate 
        # (all of this while intiial web app is open)

    def openNewWebapp(self):

        url = "https://www.ea.com/fifa/ultimate-team/web-app/"
        self.driver.execute_script("window.open('');")

        num_current_tabs = len(self.driver.window_handles)
        this_tab_just_opened = num_current_tabs - 1

        self.driver.switch_to.window(self.driver.window_handles[this_tab_just_opened])
        self.driver.get(url)

        self.current_tab_viewing = self.driver.window_handles[this_tab_just_opened]
        self.current_tab_num = this_tab_just_opened
        print("tab cur on: " + str(self.current_tab_num))

    def pushGoogle(self, row):
        # check if we have a single log, or multiple logs
        check = isinstance(row[0], list)

        if check == False: # this should mean that the first element, ie Date stamp, is NOT a list, so it is one row we are sending to gsheets
            try:

                self.sheet_instance.append_row(row, value_input_option="USER_ENTERED")
                
            except Exception as e:
                print("Google logs error: ")
                print(e)
                print("should run unfction reauthorize google here, and then reattempt append row")
                self.reAuthorizeGoogle()
                self.sheet_instance.append_row(row)
        # sending multiple rows
        else:
            try:

                self.sheet_instance.append_rows(row, value_input_option="USER_ENTERED")
                
            except Exception as e:
                print("Google logs error APPEND MULTIPLE ROWS: ")
                print(e)
                print("should run unfction reauthorize google here, and then reattempt append row")
                self.reAuthorizeGoogle()
                self.sheet_instance.append_rows(row)
            
    def reAuthorizeGoogle(self):
        # define the scope
        self.scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

        # add credentials to the account
        self.creds = ServiceAccountCredentials.from_json_keyfile_name('./data/fifa-autobidder-229964592212.json', self.scope)

        # authorize the clientsheet 
        self.client = gspread.authorize(self.creds)

        # get the instance of the Spreadsheet
        self.sheet = self.client.open('autobidder')

        # get the first sheet of the Spreadsheet
        self.sheet_instance = self.sheet.get_worksheet(0)
        


def log_event(queue, event, msg_type=""):
    """
    Sends log to queue, which GUI handles and writes to txt file for display on GUI.
    The queue objects allows us to talk to the GUI from a separate threads, which is cool.
    This was a big breakthrough in functionality.

    Parameters:
        queue (queue): GUI's queue object
        event (str): Event log to write to data/gui_logs.txt
    """
    event = str(event)

    combined = [event, msg_type]
    queue.put(combined)

def wait_for_shield_invisibility(driver, duration=0.25):
    """
    Detects loading circle and waits for it to dissappear. 
    """
    WebDriverWait(driver, 30).until(
        EC.invisibility_of_element_located(
            (By.CLASS_NAME, 'ut-click-shield showing interaction'))
    )
    sleep(.1)

def wait_for_player_shield_invisibility(driver, duration=0.25):
    """
    Detects loading circle and waits for it to dissappear. 
    """
    WebDriverWait(driver, 30).until(
        EC.invisibility_of_element_located(
            (By.XPATH, '/html/body/main/section/section/div[2]/div/div/section/div/div/div[1]/div/div[2]/div/div/div[24]/div/div[1]'))
    )

    # print("PIZZA")
    sleep(.1)

def login(queue, driver, user, email_credentials):
    try:
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
        driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/section/div[1]/form/div[6]/a').click()
        sleep(3)

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div/form/div/section/a[2]'))
        ).click()

        access_code = get_access_code(queue, email_credentials)

        driver.find_element(By.XPATH, '/html/body/div[1]/form/div/section/div[2]/div/input').send_keys(access_code)
        sleep(1)
        driver.find_element(By.ID, 'btnSubmit').click()

        log_event(queue, "Logged in successfully!")
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'icon-transfer'))
        )
        sleep(2)
    except:
        log_event(queue, "Login error - check config.ini or network connection")

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
