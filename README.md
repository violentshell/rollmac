# Rollmac
This script was produced to avoid the connect, download, hit limit, change mac, reconnect loop that a user has to repeat on a data or time limited WiFi network. Rollmac tries to automatically find the networks proxy page and simulate a user accepting the T & C form by submitting the corresponding post. 

The entire operation usually takes about 10 seconds.

You may need to configure the script slightly to adjust to individual network specifics, however, Rollmac allows you to download massive amounts of data without user input by setting the conf file and leaving it running overnight. 



The program is controlled by variables inside the conf.json file. Modify these to meet your network/host machine:
-----
Set to network ssid (Must have matching profile in "netsh wlan show profiles":

    ssid = 'Free WiFi'

Set to data limit inMB or 99999999999 for ifinite:

    MB_limit = 250
    
Set to time limit in mins or 99999999999 for infinite:

    TIME_limit = 60

Set to your wireless interface name:

    interface = 'Wireless Local Area Connection'

Set to the domain of the network you are joining (You can get it from ipconfig /all):

    domain = 'freewifi.com'

You may want to change this value to 1 to stop ie/browser opening again on each reconnect:

    # 'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings\WPAD\WpadOverride'
