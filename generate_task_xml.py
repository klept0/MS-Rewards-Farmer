import getpass
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Get the directory of the script being run
script_dir = Path(__file__).parent.resolve()

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

# Let the user choose between Miniconda and Anaconda
print("Please choose your Python distribution:")
print("1. Local (Windows system Python without virtual environment)")
print("2. Anaconda")
print("3. Miniconda")
choice = input("Enter your choice (1, 2, or 3): ")

if choice == "1":
    command = f"{script_dir}\\MS_reward.bat"
elif choice == "2":
    base_path = f"C:\\Users\\{current_user}\\anaconda3"
    command = f"{base_path}\\Scripts\\activate.bat {base_path} &amp;&amp; conda activate {{env_name}} &amp;&amp; {script_dir}\\MS_reward.bat"
elif choice == "3":
    base_path = f"C:\\Users\\{current_user}\\miniconda3"
    command = f"{base_path}\\Scripts\\activate.bat {base_path} &amp;&amp; conda activate {{env_name}} &amp;&amp; {script_dir}\\MS_reward.bat"
else:
    print("Invalid choice, please rerun the script and choose 1, 2, or 3.")
    exit(1)

# Let the user enter the name of the environment they are using
if choice in ["2", "3"]:
    env_name = input("Please enter the name of the environment you are using: ")
    command = command.format(env_name=env_name)

xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.utcnow().isoformat()}</Date>
    <Author>{computer_name}\\{current_user}</Author>
    <URI>\\Custom\\MS reward</URI>
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
      <Command>%windir%\\System32\\cmd.exe</Command>
      <Arguments>/K "{command}"</Arguments>
      <WorkingDirectory>{script_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

# Use the script directory as the output path
output_path = script_dir / "MS_reward.xml"

with open(output_path, "w", encoding="utf-16") as file:
    file.write(xml_content)

print(f"XML file has been generated and saved to: {output_path}")
print("To import, see https://superuser.com/a/485565/709704")
print("The trigger time is set to 6:00 AM on the specified day.")
print("You can modify the settings after importing the task into the Task Scheduler.")
