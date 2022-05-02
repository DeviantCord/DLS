import json

def findNextShardID(data, listkey:str):
    max = data[listkey][listkey + "-max"]
    index = 0
    chosenid = 0
    lowest = 0
    while not index == max:
        index = index + 1
        if index == 1:
            lowest = data[listkey][listkey + "-1"]
            chosenid = index
        elif data[listkey][listkey + "-" + str(index)] < lowest:
            lowest = data[listkey][listkey + "-" + str(index)]
            chosenid = index
    return chosenid

sortData = {}
sortData["sources"] = {}
sortData["sources"]["sources-max"] = 3
sortData["sources"]["sources-1"] = 3
sortData["sources"]["sources-2"] = 5
sortData["sources"]["sources-3"] = 0
sortData["categories"] = []
sortData["categories"].append("sources")
sortData["listeners"] = {}
sortData["listeners"]["listeners-1"] = 0
sortData["listeners"]["listeners-2"] = 0
sortData["listeners"]["listeners-3"] = 0
sortData["listeners"]["listeners-max"] = 3
sortData["categories"].append("listeners")
saveFile = open("shardtest.json", "w+")
saveFile.write(json.dumps(sortData, indent=4, sort_keys=True))
saveFile.close()

print(str(findNextShardID(sortData, "sources")))


