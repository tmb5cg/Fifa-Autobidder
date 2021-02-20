import helpers
import mainhelpers
import autobidder_any

from autobidder_any import AutobidderAny
from config import USER

from helpers import *
from mainhelpers import *


class RunFunction:
    def __init__(self, driver, searchdata):
        self.driver = driver
        self.playerdata = searchdata

    def test(self):
        autobidder = AutobidderAny(self.driver, self.playerdata)
        #autobidder.manageTransferlist(playerdata)
        autobidder.testfunc()

    def login(self):
        login(self.driver, USER)


    def bidAnyone(self, method):
        autobidder = AutobidderAny(self.driver, self.playerdata)
        # Methods = GUIfilters, playerlist
        autobidder.run(method)

    def getFutbinInfo(self):
        getFutbinDataAndPopulateTable(self.driver, self.playerdata)
