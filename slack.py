import datetime
from slackclient import SlackClient
from twitter import Twitter
from threading import Thread

class Slack(object):

    def __init__(self):
        self.slack = SlackClient('enter your slack bot token key')

    def mainSlack(self, href, title, price, updated, name, src, vendor, atc, atc1, stockCount, taskBot, siteType):
        # Thread(target=Twitter().twitterNotify, args=(data,)).start()

        ## These need to be updated based on your needs
        if siteType == 5:
            channel = '#bot'
        elif 'bape' in vendor:
            channel = '#bape'
        elif stockCount == 0 or stockCount == 'OOS/HIDDEN':
            channel = '#oos'
        elif 'SG' in name:
            channel = '#dsm-sg'
        else:
            channel = '#shopify_monitor'

        try:
            self.slack.api_call(
                "chat.postMessage",
                channel='shopify_test',
                username=name,
                icon_url='http://i.imgur.com/zks3PoZ.png',
                attachments=[
                    {
                        'fallback': '{}: [{}] {}'.format(name, stockCount, title),
                        'title': title,
                        'title_link': href,
                        'color': 'ff2700' if channel == '#oos' else '#36a64f',
                        'mrkdwn_in': ["fields"],
                        'fields': [
                            {
                                'title': 'Site',
                                'value': name,
                                'short': True
                            },
                            {
                                'title': 'Vendor',
                                'value': vendor.upper(),
                                'short': True
                            },
                            {
                                'title': 'Stock Count',
                                'value': stockCount,
                                'short': True
                            },
                            {
                                'title': 'Price',
                                'value': price,
                                'short': True
                            },
                            {
                                'title': 'Add Cart Links',
                                'text': 'Test',
                                'value': atc,
                                'short': True
                            },
                            {
                                'title': 'Add Cart Links',
                                'text': 'Test',
                                'value': atc1,
                                'short': True
                            },
                            {
                                'title': '-',
                                'text': 'Test',
                                'value': '',
                                'short': True
                            }
                        ],
                        'actions': [
                            {
                                'type': 'button',
                                'text': 'CyberAIO',
                                'url': 'https://cybersole.io/dashboard/quicktask?url={}'.format(href),
                                'style': 'primary'
                            },
                            {
                                'type': 'button',
                                'text': 'Project Destroyer',
                                'url': 'destroyer://{}'.format(href),
                                'style': 'primary'
                            },
                            {
                                'type': 'button',
                                'text': 'TaskBot',
                                'url': 'taskbot://startTask?store={}&url={}'.format(taskBot, href) if taskBot else None,
                                'style': 'primary'
                            }
                        ],
                        'footer': '{}|{} EST'.format(updated, datetime.datetime.now().strftime('%m-%d-%y %X')),
                        'thumb_url': src
                    }
                ]
            )
        except Exception as E:
            print(E)
        data = '{}\n{}\n{}\n{}\nSlack: {} EST'.format(href, title, price, updated, datetime.datetime.now().strftime('%m-%d-%y %X'))
        print("Change detected: " + data, '\n')
