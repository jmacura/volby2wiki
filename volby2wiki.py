# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# @author jmacura 2018
from bs4 import BeautifulSoup
import datetime
from pprint import pprint
#import mwparserfromhell as mwp
import ssl
import sys
import time
import urllib.request, urllib.parse, urllib.error

# Global variable
nuts = None
obec = None
zkr = None

# Parse command line params
usage = """Usage: volby2wiki.py -nuts kodNuts -obec kodObec [-zkr zkratkaObce]
Options:
  -nuts  Kód NUTS kraje
  -obec  Kód obce
  -zkr   Zkratka obce pro použití v názvu reference
"""
if len(sys.argv) > 4 and len(sys.argv) < 8:
    nuts = sys.argv[2]
    obec = sys.argv[4]
    if len(sys.argv) == 7:
        zkr = sys.argv[6]
else:
    print(usage)
    quit()

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

#Now hard-coded, but changeable in future
#serviceurl = 'https://volby.cz/pls/kv2018/kv1111?xjazyk=CZ&xid=1&xdz=3&xnumnuts=3203&xobec=554791&xstat=0&xvyber=0'
serviceurl = 'https://volby.cz/pls/kv2018/kv1111?' #?xjazyk=CZ&xid=1&xdz=3&xnumnuts=4102&xobec=554961&xstat=0&xvyber=0
def getPageContent():
    params = {'xjazyk': 'CZ',
       'xid': '1',
       'xdz': '3',
       'xnumnuts': nuts if nuts is not None else 3203,
       'xobec': obec if obec is not None else 554791,
       'xstat': 0,
       'xvyber': 0}
    url = serviceurl + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header('User-Agent', "volby2wiki/dev (jan.macura@wikimedia.cz)")
    print('Retrieving', url)
    try:
        data = urllib.request.urlopen(req, context=ctx).read()
    except (TimeoutError, urllib.error.URLError):
        print("Request timed out")
        return "timeout", url
    print('Retrieved', len(data), 'characters')
    return data, url

def parsePage(text):
    content = soup.find(id="publikace").find_all('table')
    data_row = content[0].find_all('tr')[2].find_all('td')
    #(pocet clenu, volebni ucast, platne hlasy)
    stats = (int(data_row[0].string), float(data_row[7].string.replace(",", '.')), int(str(data_row[9].string).replace("\xa0", '')))
    pprint(stats)

    data_block = content[1].find_all('tr')
    party_data = []
    for i, row in enumerate(data_block):
        if i > 1:
            data_row = row.find_all('td')
            #(nazev, hlasy absolutne, hlasy procenta, mandaty)
            party_data.append( (
                data_row[1].string,
                int(data_row[2].string.replace("\xa0", '')),
                float(data_row[3].string.replace(",", '.')),
                int(data_row[7].string)
            ) )
    pprint(party_data)
    return stats, party_data

print("Dialing the page...")
html, fullurl = getPageContent()
print("Parsing the page...")
soup = BeautifulSoup(html, 'html.parser')
stats, party_data = parsePage(soup)
print()
party_data.sort(reverse = True, key = lambda t: t[1])
pprint(party_data)

filename = (zkr if zkr is not None else "plzen") + ".txt"
with open(filename, 'w', encoding="utf-8") as fh:
    now = str(datetime.datetime.today())
    fh.write(
    """Volební účast v [[Plzeň|Plzni]] činila {0} %.<ref name="{1}18">{{{{Citace elektronické monografie
 | titul = Volby do zastupitelstev obcí 05.10. - 06.10.2018: Zastupitelstvo statutárního města: Plzeň
 | url = {2}
 | vydavatel = Český statistický úřad
 | datum přístupu = {3}
}}}}</ref>
\n""".format(str(stats[1]).replace(".", ','), zkr if zkr is not None else "plzen", fullurl, now.split()[0])
    )
    fh.write(
"""{{| class="wikitable sortable" style="text-align: right;"
|-
! rowspan="2" width="250" | Volební strana
! colspan="2" style="padding: 0 50px;" | Hlasy
! colspan="3" style="padding: 0 50px;" | Mandáty
|-
! počet
! v %
! data-sort-type="number" | 2018<ref name="{0}18" />
! data-sort-type="number" | [[Volby do zastupitelstev obcí v Česku 2014|2014]]
! data-sort-type="number" | bilance
""".format(zkr if zkr is not None else "plzen"))
    no_rest = 0
    rest = 0
    rest_p = 0.00
    for party in party_data:
        if party[2] < 3.00:
            no_rest += 1
            rest += party[1]
            rest_p += party[2]
        else:
            fh.write(
"""|-
| align="left" | [[{0}]]
| {{{{formatnum:{1}}}}}
| {2}
| {3}
|
|
""".format(party[0], party[1], str(party[2]).replace(".", ','), party[3])
            )
    fh.write(
    """|- class="sortbottom"
| align="left" | Ostatní celkem ({0} subjektů)
| {{{{formatnum:{1}}}}}
| {2}
| –
| –
| –
""".format(no_rest, rest, str(rest_p).replace(".", ','))
    )
    fh.write(
    """|- class="sortbottom"
! Celkem
! {{{{formatnum:{0}}}}}
! 100
! {1}
!
! –
|}}
""".format(stats[2], stats[0])
    )
print("File \"{}\" succesfully created".format(filename))

# fails = 0
# timeouts = 0
# t = time.time()
# if mod < 2:
#     i = 0
#         for row in reader(fh):
#             pageid = row[1] #56336 #29498 #4936 #67350
#             if pageid == "pageid":
#                 continue
#             i += 1
#             #if i > 1:
#                 #break # at least for testing
#             k = row[0][4:] #"amenity"
#             print("Item No. {}: {}".format(i, k))
#             if not rdflib.Literal(k) in g.objects(None, OSM.key):
#                 print("key {} is not in graph!".format(k))
#                 continue
#             print("Processing {}...".format(k))
#             key = rdflib.URIRef(OSMK + k.replace(':', "--"))
#             wikitext = getWikiInfo(pageid)
#             if not wikitext:
#                 fails += 1
#                 print("No wikitext to parse")
#                 continue
#             if wikitext == "timeout":
#                 timeouts += 1
#                 continue
#             req, group, wikidata, status, cartopic = parseWikitext(wikitext)
#             to_graph(key, req, group, wikidata, status, cartopic)
