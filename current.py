import requests, json, demjson, time, numpy, random
import utilities as u
import lxml.etree as etree
import xml.etree.cElementTree as ET
from uuid import uuid4
from concurrent import futures as cf
from slack import Slack
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# import logging
# logging.basicConfig(format="%(asctime)-15s %(message)s",level=logging.DEBUG,datefmt='%Y-%m-%d %H:%M:%S')

class Current():

    def __init__(self, data, sitemap):
        self.data = data

        self.s = requests.session()
        self.s.cookies.set_policy(u.BlockAll())
        self.s.headers.update(u.headers)
        self.s.verify = False
        adapter = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=25, pool_block=True)
        self.s.mount('https://', adapter)

        self.infoP = u.getInfoProxy()
        self.pList = u.proxies()
        random.shuffle(self.pList)
        self.p = self.pList[0]
        self.count = 1
        self.badP = None

        self.site = sitemap['sitemap']
        self.siteType = sitemap['siteType']
        self.endPoint = sitemap['end']
        self.name = sitemap['name']
        self.currency = sitemap['currency']
        self.taskBot = sitemap['task']

        self.atom = 'kith,pack,bdga,bape'.split(',')
        if not sitemap['brands']:
            self.brands = sitemap['brands'].split(',')
        else:
            self.brands = 'error,shopify,release,draw,nike,jordan,adidas,yeezy,converse,vans,puma,asics,diadora,palace,ape'.split(',')
            self.brands.extend(sitemap['brands'].split(','))
        self.ignoreKW = 'brain,acronym,sylvester,elliott,cap lx,ow ,off-,off white,jordan 11,track red,shattered,tekno,yeezy,calabasas,travis,kith,ape'.split(',')
        self.keywords = set(sitemap['keywords'].split(','))

    def checkEflashIfOos(self, tree):
        for products in tree.xpath('//div[@class="grid-view-item product-price--sold-out grid-view-item--sold-out"]'):
            href = self.site + products.xpath('a/@href')[0]
            if href in self.data:
                self.data.pop(href)

    def getEflashData(self):
        try:
            r = self.s.get(self.site + f'?_={uuid4().hex}', proxies={'https': 'http://{}'.format(self.p)}, timeout=(1,5))
            r.raise_for_status()

            tree = etree.HTML(r.content)
            self.checkEflashIfOos(tree)

            for products in tree.xpath('//div[@class="grid-view-item"]'):
                href = self.site + products.xpath('a/@href')[0]
                updated = None
                if href not in self.data:
                    self.data[href] = {'href': href, 'updated': updated}
                    key = {'href': href, 'updated': updated, 'oldStockCount': 'NEW'}
                    cf.ThreadPoolExecutor().submit(self.getVendorAndStock, key, random.choice(self.infoP)).add_done_callback(self.callback)
        except (requests.Timeout, requests.ConnectionError):
            pass
        except requests.HTTPError:
            if r.status_code == 430:
                self.badP = self.p
        except Exception as e:
            print(u.getDatetime(), self.site, e)

    def getKith429(self):
        try:
            r = self.s.get(self.site + f'collections/sneakers.atom?_={uuid4().hex}', proxies={'https': 'http://{}'.format(self.p)}, timeout=(1,5))
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
                if href in self.data:
                    if updated > self.data[href]['updated']:
                        self.data[href]['updated'] = updated
                        key = {'href': href, 'updated': updated, 'vendor': self.data[href]['vendor'], 'oldStockCount': self.data[href]['stockCount']}
                        cf.ThreadPoolExecutor().submit(self.getVendorAndStock, key, random.choice(self.infoP)).add_done_callback(self.callback)
                else:
                    self.data[href] = {'href': href, 'updated': updated}
                    key = {'href': href, 'updated': updated, 'oldStockCount': 'NEW'}
                    cf.ThreadPoolExecutor().submit(self.getVendorAndStock, key, random.choice(self.infoP)).add_done_callback(self.callback)
        except (requests.Timeout, requests.ConnectionError):
            pass
        except requests.HTTPError:
            if r.status_code == 430:
                self.badP = self.p
        except Exception as e:
            print(u.getDatetime(), self.site, e)

    def getSitemapData(self):
        try:
            r = self.s.get(self.site + f'sitemap_products_1.xml?_={uuid4().hex}', proxies={'https': 'http://{}'.format(self.p)}, timeout=(1,5))
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
                if href in self.data:
                    if updated > self.data[href]['updated']:
                        self.data[href]['updated'] = updated
                        key = {'href': href, 'updated': updated, 'vendor': self.data[href]['vendor'], 'oldStockCount': self.data[href]['stockCount']}
                        cf.ThreadPoolExecutor().submit(self.getVendorAndStock, key, random.choice(self.infoP)).add_done_callback(self.callback)
                else:
                    self.data[href] = {'href': href, 'updated': updated}
                    key = {'href': href, 'updated': updated, 'oldStockCount': 'NEW'}
                    cf.ThreadPoolExecutor().submit(self.getVendorAndStock, key, random.choice(self.infoP)).add_done_callback(self.callback)
        except (requests.Timeout, requests.ConnectionError) as e:
            pass
        except requests.HTTPError:
            if r.status_code == 429 and 'kith' in self.site:
                self.getKith429()
            elif r.status_code == 430:
                self.badP = self.p
        except Exception as e:
            print(u.getDatetime(), self.site, e)

    def getAtomData(self):
        try:
            r = self.s.get(self.site + f'collections/all.atom?_={uuid4().hex}', proxies={'https': 'http://{}'.format(self.p)}, timeout=(1,5))
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
                if href in self.data:
                    if updated > self.data[href]['updated']:
                        self.data[href]['updated'] = updated
                        key = {'href': href, 'updated': updated, 'vendor': self.data[href]['vendor'], 'oldStockCount': self.data[href]['stockCount']}
                        cf.ThreadPoolExecutor().submit(self.getVendorAndStock, key, random.choice(self.infoP)).add_done_callback(self.callback)
                else:
                    self.data[href] = {'href': href, 'updated': updated}
                    key = {'href': href, 'updated': updated, 'oldStockCount': 'NEW'}
                    cf.ThreadPoolExecutor().submit(self.getVendorAndStock, key, random.choice(self.infoP)).add_done_callback(self.callback)
        except (requests.Timeout, requests.ConnectionError) as e:
            pass
        except requests.HTTPError:
            if r.status_code == 430:
                self.badP = self.p
        except Exception as e:
            print(u.getDatetime(), self.site, e)

    def getProductJsonData(self):
        try:
            r = self.s.get(self.site + f'products.json?_={uuid4().hex}', proxies={'https': 'http://{}'.format(self.p)}, timeout=(1,1))
            r.raise_for_status()

            for products in r.json()['products']:
                title = products['title']
                if any(keyword in title.lower() for keyword in self.keywords) and not any(keyword in title.lower() for keyword in self.ignoreKW):
                    continue
                href = '{}products/{}'.format(self.site, products['handle'])
                updated = products['updated_at']
                if href in self.data:
                    if updated > self.data[href]['updated']:
                        self.data[href]['updated'] = updated
                        key = {'href': href, 'updated': updated, 'vendor': self.data[href]['vendor'], 'oldStockCount': self.data[href]['stockCount']}
                        cf.ThreadPoolExecutor().submit(self.getVendorAndStock, key, random.choice(self.infoP)).add_done_callback(self.callback)
                else:
                    self.data[href] = {'href': href, 'updated': updated}
                    key = {'href': href, 'updated': updated, 'oldStockCount': 'NEW'}
                    cf.ThreadPoolExecutor().submit(self.getVendorAndStock, key, random.choice(self.infoP)).add_done_callback(self.callback)
        except (requests.Timeout, requests.ConnectionError) as e:
            pass
        except requests.HTTPError:
            if r.status_code == 430:
                self.badP = self.p
        except Exception as e:
            print(u.getDatetime(), self.site, e)

    def getProductJson2Data(self, page):
        try:
            r = self.s.get(self.site + f'products.json?page={str(page)}&_={uuid4().hex}', proxies={'https': 'http://{}'.format(self.p)}, timeout=(1,1))
            r.raise_for_status()

            for products in r.json()['products']:
                title = products['title']
                if any(keyword in title.lower() for keyword in self.keywords) and not any(keyword in title.lower() for keyword in self.ignoreKW):
                    continue
                href = '{}products/{}'.format(self.site, products['handle'])
                updated = products['updated_at']
                vendor = products['vendor'].lower()
                stockCount = 'IN STOCK/HIDDEN' if [avail['available'] for avail in products['variants'] if avail['available']] else 'OOS/HIDDEN'
                if href in self.data:
                    if updated > self.data[href]['updated']:
                        self.data[href]['updated'] = updated
                        if self.data[href]['stockCount'] == 'OOS/HIDDEN' and stockCount == 'IN STOCK/HIDDEN':
                            if any(brand in vendor for brand in self.brands) or len(vendor) < 3:
                                cf.ThreadPoolExecutor().submit(self.sendToSlack, href, updated, products, stockCount, vendor)
                        self.data[href]['stockCount'] = stockCount
                else:
                    self.data[href] = {'href': href, 'updated': updated, 'vendor': vendor, 'stockCount': stockCount}
                    if (any(brand in vendor for brand in self.brands) or len(vendor) < 3) and updated.split('T')[0] >= u.getDate():
                        cf.ThreadPoolExecutor().submit(self.sendToSlack, href, updated, products, stockCount, vendor)
        except (requests.Timeout, requests.ConnectionError) as e:
            pass
        except requests.HTTPError:
            if r.status_code == 430:
                self.badP = self.p
        except Exception as e:
            print(u.getDatetime(), self.site, e)

    def keyChange(self, key, p):
        oldStockCount = key['oldStockCount']

        if any(brand in key['vendor'] for brand in self.brands) or len(key['vendor']) < 3:

            if self.siteType == 1:
                return self.getHiddenSites(key, oldStockCount, p)
            if self.siteType == 2:
                return self.getHiddenStockSites(key, oldStockCount, p)
            if oldStockCount != 'HIDDEN':
                return self.getProdInfo(key, oldStockCount, p)
            else:
                key['stockCount'] = key.pop('oldStockCount')
                return key
        else:
            key['stockCount'] = key.pop('oldStockCount')
            return key

    def newKeyData(self, key, p):
        oldStockCount = 'NEW'

        if self.siteType == 1:
            return self.getHiddenSites(key, oldStockCount, p)
        if self.siteType == 2:
            return self.getHiddenStockSites(key, oldStockCount, p)
        else:
            return self.getProdInfo(key, oldStockCount, p)

    def getVendorAndStock(self, key, p):
        if key['oldStockCount'] != 'NEW':
            return self.keyChange(key, p)
        else:
            return self.newKeyData(key, p)

    def getProdInfo(self, key, oldStockCount, p):
        try:
            sites = self.s.get(key['href'] + f'.json?_={uuid4().hex}', proxies={'https': 'http://{}'.format(p)}, timeout=5)
            sites.raise_for_status()

            vendor = sites.json()['product']['vendor'].lower()
            try:
                stockCount = sum(variant['inventory_quantity'] for variant in sites.json()['product']['variants'] if variant['inventory_quantity'] >= 1)
            except:
                stockCount = 'HIDDEN'

            if (oldStockCount == 0 and stockCount >= 1) or oldStockCount == 'HIDDEN':
                self.sendToSlack(key['href'], key['updated'], sites.json(), stockCount, vendor)
            elif oldStockCount == 'NEW':
                if (any(brand in vendor for brand in self.brands) or len(vendor) < 3) and key['updated'].split('T')[0] >= u.getDate():
                    self.sendToSlack(key['href'], key['updated'], sites.json(), stockCount, vendor)

            return {'href': key['href'], 'updated': key['updated'], 'vendor': vendor, 'stockCount': stockCount}

        except requests.HTTPError as e:
            print(u.getDatetime(), e)
            if sites.status_code == 430:
                return self.getProdInfo(key, oldStockCount, random.choice(u.getInfoProxy()))
            if sites.status_code == 404:
                return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 0}
            else:
                return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 0 if oldStockCount == 'NEW' else oldStockCount}
        except IndexError as e:
            print(u.getDatetime(), key['href'], e)
            return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 0 if oldStockCount == 'NEW' else oldStockCount}
        except Exception as e:
            print(u.getDatetime(), p, e)
            return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 0 if oldStockCount == 'NEW' else oldStockCount}

    def getHiddenSites(self, key, oldStockCount, p):
        try:
            sites = self.s.get(key['href'] + f'?_={uuid4().hex}', proxies={'https': 'http://{}'.format(p)}, timeout=5)
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

            elif 'doverstreetmarket.com' in self.site or 'deadstock.ca' in self.site or 'stashedsf.com' in self.site or\
                    'worldofhombre.com' in self.site:
                r = r[2]

            r = json.loads(r)
            vendor = r['vendor'].lower()
            stockCount = sum(variant['inventory_quantity'] for variant in r['variants'] if variant['inventory_quantity'] >= 1)

            if oldStockCount == 0 and stockCount >= 1:
                self.sendToSlack(key['href'], key['updated'], r, stockCount, vendor)

            elif oldStockCount == 'NEW':
                if not self.endPoint or ((any(brand in vendor for brand in self.brands) or len(vendor) < 3) and key['updated'].split('T')[0] >= u.getDate()):
                    self.sendToSlack(key['href'], key['updated'], r, stockCount, vendor)

            return {'href': key['href'], 'updated': key['updated'], 'vendor': vendor, 'stockCount': stockCount}

        except requests.HTTPError as e:
            print(u.getDatetime(), e)
            if sites.status_code == 430:
                self.getHiddenSites(key, oldStockCount, random.choice(u.getInfoProxy()))
            if sites.status_code == 404:
                return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 0}
            else:
                return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 0 if oldStockCount == 'NEW' else oldStockCount}
        except IndexError as e:
            print(u.getDatetime(), key['href'], e)
            return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 0 if oldStockCount == 'NEW' else oldStockCount}
        except Exception as e:
            print(u.getDatetime(), p, e)
            return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 0 if oldStockCount == 'NEW' else oldStockCount}

    def getHiddenStockSites(self, key, oldStockCount, p):
        try:
            sites = self.s.get(key['href'] + f'?_={uuid4().hex}', proxies={'https': 'http://{}'.format(p)}, timeout=5)
            sites.raise_for_status()

            r = [line for line in sites.text.split('\n') if '{"id"' in line]
            if 'kith.com' in self.site:
                r = r[2][:-1]
            r = json.loads(r)
            vendor = r['vendor'].lower()
            stockCount = 'IN STOCK/HIDDEN' if r['available'] else 'OOS/HIDDEN'

            if oldStockCount == 'OOS/HIDDEN' and stockCount == 'IN STOCK/HIDDEN':
                self.sendToSlack(key['href'], key['updated'], r, stockCount, vendor)
            elif oldStockCount == 'NEW':
                if (any(brand in vendor for brand in self.brands) or len(vendor) < 3) and key['updated'].split('T')[0] >= u.getDate():
                    self.sendToSlack(key['href'], key['updated'], r, stockCount, vendor)

            return {'href': key['href'], 'updated': key['updated'], 'vendor': vendor, 'stockCount': stockCount}

        except requests.HTTPError as e:
            print(u.getDatetime(), e)
            if sites.status_code == 430:
                return self.getHiddenStockSites(key, oldStockCount, random.choice(u.getInfoProxy()))
            if sites.status_code == 404:
                return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 'OOS/HIDDEN'}
            else:
                return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 'OOS/HIDDEN' if oldStockCount == 'NEW' else oldStockCount}
        except IndexError as e:
            print(u.getDatetime(), key['href'], e)
            return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 'OOS/HIDDEN' if oldStockCount == 'NEW' else oldStockCount}
        except Exception as e:
            print(u.getDatetime(), p, e)
            return {'href': key['href'], 'updated': key['updated'], 'vendor': 'error', 'stockCount': 'OOS/HIDDEN' if oldStockCount == 'NEW' else oldStockCount}

    def sendToSlack(self, href, updated, r, stockCount, vendor):
        variants_data = []
        name = self.name

        if not self.siteType:
            r = r['product']
            try:
                src = r['image']['src']
            except:
                src = None
        elif self.endPoint == 'json2':
            try:
                src = r['images'][0]['src']
            except:
                src = None
        else:
            try:
                src = 'https:' + r['images'][0]
            except:
                src = None

        title = r['title']

        if self.currency == 'USD':
            price = '$' + str(r['variants'][0]['price']).replace('.', '')[:-2]
        elif self.currency == 'AED':
            price = str(r['variants'][0]['price']).replace('.', '')[:-2] + ' AED'
        else:
            price = u.convertCurrency(str(r['variants'][0]['price']).replace('.', '')[:-2], self.currency)

        for variants in r['variants']:
            variants_id = variants['id']
            variants_size = variants['title']

            if stockCount == 0 or stockCount == 'OOS/HIDDEN':
                atc_link = '{}[{}]'.format(variants_size, variants_id)
                variants_data.append(atc_link)
            elif stockCount == 'HIDDEN':
                atc_link = '<{}cart/{}:1|{}_ATC>'.format(self.site, variants_id, variants_size)
                variants_data.append(atc_link)
            elif self.siteType in [2, 3, 4, 5]:
                if variants['available']:
                    atc_link = '<{}cart/{}:1|{}_ATC>'.format(self.site, variants_id, variants_size)
                    variants_data.append(atc_link)
            else:
                variants_qty = variants['inventory_quantity']
                if variants_qty >= 1:
                    atc_link = '<{}cart/{}:1|{}_ATC /> {}'.format(self.site, variants_id, variants_size, variants_qty)
                    variants_data.append(atc_link)

            split = numpy.array_split(variants_data, 2)
            atc_link = '\n\n'.join(split[0])
            atc_link1 = '\n\n'.join(split[1])

        Slack().mainSlack(href, title, price, updated, name, src, vendor, atc_link, atc_link1, stockCount, self.taskBot, self.siteType)

    def callback(self, x):
        try:
            self.data[x.result()['href']] = x.result()
        except:
            print(u.getDatetime(), self.site, 'CF callback exception.')

    def misc(self):
        if self.badP:
            #print(u.getDatetime(), self.site, self.p, 430)
            self.badP = None
            self.s.close()
            self.proxyRotation()

    def proxyRotation(self):
        if self.count >= len(self.pList):
            self.count = 0
        self.p = self.pList[self.count]
        self.count += 1

    def runEflash(self):
        self.getEflashData()

    def runSitemap(self):
        with cf.ThreadPoolExecutor(max_workers=2) as thread:
            if any(site in self.site for site in self.atom):
                thread.submit(self.getAtomData)
            else:
                thread.submit(self.getProductJsonData)
            thread.submit(self.getSitemapData)

    def runAtom(self):
        self.getAtomData()

    def runJson(self):
        self.getProductJsonData()

    def runJson2(self):
        if self.siteType in [3, 5]:
            self.getProductJson2Data(None)
        else:
            with cf.ThreadPoolExecutor(5) as thread:
                thread.map(self.getProductJson2Data, range(1, 6))

    def run(self):
        if not self.endPoint:
            methodToRun = self.runEflash
        elif self.endPoint == 'xml':
            methodToRun = self.runSitemap
        elif self.endPoint == 'atom':
            methodToRun = self.runAtom
        elif self.endPoint == 'json':
            methodToRun = self.runJson
        elif self.endPoint == 'json2':
            methodToRun = self.runJson2

        while True:
            try:
                methodToRun()
                self.misc()
            except Exception as e:
                print(u.getDatetime(), self.site, e)
