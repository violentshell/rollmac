import bs4 as soup
import datetime
import json
import logging
import psutil
import requests
import spoofmac
import subprocess
import sys
import time


# noinspection PyAttributeOutsideInit
class RollMac:
    def __init__(self):
        self.setup_logging()
        self.get_config()
        self.info = {'domain': self.domain}
        self.over_limit = True
        self.old_t_mbytes = 0

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

                # Reset limits ( Data is done automatically by flapping interface)
                self.over_limit = False
                self.start_time = datetime.datetime.now()

        elif not self.over_limit:
            time.sleep(15)

            # Print output and check limits
            self.over_limit = self.limit_check()

    def spoof(self):
        """
        :return: Nothing. Sets mac on interface
        """
        self.mac = spoofmac.random_mac_address()
        spoofmac.set_interface_mac(self.interface, self.mac)
        self.log.debug('Changed mac of {} to: {}'.format(self.interface, self.mac))

    def limit_check(self):
        """
        :return: True if within 5% of MB limit; False if outside 5% of MB limit
        """

        # Check time limit and MB limit
        if self.time_check() or self.data_check():
            return True
        return False

    def time_check(self):
        """
        :return: True if within 5 min of limit; False if outside 5 min of limit
        """

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
        if self.time_limit - online_time <= 5:
            self.log.warn('Over time limit.')
            return True
        return False

    def data_check(self):
        # Raw interface bytes TODO Linux compatible?
        netbytes = psutil.net_io_counters(True)[self.interface]

        # Convert total to MB
        t_mbytes = (netbytes.bytes_recv + netbytes.bytes_sent) >> 20

        # For info
        self.log.debug('{} MB remaining'.format(self.limit - t_mbytes))

        # Return True if over limit threshold
        if t_mbytes >= (self.limit - (5 / 100 * self.limit)):
            self.log.warn('Over data limit.')
            return True
        return False

    def connect(self):
        """
        :return: True if connected, False for fail
        """

        netsh = subprocess.check_output('netsh wlan connect name="{}"'.format(self.ssid))
        if b'Connection request was completed successfully.' in netsh:
            return self.log.debug('Re-assosiated with {}'.format(self.ssid))

    def retry_get(self, url):
        """
        :param url: string of a url to fetch
        :return: data if it works, raises error if not
        """
        for i in range(5):
            try:
                data = requests.get(url)
                return data
            except:
                self.log.warn('Get failed for {} try number {}'.format(url, i))
                time.sleep(3)

        raise ConnectionError

    def get_redirect(self):
        """
        :return: url of the page redirected to from wpad
        """
        wpad_data = self.retry_get('http://wpad.{}'.format(self.info['domain']))

        if wpad_data.status_code != 200:
            self.log.error('Failed to retrieve wpad from {}'.format(self.info['domain']))
            sys.exit()

        so = soup.BeautifulSoup(wpad_data.content, 'lxml')

        self.info['url'] = so.find('meta', attrs={'http-equiv': 'refresh'})['content'].partition('=')[2]

        self.log.info('Found redirect url: {}'.format(self.info['url']))

    def login(self):
        """
        :return: Status code for our post to the login page
        """
        logon_page = self.retry_get(self.info['url'])

        so2 = soup.BeautifulSoup(logon_page.content, 'lxml')

        form = so2.find('form')

        post_data = form.find_all('input', attrs={'type': 'hidden'})

        post_dict = {}
        for entry in post_data:
            post_dict[entry['name']] = entry['value']

        self.log.debug('Login form data: {}'.format(post_dict))

        return requests.post(form['action'], data=post_dict).status_code

    def get_config(self):
        try:
            with open('conf.json', 'r') as f:
                self.config = json.load(f)
            self.ssid = self.config['ssid']
            self.limit = self.config['MB_limit']
            self.time_limit = self.config['TIME_limit']
            self.interface = self.config['interface']
            self.domain = self.config['domain']

        except Exception as e:
            sys.exit(e)

    def setup_logging(self):
        # Silence request module
        logging.getLogger("requests").setLevel(logging.WARNING)

        # Setup log vars
        self.log = logging.getLogger('')

        self.format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Main logger
        rootlogger = logging.getLogger()
        rootlogger.setLevel(logging.DEBUG)

        # Print to console
        consolehandler = logging.StreamHandler()
        consolehandler.setFormatter(self.format)
        rootlogger.addHandler(consolehandler)

        # Good to go
        self.log.debug('Logging setup complete')


if __name__ == '__main__':

    # Init class
    main = RollMac()

    # Loop forever
    while True:
        main.run()
