import requests, datetime, time, random, numpy, math, json, demjson
import utilities as u
import xml.etree.cElementTree as ET
import psutil
from lxml import etree
from concurrent import futures as cf
from functools import partial

class Initial(object):

    def __init__(self, sitemap, p):
        self.data = {}
        self.listDict = []

        self.s = requests.session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=2, max_retries=1)
        self.s.mount('https://', adapter)
        self.s.headers.update(u.headers)
        self.p = p
        self.proxies = u.parseProxies()

        self.ignoreKW = set('harvest,brain,acronym,sylvester,elliott,cap lx,ow ,off-,off white,jordan 11,track red,shattered,tekno,yeezy,calabasas,travis,kith,ape'.split(','))
        self.keywords = set(sitemap['keywords'].split(','))

        self.site = sitemap['sitemap']
        self.siteType = sitemap['siteType']
        self.endPoint = sitemap['end']

        self.atom = set('kith,pack,bdga,bape'.split(','))

    def getDatetime(self):
        return '[{}]'.format(str(datetime.datetime.now())[:-3])

    def threadPool(self, listDict):
        if self.listDict:
            cpu = psutil.cpu_count(logical=False)
            random.shuffle(self.proxies)
            self.proxies = numpy.array_split((self.proxies * math.ceil(len(listDict)/len(self.proxies))), cpu)
            listDict = numpy.array_split(listDict, cpu)
            with cf.ProcessPoolExecutor(cpu) as pool:
                for x in pool.map(self.doThreadPool, listDict, self.proxies):
                    self.data.update(x)

    def doThreadPool(self, keys, p):
        a = {}
        with cf.ThreadPoolExecutor() as pool:
            for x in pool.map(partial(self.getProductsInfo), keys, p):
                a[x['href']] = x
        return a

    # Parse DSM Data
    def getEflashData(self):
        try:

            with self.s as s:
                r = s.get(self.site, proxies={'https': self.p}, timeout=(5,5))
            r.raise_for_status()
            tree = etree.HTML(r.content)
            for products in tree.xpath('//div[@class="grid-view-item"]'):
                href = self.site + products.xpath('a/@href')[0]
                updated = None
                key = {'href': href, 'updated': updated}
                if key not in self.listDict:
                    self.listDict.append(key)

        except requests.HTTPError as e:
            print(self.getDatetime(), e)
            if r.status_code == 430:
                self.p = random.choice(u.proxies())
                self.getEflashData()
        except (requests.ReadTimeout, requests.ConnectionError) as e:
            print(self.getDatetime(), e)
            self.p = random.choice(u.proxies())
            self.getEflashData()
        except Exception as e:
            print(self.getDatetime(), self.site, e)

    # Parse Sitemap Data
    def getSitemapData(self):
        try:

            with self.s as s:
                r = s.get(self.site + 'sitemap_products_1.xml', proxies={'https': self.p}, timeout=(5,5))
            r.raise_for_status()
            tree = ET.fromstring(r.content)
            for child in tree[1:]:
                try:
                    title = child[3][1].text
                    if any(keyword in title.lower() for keyword in self.keywords) and not any(keyword in title.lower() for keyword in self.ignoreKW):
                        continue
                except:
                    pass
                href = child[0].text
                updated = child[1].text
                key = {'href': href, 'updated': updated}
                if key not in self.listDict:
                    self.listDict.append(key)

        except requests.HTTPError as e:
            print(self.getDatetime(), e)
            if r.status_code == 430:
                self.p = random.choice(u.proxies())
                self.getSitemapData()
        except (requests.Timeout, requests.ConnectionError) as e:
            print(self.getDatetime(), e)
            self.p = random.choice(u.proxies())
            self.getSitemapData()
        except Exception as e:
            print(self.getDatetime(), self.site, e)

    # Parse Atom data
    def getAtomData(self):
        try:

            with self.s as s:
                r = s.get(self.site + 'collections/all.atom', proxies={'https': self.p},timeout=(5,5))
            r.raise_for_status()
            tree = ET.fromstring(r.content)
            for child in tree[6:]:
                try:
                    title = child[4].text
                    if any(keyword in title.lower() for keyword in self.keywords) and not any(keyword in title.lower() for keyword in self.ignoreKW):
                        continue
                except:
                    pass
                href = child[3].get('href')
                updated = child[2].text
                key = {'href': href, 'updated': updated}
                if key not in self.listDict:
                    self.listDict.append(key)

        except requests.HTTPError as e:
            print(self.getDatetime(), e)
            if r.status_code == 430:
                self.p = random.choice(u.proxies())
                self.getAtomData()
        except (requests.Timeout, requests.ConnectionError) as e:
            print(self.getDatetime(), e)
            self.p = random.choice(u.proxies())
            self.getAtomData()
        except Exception as e:
            print(self.getDatetime(), self.site, e)

    # Parse Product Json Data
    def getProductJsonData(self):
        try:

            with self.s as s:
                r = s.get(self.site + 'products.json', proxies={'https': self.p}, timeout=(5,5))
            r.raise_for_status()
            for products in r.json()['products']:
                title = products['title']
                if any(keyword in title.lower() for keyword in self.keywords) and not any(keyword in title.lower() for keyword in self.ignoreKW):
                    continue
                href = '{}products/{}'.format(self.site, products['handle'])
                updated = products['updated_at']
                key = {'href': href, 'updated': updated}
                if key not in self.listDict:
                    self.listDict.append(key)

        except requests.HTTPError as e:
            print(self.getDatetime(), e)
            if r.status_code == 430:
                self.p = random.choice(u.proxies())
                self.getProductJsonData()
        except (requests.Timeout, requests.ConnectionError) as e:
            print(self.getDatetime(), e)
            self.p = random.choice(u.proxies())
            self.getProductJsonData()
        except Exception as e:
            print(self.getDatetime(), self.site, e)

    def getProductJson2Data(self):
        try:

            with self.s as s:
                r = s.get(self.site + 'products.json?limit=250', proxies={'https': self.p}, timeout=(5,5))
            r.raise_for_status()
            for products in r.json()['products']:
                title = products['title']
                if any(keyword in title.lower() for keyword in self.keywords) and not any(keyword in title.lower() for keyword in self.ignoreKW):
                    continue
                href = '{}products/{}'.format(self.site, products['handle'])
                updated = products['updated_at']
                vendor = products['vendor'].lower()
                stockCount = 'IN STOCK/HIDDEN' if [avail['available'] for avail in products['variants'] if avail['available']] \
                            else 'OOS/HIDDEN'
                self.data[href] = {'href': href, 'updated': updated, 'vendor': vendor, 'stockCount': stockCount}

        except requests.HTTPError as e:
            print(self.getDatetime(), e)
            if r.status_code == 430:
                self.p = random.choice(u.proxies())
                self.getProductJson2Data()
        except (requests.Timeout, requests.ConnectionError) as e:
            print(self.getDatetime(), e)
            self.p = random.choice(u.proxies())
            self.getProductJson2Data()
        except Exception as e:
            print(self.getDatetime(), self.site, e)

    # Parse Inventory of Hidden Inventory Sites
    def getHiddenProductsInfo(self, key, p):
        href = key['href']
        updated = key['updated']

        try:

            sites = self.s.get(href, proxies={'https': p}, timeout=3)
            sites.raise_for_status()

            if self.site in ['https://lessoneseven.com/', 'https://www.thegoodlifespace.com/']:
                r = [line for line in sites.text.split('\n') if '{&quot' in line]
            else:
                r = [line for line in sites.text.split('\n') if '{"id"' in line]

            if 'trophyroomstore.com' in self.site:
                r = r[4].split(' = ')[1][:-1]

            elif 'thedarksideinitiative.com' in self.site:
                r = r[3].split(' = ')[1].replace(';</script>', '')

            elif 'featuresneakerboutique.com' in self.site:
                r = r[2].replace('product: ', '').strip()[:-1]
                if ' = ' in r:
                    r = r.split(' = ')[1]

            elif 'notre-shop.com' in self.site or 'alifenewyork.com' in self.site:
                r = r[2].replace('product: ', '').strip()[:-1]

            elif 'blendsus.com' in self.site:
                r = r[2].split('product: ')[1].replace(', onVariantSelected:', '')

            elif 'octobersveryown.com' in self.site:
                r = r[2].split(' = ')[1].strip()[:-1]

            elif 'undefeated.com' in self.site:
                r = r[2].split('product = ')[1].strip()[:-1]

            elif 'xhibition.co' in self.site:
                r = r[3]

            elif 'hanon-shop.com' in self.site:
                r = r[2].split('{ product: ')[1].split(', onV')[0]

            elif 'thegoodlifespace.com' in self.site:
                r = r[0].split('="')[1].split('"')[0].replace('&quot;', '"')

            elif 'lessoneseven.com' in sites.url:
                r = r[0].split('"')[1].replace('&quot;', '"')

            elif 'doverstreetmarket.com' in self.site or 'deadstock.ca' in self.site or 'stashedsf.com' in self.site or \
                    'worldofhombre.com' in self.site:
                r = r[2]

            r = json.loads(r)
            stockCount = sum(variant['inventory_quantity'] for variant in r['variants'] if variant['inventory_quantity'] >= 1)
            vendor = r['vendor'].lower()

        except IndexError as e:
            print(self.getDatetime(), key['href'], e)
            vendor = 'error'
            stockCount = 0
        except Exception as e:
            print(self.getDatetime(), e)
            vendor = 'error'
            stockCount = 0

        return {'href': href, 'updated': updated, 'vendor': vendor, 'stockCount': stockCount}

    # Parse Hidden Inventory Site
    def getHiddenStockSitesInfo(self, key, p):
        href = key['href']
        updated = key['updated']

        try:

            sites = self.s.get(href, proxies={'https': p}, timeout=3)
            sites.raise_for_status()

            r = [line for line in sites.text.split('\n') if '{"id"' in line]

            if 'kith.com' in self.site:
                r = r[2][:-1]

            elif 'hannibalstore.it' in self.site:
                r = r[2]

            elif 'lustmexico.com' in self.site:
                r = r[2].replace('"product" : ', '')
                print(r)

            r = json.loads(r)
            stockCount = 'IN STOCK/HIDDEN' if r['available'] else 'OOS/HIDDEN'
            vendor = r['vendor'].lower()

        except IndexError as e:
            print(self.getDatetime(), key['href'], e)
            vendor = 'error'
            stockCount = 0
        except Exception as e:
            print(self.getDatetime(), e)
            vendor = 'error'
            stockCount = 'OOS/HIDDEN'

        return {'href': href, 'updated': updated, 'vendor': vendor, 'stockCount': stockCount}

    # Convert Parse Script To Dict
    def convertJStoDict(self, r):
        tree = etree.HTML(r.content)
        x = tree.xpath('//div[@id="js-content"]/script/text()')[0].split('p = ')[1].split('\n\n')[0].split(';')[0]
        product = demjson.decode(x)
        return product

    # Parse JS/Script of Hidden Sites
    def getJsSite(self, key, p):
        href = key['href']
        updated = key['updated']

        try:

            sites = self.s.get(href, proxies={'https': p}, timeout=3)
            sites.raise_for_status()

            r = self.convertJStoDict(sites)
            stockCount = 'IN STOCK/HIDDEN' if r['available'] else 'OOS/HIDDEN'
            vendor = r['vendor'].lower()

        except IndexError as e:
            print(self.getDatetime(), key['href'], e)
            vendor = 'error'
            stockCount = 'OOS/HIDDEN'
        except Exception as e:
            print(self.getDatetime(), e)
            vendor = 'error'
            stockCount = 'OOS/HIDDEN'

        return {'href': href, 'updated': updated, 'vendor': vendor, 'stockCount': stockCount}

    # Parse Products of Any Sites
    def getProductsInfo(self, key, p):
        href = key['href']
        updated = key['updated']

        if self.siteType == 1:
            return self.getHiddenProductsInfo(key, p)

        elif self.siteType == 2:
            return self.getHiddenStockSitesInfo(key, p)

        else:
            try:

                sites = self.s.get(href + '.json', proxies={'https': p}, timeout=3)
                sites.raise_for_status()

                vendor = sites.json()['product']['vendor'].lower()
                try:
                    stockCount = sum(variant['inventory_quantity'] for variant in sites.json()['product']['variants'] if variant['inventory_quantity'] >= 1)
                except:
                    stockCount = 'HIDDEN'

            except Exception as e:
                print(self.getDatetime(), e)
                vendor = 'error'
                stockCount = 0

            return {'href': href, 'updated': updated, 'vendor': vendor, 'stockCount': stockCount}

    def sendSites(self):
        try:
            if not self.endPoint:
                self.getEflashData()
                self.threadPool(self.listDict)
                return self.data

            elif 'xml' == self.endPoint:
                if any(site in self.site for site in self.atom):
                    self.getAtomData()
                else:
                    self.getProductJsonData()
                self.getSitemapData()
                self.threadPool(self.listDict)
                return self.data

            elif 'atom' == self.endPoint:
                self.getAtomData()
                self.threadPool(self.listDict)
                return self.data

            elif 'json' == self.endPoint:
                self.getProductJsonData()
                self.threadPool(self.listDict)
                return self.data

            elif 'json2' == self.endPoint:
                self.getProductJson2Data()
                return self.data
        except Exception as e:
            print(u.getDatetime(), self.site, e)