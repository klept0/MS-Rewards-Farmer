import datetime as dt
import getpass
import os
import subprocess
from pathlib import Path

# Get the directory of the script being run
script_dir = Path(__file__).parent.resolve()
script_path = script_dir / "run.ps1"

# Get the current user's name
current_user = getpass.getuser()


# Get the current user's SID
def get_user_sid(username):
    try:
        command = [
            "powershell",
            "-Command",
            f"(Get-WmiObject -Class Win32_UserAccount -Filter \"Name='{username}'\").SID",
        ]
        output = subprocess.check_output(command, universal_newlines=True)
        sid = output.strip()
        return sid
    except Exception as e:
        print(f"Error getting SID for user {username}: {e}")
        return None


sid = get_user_sid(current_user)

if sid is None:
    print("Unable to retrieve SID automatically.")
    print(
        "Please manually check your SID by running the following command in Command Prompt:"
    )
    print("whoami /user")
    sid = input("Enter your SID manually: ")

computer_name = os.environ["COMPUTERNAME"]

xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{dt.datetime.now(dt.UTC).isoformat()}</Date>
    <Author>{computer_name}\\{current_user}</Author>
    <URI>\\Custom\\MsReward</URI>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2024-08-09T06:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{sid}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>true</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>true</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>%windir%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe</Command>
      <Arguments>-File "{script_path}" -ExecutionPolicy Bypass</Arguments>
      <WorkingDirectory>{script_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

# Use the script directory as the output path
output_path = script_dir / "MsReward.xml"

with open(output_path, "w", encoding="utf-16") as file:
    file.write(xml_content)

print(f"XML file has been generated and saved to: {output_path}")
print("To import, see https://superuser.com/a/485565/709704")
print("The trigger time is set to 6:00 AM on the specified day.")
print("You can modify the settings after importing the task into the Task Scheduler.")
