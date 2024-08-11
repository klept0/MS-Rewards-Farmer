# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-08-09

### Added

- Initial release of the Python script:
  - Generates a Task Scheduler XML file
  - Allows users to choose between Miniconda, Anaconda, and Local Python
  - Prompts users to input the name of their environment (if using Miniconda or Anaconda)
  - Uses the script directory as the output path
  - Default trigger time is set to 6:00 AM on a specified day, with instructions to modify settings after importing to Task Scheduler
  - Includes a batch file (`MS_reward.bat`) for automatic execution of the Python script

### Fixed

- [Error when trends fail to load](https://github.com/klept0/MS-Rewards-Farmer/issues/163)

## [0.1.0] - 2024-07-27

### Added

- New [config.yaml](config.yaml) options
  - `retries`
    - `base_delay_in_seconds`: how many seconds to delay
    - `max`: the max amount of retries to attempt
    - `strategy`: method to use when retrying, can be either:
      - `CONSTANT`: the default; a constant `base_delay_in_seconds` between attempts
      - `EXPONENTIAL`: an exponentially increasing `base_delay_in_seconds` between attempts
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
