import requests
import json
import math
from requests.auth import HTTPBasicAuth
import copy
from generateTitles import genTitles
import nltk
from collections import defaultdict
from PIL import Image
from io import BytesIO
import os
import numpy as np
from google.cloud import storage
from google.auth import credentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import ast
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import re

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'lesuq-jewelry-22533778a54a.json'

storage_client = storage.Client()

skuInd, descInd, priceInd, imgInd, sizeInd, urlInd = 0,0,0,0,0,0
shortInd, groupInd, detailedCatInd, catInd, productInd, weightInd = 0,0,0,0,0,0
quality1Ind, qualityInd2, qualityInd3, qualityInd4, extendedTypeInd, countryInd = 0,0,0,0,0,0
actionInd = 0
customLabelInd = 0
quantityInd, titleInd, condIDInd, metInd, typeInd, colorInd, metPurityInd, suitForInd, numPiecesInd, matInd, brandInd, jewlDepInd, formatInd, durInd, dispInd, retAccInd = 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
relDetInd,relInd,payPalAccInd,shipTypeInd, payPalEmaInd, immPay, shipOptInd1, shipOptInd2, shipCostInd, shipCostInd2, promInd, retWithInd, refOptInd, shipPaidInd = 0,0,0,0,0,0,0,0,0,0,0,0,0,0
lengthOfRow = 0
identifiers = []
listings = []
rowTemplate = []
varTemplate = []
priceMult = 2.2
minPrice = 16
header = 0
header2 = 0
variations = True
currentSKUs = set()
currentTitles = []
specInd, img2Ind,img3Ind = 0,0,0
gWeightInd, dClarInd, dWeightInd,dColInd = 0,0,0,0
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
driver.get('https://www.stuller.com/')

quantityTable = {}
chainTypes = ["Anchor/Mariner", "Ball", "Bead", "Bar Link", "Book", "Box","Braided","Byzantine","Cable","Caprice","Cord",
'Crisscross','Cuban Link','Cup Chain','Curb Link','Figaro','Figure 8','Foxtail','Herringbone','Marquise','Mesh','Omega'
'Oval Link','Panther','Popcorn','Rolo','Rope','Round Link','San Marco','Serpentine','Singapore','Snake','Spiga/Wheat','Tube'
'Venetian Link','Wire']

types = ["Bead Cap","Beading Pin","Beads","Box","Brooch Back","Cap","Chain","Charm Finding","Chatelaine","Clasp/Closure","Clip"
,"Connector","Cord","Crimp","Crimp Bead","Crown","Ear Climber","Ear Cuff","Earnut","Earring Back/Stopper","Earring Hook"
,"Earstud Components","Ear Thread","Ear Wrap","End Bead","Eye Hook","Eye Pin","Frame","Gear Cog","Head Pin","Jewelry Elastic"
,"Jewelry Making Kit","Jump Ring","Link Chain","Locket Finding","Metal Sheet","Necklace Extender","Needle","Pendant Finding"
,"Pin","Safety Chain","Screw","Spacer","Split Ring","Strip","Stud","Thread","Wire"]

typeMatches = [{
    'type': "Necklace Extender",
    'compatible': ['Necklace']
    },{
    'type': "Split Ring",
    'compatible': ['Split Ring']
    },{
    'type': "Beads",
    'compatible': ['Spacer', 'Roundel', 'Bead']
    },{
    'type': "Nose Stud",
    'compatible': ['Nose']
    },{
    'type': "Barbell",
    'compatible': ['Barbell']
    },{
    'type': "End Cap",
    'compatible': ['End Cap']
    },{
    'type': "Brooch",
    'compatible': ['Brooch', 'Safety Catch']
    },{
    'type' : "Component",
    'compatible': ['Sleeve', 'Rivet', 'Component', 'Cuff Link']
    },{
    'type' : "Pin",
    'compatible': ['Tie Tac', 'Pin']
    },{
    'type' : "Wire",
    'compatible': ['Wire']
    },{
    'type' : "Clasp/Closure",
    'compatible': ['Ball Joint']
    },{
    'type' : "Accessory",
    'compatible': ['Collar Stay']
    }, {
    'type' : "Ring",
    'compatible': ['Bezel Setting']
    },{
    'type' : "Screw",
    'compatible': ['Scrimp']
    },{
    'type' : "Crimp",
    'compatible': ['Crimp']
    }
    ]
# if a listing has variations with both set and unset, choose the one with less listings
# earrings have to be even number, make sure all listings have price above 10$ by multiplying quantity
#add xQuantity to the end of
tokenized_titles, word_fd, bigram_fd, trigram_fd = 0,0,0,0

descPrefix = '<font size="4"><p><b>Jeweler Grade findings and components. High quality products manufactured for use by industry jewelry professionals and hobbyists. Diamonds graded and sorted by GIA graduate of diamonds. Why settle for less?</b></p><p><b>Le Suq offers an assortment of 10K/14K/18K Solid Gold and .925 Sterling Silver finished jewelry findings and jewelry making products at prices that are extremely competitive with today\'s precious metals market.</b></p>'

api_key = 'AIzaSyAp5cL5k0nL8SlqHojdpqge0OlIvIbL7rA'

def readAndCopy(readFile, copyFile, writeFile, activeListingsFile):
    global listings, lengthOfRow, rowTemplate, varTemplate, header, header2

    f = open(activeListingsFile, 'r')
    lines = f.readlines()
    header3 = lines[0].split(",")
    defineIndices(header3)
    lines.pop(0)
    createInventory(lines)
    f.close()

    f = open(readFile, 'r')
    lines = f.readlines()
    header = lines[0].split(",")
    defineIndices(header)
    lines.pop(0)
    createListings(lines)
    f.close()

    c = open(copyFile, 'r')
    lines2 = c.readlines()
    header2 = lines2[1].split(",")
    rowTemplate = lines2[2].split(",")
    varTemplate = lines2[3].split(",")
    lengthOfRow = len(header2)
    defineIndices(header2)
    c.close()

    w = open(writeFile, "w")
    w.write(lines2[0])
    w.write(lines2[1])
    if variations == True:
        for i in createVaryingRows():
            w.write(i)
    else:
        for i in createNormalRows():
            w.write(i)
    w.close()
    #driver.quit()

def createInventory(lines):
    global tokenized_titles, word_fd, bigram_fd, trigram_fd
    for line in lines:
        line = line.split(',')
        currentSKUs.add(line[skuInd])
    #tokenized_titles = [nltk.word_tokenize(title) for title in currentTitles]
    # Extract common words and phrases from the titles
    #word_fd = nltk.FreqDist(word for words in tokenized_titles for word in words)
    #bigram_fd = nltk.FreqDist(nltk.bigrams(words) for words in tokenized_titles)
    #trigram_fd = nltk.FreqDist(nltk.trigrams(words) for words in tokenized_titles)

def defineIndices(header):
    global skuInd, descInd, priceInd, imgInd, sizeInd, urlInd, shortInd, groupInd, detailedCatInd, catInd, productInd, weightInd, quality1Ind, qualityInd2, qualityInd3, qualityInd4, extendedTypeInd, countryInd
    global quantityInd, titleInd, condIDInd, metInd, typeInd, colorInd, metPurityInd, suitForInd, numPiecesInd, matInd, brandInd, jewlDepInd, formatInd, durInd, dispInd, retAccInd
    global relDetInd,relInd,payPalAccInd,payPalEmaInd, immPay, shipTypeInd, shipOptInd1, shipOptInd2, shipCostInd, shipCostInd2, promInd, retWithInd, refOptInd, shipPaidInd, customLabelInd
    global specInd, img2Ind, img3Ind, gWeightInd, dColInd,dClarInd,dWeightInd
    for index, title in enumerate(header):
        loweredTitle = title.lower().replace("*","")
        if loweredTitle.__contains__("sku"):
            skuInd = index
        elif loweredTitle == "customlabel":
            customLabelInd = index
        elif loweredTitle == "description":
            descInd = index
        elif loweredTitle == "shortdescription":
            shortInd = index
        elif loweredTitle == "groupdescription":
            groupInd = index
        elif loweredTitle == "producttype":
            productInd = index
        elif loweredTitle == "price" or loweredTitle == "startprice":
            priceInd = index
        elif loweredTitle == "weight":
            weightInd = index
        elif loweredTitle == "gramweight":
            gWeightInd = index
        elif loweredTitle == "image1" or loweredTitle == "picurl":
            imgInd = index
        elif loweredTitle == "image2" or loweredTitle == "picurl":
            img2Ind = index
        elif loweredTitle == "image3" or loweredTitle == "picurl":
            img3Ind = index
        elif loweredTitle.__contains__("country") or loweredTitle == "location":
            countryInd = index
        elif loweredTitle == "quantity":
            quantityInd = index
        elif loweredTitle == "category":
            catInd = index
        elif loweredTitle == "title":
            titleInd = index
        elif loweredTitle == "conditionid":
            condIDInd = index
        elif loweredTitle == "c:metal":
            metInd = index
        elif loweredTitle == "c:type":
            typeInd = index
        elif loweredTitle == "c:color":
            colorInd = index
        elif loweredTitle == "c:metal purity":
            metPurityInd = index
        elif loweredTitle == "c:suitable for":
            suitForInd = index
        elif loweredTitle == "c:number of pieces":
            numPiecesInd = index
        elif loweredTitle == "c:material":
            matInd = index
        elif loweredTitle == "c:brand":
            brandInd = index
        elif loweredTitle == "c:jewelry department":
            jewlDepInd = index
        elif loweredTitle == "format":
            formatInd = index
        elif loweredTitle == "duration":
            durInd = index
        elif loweredTitle == "dispatchtimemax":
            dispInd = index
        elif loweredTitle == "returnsacceptedoption":
            retAccInd = index
        elif loweredTitle == "relationshipdetails":
            relDetInd = index
        elif loweredTitle == "relationship":
            relInd = index
        elif loweredTitle == "relationshipdetails":
            relDetInd = index
        elif loweredTitle == "paypalaccepted":
            payPalAccInd = index
        elif loweredTitle == "paypalemailaddress":
            payPalEmaInd = index
        elif loweredTitle == "immediatepayrequired":
            immPay = index
        elif loweredTitle == "shippingtype":
            shipTypeInd = index
        elif loweredTitle == "merchandisingcategory4":
            typeInd = index
        elif loweredTitle.__contains__("size"):
            sizeInd = index
        elif loweredTitle == 'descriptiveelementname1':
            specInd = index
        elif loweredTitle == 'diamondcolor':
            dColInd = index
        elif loweredTitle.__contains__('totaldiamondcaratweight'):
            dWeightInd = index
        elif loweredTitle == 'diamondclarity':
            dClarInd = index

def createListings(lines):
    global listings, identifiers
    for line in lines:
        line = line.split(",")
        id = line[skuInd].split(":")[0]
        if not line[skuInd] in currentSKUs:
            if line[priceInd] == '':
                continue
            item = createItem(line, id)
            if item == -1:
                continue
            if id in identifiers:
                idx = identifiers.index(id)
                listings[idx].append(item)
            else:
                identifiers.append(id)
                listings.append([item])
        
def notInCurrentSKUs(id, skus):
    for s in list(skus):
        if id in s:
            return False
    return True

def createItem(line, id):
    specifics = parseShortDescription(line[shortInd])
    priceDet = quantifyPriceAndSku(roundPrice(line[priceInd], priceMult), id, specifics["metal"])
    realSpecs = determineSpecs(line, specInd, str(line[skuInd]))
    if realSpecs == -1:
        return -1
    #.replace('"', 'INCHES')
    return {
    "sku" : str(line[skuInd]) + priceDet["sku"],
    "price": priceDet["price"],
    "weight" : determineWeight(line),
    "imgUrl" : line[imgInd],
    "images" : [line[imgInd], line[img2Ind], line[img3Ind]],
    "title" : line[descInd],
    "metal" : specifics["metal"],
    "size" : specifics["size"],
    "set" : specifics["set"],
    "length" : specifics["length"],
    "quantity" : priceDet["sku"].replace("*","") or 1,
    "color" : getColorFromMetal(specifics["metal"]),
    "purity" : determinePurity(specifics["metal"]),
    "type" : line[typeInd],
    "specs" : realSpecs
    }

def determineDiamondSpecs(line):
    d = {
        "Diamond Clarity" : '',
        "Diamond Color" : '',
        "Total Diamond Carat Weight" : ''

    }
    d["Diamond Clarity"] = line[dClarInd] if not (line[dClarInd] == 'N/A' or line[dClarInd] == '' or line[dClarInd].__contains__('CT')) else ''
    d["Diamond Color"] = line[dColInd] if not (line[dColInd] == 'N/A' or line[dColInd] == '') else ''
    d["Total Diamond Carat Weight"] = line[dWeightInd].replace('CT\n','CTW').replace('\n','') if not (line[dWeightInd] == 'N/A' or line[dWeightInd] == '' or line[dWeightInd] == '\n') else ''
    return d

def determineWeight(line):
    if line[weightInd+1].lower().__contains__('z'):
        return str(round(float(line[weightInd]),3)) + ' ounces'
    else:
        return line[gWeightInd] + ' grams'

def quantifyPriceAndSku(price, id, met):
    global quantityTable
    col = {
        'sku' : '',
        'price' : price
    }
    if id in quantityTable and met in quantityTable[id]:
        q = quantityTable[id][met]
        col['price'] = roundPrice(price*q, 1)
        if not q == 1:
            col['sku'] = f'*{q}'
        return col
    
    if not id in quantityTable:
        quantityTable.update({id:{met:1}})
    elif not met in quantityTable[id]:
        quantityTable[id].update({met:1})

    if price < minPrice:
        mult = minPrice / price
        if mult < 2:
            col['price'] = roundPrice(price*2,1)
            col['sku'] = '*2'
            quantityTable[id].update({met:2})
        elif mult < 5:
            col['price'] = roundPrice(price*5,1)
            col['sku'] = '*5'
            quantityTable[id].update({met:5})
        elif mult < 10:
            col['price'] = roundPrice(price*10,1)
            col['sku'] = '*10'
            quantityTable[id].update({met:10})
        elif mult < 20:
            col['price'] = roundPrice(price*20,1)
            col['sku'] = '*20'
            quantityTable[id].update({met:20})
        else:
            col['price'] = roundPrice(price*40,1)
            col['sku'] = '*40'
            quantityTable[id].update({met:40})
    
    return col

def roundPrice(price, priceMult):
    return math.ceil(float(price)*priceMult) - .01

def parseShortDescription(desc):
    potSizes = []
    col = {
        "metal" : "N/A",
        "size" : "",
        "length" : "N/A",
        "set" : "N/A"
    }
    for i in desc.split("/"):
        print(i)
        if col['metal'] == "N/A":
            if i.__contains__("K ") or i.lower().__contains__("platinum") or i.lower().__contains__("stainless") or i.lower().__contains__("silver") or i.lower().__contains__("brass") or i.lower().__contains__("nickel") or i.lower().__contains__("plated") or i.lower().__contains__("sterlium"):
                col["metal"] = i.strip()
            elif i.lower().__contains__('krgf'):
                col["metal"] = i.strip().replace("rgf", ' Rose Gold Filled')
            elif i.lower().__contains__('yp'):
                col["metal"] = i.lower().strip().replace("yp", 'Yellow Plated')
        if i.lower().__contains__("mm") and notSpecialSize(i):
            print('SizeGood')
            potSizes.append(i.lower().strip())
        elif i.lower().__contains__("in "):
            col["length"] = i.strip()
        elif i.lower().__contains__("unset"):
            col["set"] = "Unset"
        elif i.lower().__contains__("set"):
            col["set"] = "Set"
    if len(potSizes) > 0:
        col["size"] = max(potSizes, key = lambda a: (float(a.split('mm')[0]) if not a.__contains__('x') else float(a.split('mm')[0].replace(' ','').split('x')[0])*float(a.split('mm')[0].replace(' ','').split('x')[1])))
    return col

def notSpecialSize(size):
    if size.lower().__contains__('x') and len(size.strip().split(' ')) < 6:
        return True
    elif size.__contains__('::'):
        return True
    elif len(size.strip().split(' ')) > 5:
        return False
    return True

def determineColor(metal):
    
    if metal.__contains__("K "):
        if metal.__contains__("Palladium"):
            return metal.split(" ")[2]
        return metal.split("K ")[1]
    if metal.__contains__("Silver") or metal.__contains__("Stainless"):
        return "White"
    return metal

def determinePurity(metal):
    if metal.__contains__("K "):
        return metal.split(" ")[0].lower() + 't'
    elif metal.__contains__("Platinum"):
        return 'PT950'
    elif metal.__contains__("Silver"):
        return '925'
    else:
        return ''

def determineType(desc):
    for t in typeMatches:
        for c in t["compatible"]:
            if desc.__contains__(c):
                return t["type"]
    return "N/A"

def determineSpecs(line, ind, sku):
    specs = getItemURLSpecs(sku)
    #specs = {}
    if specs == -1:
        return -1
    for i in range(0,15):
        if not line[ind + i*2] == '':
            specs.update({line[ind + i*2] : line[ind + 1 + i*2]})
    d = determineDiamondSpecs(line)
    for k in d:
        if not d[k] == '':
            specs.update({k : d[k]})
    return specs

def grabMM(i):
    for k in i.split("::"):
        if k.lower().__contains__("mm"):
            return k

def createVaryingRows():
    finalArr = []
    #add parent row
    for set in range(len(listings)):
        if len(listings[set]) == 1:
            finalArr.append(createSingleRow(listings[set][0], set))
            continue
        setness = 0
        finalArr.append(createCommaString(createAddRow(set)))
        detRet = determineRelationshipDetails(listings[set])
        for item in listings[set]:
            if setness == 0:
                if not item["set"] == "N/A":
                    setness = item["set"]
            elif not (item["set"] == setness or item["set"] == "N/A"):
                continue
            row = createVarRow(item)
            row[relDetInd] = getRelDet(detRet, item)
            row[titleInd] = ''
            finalArr.append(createCommaString(row) + "\n")
    return finalArr

def getRelDet(detRet, item):
    metal = sortMetals([item["metal"]],0)[0]
    if 'Metal' in detRet and 'Size' in detRet:
        return "Metal Type=" + metal if (item["size"] == 'N/A' or item["size"] == '') else "Metal Type=" + metal + "|Size=" + item["size"]
    elif 'Metal' in detRet:
        return "Metal Type=" + metal
    elif 'Size' in detRet:
        return "Size=" + item["size"] if not (item["size"] == 'N/A' or item["size"] == '') else ''
    return ''

def createNormalRows():
    finalArr = []
    for col in range(len(listings)):
        for item in listings[col]:
            finalArr.append(createSingleRow(item), col)
    return finalArr

def createSingleRow(item, index):
    row = createVarRow(item)
    row2 = createAddRow(index)
    row = copyFromTemplate(row2,row)
    row[relInd] = ''
    row[relDetInd] = ''
    return createCommaString(row)

def copyFromTemplate(row, copyRow):
    for index, i in enumerate(copyRow):
        if len(str(i)) > 0:
            row[index] = i
    return row

def createAddRow(index):
    baseArr = copy.deepcopy(rowTemplate)
    baseArr[customLabelInd] = identifiers[index]
    title = determineTitle(listings[index])
    baseArr[titleInd] = title
    baseArr[imgInd] = determineImage(identifiers[index],listings[index])
    baseArr[descInd] = determineDescription(listings[index], title)
    baseArr[relDetInd] = determineRelationshipDetails(listings[index])
    baseArr[typeInd] = listings[index][0]["type"]
    baseArr[metInd] = determineMetals(listings[index])
    baseArr[colorInd] = determineColors(listings[index])
    baseArr[metPurityInd] = determineMetPurs(listings[index])
    baseArr[numPiecesInd] = determineNumPieces(listings[index])
    baseArr[sizeInd] = determineSizes(listings[index])
    return baseArr

def createVarRow(item):
    varArr = copy.deepcopy(varTemplate)
    varArr[customLabelInd] = item["sku"]
    #varArr[metInd] = sortMetals([item["metal"]],0)[0]
    #varArr[sizeInd] = item["size"]
    varArr[priceInd] = item["price"]
    #varArr[numPiecesInd] = item["quantity"]
    #varArr[colorInd] = item["color"]
    #varArr[metPurityInd] = item["purity"]
    varArr[titleInd] = item["title"]
    #varArr[typeInd] = item["type"]
    return varArr

def createCommaString(arr):
    stri = ""
    for cell in arr:
        stri += str(cell) + ","
    stri = stri[:-1]
    return stri

def generate_title(prompts):
    # Choose a random selection of words and phrases from the prompts
    new_title = []
    for word in prompts:
        if word in word_fd:
            new_title.append(word)
        elif word in bigram_fd:
            new_title.extend(word)
        elif word in trigram_fd:
            new_title.extend(word)
    return ' '.join(new_title)

def determineSizes(items):
    s = set()
    for i in items:
        s.add(i["size"])
    ss = sortSizes(list(s), 'mm')
    return (ss[0] if ss[0] == ss[len(ss)-1] else ss[0] + ' to ' + ss[len(ss)-1]) if not len(ss) == 0 else ''

def determineNumPieces(items):
    qs = [int(i["quantity"]) for i in items]
    return str(min(qs)) if max(qs) == min(qs) else str(min(qs)) + ' to ' + str(max(qs))

def determineMetPurs(items):
    s = set()
    for i in items:
        if i["purity"] == 'Silver':
            s.add('White')
        else:
            s.add(i["purity"])
    s = [i for i in s if not (i == 'N/A' or i == '')]
    return arrayToStringOr(sorted(list(s), key = lambda a: int(''.join(filter(str.isdigit, a)))))

def determineMetals(items):
    return arrayToStringOr(sortMetals([i["metal"] for i in items], 0))

def determineColors(items):
    ss = set()
    for i in items:
        ss.add(i['color'])
    return arrayToStringOr(list(ss))
        
def arrayToStringOr(arr):
    s = ''
    for ind,m in enumerate(arr):
        if m == '':
            continue
        if ind + 2 == len(arr):
            s += m + ' or '
        else:
            s += m + ' '
    return s

def determineTitle(items):
    #prompts = []
    #for item in items:
    #    for val in item.values():
    #        for word in str(val).split(" "):
    #            prompts.append(str(word))
    #title = generate_title(prompts)
    title = ''
    title += titlePrefix(items)
    startCollecting = False
    specials = ['Sterling', 'Silver', 'Yellow', 'White', 'Rose']
    for word in items[0]["title"].replace('"','').split(' '):
        if not word + ' ' in title and not word in specials:
            startCollecting = True
        if startCollecting:
            title += word + ' '
    title = removeSize(title)
    #re.sub('[mm]','',title)
    asterisk = True
    for i in items:
        if not '*' in i["sku"]:
            asterisk = False
    if asterisk == True:
        title += str(items[0]["quantity"]) + ' pcs'
    title = ' '.join(title.split())
    return title

def removeSize(title):
    tit = ''
    tSplit = title.split(' ')
    for word in range(len(tSplit)):
        integer = True
        if tSplit[word] == 'mm':
            continue
        try:
            float(tSplit[word])
        except ValueError:
            integer = False
        wSplit = tSplit[word].split('x')
        if integer == True:
            if word < len(tSplit) - 1:
                if tSplit[word + 1] == 'mm':
                    continue
            integer = False
        elif len(wSplit) > 1:
            integer = True
            try:
                float(wSplit[0])
            except ValueError:
                integer = False
        if integer == True:
            continue
        tit += tSplit[word] + ' '
    return tit

def titlePrefix(items):
    title = ''
    karats = set()
    metals = set()
    for item in items:
        if item["metal"].__contains__("K "):
            karat = item["metal"].split("K ")[0]
            karats.add(int(karat))
            if item["metal"].__contains__("Palladium"):
                metals.add("Palladium")
            else:
                metals.add("Gold")
        elif item["metal"].__contains__("Silver"):
                karats.add(925)
                metals.add("Silver")
        elif item["metal"].__contains__("Platinum"):
                karats.add(950)
                metals.add("Platinum")
        else:
            metals.add(item["metal"])

    karats = sorted(karats)
    metals = sorted(metals, key = len)
    for k in karats:
        if not k > 100:
            title+= str(k) + "K "
        elif k == 950:
            title += 'PT950 '
        else:
            title += str(k) + ' '
    c = 1
    for met in metals:
        if c + 1 == len(metals):
            title += met + ' or '
        else:
            title += met + ' '
        c += 1
    return title

def determineImage(id,items):
    urls = ''
    images = mainImages(items)
    if len(images[0]) == 1:
        urls += mergeImages(images[1][0][0], id, images[1][0][1])
    else:
        urls += mergeImages(images[0], id, id)
        for i in images[1]:
            if not i == '':
                urls += '|' + mergeImages(i[0], id, i[1])
    return urls

def mainImages(items):
    images = []
    secondaries = []
    whiteImg = 0
    yellowImg = 0
    roseImg = 0
    for i in items:
        col = getColorFromMetal(i["metal"])
        if col == 'White':
            if whiteImg == 0:
                whiteImg = 1
            else:
                continue
        elif col == 'Yellow':
            if yellowImg == 0:
                yellowImg = 1
            else:
                continue
        elif col == 'Rose':
            if roseImg == 0:
                roseImg = 1
            else:
                continue
        else:
            continue
        images.append(i["imgUrl"])
        secondaries.append((i["images"], i["sku"]))
    return (images, secondaries)

def getColorFromMetal(metal):
    if metal.__contains__("Silver") or metal.__contains__("Platinum") or metal.__contains__("Nickel") or metal.__contains__("Steel") or metal.__contains__("White") or metal.__contains__("Palladium") or metal.__contains__("Sterlium"):
        return 'White'
    elif metal.__contains__("Yellow") or metal.__contains__("Brass") or (metal.__contains__("Gold") and not (metal.__contains__("Rose") or metal.__contains__("White"))):
        return 'Yellow'
    elif metal.__contains__("Rose"):
        return 'Rose'
    else:
        return '??Idontknowcolor'

def mergeImages(images, id, sku):
    imgs = []
    for image in images:
        if image == '':
            continue
        response = requests.get(image)
        imgs.append(Image.open(BytesIO(response.content)))
    if len(imgs) == 0:
        return ''
    maxW = max(imgs, key = lambda i: i.width).width
    maxH = max(imgs, key = lambda i: i.height).height
    num_images = len(imgs)
    num_rows = round(num_images ** 0.5)
    num_columns = num_images // num_rows
    if num_images % num_rows != 0:
        num_columns += 1
    # Create a new image that is the size of the grid
    grid_image = Image.new("RGB", (num_columns * maxW, num_rows * maxH), "white")
    # Paste the images onto the grid image
    offset = 0
    for i, img in enumerate(imgs):
        row = i // num_columns
        col = i % num_columns
        extras = len(imgs) - i
        if col == 0 and extras < num_columns:
            offset = int((num_columns - extras) * maxW / 2)
        grid_image.paste(extendBounds(img), (col * maxW + offset, row * maxH))
    grid_image = resizeImage(grid_image)
    grid_image = centerImage(grid_image)
    # Save the grid image to a file
    os.makedirs(os.path.join('images', str(id)), exist_ok=True)
    filename = f"./images/{id}/{sku}.jpg"
    grid_image.save(filename, "JPEG")
    if id == sku:
        return uploadImage(id, sku, filename, 1)
    else:
        return uploadImage(id, sku, filename, 0)

def centerImage(image):
    img = image.convert('L')
    img_data = np.asarray(img)
    non_white_pixels = np.argwhere(img_data != 255)
    x0, y0 = non_white_pixels.min(axis=0)
    x1, y1 = non_white_pixels.max(axis=0) + 1
    # Crop the image and return it
    centerX = int((image.width-y1-y0)/2 + y0)
    centerY = int((image.height-x1-x0)/2 + x0)
    background = Image.new('RGB', (image.width, image.height) , (255,255,255))
    image = image.crop((y0-7,x0-7,y1+7,x1+7))
    background.paste(image,(centerX,centerY))
    return background

def resizeImage(image):
    w, h = image.size
    if w!=h:
        ratio = 2000/max(w,h)
        image = image.resize((int(w*ratio),int(h*ratio)))
        background = Image.new('RGB', (2000, 2000), (255, 255, 255))
        offset = (int((2000 - image.width) / 2), int((2000 - image.height) / 2))
        background.paste(image, offset)
        image = background
    else:
        image_size = (2000,2000)
        image = image.resize(image_size)
    return image

def uploadImage(name, sku, filename, folder = 0):
    print(name, sku, filename)
    bucket_name = 'lesuq_bucket_1'
    bucket = storage_client.bucket(bucket_name)
    if folder == 1:
        folder_blob = bucket.blob(f'{name}/')
        folder_blob.upload_from_string(content_type='application/x-directory', data=b'')
    blob = bucket.blob(f'{name}/{sku}.jpg')
    blob.upload_from_filename(filename, content_type='image/jpeg')
    return blob.public_url

def extendBounds(image):
    img = image.convert('L')
    img_data = np.asarray(img)
    non_white_pixels = np.argwhere(img_data != 255)
    x0, y0 = non_white_pixels.min(axis=0)
    x1, y1 = non_white_pixels.max(axis=0) + 1

    xbounds = abs(x1 - x0)
    ybounds = abs(y1 - y0)
    if xbounds > image.width-10 or ybounds > image.height-10:
        background = Image.new('RGB', (image.width, image.height) , (255,255,255))
        image = image.resize((image.width-14, image.height-14))
        background.paste(image,(7,7))
        image = background

        # IF IMAGES ARE TOO SMALL:
    #if xbounds < 200 and ybounds < 200:
    #    print('mhm')
    #    image = img.crop((y0-10,x0-10,y1+10,x1+10)).resize((300,300))

        #IF WE WANT TO MAKE THE IMAGES FIT BETTER
    #img_cropped = img.crop((y0, x0, y1, x1))
    return image

def getFloat(num):
    arr = []
    for n in num.split(' '):
        if n == '':
            continue
        if n.__contains__('/'):
            arr.append(float(float(n.split('/')[0])/float(n.split('/')[1])))
        else:
            arr.append(float(n))
    return sum(arr)

def determineDescription(items, title):
    desc = descPrefix
    desc += f'<p><b><u>{title}</u></b></p>'
    desc += '<p><b>Available Metal Types: </b></p>'
    metals = set()
    for item in items:
        metals.add(item["metal"])
    for m in sortMetals(metals):
        desc += f'<p>{m}</p>'
    
    sizes = set()
    for item in items:
        sizes.add(item["size"])
    sizeNotAdded = True
    #sizes = sortSizes(sizes, 'mm')
    sizes = sortByNumbers(sizes)
    for s in sizes:
        if not (s == 'N/A' or s == ''):
            if sizeNotAdded == True:
                desc += '<br><p><b>Sizes: </b></p>'
                sizeNotAdded = False
            desc += f'<p>{s}</p>'
        
    desc += '<br><p><b>Additional Specifications: </b></p>'
    if len(metals) > 1 and len(sizes) > 1:
        desc += '<p>Weight: Varies by metal type/size</p>'
    elif len(metals) > 1:
        desc += '<p>Weight: Varies by metal type</p>'
    elif len(sizes) > 1:
        desc += '<p>Weight: Varies by size</p>'
    elif not items[0]["weight"] == '' :
        desc += f'<p>Weight: {items[0]["weight"]}</p>'

    dontInclude = ['Series','Quality', 'Description', 'Gender', 'Weight', 'Finish State', 'Finished State', 'Finish']
    varyingSpecs = set()

    specs = {}
    for item in items:
        for spec in item["specs"]:
            if not spec in dontInclude:
                if not (item["specs"][spec] == 'N/A' or item["specs"][spec] == 'None' or item["specs"][spec] == ''):
                    if not spec in specs:
                        specs.update({spec:set()})
                    if item["specs"][spec].__contains__('Mm'):
                        specs[spec].add(simplify(item["specs"][spec], 1))
                    else:
                        specs[spec].add(simplify(item["specs"][spec]))
        
    for i in specs:
        if len(specs[i]) > 1 and any(containsDigit(s) for s in specs[i]):
            varyingSpecs.add(i)
    
    if len(varyingSpecs) > 0:
        j = '/'.join(list(varyingSpecs)) + ':'
        desc += f'<p>{j}</p>'
        varys = set()
        for i in items:
            row = []
            for k in varyingSpecs:
                if k in i["specs"]:
                    if i["specs"][k].__contains__('Mm'):
                        row.append(simplify(i["specs"][k],1))
                    else:
                        row.append(simplify(i["specs"][k]))
                else:
                    row.append('N/A')
            varys.add('/'.join(row))
        
        varys = sortByNumbers(list(varys))
        for v in varys:
            if not v == '':
                desc += f'<p>{v}</p>'

    for i in specs:
        if i not in varyingSpecs:
            #if list(specs[i])[0].lower().__contains__('in'):
            #    specs[i] = sortSizes(specs[i], 'in')
            #elif i.lower().__contains__('size') or i.lower().__contains__('dimension'):
            #    specs[i] = sortSizes(specs[i], 'mm')
            #elif i == 'Total Diamond Carat Weight':
            #    specs[i] = sorted(specs[i], key= lambda a: getFloat(a.lower().split(' ctw')[0]))
            specs[i] = sortByNumbers(specs[i])
            desc += f'<p>{i}: {"/".join(specs[i])}</p>'

    #normalizePricesAndQuantities(items)
    desc += '<br>' + separateNumberOfPieces(items)

    desc += '</font>'
    return desc

def normalizePricesAndQuantities(items):
    d = {}
    for i in items:
        if not i["metal"] in d:
            d.update({i["metal"]:[]})
        d[i["metal"]].append(i["quantity"])

def separateNumberOfPieces(items):
    pieces = set()
    for i in items: pieces.add(int(i["quantity"]))
    pieces = sorted(list(pieces))
    if len(pieces) == 1:
        if pieces[0] == 1:
            return '<p><b>Sold by each piece.</b></p>'
        else:
            return f'<p><b>Sold in sets of {pieces[0]} pieces. Please get in touch if a reduced quantity is desired.</b></p>'
    s = '<p><b>Sold in quantities according to metal type:</b></p>'
    for i in pieces:
        if i == 1:
            s += '<p>1 piece:</p>'
        else:
            s += f'<p>{i} pieces:</p>'
        m = set()
        for k in items:
            if int(k["quantity"]) == i:
                m.add(k["metal"])
        for met in sortMetals(list(m)):
            s += f'<p>{met}</p>'
    s += '<p>Please get in touch if a specific quantity for a variation is desired.</p>'
    return s

def containsDigit(s):
    return any(a.isdigit() for a in s)

def sortByNumbers(strings):
    return sorted(strings, key = lambda a : valueOfString(a))

def valueOfString(a):
    s = ''
    nums = []
    numFound = False
    for i in a:
        if i.isdigit() or i == '.' or (i == '/' and numFound == True):
            s += i
            numFound = True
        elif numFound == True:
            numFound = False
            nums.append(getFloat(s))
            s = ''
    if numFound == True:
        nums.append(getFloat(s))
    if nums:
        return np.prod(np.array(nums))  
    return 1000000
        
def simplify(s, l = 0):
    if l == 1:
        return re.sub(' +', ' ', s.lower().strip())
    else:
        return re.sub(' +', ' ', s.strip())

def sortSizes(sizes,unit):
    return sorted([x.lower() for x in sizes if not x == ''], key = lambda a: (getFloat(a.split(unit)[0]) if not a.lower().__contains__('x') else getFloat(a.lower().split(unit)[0].replace(' ','').split('x')[0])*getFloat(a.split(unit)[0].replace(' ','').split('x')[1])))

def sortMetals(metals, default = 0):
    karatMetals = defaultdict(set)
    for metal in metals:
        if metal.__contains__("K "):
            karat = int(metal.split("K ")[0])
            
            if not (metal.split("K ")[1].__contains__('Palladium') or metal.__contains__('Gold') or metal.__contains__('Vermeil')):
                karatMetals[karat].add(metal + ' Gold')
            else:
                karatMetals[karat].add(metal)
        elif metal.__contains__("Sterling"):
            karatMetals[925].add("925 Sterling Silver") if default == 0 else karatMetals[925].add("Sterling Silver")
        elif metal.__contains__("Platinum"):
            if default == 1:
                karatMetals[950].add("Platinum")
            else: 
                karatMetals[950].add("PT950 Platinum")
        elif metal.__contains__("Steel"):
            karatMetals[10000].add(metal)
        elif metal.__contains__("Sterlium"):
            karatMetals[11000].add(metal)
        elif metal.__contains__("Plated"):
            karatMetals[6000].add(metal)
        elif metal.__contains__("Brass"):
            karatMetals[500].add(metal)
        else:
            karatMetals[20000].add(metal)
    finals = []
    for i in sorted(karatMetals.items()):
        finals += sorted(i[1], key = len)
    return finals

def determineRelationshipDetails(items):

    mets = sortMetals([i["metal"] for i in items], 0)
    if len(mets) > 1:
        s = "Metal Type=" + mets[0]
    else:
        s = ''
    sizes = set()
    if not (items[0]["size"] == 'N/A' or items[0]["size"] == ''):
            sizes.add(items[0]['size'])
    for i in range(1, len(mets)):
        if not mets[i] in s:
            s += ';' + mets[i]
    for i in range(1,len(items)):
        if not (items[i]["size"] == 'N/A' or items[i]["size"] == ''):
            sizes.add(items[i]['size'])
    lsizes = sortSizes(list(sizes),'mm')
    if len(sizes) > 1 and len(mets) > 1:
        s += "|Size=" + lsizes[0]
    elif len(sizes) > 1:
        s += "Size=" + lsizes[0]
    for k in range(1,len(sizes)):
        s += ';' + lsizes[k]
    return s

def getItemURLSpecs(sku):

        #url = f"https://www.stuller.com/search/results?query={str(sku).replace(':','%3A')}"
        
        #loadedItem = driver.find_element(By.CLASS_NAME, "unzoomedImage img-responsive center-block")
        
        s = searchForItem(sku)
        if s == 'Failed':
            print(f"Item {sku} discontinued")
            return -1
        specsChunk = findSpecsChunk(str(s))
        print(specsChunk)
        sChunk = specsChunk.split('\\u003ctd\\u003e')
        d = {}
        for i in range(1, len(sChunk), 2):
            if i == len(sChunk) - 1:
                break
            d.update({getVal(sChunk[i]).replace(':',''):getVal(sChunk[i+1])})
            i += 1
        print(d)
        return d

def getVal(val):
    return val[0:val.find('\\')]

def getRedirectedURLContent(url):
    driver.get(url)
    current_url = driver.current_url
    print("Current URL:", current_url)
    return requests.get(current_url).content

def searchForItem(sku, k = 0):
    searchbar = driver.find_elements(By.CLASS_NAME, "autocomplete-input")
    button = driver.find_elements(By.CLASS_NAME, "search-submit-btn")
    redH = []
    try:
        redH = driver.find_elements(By.CLASS_NAME, "c-red")
    except:
        redH = []
    if not redH == []:
        if any(i.text.__contains__('discontinued') for i in redH) and driver.page_source.__contains__(sku):
            print(redH)
            return 'Failed'
    for ind,i in enumerate(searchbar):
        try:
            i.send_keys(sku)
            break
        except:
            print(str(ind) + " failed")
    button[ind].click()
    try:
        wait = WebDriverWait(driver,30)
        img = wait.until(ec.visibility_of_element_located((By.CLASS_NAME, "unzoomedImage")))
    except:
        return searchForItem(sku, k + 1)
    return driver.page_source

def findSpecsChunk(content):
    startInd = content.find('"Specifications"')
    endInd = startInd
    qFound = False
    semiFound = False
    q = 0
    while(qFound == False):
        if content[endInd] == ':':
            semiFound = True
        if semiFound == True and content[endInd] == '"':
            q += 1
        if q == 2:
            qFound = True
        endInd += 1
    return content[startInd:endInd]

    
#getItemURLSpecs('22940:287068:S')
#getItemURLSpecs('1840')
#getRedirectedURLContent("https://www.stuller.com/search/results?query=1841")
readAndCopy("toBeConverted2.csv", "trueTemplate.csv", "priceyVersion.csv","activeListings.csv")
#print(valueOfString("1"))