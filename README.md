# TMB's Sniping BOT - FIFA 21 Autobuyer + Autobidder


## How it works

![](./readme/windows_gui.png)

The only all-in-one Autobuyer and Autobidder that works on Mac, Windows, and Linux.

Originally built for me and my friends as a fun side project, I'm making it open source since I am not actively updating it. This is my first experience with tkinter (for GUI) as well as Selenium WebDriver, which is a library that can interact with any site.

Check out our Discord here: 

This bot is built entirely in Python and features a User Interface for easy operation.
Built in Python, this bot uses Selenium to interact with FIFA 21 Webapp. Unlike other bots, its actions can be monitored by the user. It is also safer than other Javascript injection bots, as the only Javascript injected is Selenium's, rendering EA's bot detection useless. 

Features:
- Dynamic GUI displays logs and stats in real time from autobidder and autobuyer methods.
- All methods are threaded separately, so GUI is always active


[insert gif of autobidding]

Initial bids will reap low profit, but once you fight off other bidders, you have the player cornered. You will start winning players for 350 that you can sell for 800. These margins at high volumes reap ~30k coins an hour.


Project Structure
-Main.py is gui tkinter, creates selenium driver
-on button click, calls thread runner which creates autobidder. driver is passed along
- autobidder creates helper



Bot uses selenium framework to run fut web app. This is the best way to not get banned, because it is very similar to a normal user activity.

First step is logging in. You can do it manually or automatically.
If automatically - Bot have access to your email inbox, so it can read the newest ea message with an access code.
After running the web app, your filters are used to find a player (name and max price). 

The min price is increased before every search to have the results refreshed every time. 
By default bot clicks **+** button of min price 20 times, and starts again from 0.
You can change the number of increases using `INCREASE_COUNT` variable in the `config.py` file.

When the player is found, bot buys him, but sometimes it's too late. The result appears in the console:
- **Success**: *"Success! You bought player_name for X coins."*
- **Failed**: *"Found something, but it was too late."*

The bot stops working when you have no more money, or after 5 bought players (because you have to assign them, the feature is not done yet).

The current status is described in the console logs, so you have real-time access to information about the activities performed.

## Installation

```
pip install -r requirements.txt
```

## Configuration

Everything is configured using `config.py` file.

Enter the name of the player name and the maximum number of coins you want to spend for him.
Example:

```
PLAYER = {
    "name": "Sterling",
    "cost": 100000,
}
```

### Automatic login

If you want to automatically login to web app, change this variable to False:

```
LOGIN_MANUALLY = False
```

Provide your credentials:

```
USER = {
    "email": "your_email@example.com",
    "password": "your_password",
}
```

You have to also provide your email credentials. It's needed to check the access code sent to your email address. 
**Remember to allow external tools in your mail configuration.**

```
EMAIL_CREDENTIALS = {
    "email": "your_email@example.com",
    "password": "your_password",
}
```

## Running

**Linux/Mac systems**

Run:

```
make run
```

**Windows**

Set the PYTHONPATH variable with the value of the code directory - [check this link](https://stackoverflow.com/questions/3701646/how-to-add-to-the-pythonpath-in-windows-so-it-finds-my-modules-packages).

Run:

```
python src\main.py
```


## Info

Currently it works on Linux, Mac and Windows systems with Chrome version >=86.

It's just first version of fut web app bot. The project will be further developed and new features will appear.
 
Good luck!

