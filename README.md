# TMB's FIFA 22 Autobidder

Mac             |  Windows
:-------------------------:|:-------------------------:
![](./demos/gui_mac_v23.PNG)  |  ![](./demos/gui_windows_v23.PNG)

[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/hwKYU734tY)

_Note 1: I built this for me and my friends as a fun side project. I'm making it open source because it's awesome, and paid bots are sus. It is not perfect and use it at your own risk. This is/was my first project working with [Tkinter](https://wiki.python.org/moin/TkInter) as well as [Selenium WebDriver](https://www.selenium.dev/documentation/en/), a library that interacts with [ChromeDriver](https://www.chromium.org/)._

_Note 2: (1/26/22) This is an entirely new version that works really well -- don't make more than 1000 bids in a day (or 2000 lol). Remember that in using this you are taking a risk and CAN get banned. The stats in config.ini are my last resting stats and [see here](https://docs.google.com/spreadsheets/d/15PRwG_wVajMtrCvhV2PRkPFTdEkvgdzcOdb_XwKUxxA/edit#gid=0) for my logs down to the minute and second!_

_Note 3: (1/27/22) The below readme has been semi-updated for the new bot, but not entirely. I created a [Discord](https://discord.gg/hwKYU734tY) for troubleshooting since this is an entirely new release and I will finish the Readme later, also I might make a Youtube video explaining it_

## Intro

This project is an Autobidder trading bot that buys and sells players on the FUT (FIFA 22 Ultimate Team) Transfer Market.

## Overview & Features

Bidding war             |  Autolisting
:-------------------------:|:-------------------------:
![](./demos/bidwar1_lowframerate.gif)  |  ![](./demos/transferlisting1.gif)


Built in Python, this bot uses [Selenium](https://www.selenium.dev/documentation/en/) to interact with FUT Webapp via [ChromeDriver](https://www.chromium.org/) and features a [Tkinter](https://wiki.python.org/moin/TkInter) User Interface for easy operation.

Unlike the more common and widely known botting methods, such as [Autobuyers or snipers](https://github.com/chithakumar13/Fifa21-AutoBuyer) that rely on speed and luck (and custom JS injection), Autobidding relies on lower margins at higher volumes (around 100 - 200 coins per card). This makes Autobidding not only more lucrative long term, but also more consistent, and in my opinion, safer. It is also more fun to watch compared to card sniping.

Advantages:

- Consistent profits
  - Does not rely on luck, more importantly not competing with other bots (think of how many bots just searched for Ronaldo as you read this)
- Efficiency
  - Guaranteed profits since supply of undervalued auctions is infinitely greater than snipes
- Security / Detectability
  - Selenium's Javascript injection is the only indication of something 'off' - and Selenium in itself is harmless and no different than a typical browser extension's JS, like an Adblocker

Instead of specific players, it takes in a generic filter for gold nonrares. I found CM's from top nations to be most effective. For example search all gold non rare RWs on Futbin, copy the link and update line 111 in autobidder.py (see the furthest right column in my [Google Sheets logs](https://docs.google.com/spreadsheets/d/15PRwG_wVajMtrCvhV2PRkPFTdEkvgdzcOdb_XwKUxxA/edit#gid=0) to see what URL I was using at different times).

Go to "Search the Transfer Market" page, enter gold, non rare, position CM, on the webapp (you must manually enter the filters, this is a free bot so don't complain lol), 9900 min bin and 10k max bin, then click start bot (do not click the search button). The bot will click the search button for you, and depending on how many cycles you select, will run on autopilot. A cycle is defined as 50 bids (when the watchlist is full). You want to have a conversion rate around 50%, at 100-150 margin that is 25 players * ~125 profit each, totalling ~3200 coins every 20 mins, or abuot 10k an hour at the absolute minimum. Some days I would find a filter list and make 30k an hour, it's fun.

Some GUI buttons were never implemented, such as the position filter change which would've just edited a futbin url substring. 

## Installation

First ensure Python 3.x is installed on your machine. See *Troublehoosting* below for help, but to be honest if you are entirely new to Python I don't think you should be running random Github projects on your machine just yet!

Then download the latest release of Chromedriver for your system [here](https://chromedriver.chromium.org/downloads). Replace the chromedriver in either the *chrome_windows* or *chrome_mac* with your download depending on your machine.

Navigate to the project's root directory via Terminal or Command Prompt, in this example it is on my Desktop.

Terminal (Mac):

```
cd ~/Desktop/Fifa21-Autobidder
```

Command Prompt (Windows):
```
cd Desktop/Fifa21-Autobidder
```

Then run the following to install Selenium and any other requirements (see [requirements.txt](./requirements.txt)): 

```
pip install -r requirements.txt
```

Make sure pip is installed ([see here](https://pip.pypa.io/en/stable/installing/)). 

If there are any errors, such as 'missing xyz module', simply ```pip install [xyz]```. Feel free to post an issue on this Repository.

For any other errors, it is likely your system's Python interpreter which can be a huge headache. See *troubleshooting* below.

## Running

Navigate to the project's directory via command prompt / terminal described above and:

**Linux/Mac systems**

In Terminal, run:

```
make run
```

See [troubleshooting] for help.

**Windows**

Run:

```
python src/main.py
```


## Configuration

Everything is configured via the user interface.

The bot uses Xbox prices, to switch the pricing fetcher see function enable_xbox_prices() in autobidder.py change "li[2]" on [this line](https://github.com/tmb5cg/Fifa21-Autobidder/blob/e43ccd3de0e7833304d7f396bfd8bd062c3b1c8d/src/autobidder.py#L851):
  - li[1] is Playstation
  - li[2] is Xbox
  - li[3] is PC


Line 111 in autobidder.py is where the Futbin URL is updated. I intended to have config.ini control this, and push it to the UI, but config.ini is constantly refreshing and only will update on a new instance of the bot. Join the Discord if this is confusing. 

### Automatic login

Mac             |  Windows
:-------------------------:|:-------------------------:
![](./demos/maclogin_compressed.gif)  |  ![](to do)

If you would like to automatically login, ensure that your credentials are entered in [config.ini](config.ini).

Auto login is not required, it is just convenient. If you can't read/understand most or all of my code you probably shouldn't use auto-login (it is safe, but rule of thumb be cautious on the internet). Login manually and the Start Bot button will function as normal.

Email credentials are used to fetch the authorization code which requires a bit more work and honestly is needlessly dangerous, you need to enable third party app access on your Gmail which in hindsight just login manually. But if you are curious, (see **[here](https://support.google.com/accounts/answer/3466521?hl=en_)**). I'd recommend creating a new separate Gmail account that gets auto-forwarded your EA security code, that way you are not exposing your actual email (I did this because I almost pushed this new bot to Github with my actual email's credentials, which freaked me out).


## Troubleshooting

### Python

Python3 or greater is required to run the program. The most likely cause for errors is having an outdated Python version installed. To see your version of Python:

##### Mac

Open Terminal and type:

```
python --version
```

##### Windows

Open Command Prompt and type:

```
python --version
```

If you see Python 2.x, see [here](https://docs.python-guide.org/starting/install3/osx/) for installing Python 3.

If you know you have Python 3 installed, but see 2.x, your system's Python PATH must be assigned to Python 3.x. To do this, see [here](https://dev.to/malwarebo/how-to-set-python3-as-a-default-python-version-on-mac-4jjf) for Mac and [here](https://stackoverflow.com/questions/3701646/how-to-add-to-the-pythonpath-in-windows-so-it-finds-my-modules-packages) for Windows.

You might need to add the PYTHONPATH variable with the value of the code directory - [check this link](https://stackoverflow.com/questions/3701646/how-to-add-to-the-pythonpath-in-windows-so-it-finds-my-modules-packages).


I suspect this will cause the biggest number of issues.

### Chomedriver

If the bot is correctly starting, and you are sure Python is not the issue, then Chromedriver is the issue. The Chromedriver files ([chrome_windows](./chrome_windows) and [chrome_mac](./chrome_mac)) are the versions used by my system. 

In order for Chromedriver to work, it must match your systems version of Chrome. This can easily be fixed by redownloading Chromedriver.

Go [here](https://chromedriver.chromium.org/downloads) and download the latest release. Replace the chromedriver in either the *chrome_windows* or *chrome_mac* with your download.


