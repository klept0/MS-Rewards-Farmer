import csv
import json
import logging
import logging.config
import logging.handlers as handlers
import sys
import traceback
from datetime import datetime
from enum import Enum, auto

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
from src.utils import CONFIG, sendNotification, getProjectRoot, formatNumber


def main():
    setupLogging()

    # Load previous day's points data
    previous_points_data = load_previous_points_data()

    for currentAccount in CONFIG.accounts:
        try:
            earned_points = executeBot(currentAccount)
        except Exception as e1:
            logging.error("", exc_info=True)
            sendNotification(
                f"⚠️ Error executing {currentAccount.email}, please check the log",
                traceback.format_exc(),
                e1,
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

    with open(csv_filename, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if is_new_file:
            writer.writeheader()

        writer.writerow(new_row)


def setupLogging():
    _format = CONFIG.logging.format
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(ColoredFormatter(_format))

    logs_directory = getProjectRoot() / "logs"
    logs_directory.mkdir(parents=True, exist_ok=True)

    # so only our code is logged if level=logging.DEBUG or finer
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
        }
    )
    logging.basicConfig(
        level=logging.getLevelName(CONFIG.logging.level.upper()),
        format=_format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                logs_directory / "activity.log",
                when="midnight",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            ),
            terminalHandler,
        ],
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
            ReadToEarn(mobileBrowser).completeReadToEarn()
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
                f"[POINTS] You are now at {(formatNumber((accountPoints / goalPoints) * 100))}% of your "
                f"goal ({goalTitle}) !"
            )
            goalStatus = (
                f"🎯 Goal reached: {(formatNumber((accountPoints / goalPoints) * 100))}%"
                f" ({goalTitle})"
            )

        sendNotification(
            "Daily Points Update",
            "\n".join(
                [
                    f"👤 Account: {currentAccount.email}",
                    f"⭐️ Points earned today: {formatNumber(accountPoints - startingPoints)}",
                    f"💰 Total points: {formatNumber(accountPoints)}",
                    goalStatus,
                ]
            ),
        )
    elif appriseSummary == AppriseSummary.ON_ERROR:
        if remainingSearches.getTotal() > 0:
            sendNotification(
                "Error: remaining searches",
                f"account email: {currentAccount.email}, {remainingSearches}",
            )
    elif appriseSummary == AppriseSummary.NEVER:
        pass

    return accountPoints


def export_points_to_csv(points_data):
    logs_directory = getProjectRoot() / "logs"
    csv_filename = logs_directory / "points_data.csv"
    with open(csv_filename, mode="a", newline="") as file:  # Use "a" mode for append
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
        with open(getProjectRoot() / "logs" / "previous_points_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Define a function to save the current day's points data for the next day in the "logs" folder
def save_previous_points_data(data):
    logs_directory = getProjectRoot() / "logs"
    with open(logs_directory / "previous_points_data.json", "w") as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("")
        sendNotification(
            "⚠️ Error occurred, please check the log", traceback.format_exc(), e
        )
        exit(1)
