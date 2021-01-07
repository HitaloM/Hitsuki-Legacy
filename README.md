# Haruka Aya

![](images/haruka_banner.png)

HarukaAya is an open source Telegram group manager bot, this is a modular based 
Telegram Python Bot running on Python3 with sqlalchmey database.

This bot can be found and used on telegram as [Haruka Aya](https://t.me/HarukaAyaBot).
 
## Useful links
  - Help localize the bot with [Crowdin](https://crowdin.com/project/haruka)
  - [Haruka Aya Support](https://t.me/HarukaAyaGroup)
  - [Haruka Aya's News](https://t.me/HarukaAya)
  - [Intellivoid](https://t.me/Intellivoid)
  - [Intellivoid Discussions](https://t.me/IntellivoidDiscussions)
  - [Intellivoid Community](https://t.me/IntellivoidCommunity)

If you want to join our group chats, **we advise that you read the rules carefully**
before participating in them.


-------------------------------------------------------------------------------------


## Installation

First what you want to do is prepare the configuration file for Haruka Aya, copy
[sample_config.yml](sample_config.yml) to [config.yml](config.yml) and begin to
fill out all the required information

| Name                     | Required | Description                                                                                                                                         |
|--------------------------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| is_example_config_or_not | Yes      | You need to change the value of this property to `not_sample_anymore` to verify that the configuration file you are running is indeed not a sample. |
| bot_token                | Yes      | Your bot API token that you obtain from BotFather                                                                                                   |
| api_key                  | Yes      | Your Telegram API Key                                                                                                                               |
| api_hash                 | Yes      | Your Telegram API Hash                                                                                                                              |
| owner_username           | Yes      | The username of the owner of this bot (Without the leading @)                                                                                       |
| message_dump             | Yes      | ???                                                                                                                                                 |
| load                     | No       | ???                                                                                                                                                 |
| no_load                  | No       | ???                                                                                                                                                 |
| strict_antispam          | No       | ???                                                                                                                                                 |
| workers                  | No       | ???                                                                                                                                                 |
| del_cmds                 | No       | ???                                                                                                                                                 |
| sw_api                   | No       | The API Token for SpamWatch                                                                                                                         |
| database_url             | Yes      | The URL for the Postgres Database, required for the bot to store and retrieve data                                                                  |
| sudo_users               | No       | A list of users that have sudo permissions to this bot (User IDs)                                                                                   |
| whitelist_users          | No       | ???                                                                                                                                                 |

#### How can I obtain `bot_token`?

Just talk to [BotFather](https://t.me/BotFather) (described [here](https://core.telegram.org/bots#6-botfather))
and follow a few simple steps. Once you've created a bot and received your
authorization token, that's it! that's your `bot_token`.

#### How can I obtain a `api_key` and `api_hash`?

In order to obtain an API key and hash you need to do the following:

 - Sign up for Telegram using any application.
 - Login to your Telegram core: [https://my.telegram.org](https://my.telegram.org).
 - Go to '[API Development tools](https://my.telegram.org/apps)' and fill out the form.
 - You will get basic addresses as well as the `api_id` and `api_hash` parameters 
   required for Haruka's configuration file.

### Requirements

 - PostgreSQL
 - Docker (*optional*)
 - Python3.6

### Docker 

Run with docker! you can a local instance of haruka from the production branch
using the [Dockerfile](Dockerfile)

```shell
docker build -t="haruka" -f Dockerfile .
docker run -t --name haruka --restart always haruka
```

### From source

```shell
pip install -r requirements.txt
python -m haruka
```

-------------------------------------------------------------------------------------

## Branch purposes

HarukaAya will have multiple branches for different purposes, these are the
main branches you should understand before contributing to this project.

 - `production` This is the production branch that the server (or Dockerfile)
    will pull from and run Haruka Aya. This is the most stable branch, and it's
    ready for production. **We do not push experimental or patches to this branch
    until we can confirm that it's stable for production**
 
 - `master` This is the next thing to production in terms of stable, here this is
    where all new changes are pushed before they are merged into the production
    branch. This is like the testing branch where we would run in test
    environment to double check before pushing to production. Everything pushed to
    this branch must be stable and finished.
   
Any other branches should be treated as work in progress features that is currently
being worked on to release to production.

## Contributing to the project
 - You must sign off on your commit.
 - You must sign the commit via GPG Key.
 - Make sure your PR passes all CI.

## Thanks to
 - RealAkito - Original Haruka Aya Owner
 - [Davide](https://t.me/DavideGalileiPortfolio) - For designing and creating Haruka Aya's display picture and banner
 - zakaryan2004 - For helping out a lot with this project.
 - MrYacha - For Yana :3
 - Skittle - For memes and sticker stuff.
 - 1mavarick1 - Introducing Global Mutes, etc.
 - AyraHikari - Reworked Welcome, Fed v2
 - Paul Larsen - Marie and Rose creator

And much more that we couldn't list it here!