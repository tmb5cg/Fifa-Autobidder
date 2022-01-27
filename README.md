# TMB's FIFA 22 Autobidder

Mac             |  Windows
:-------------------------:|:-------------------------:
![](./demos/gui_mac_v23.PNG)  |  ![](./demos/gui_windows_v23.PNG)


_Note 1: I built this for me and my friends as a fun side project. I'm making it open source because it's awesome. It is not perfect and use it at your own risk. This is/was my first project working with [Tkinter](https://wiki.python.org/moin/TkInter) as well as [Selenium WebDriver](https://www.selenium.dev/documentation/en/), a library that interacts with [ChromeDriver](https://www.chromium.org/)._

_Note 2: This new bot actually works really well -- don't make more than 1000 bids in a day (or 2000). I encourage everyone to tackle a project like this. The stats in config.ini are my last resting stats and [see here](https://docs.google.com/spreadsheets/d/15PRwG_wVajMtrCvhV2PRkPFTdEkvgdzcOdb_XwKUxxA/edit#gid=0) for my logs!_

_Note 3: The below readme has been semi-updated for the new bot, but not entirely. I created a Discord for troubleshooting since this is an entirely new release and I don't have time to update this readme: [Discord](https://discord.gg/hwKYU734tY). For example I don't have any GIFs at the moment, if anyone wants to create any and send them in the Discord please do!_

## Intro

This project is an Autobidder trading bot that buys and sells players on the FUT (FIFA 22 Ultimate Team) Transfer Market.

Unlike the more common and widely known botting methods, such as [Autobuyers or snipers](https://github.com/chithakumar13/Fifa21-AutoBuyer) that rely on speed and luck, Autobidding relies on lower margins at higher volumes (around 100 - 200 coins per card). This makes Autobidding not only more lucrative long term, but also more consistent, and in my opinion, safer.

## Overview & Features

Bidding war             |  Autolisting
:-------------------------:|:-------------------------:
![](./demos/bidwar1_lowframerate.gif)  |  ![](./demos/transferlisting1.gif)

Built in Python, this bot uses [Selenium](https://www.selenium.dev/documentation/en/) to interact with FUT Webapp via [ChromeDriver](https://www.chromium.org/) and features a [Tkinter](https://wiki.python.org/moin/TkInter) User Interface for easy operation.

Unlike other bots, its operations can be monitored in real time, and appears identical to a human's actions. I would argue it is safer than other Javascript injection bots, since the only Javascript injected to my knowledge is Selenium. Chromedriver flags have also been obfuscated, although the scale of EA's bot detection seems tiny so this is done out of an abundance of caution.

Instead of specific players, it takes in a generic filter for gold nonrares. I found CM's from top nations to be most effective. For example search all gold non rare RWs on Futbin, copy the link and insert into config.ini before running the bot.

Enter gold non rare RWs on the webapp (you must manually enter the filters, this is a free bot so don't complain lol), 9900 min bin and 10k max bin, then click start bot. The bot will click the search button for you, and depending on how many cycles you select, will run on autopilot. A cycle is defined as 50 bids (when the watchlist is full). You want to have a conversion rate around 50%, at 100-150 margin that is 25 players * ~125 profit each, totalling ~3200 coins every 20 mins, or abuot 10k an hour at the absolute minimum. Some days I would find a filter list and make 30k an hour, it's fun.

Some GUI buttons were never implemented, such as the position filter change which would've just edited a futbin url substring.

Leave a comment if you get it working, unfortunately I can't test it and I never really intended on releasing this one but have fun. I had it logging actions to Google sheets and just removed my keys, all the code is untouched so I imagine you'll have a couple simple errors to fix before getting it working. If you get it running, trust me this one works. Best margin is 100 to 200 depending on time of day, you'll slowly learn trends as you run it.

The below is semi-outdated and from my FIFA 21 bot. This new release works entirely differently but the installation steps and troubleshooting are still relevant:

Advantages:

- Consistent profits
  - Does not rely on luck, more importantly not competing with other bots (think of how many bots just searched for Ronaldo as you read this)
- Efficiency
  - Guaranteed profits since supply of undervalued auctions is infinitely greater than snipes
- Security / Detectability
  - Selenium's Javascript injection is the only indication of something 'off' - thankfully Selenium in itself is harmless, and no different than an Adblocker's injected Javascript

Initial bids will reap low profit, but once you fight off other bidders, you have the player cornered. You will start winning players for 350 that you can sell for 800. These margins at high volumes reap ~30k coins an hour.

## Installation

First ensure Python 3.x is installed on your machine. See *Troublehoosting* below for help, but to be honest if you are entirely new to Python I don't think you should be running random Github projects on your machine just yet!

Then download the latest release of Chromedriver for your system [here](https://chromedriver.chromium.org/downloads). Replace the chromedriver in either the *chrome_windows* or *chrome_mac* with your download.

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

I suspect this will cause the biggest number of issues.

### Chomedriver

If the bot is correctly starting, and you are sure Python is not the issue, then Chromedriver is the issue. The Chromedriver files ([chrome_windows](./chrome_windows) and [chrome_mac](./chrome_mac)) are the versions used by my system. 

In order for Chromedriver to work, it must match your systems version of Chrome. This can easily be fixed by redownloading Chromedriver.

Go [here](https://chromedriver.chromium.org/downloads) and download the latest release. Replace the chromedriver in either the *chrome_windows* or *chrome_mac* with your download.

## Configuration

Everything is configured via the user interface.

To add a player, retrieve their Futbin (insert link) URL and click Add Player. The bot will automatically open the Futbin link and retrieve the data. 

### Automatic login

Mac             |  Windows
:-------------------------:|:-------------------------:
![](./demos/maclogin_compressed.gif)  |  ![](to do)

If you would like to automatically login, ensure that your credentials are entered in [config.ini](config.ini).

Auto login is not required, it is just convenient. If you can't read/understand most or all of my code you probably shouldn't use it (it is safe, but rule of thumb never trust anyone on the internet)


Email credentials are used to fetch the authorization code which requires a bit more work and honestly is needlessly dangerous, you need to enable third party apps (see **[here](https://support.google.com/accounts/answer/3466521?hl=en_)**). I'd recommend creating a new separate Gmail account that gets auto-forwarded your EA security code, that way you are not exposing your actual email.


## Running

**Linux/Mac systems**

In Terminal, run:

```
make run
```

See [troubleshooting] for help.

**Windows**

Set the PYTHONPATH variable with the value of the code directory - [check this link](https://stackoverflow.com/questions/3701646/how-to-add-to-the-pythonpath-in-windows-so-it-finds-my-modules-packages).

Run:

```
python src\main.py
```

