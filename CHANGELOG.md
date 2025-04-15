# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-04-08

### Added

- Consolidated all language-specific data into a single dictionary for `localized_activities`, simplifying management and improving performance.
- New activity handling.
- Added country and language code validation functions and updated browser geolocation handling.
- Added configuration options in `config.yaml` for activity handling and error notifications:
  - `apprise.notify.incomplete-activity` for incomplete activity notifications.
  - `apprise.notify.login-code` for login with phone code notifications.
- Added reset functionality to delete session files and terminate Chrome processes.
- Added CODEOWNERS file for repository management.
- Added Docker build for easier deployment and execution.
- Added `run.ps1` script with the following features:
  - Automatic detection of Python installations or virtual environments.
  - Retry logic for running the main script with configurable maximum attempts.
  - Automatic cleanup of Chrome processes and session files on failure.
  - Support for updating the script via Git if in a Git repository.
  - Command-line options for customization, including Python path, script directory, and session folder.

### Changed

- Improved retry logic in `getBingInfo` and updated backoff factor configuration.
- Updated `config.yaml` to enhance logging and error reporting configurations.
- Refactored activity handling to use localized titles and queries.
- Improved logging for activity completion, error reporting, and localization warnings.
- Enhanced JSON response handling in `utils.py` and updated parameters in `run.ps1`.
- Replaced `accounts.json` with account information now stored in `config.yaml` for better configuration management.
- Adjusted cooldowns and wait times for better performance.

### Fixed

- Fixed issues with quiz completion logic for "This or That" and "ABC" activities.
- Addressed edge cases where activities were incorrectly marked as incomplete.
- Fixed activities containing non-breakable spaces in their names.
- Fixed Google Trends API integration and improved trend keyword handling.
- Fixed click handling in `activities.py` to use the correct answer element.
- Fixed issue related to mobile search for level 1 users.
- Fixed Apprise notification error.
- Fixed exit code to return `exit 1` on errors instead of `exit 0`.

### Removed

- Removed unused imports and deprecated classes for cleaner codebase.
- Removed `MS_reward.bat` in favor of the more robust `run.ps1` script.
- Removed `config-private.yaml` in favor of consolidating configurations into `config.yaml`.
- Removed password logging.

### Other

- Added locked/banned user detection.
- Skipped un-doable activities.

## [1.1.0] - 2024-08-30

### Added

- Promotions/More activities
  - Expand your vocabulary
  - What time is it?

## [1.0.1] - 2024-08-25

### Fixed

- [AssertionError from apprise.notify(title=str(title), body=str(body))](https://github.com/klept0/MS-Rewards-Farmer/issues)

## [1.0.0] - 2024-08-23

### Removed

- `apprise.urls` from [config.yaml](config.yaml)
  - This now lives in `config-private.yaml`, see [.template-config-private.yaml](.template-config-private.yaml) on how
    to configure
  - This prevents accidentally leaking sensitive information since `config-private.yaml` is .gitignore'd

### Added

- Support for automatic handling of logins with 2FA and for passwordless setups:
  - Passwordless login is supported in both visible and headless mode by displaying the code that the user has to select
    on their phone in the terminal window
  - 2FA login with TOTPs is supported in both visible and headless mode by allowing the user to provide their TOTP key
    in `accounts.json` which automatically generates the one time password
  - 2FA login with device-based authentication is supported in theory, BUT doesn't currently work as the undetected
    chromedriver for some reason does not receive the confirmation signal after the user approves the login
- Completing quizzes started but not completed in previous runs
- Promotions/More activities
  - Find places to stay
  - How's the economy?
  - Who won?
  - Gaming time

### Changed

- Incomplete promotions Apprise notifications
  - How incomplete promotions are determined
  - Batched into single versus multiple notifications
- Full exception is sent via Apprise versus just error message

### Fixed

- Promotions/More activities
  - Too tired to cook tonight?
- [Last searches always timing out](https://github.com/klept0/MS-Rewards-Farmer/issues/172)
- [Quizzes don't complete](https://github.com/klept0/MS-Rewards-Farmer/issues)

## [0.2.1] - 2024-08-13

### Fixed

- [Fix ElementNotInteractableException](https://github.com/klept0/MS-Rewards-Farmer/pull/176)

## [0.2.0] - 2024-08-09

### Added

- Initial release of the Python script:
  - Generates a Task Scheduler XML file
  - Allows users to choose between Miniconda, Anaconda, and Local Python
  - Prompts users to input the name of their environment (if using Miniconda or Anaconda)
  - Uses the script directory as the output path
  - Default trigger time is set to 6:00 AM on a specified day, with instructions to modify settings after importing to
    Task Scheduler
  - Includes a batch file (`MS_reward.bat`) for automatic execution of the Python script

### Fixed

- [Error when trends fail to load](https://github.com/klept0/MS-Rewards-Farmer/issues/163)

## [0.1.0] - 2024-07-27

### Added

- New [config.yaml](config.yaml) options
  - `retries`
    - `base-delay-in-seconds`: how many seconds to delay
    - `max`: the max amount of retries to attempt
    - `strategy`: method to use when retrying, can be either:
      - `CONSTANT`: the default; a constant `base-delay-in-seconds` between attempts
      - `EXPONENTIAL`: an exponentially increasing `base-delay-in-seconds` between attempts
  - `apprise.summary`: configures how results are summarized via Apprise, can be either:
    - `ALWAYS`: the default, as it was before, how many points were gained and goal percentage if set
    - `ON_ERROR`: only sends email if for some reason there's remaining searches
    - `NEVER`: never send summary
- Apprise notification if activity isn't completed/completable
- Support for more activities
- New arguments (see [readme](README.md#launch-arguments) for details)
- Some useful JetBrains config
- More logging
- Config to make `requests` more reliable
- More checks for bug report
- Me, cal4, as a sponsoree

### Changed

- More reliable searches and closer to human behavior
- When logger is set to debug, doesn't include library code now
- Line endings to LF

### Removed

- Calls to close all Chrome processes

### Fixed

- [Error when executing script from .bat file](https://github.com/klept0/MS-Rewards-Farmer/issues/113)
- [\[BUG\] AttributeError: 'Browser' object has no attribute 'giveMeProxy'](https://github.com/klept0/MS-Rewards-Farmer/issues/115)
- [\[BUG\] driver.quit causing previous issue of hanging process with heavy load on cpu](https://github.com/klept0/MS-Rewards-Farmer/issues/136)
- Login
- Errors when [config.yaml](config.yaml) doesn't exist
- General reliability and maintainability fixes

## [0.0.0] - 2023-03-05

### Added

- Farmer and lots of other things, but gotta start a changelog somewhere!
