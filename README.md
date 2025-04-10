### A "simple" python application that uses Selenium to help with your M$ Rewards

![Static Badge](https://img.shields.io/badge/Made_in-python-violet?style=for-the-badge)
![MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge)
![GitHub contributors](https://img.shields.io/github/contributors/klept0/MS-Rewards-Farmer?style=for-the-badge)
![GitHub issues](https://img.shields.io/github/issues/klept0/MS-Rewards-Farmer?style=for-the-badge)



> [!IMPORTANT]
> If you are multi-accounting and abusing the service for which this is intended - *
*_DO NOT COMPLAIN ABOUT BANS!!!_**



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

[//]: # (todo - add Docker installation instructions)

1. Create a virtual environment using `venv`:
   ```sh
   python -m venv venv
   ```
2. Activate the virtual environment:

   * On Windows:

   ```sh
   venv\Scripts\activate
   ```

   * On macOS/Linux:

   ```sh
   source venv/bin/activate
   ```

3. Install requirements with the following command :
   ```sh
   pip install -r requirements.txt
   ```

   Or, if developing or running tests, install the dev requirements with:
   ```sh
    pip install -r requirements-dev.txt
   ```

   Upgrade all required with the following command:
   `pip install --upgrade -r requirements.txt`

4. Make sure you have Chrome installed

5. (Windows Only) Make sure Visual C++ redistributable DLLs are installed

   If they're not, install the current "vc_redist.exe" from
   this [link](https://learn.microsoft.com/en-GB/cpp/windows/latest-supported-vc-redist?view=msvc-170)
   and reboot your computer

6. Run the script with the following arguments:
   ```sh
   python main.py -C
   ```

7. Open the generated `config.yaml` file and edit it with your information.

   The "totp" field is not mandatory, only enter your TOTP key if you use it for 2FA (if
   ommitting, don't keep it as an empty string, remove the line completely).

   The "proxy" field is not mandatory, you can omit it if you don't want to use proxy (don't
   keep it as an empty string, remove the line completely).

   You can add or remove accounts according to your will.

   the "apprise.urls" field is not mandatory, you can remove it if you don't want to get notifications.

8. Run the script:
   ```sh
   python main.py
   ```

   (Windows Only) You can also run the script wrapper that will detect your python installation
   and re-run the script if it crashes using `.\run.ps1` (`.\run.ps1 -help` for more
   information). To allow script execution without confirmation, use the following command:
   `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`.

9. (Windows Only) You can set up automatic execution by generating a Task Scheduler XML file.

   If you are a Windows user, run the `generate_task_xml.py` script to create a `.xml` file.
   After generating the file, import it into Task Scheduler to schedule automatic execution of
   the script. This will allow the script to run at the specified time without manual
   intervention.

   To import the XML file into Task Scheduler,
   see [this guide](https://superuser.com/a/485565/709704).

## Configuration file

All the variable listed here can be added to you `config.yaml` configuration file, and the values represented here show
the default ones, if not said otherwise.

> [!CAUTION]
> Please don't use this as your configuration. It's an example to show configuration possibilities,
> not the best configuration for you. Doing so will only prevent default values from being used,
> and it'll result in preventing updates (such as ignored activities).
> You should only add a variable to your configuration file if you want to change it.

```yaml
# config.yaml
apprise: # 'apprise' is the name of the service used for notifications https://github.com/caronc/apprise
  enabled: true  # set it to false to disable apprise globally, can be overridden with command-line arguments.
  notify:
    incomplete-activity: true # set it to false to disable notifications for incomplete activities
    uncaught-exception: true # set it to false to disable notifications for uncaught exceptions
    login-code: true # set it to false to disable notifications for the temporary M$ Authenticator login code
  summary: ON_ERROR # set it to ALWAYS to always receive a summary about your points progression or errors, or to 
  # NEVER to never receive a summary, even in case of an error. 
  urls: # add apprise urls here to receive notifications on the specified services :
    # https://github.com/caronc/apprise#supported-notifications
    # Empty by default.
    - discord://{WebhookID}/{WebhookToken} # Exemple url 
browser:
  geolocation: US # Replace with your country code https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2.
  # Detected by default, can be overridden with command-line arguments.
  language: en # Replace with your language code https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes.
  # Detected by default, can be overridden with command-line arguments.
  visible: false # set it to true to show the browser window, can be overridden with command-line arguments.
  proxy: null # set the global proxy using the 'http://user:pass@host:port' syntax.
  # Override per-account proxies. Can be overridden with command-line arguments.
rtfr: true # If true, display the "read the readme" message at the start of the script and prevent the script
# from running. Default is false.
logging:
  level: INFO # Set to DEBUG, WARNING, ERROR or CRITICAL to change the level of displayed information in the terminal
  # See https://docs.python.org/3/library/logging.html#logging-levels. Can be overridden with command-line arguments.
retries:
  backoff-factor: 120 # The base wait time between each retries. Multiplied by two each try.
  max: 4 # The maximal number of retries to do
  strategy: EXPONENTIAL # Set it to CONSTANT to use the same delay between each retries.
  # Else, increase it exponentially each time.
cooldown:
  min: 300 # The minimal wait time between two searches/activities
  max: 600 # The maximal wait time between two searches/activities
search:
  type: both # Set it to 'mobile' or 'desktop' to only complete searches on one plateform,
  # can be overridden with command-line arguments.
accounts: # The accounts to use. You can put zero, one or an infinite number of accounts here.
  # Empty by default, can be overridden with command-line arguments.
  - email: Your Email 1 # replace with your email
    password: Your Password 1 # replace with your password
    totp: 0123 4567 89ab cdef # replace with your totp, or remove it
    proxy: http://user:pass@host1:port # replace with your account proxy, or remove it
  - email: Your Email 2 # replace with your email
    password: Your Password 2 # replace with your password
    totp: 0123 4567 89ab cdef # replace with your totp, or remove it
    proxy: http://user:pass@host2:port # replace with your account proxy, or remove it
```

## Usage

```
usage: main.py [-h] [-c CONFIG] [-C] [-v] [-l LANG] [-g GEO] [-em EMAIL] [-pw PASSWORD]
               [-p PROXY] [-t {desktop,mobile,both}] [-da] [-d] [-r]

A simple bot that uses Selenium to farm M$ Rewards in Python

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Specify the configuration file path
  -C, --create-config   Create a fillable configuration file with basic settings and given
                        ones if none exists
  -v, --visible         Visible browser (Disable headless mode)
  -l LANG, --lang LANG  Language (ex: en) see https://serpapi.com/google-languages for options
  -g GEO, --geo GEO     Searching geolocation (ex: US) see https://serpapi.com/google-trends-
                        locations for options (should be uppercase)
  -em EMAIL, --email EMAIL
                        Email address of the account to run. Only used if a password is given.
  -pw PASSWORD, --password PASSWORD
                        Password of the account to run. Only used if an email is given.
  -p PROXY, --proxy PROXY
                        Global Proxy, supports http/https/socks4/socks5 (overrides config per-
                        account proxies) `(ex: http://user:pass@host:port)`
  -t {desktop,mobile,both}, --searchtype {desktop,mobile,both}
                        Set to search in either desktop, mobile or both (default: both)
  -da, --disable-apprise
                        Disable Apprise notifications, useful when developing
  -d, --debug           Set the logging level to DEBUG
  -r, --reset           Delete the session folder and temporary files and kill all chrome
                        processes. Can help resolve issues.

At least one account should be specified, either using command line arguments or a
configuration file. All specified arguments will override the configuration file values
```

You can display this message at any moment using `python main.py -h`.

## Features

- Bing searches (Desktop and Mobile) with current User-Agents
- Complete the daily set automatically
- Complete punch cards automatically
- Complete the others promotions automatically
- Headless Mode
- Multi-Account Management
- Session storing
- 2FA Support
- Notifications via [Apprise](https://github.com/caronc/apprise) - no longer limited to
  Telegram or Discord
- Proxy Support (3.0) - they need to be **high quality** proxies
- Logs to CSV file for point tracking

## Contributing

Fork this repo and:

* if providing a bugfix, create a pull request into master.
* if providing a new feature, please create a pull request into develop. Extra points if you
  update the [CHANGELOG.md](CHANGELOG.md).
