# FIFA 21 Web App Autobidder & Autobuyer
 

## Intro

FIFA 21 web app autobuyer/autobidder built with a GUI. I decided to release the code to this project since I am too busy with actual work. I made a million coins using this sparingly and want to revive my energy to fix it, so if you find this helpful please add to the code via GitHub. I spent all my dev time on the autobidder for some reason, in its current state. There is a lot of unused autobuyer code and general methods. Beautifying the code, rewriting and reorganizing file structure took up the bulk of the time as I hoped to eventually create a perfect Autobuyer. 

If anyone sees this, feel free to reach out with issues or suggestions. This is my first read me and is probably incredibly unhelpful, in fact I'm assuming anyone using this has a programming background. In the future, I will create a hold-your-hand guide if people want but yea feel free to work on my project, would love to collaborate with someone too. 

## General Structure

Main.py --> Tkinter GUI with buttons and actions, each button passes action to Thread Runner 
ThreadRunner --> creates separate threads for actions so GUI is interactable, also makes debugging easy (click reload functions button to edit code without restarting webdriver). Calls function runner
FunctionRunner --> Creates autobuyer object and calls methods

There is a Bid Using Any tool that pulls prices data from futbin, I tested it a little bit but never had time to make perfect. It works decently well, and I think has potential. Opens a new tab to aggregate all Futbin price data at once so Futbin doesn't block your IP

## Notes
I used this for the past couple months and had 0 issues, but using common sense goes without saying. If you start getting more and more captcha's, take a break.

Security measures:
- **Chromedriver flags removed**
- **Chromedriver build variables renamed**: 
- **Doesn't run headless, has actual window size / resolution etc sent back to EA (if they even check that)
- **Lots of sleep / pause durations between actions**: 



## Installation

```
pip install -r requirements.txt
```

Download chromedriver from Google, for some reason it doesn't download from Github well. Make sure to put it in the host folder. I have never really used GitHub so I'm not sure how to create an accurate requirements.txt

## Test

Hopefully you understand my code because this readme isn't helpful at all
