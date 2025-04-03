import csv
import json
import logging
import logging.config
import sys
from datetime import datetime
from enum import Enum, auto
from logging import handlers

from src import (
    Browser,
    Login,
    PunchCards,
    Searches,
    ReadToEarn,
)
from src.activities import Activities
from src.browser import RemainingSearches
from src.loggingColoredFormatter import ColoredFormatter
from src.utils import CONFIG, APPRISE, getProjectRoot, formatNumber


def main():
    setupLogging()

    # Load previous day's points data
    previous_points_data = load_previous_points_data()

    foundError = False

    for currentAccount in CONFIG.accounts:
        try:
            earned_points = executeBot(currentAccount)
        except Exception as e1:
            logging.error("", exc_info=True)
            foundError = True
            if CONFIG.get("apprise.notify.uncaught-exception"):
                APPRISE.notify(
                    f"{type(e1).__name__}: {e1}",
                    f"⚠️ Error executing {currentAccount.email}, please check the log",
                )
            continue

        previous_points = previous_points_data.get(currentAccount.email, 0)

        # Calculate the difference in points from the prior day
        points_difference = earned_points - previous_points

        # Append the daily points and points difference to CSV and Excel
        log_daily_points_to_csv(earned_points, points_difference)

        # Update the previous day's points data
        previous_points_data[currentAccount.email] = earned_points

        logging.info(
            f"[POINTS] Data for '{currentAccount.email}' appended to the file."
        )

    # Save the current day's points data for the next day in the "logs" folder
    save_previous_points_data(previous_points_data)
    logging.info("[POINTS] Data saved for the next day.")

    if foundError:
        sys.exit(1)


def log_daily_points_to_csv(earned_points, points_difference):
    logs_directory = getProjectRoot() / "logs"
    csv_filename = logs_directory / "points_data.csv"

    # Create a new row with the date, daily points, and points difference
    date = datetime.now().strftime("%Y-%m-%d")
    new_row = {
        "Date": date,
        "Earned Points": earned_points,
        "Points Difference": points_difference,
    }

    fieldnames = ["Date", "Earned Points", "Points Difference"]
    is_new_file = not csv_filename.exists()

    with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if is_new_file:
            writer.writeheader()

        writer.writerow(new_row)


def setupLogging():
    _format = CONFIG.logging.format
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(ColoredFormatter(_format))
    terminalHandler.setLevel(logging.getLevelName(CONFIG.logging.level.upper()))

    logs_directory = getProjectRoot() / "logs"
    logs_directory.mkdir(parents=True, exist_ok=True)

    fileHandler = handlers.TimedRotatingFileHandler(
        logs_directory / "activity.log",
        when="midnight",
        backupCount=2,
        encoding="utf-8",
    )
    fileHandler.namer = lambda name: name.replace('.log.', '-') + '.log'
    fileHandler.setLevel(logging.DEBUG)

    logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": True,
    })

    logging.basicConfig(
        level=logging.DEBUG,
        format=_format,
        handlers=[fileHandler, terminalHandler],
        force=True,
    )


class AppriseSummary(Enum):
    """
    configures how results are summarized via Apprise
    """

    ALWAYS = auto()
    """
    the default, as it was before, how many points were gained and goal percentage if set
    """
    ON_ERROR = auto()
    """
    only sends email if for some reason there's remaining searches 
    """
    NEVER = auto()
    """
    never send summary 
    """


def executeBot(currentAccount):
    logging.info(f"********************{currentAccount.email}********************")

    startingPoints: int | None = None
    accountPoints: int
    remainingSearches: RemainingSearches
    goalTitle: str
    goalPoints: int

    if CONFIG.search.type in ("desktop", "both", None):
        with Browser(mobile=False, account=currentAccount) as desktopBrowser:
            utils = desktopBrowser.utils
            Login(desktopBrowser).login()
            startingPoints = utils.getAccountPoints()
            logging.info(
                f"[POINTS] You have {formatNumber(startingPoints)} points on your account"
            )
            Activities(desktopBrowser).completeActivities()
            PunchCards(desktopBrowser).completePunchCards()
            # VersusGame(desktopBrowser).completeVersusGame()

            with Searches(desktopBrowser) as searches:
                searches.bingSearches()

            goalPoints = utils.getGoalPoints()
            goalTitle = utils.getGoalTitle()

            remainingSearches = desktopBrowser.getRemainingSearches(
                desktopAndMobile=True
            )
            accountPoints = utils.getAccountPoints()

    if CONFIG.search.type in ("mobile", "both", None):
        with Browser(mobile=True, account=currentAccount) as mobileBrowser:
            utils = mobileBrowser.utils
            Login(mobileBrowser).login()
            if startingPoints is None:
                startingPoints = utils.getAccountPoints()
            try:
                ReadToEarn(mobileBrowser).completeReadToEarn()
            except Exception:
                logging.exception("[READ TO EARN] Failed to complete Read to Earn")
            with Searches(mobileBrowser) as searches:
                searches.bingSearches()

            goalPoints = utils.getGoalPoints()
            goalTitle = utils.getGoalTitle()

            remainingSearches = mobileBrowser.getRemainingSearches(
                desktopAndMobile=True
            )
            accountPoints = utils.getAccountPoints()

    logging.info(
        f"[POINTS] You have earned {formatNumber(accountPoints - startingPoints)} points this run !"
    )
    logging.info(f"[POINTS] You are now at {formatNumber(accountPoints)} points !")
    appriseSummary = AppriseSummary[CONFIG.apprise.summary]
    if appriseSummary == AppriseSummary.ALWAYS:
        goalStatus = ""
        if goalPoints > 0:
            logging.info(
                f"[POINTS] You are now at {(formatNumber((accountPoints / goalPoints) * 100))}%"
                f" of your goal ({goalTitle}) !"
            )
            goalStatus = (
                f"🎯 Goal reached: {(formatNumber((accountPoints / goalPoints) * 100))}%"
                f" ({goalTitle})"
            )

        APPRISE.notify(
            "\n".join(
                [
                    f"👤 Account: {currentAccount.email}",
                    f"⭐️ Points earned today: {formatNumber(accountPoints - startingPoints)}",
                    f"💰 Total points: {formatNumber(accountPoints)}",
                    goalStatus,
                ]
            ),
            "Daily Points Update",
        )
    elif appriseSummary == AppriseSummary.ON_ERROR:
        if remainingSearches.getTotal() > 0:
            APPRISE.notify(
                f"account email: {currentAccount.email}, {remainingSearches}",
                "Error: remaining searches",
            )
    elif appriseSummary == AppriseSummary.NEVER:
        pass

    return accountPoints


def export_points_to_csv(points_data):
    logs_directory = getProjectRoot() / "logs"
    csv_filename = logs_directory / "points_data.csv"
    with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
        fieldnames = ["Account", "Earned Points", "Points Difference"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Check if the file is empty, and if so, write the header row
        if file.tell() == 0:
            writer.writeheader()

        for data in points_data:
            writer.writerow(data)


# Define a function to load the previous day's points data from a file in the "logs" folder
def load_previous_points_data():
    try:
        with open(
                getProjectRoot() / "logs" / "previous_points_data.json", encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Define a function to save the current day's points data for the next day in the "logs" folder
def save_previous_points_data(data):
    logs_directory = getProjectRoot() / "logs"
    with open(logs_directory / "previous_points_data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("")
        if CONFIG.get("apprise.notify.uncaught-exception"):
            APPRISE.notify(
                f"{type(e).__name__}: {e}",
                "⚠️ Error occurred, please check the log",
            )
        sys.exit(1)
