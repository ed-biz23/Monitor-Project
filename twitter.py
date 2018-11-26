from twython import Twython
import time

class Twitter(object):

    def __init__(self):
        self.twitter = Twython('YPFktVAwuQWl27HISiBto7RYM', 'AIbpgtCZO9c1o8wI1srXmmRrcvhRnXW2foInmVWv0FvCbiCxWc',
                               '922266756466532353-XSDpuWWO5n9h2onBeHz9TDiJGBGFYxV', 'EyYBjpHixEtTsZAX6xkyRQGM5PO5UYUu09SubA9CcUzrp')

        self.twitterPvt = Twython('gGhnyoyKEAtlBD5gydIDqB2oe', 'lGbWyPxHedWoQK97eqpNXCvGJKkLgQ8lrxz2JeZ6WYCYtgln6p',
                                  '958904306266144768-mPteTdVqjiJMqygstyHttvguzsdtUb2', 'd0IZ5jwSVZcEDXv2hLZLsCcRVsGs2FbQ4KAZWP7vw6vdZ')

    def twitterNotify(self, data):
        try:
            self.twitterPvt.update_status(status=data)
        except:
            try:
                self.twitterPvt.update_status(status=data)
            except Exception as twitter_exception:
                print("Failed to send tweet: {}".format(twitter_exception))

    def pvTwitterNotify(self, data):
        time.sleep(15)
        try:
            self.twitter.update_status(status='{}\n15 sec delay'.format(data))
        except:
            try:
                self.twitter.update_status(status='{}\n15 sec delay'.format(data))
            except Exception as twitter_exception:
                print("Failed to send tweet: {}".format(twitter_exception))