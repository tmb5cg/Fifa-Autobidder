import src.helpers
import src.mainhelpers
import src.autobidder_list
import src.autobidder_any

from src.autobidder_list import AutobidderPlayerlist
from src.autobidder_any import AutobidderAny
from src.config import USER

from src.helpers import *
from src.mainhelpers import *


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
