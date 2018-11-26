import datetime, time, json, random, numpy
import utilities as u
from initial import Initial
from current import Current
from multiprocessing import Process

if __name__ == '__main__':

    proxies = u.proxies()
    random.shuffle(proxies)

    with open('sites.json') as sitemaps_json:
        start = time.time()
        print("Attempting to initialize sitemap data...")
        sitemaps = json.load(sitemaps_json)
        sitemaps_length = len(sitemaps['sitemaps'])
        print(str(sitemaps_length) + " sitemap(s) detected.")
        data = [0 for x in range(sitemaps_length)]

    for i in range(sitemaps_length):
        try:
            data[i] = Initial(sitemaps['sitemaps'][i], proxies[i]).sendSites()
            print(u.getDatetime(), i, 'Initialized {}'.format(sitemaps['sitemaps'][i]['sitemap']), len(data[i]))
            # print(data[i])
        except Exception as e:
            print(e)
    print("Sitemap data initialized.")
    print(time.time()-start)

    try:

        for i in range(sitemaps_length):
            Process(target=ShopifyMonitor(data[i], sitemaps['sitemaps'][i]).run, name=sitemaps['sitemaps'][i]['name']).start()

    except Exception as E:
        print(u.getDatetime(), 'Run Error:', E)
