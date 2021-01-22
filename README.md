# FIFA 21 Web App Autobidder & Autobuyer
 

## Intro

AFAIK, only Autobidder and Autobuyer combo that works on Windows, Mac, Linux, & anything that can run Python (ignoring the fancy new JS extension autobuyers kids get these days)

I decided to release the code to this project since I am too busy with actual work. I made a million coins using this sparingly and want to revive my energy to fix it, so please reach out. I think the Autobuyer is half working right now, I spent all my dev time on the autobidder for some reason. Lots and lots of feature ideas, but few have been implemented. Beautifying the code, rewriting and reorganizing file structure took up the bulk of the time as I hoped to eventually create a perfect Autobuyer.

If anyone sees this, feel free to reach out with issues or suggestions. This is my first read me and is incredibly unhelpful, in fact I'm assuming anyone using this has a programming background. In the future, I will create a hold-your-hand guide if people want but yea feel free to work on my project, would love to collaborate with someone too. 

## Why it's superior
I'm not an expert, but I consider it to be the safest botting experience because you watch the bot perform actions, as opposed to most bots that work behind the scenes via HTTP requests or JS injection (which this is, but Selenium scripts, not custom like chithak's). I used this for the past couple months and had 0 issues, but using common sense goes without saying. If you start getting more and more captcha's, take a break. Even non cheaters get banned for failing captcha's and trying to snipe players, so why not use a bot if you're not safe either way, right?

Security measures:
- **Flags removed**: *"Chromedriver flags hidden"*
- **Chromedriver build variables renamed**: *"Can't remember what this does, but it hides Selenium from commercial bot checkers apparently"*
- **Not headless**: *"EA checks if browser is headless, this bot runs in front of you (makes debugging easy, but EA's web app is so unstable it's impossible to account for random glitches"*
- **Browser resolution**: *"Similar to the above, basically all the things sent back to host (EA) about your browser window size, screen resolution, etc. are 100% legitimate, because well, they are legitimate. You watch the bot run in your browser"*
- **Overkill pauses / pause durations between actions**: *"Self explanatory, lots of sleep() between actions"*



## Installation

```
pip install -r requirements.txt
```

Download chromedriver from Google, for some reason it doesn't download from Github well. Make sure to put it in the host folder.

## Test

Hopefully you understand my code because this readme isn't helpful at all


Currently it works on Linux, Mac and Windows systems with Chrome version >=86.
