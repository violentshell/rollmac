# Rollmac
Free WiFi networks often impose either a time or data restriction and this can be used quickly. When this happens a user can often change thier MAC address and reconnect to reset the limitation, but this is annoying, and it takes time. In addition, most networks will ask the user to re-accept the terms and conditions of the network in order to continue.

Rollmac is designed to automate this process by changing the MAC address, then using the WPAD protocol to discover the login page and automatically re-accept the terms and conditions. It also maintains a watch of the network current usage and/or time limit to ensure it is never reached. This means you can run downloads overnight or while you are away from your computer, automatically rolling mac's and reconnecting to the free network.

The entire recconnect operation usually takes about 10 seconds.

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
