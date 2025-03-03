### A "simple" python application that uses Selenium to help with your M$ Rewards

![Static Badge](https://img.shields.io/badge/Made_in-python-violet?style=for-the-badge)
![MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge)
![GitHub contributors](https://img.shields.io/github/contributors/klept0/MS-Rewards-Farmer?style=for-the-badge)
![GitHub issues](https://img.shields.io/github/issues/klept0/MS-Rewards-Farmer?style=for-the-badge)



> [!IMPORTANT]
> If you are multi-accounting and abusing the service for which this is intended - **_DO NOT COMPLAIN ABOUT BANS!!!_**



> [!CAUTION]
> Use it at your own risk, M$ may ban your account (and I would not be responsible for it)
>
> Do not run more than one account at a time.
>
> Do not use more than one phone number per 5 accounts.
>
> Do not redeem more than one reward per day.

#### Group Chat - [Telegram](https://t.me/klept0_MS_Rewards_Farmer/) (pay attention to captchas - helps prevent spam)

#### Original bot by [@charlesbel](https://github.com/charlesbel) - refactored/updated/maintained by [@klept0](https://github.com/klept0) and a community of volunteers.

#### PULL REQUESTS ARE WELCOME AND APPRECIATED!

## Installation

1. Install requirements with the following command :

   `pip install -r requirements.txt`

   Upgrade all required with the following command:
   `pip install --upgrade -r requirements.txt`

2. Make sure you have Chrome installed

3. (Windows Only) Make sure Visual C++ redistributable DLLs are installed

   If they're not, install the current "vc_redist.exe" from
   this [link](https://learn.microsoft.com/en-GB/cpp/windows/latest-supported-vc-redist?view=msvc-170) and reboot your
   computer

4. Edit the `accounts.json.sample` with your accounts credentials and rename it by removing `.sample` at the end.

   The "totp" field is not mandatory, only enter your TOTP key if you use it for 2FA (if ommitting, don't keep
   it as an empty string, remove the line completely).

   The "proxy" field is not mandatory, you can omit it if you don't want to use proxy (don't keep it as an empty string,
   remove the line completely).

    - If you want to add more than one account, the syntax is the following:

   ```json
   [
    {
        "username": "Your Email 1",
        "password": "Your Password 1",
        "totp": "0123 4567 89ab cdef",
        "proxy": "http://user:pass@host1:port"
    },
    {
        "username": "Your Email 2",
        "password": "Your Password 2",
        "totp": "0123 4567 89ab cdef",
        "proxy": "http://user:pass@host2:port"
    }
   ]
   ```

5. Run the script:

   `python main.py`

6. (Windows Only) You can set up automatic execution by generating a Task Scheduler XML file.

   If you are a Windows user, run the `generate_task_xml.py` script to create a `.xml` file. After generating the file, import it into Task Scheduler to schedule automatic execution of the script. This will allow the script to run at the specified time without manual intervention. 

   To import the XML file into Task Scheduler, see [this guide](https://superuser.com/a/485565/709704).


## Launch arguments

- `-v/--visible` to disable headless
- `-l/--lang` to force a language (ex: en)
- `-g/--geo` to force a searching geolocation (ex: US)
  `https://trends.google.com/trends/ for proper geolocation abbreviation for your choice. These MUST be uppercase!!!`
- `-p/--proxy` to add a proxy to the whole program, supports http/https/socks4/socks5 (overrides per-account proxy in
  accounts.json)
  `(ex: http://user:pass@host:port)`
- `-cv/--chromeversion` to use a specific version of chrome
  `(ex: 118)`
- `-da/--disable-apprise` disables Apprise notifications for the session, overriding [config.yaml](config.yaml).
  Useful when running manually as opposed to on a schedule.
- `-t/--searchtype` to only do `desktop` or `mobile` searches, `(ex: --searchtype=mobile)`

## Features

- Bing searches (Desktop and Mobile) with current User-Agents
- Complete the daily set automatically
- Complete punch cards automatically
- Complete the others promotions automatically
- Headless Mode - _not recommended at all_
- Multi-Account Management
- Session storing
- 2FA Support
- Notifications via [Apprise](https://github.com/caronc/apprise) - no longer limited to Telegram or Discord
- Proxy Support (3.0) - they need to be **high quality** proxies
- Logs to CSV file for point tracking

## Contributing

Fork this repo and:

* if providing a bugfix, create a pull request into master.
* if providing a new feature, please create a pull request into develop. Extra points if you update
  the [CHANGELOG.md](CHANGELOG.md).

## To Do List (When time permits or someone makes a PR)

- [x] Complete "Read To Earn" (30 pts)
- [x] Setup flags for mobile/desktop search only
- [ ] Setup flags to load config / save data in working directory
- [x] Provide Windows Task Scheduler config
