import requests, spoofmac, psutil, datetime, logging, time, subprocess
import bs4 as soup


class RollMac():
    def __init__(self, ssid, limit, time_limit, interface, domain):
        self.setup_logging()
        self.info = {'domain': domain}
        self.ssid = ssid
        self.limit = limit
        self.time_limit = time_limit
        self.over_limit = True
        self.old_t_mbytes = 0
        self.interface = interface

    def run(self):
        # Will hit on first loop, then on over limit
        if self.over_limit:

            # Spoof Mac
            self.spoof()

            # Let interface come back up
            time.sleep(1)

            # Re-connect
            self.connect()

            # Get redirect url from wpad
            self.get_redirect()

            # login to page with post values
            if self.login() == 200:
                self.log.info('Reconnected to AP with new mac. Resetting data limit')

                # Reset limits ( Data is doen automatically by flapping interface)
                self.over_limit = False
                self.start_time = datetime.datetime.now()

        elif not self.over_limit:
            time.sleep(15)

            # Print output and check limits
            self.over_limit = self.limit_check()

    def spoof(self):
        '''
        :return: Nothing. Sets mac on interface
        '''
        self.mac = spoofmac.random_mac_address()
        spoofmac.set_interface_mac(self.interface, spoofmac.random_mac_address())
        self.log.debug('Changed mac of {} to: {}'.format(self.interface, self.mac))

    def limit_check(self):
        '''
        :return: True if within 5% of MB limit; False if outside 5% of MB limit
        '''

        # Raw interface bytes
        bytes = psutil.net_io_counters(True)[self.interface]

        # Convert total to MB
        self.t_mbytes =  (bytes.bytes_recv + bytes.bytes_sent) >>20

        self.log.debug('{} MB remaining'.format(self.limit - self.t_mbytes))

        # Check time limit and MB limit
        if self.time_check() or self.t_mbytes >= (self.limit - (5 / 100 * self.limit)):
            return True
        return False

    def time_check(self):
        '''
        :return: True if within 5 min of limit; False if outside 5 min of limit
        '''

        try:
            self.start_time
        except NameError:
            self.start_time = datetime.datetime.now()
            self.log.info("Connected at {}".format(datetime.datetime.now().strftime('%H:%M:%S')))

        # Online time in minutes
        online_time = (datetime.datetime.now() - self.start_time).seconds / 60

        # For info
        self.log.info('{} minutes remaining'.format(round(self.time_limit - online_time - 5)))

        # Return True if over limit threshold
        if self.time_limit - online_time <= 5 :
            self.log.warn('Over Time Limit')
            return True
        return False

    def connect(self):
        '''
        :param profile: A string representing the ssid profile name in netsh
        :return: True if connected, False for fail
        '''

        netsh = subprocess.check_output('netsh wlan connect name="{}"'.format(self.ssid))
        if b'Connection request was completed successfully.' in netsh:
             return self.log.debug('Re-assosiated with {}'.format(self.ssid))


    def retry_get(self,url):
        '''
        :param url: string of a url
        :return: data if it works, raises error if not
        '''
        for i in range(5):
            try:
                data = requests.get(url)
                return data
            except:
                self.log.warn('Get failed for {} try number {}'.format(url,i))
                time.sleep(3)

        raise ConnectionError

    def get_redirect(self):
        '''

        :param self.info['domain']: The address of the wpad server: 'wpad.domain.com'
        :return: url of the page redirected to from wpad
        '''
        wpad_data = self.retry_get('http://wpad.{}'.format(self.info['domain']))

        if wpad_data.status_code != 200:
            self.log.error('Failed to retrieve wpad from {}'.format(self.info['domain']))
            sys.exit()

        so = soup.BeautifulSoup(wpad_data.content, 'lxml')

        self.info['url'] = so.find('meta', attrs={'http-equiv': 'refresh'})['content'].partition('=')[2]

        self.log.info('Found redirect url: {}'.format(self.info['url']))

    def login(self):
        '''
        :return: Status code for our post to the login page
        '''
        logon_page = self.retry_get(self.info['url'])

        so2 = soup.BeautifulSoup(logon_page.content, 'lxml')

        form = so2.find('form')

        post_data = form.find_all('input', attrs={'type': 'hidden'})

        post_dict = {}
        for entry in post_data:
            post_dict[entry['name']] = entry['value']

        self.log.debug('Login form data: {}'.format(post_dict))

        return requests.post(form['action'], data=post_dict).status_code

    def setup_logging(self):
        # Silence request module
        logging.getLogger("requests").setLevel(logging.WARNING)

        # Setup log vars
        self.log = logging.getLogger('')

        self.format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Main logger
        rootLogger = logging.getLogger()
        rootLogger.setLevel(logging.DEBUG)

        # Print to console
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(self.format)
        rootLogger.addHandler(consoleHandler)

        # Good to go
        self.log.debug('Logging setup complete')


if __name__ =='__main__':

    # Change these to suit your system:
    ssid = 'Free WiFi'

    # Set to MB or 9999999999999 for ifinite
    MB_limit = 250

    # Set to mins or 99999999999 for infinite
    TIME_limit = 60

    # Set to your Interface name
    interface = 'Wireless Local Area Connection'

    # Set to the domain of the network you are joining (You can get it from ipconfig /all)
    domain = 'xxx.com'

    # You may want to change this value to 1 to stop ie/browser opening again on reconnect
    # 'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings\WPAD\WpadOverride'

    # Init class
    main = RollMac(ssid, MB_limit, TIME_limit, interface, domain)

    # Loop forever
    while True:
        main.run()



