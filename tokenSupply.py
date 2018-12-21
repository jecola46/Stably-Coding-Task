from flask import Flask, render_template, url_for
import json
from datetime import datetime
from web3 import Web3
web3 = Web3(Web3.WebsocketProvider("wss://mainnet.infura.io/ws/v3/de805f41b07443cfabac888255f682c7"))

## How many data points which also determines how many hours back in time to check. It will only go back
## to the first block Stable Coin was in.
numOfDataPoints = 10000000000000000000000000000

stableCoinFirstBlock = 6154054
firstBlockTime = web3.eth.getBlock(stableCoinFirstBlock).timestamp

app = Flask(__name__)

import os
dirName = os.path.dirname(__file__)
fileName = os.path.join(dirName, "static", "abi.txt")
file = open(fileName, "r")

## Defines the Stable coin contract
myContract = web3.eth.contract(address="0xA4Bdb11dc0a2bEC88d24A3aa1E6Bb17201112eBe", abi=file.read())

file.close()

## Returns a block between lo and hi thats timestamp is close to targetTime.
def binarySearchForBlock(targetTime, lo, hi):
	## Gets within 5 blocks to the one closest to Target time, can be adjusted to help performance or accuracy.
	if hi - lo <= 5:
		return lo
	mid = lo + int((hi - lo) / 2)
	if web3.eth.getBlock(int(mid)).timestamp > targetTime:
		return binarySearchForBlock(targetTime, lo, mid)
	return binarySearchForBlock(targetTime, mid, hi)

## Index Page
@app.route('/')
def hello():
    blockNum = web3.eth.blockNumber
    dataArr = []
    labelArr = []
    currentTime = web3.eth.getBlock(blockNum).timestamp
    hoursSinceFirstBlock = (currentTime - firstBlockTime) / 3600

    ## Get the array from file, it is an array of arrays of form [block, Timestamp, TotalSupply at block]
    dataFileName = os.path.join(dirName, "static", "data.json")
    with open(dataFileName, "r") as filehandle:
       fileArr = json.load(filehandle)

    fileArrLength = len(fileArr)

    ## There should be one data point for the start and then one for each hour after. If there are less
    ## elements in the array we need to update it
    if fileArrLength < hoursSinceFirstBlock + 1:
    	## Average number of blocks in an hour, updates to be a better guess
    	movingAverage = 266
    	for i in range(fileArrLength, int(hoursSinceFirstBlock) + 1):
    		latestData = fileArr[len(fileArr) - 1]
    		latestBlock = latestData[0]

    		targetTime = i * 3600 + firstBlockTime
    		newBlock = binarySearchForBlock(targetTime, latestBlock, latestBlock + 2 * movingAverage)
    		movingAverage = newBlock - latestBlock

    		fileArr.append([newBlock, web3.eth.getBlock(newBlock).timestamp, myContract.functions.totalSupply().call(block_identifier=newBlock)])
    	with open(dataFileName, "w") as filehandle:
    		json.dump(fileArr, filehandle)

    for i in range(numOfDataPoints):
    	dataArr = [(fileArr[-(i + 1)])[2]] + dataArr
    	labelArr = [datetime.utcfromtimestamp((fileArr[-(i + 1)])[1]).strftime('%Y-%m-%d %H:%M:%S')] + labelArr
    	if(i >= hoursSinceFirstBlock - 1):
    	   break

    ## The graph only updates every hour so to get faster updates the most current supply is shown in the top
    ## of the page.
    supplyRightNow = myContract.functions.totalSupply().call()

    ## Returns the html template called supply.html with a dictionary updated to have current be the current
    ## supply, script to be the location of the graphing bundle, data to be an array of the total supply
    ## of Stable coins across time. Labels is the array that corresponds to data and holds what block
    ## number each of those points is from.
    return render_template('supply.html', current=supplyRightNow, 
    	script=url_for('static', filename='Chart.bundle.js'), data=dataArr, labels=labelArr)
