from utils import *
import js_regex


milesToKilometersFactor = 1.609344
poundsToKilogramFactor = 0.45359237
gallonsToLitersFactor = 3.785411784
kiloPascalToPoundPerSquareInchFactor = 6.894757293


def parceDbc(dbcString, options):
    print('The raw dbcString:\n', dbcString)
    dbcArray = dbcString.split('\n')
    print('\ndbcArray\n', dbcArray)

    dbcData = []
    for (index, value) in enumerate(dbcArray):

        dbcData.append(re.findall('"(?:[^"]|.)*"|[^\s]+', value))

    print('\ndbcData:\n', dbcData)

    currentBo = {}
    boList = []
    valList = []
    dataTypeList = []
    commentList = []
    problems = []

    for (index, line) in enumerate(dbcData):
        if(not line or len(line) == 11):
            return

        print(line[0])
        if(line[0] == "BO_"):
    
            if(len(line) != 5):
                raise Exception(
                    f"BO_ on line {index+1} does not follow DBC standard (should have five pieces of text/numbers), all signals in this message won't have a PGN or source.")

            if(len(currentBo) == 0):
                if(len(currentBo["signals"]) == 0):
                    problems.append({"severity": "warning", "line": currentBo["lineInDbc"],
                                    "description": "BO_ does not contain any SG_ lines; message does not have any signals."})

                boList.append(currentBo)
            
                currentBo = {}

            [temp, canId, name, dlc] = line
            if(canId is None):
                raise Exception(
                    f"BO_ CAN ID on line {index + 1} is not a number, all signals in this message won't have a PGN or source.")
            name = name[0, -1]
            canId = int(canId)
            dlc = int(dlc)

            duplicateCanId = boList.get("canId")

            if(duplicateCanId):
                roblems.append({"severity": "warning", "line": index + 1,
                               "description": "BO_ CAN ID already exists in this file. Nothing will break on our side, but the data will be wrong because the exact same CAN data will be used on two different signals."})
            try:

                for k, v in splitCanId(canId).items():
                    exec("%s = %s" % (k, v))
                label = snake_case(name)
                if(options["extendedLabel"]):
                    label = snake_case(currentBo["name"])+label

                currentBo = {"canId": canId,
                             "pgn": pgn,
                             "source": source,
                             "name": name,
                             "priority": priority,
                             "label": label,
                             "isExtendedFrame": isExtendedFrame,
                             "dlc": dlc,
                             "comment": null,
                             "signals": [],
                             "lineInDbc": (index + 1),
                             "problems": []}

            except Exception as e:
                raise Exception(
                    f"The parser broke unexpectedly :( Please contact the VT team and send them the DBC file you were trying to parse as well as this error message:\n{e}")
        elif(line[0] == "SG_"):
            if(len(line) < 8 or len(line) > 9):
                raise Exception(
                    f"SG_ line at {index + 1} does not follow DBC standard; should have eight pieces of text/numbers (or nine for multiplexed signals).")

            try:
                signalData = extractSignalData(
                    line, currentBo["label"], index+1)
                if(signalData["min"] == 0 and signalData["max"] == 0):
                    signalData.pop(signalData["min"])
                    signalData.pop(signalData["max"])
                if(min(signalData) >= max(signalData)):

                    problems.append(
                        {"severity": "error", "line": index + 1,
                            "description": f"SG_ {signalData['name']} in BO_ {currentBo['name']} will not show correct data because minimum allowed value = {signalData['min']} and maximum allowed value = {signalData['max']}. Please ask the customer for a new .dbc file with correct min/max values if this errors pops up often."}
                    )
                if(signalData["sourceUnit"]):
                    temp = signalData["sourceUnit"].lower()
                    if temp == "-" or temp == "n/a" or temp == "none":
                        signalData["postfixMetric"] = ""
                        signalData["postfixImperial"] = ""
                    elif temp == "km/h" or temp == "km/u" or temp == "kmph" or temp == "kph":
                        signalData["postfixMetric"] = "km/h"
                        signalData["postfixImperial"] = "mi/h"
                    elif temp == "kilometer" or temp == "kilometers" or temp == "km":
                        signalData["postfixMetric"] = "km"
                        signalData["postfixImperial"] = "mi"
                    elif temp == "m":
                        if("distance" in signalData["label"] or 'odo' in signalData["label"]):
                            signalData["postfixMetric"] = "km"
                            signalData["postfixImperial"] = "mi"
                            signalData["factor"] = signalData["factor"]/1000
                            signalData["offset"] = signalData["offset"]/1000
                            signalData["min"] = signalData["min"]/1000
                            signalData["max"] = signalData["max"]/1000
                        else:
                            signalData["postfixMetric"] = signalData["sourceUnit"]
                    elif temp == "meter" or temp == 'meters':
                        signalData["postfixMetric"] = "km"
                        signalData["postfixImperial"] = "mi"
                        signalData["factor"] = signalData["factor"]/1000
                        signalData["offset"] = signalData["offset"]/1000
                        signalData["min"] = signalData["min"]/1000
                        signalData["max"] = signalData["max"]/1000
                    elif temp == "deg c" or temp == "degc" or temp == "°c" or temp == "℃" or temp == "�c":
                        signalData["postfixMetric"] = "°C"
                        signalData["postfixImperial"] = "°F"

                    elif temp == "��" or temp == "c" or temp == "¡æ":
                        if("temp" in signalData["label"]):
                            signalData["postfixMetric"] = "°C"
                            signalData["postfixImperial"] = "°F"
                        else:
                            signalData["postfixMetric"] = signalData["sourceUnit"]
                    elif temp == "kg":
                        signalData["postfixMetric"] = "kg"
                        signalData["postfixImperial"] = "lbs"
                    elif temp == "l" or temp == "liter" or temp == "liters":
                        signalData["postfixMetric"] = "l"
                        signalData["postfixImperial"] = "gal"
                    elif temp == "l/h" or temp == "l per h":
                        signalData["postfixMetric"] = "l/h"
                        signalData["postfixImperial"] = "gal/h"
                    elif temp == "km/l" or temp == "km per l":
                        signalData["postfixMetric"] = "km/l"
                        signalData["postfixImperial"] = "mi/gal"
                    elif temp == "l/km" or temp == "l per km" or temp == "liter per km" or temp == "liters per km" or temp == "liters per kilometer" or temp == "liters per kilometers":
                        signalData["postfixMetric"] = "l/km"
                        # bug in main code line 223
                        signalData["postfixImperial"] = "gal/mi"
                    elif temp == "kwh/km" or temp == "kwh per km":
                        signalData["postfixMetric"] = "kWh/km"
                        signalData["postfixImperial"] = "kWh/mi"
                    elif temp == "wh/km" or temp == "wh per km":
                        signalData["postfixMetric"] = "Wh/km"
                        signalData["postfixImperial"] = "Wh/mi"
                    elif temp == "kwh/100km" or temp == "kwh/100 km" or temp == "kwh per 100km" or temp == 'kwh per 100 km':
                        signalData["postfixMetric"] = "kWh/100 km"
                        signalData["postfixImperial"] = "kWh/100 mi"
                    elif temp == "kpa":
                        signalData["postfixMetric"] = "kPa"
                        signalData["postfixImperial"] = "psi"
                    elif temp == "mi" or temp == "miles":
                        signalData["postfixMetric"] = "km"
                        signalData["postfixImperial"] = "mi"
                        signalData['factor'] *= milesToKilometersFactor
                        signalData['offset'] *= milesToKilometersFactor
                        signalData['min'] *= milesToKilometersFactor
                        signalData['max'] *= milesToKilometersFactor
                    elif temp == "m":
                        if "mile" in signalData["label"]:
                            signalData["postfixMetric"] = "km"
                            signalData["postfixImperial"] = "mi"
                            signalData['factor'] *= milesToKilometersFactor
                            signalData['offset'] *= milesToKilometersFactor
                            signalData['min'] *= milesToKilometersFactor
                            signalData['max'] *= milesToKilometersFactor
                        else:
                            signalData["postfixMetric"] = signalData["sourceUnit"]
                    elif temp == "mi/h" or temp == "mph" or temp == "miles per hour":
                        signalData["postfixMetric"] = "km/h"
                        signalData["postfixImperial"] = "mi/h"
                        signalData['factor'] *= milesToKilometersFactor
                        signalData['offset'] *= milesToKilometersFactor
                        signalData['min'] *= milesToKilometersFactor
                        signalData['max'] *= milesToKilometersFactor
                    elif temp == "deg f" or temp == "degf" or temp == "°f" or temp == "℉" or temp == "�f":
                        signalData["postfixMetric"] = "°C"
                        signalData["postfixImperial"] = "°F"
                        signalData["offset"] = (
                            signalData["offset"] - 32) * (5/9)
                        signalData["min"] = (signalData["min"] - 32) * (5/9)
                        signalData["max"] = (signalData["max"] - 32) * (5/9)
                    elif temp == "lbs" or temp == "pound" or temp == "pounds":
                        signalData["postfixMetric"] = "kg"
                        signalData["postfixImperial"] = "lbs"
                        signalData['factor'] *= poundsToKilogramFactor
                        signalData['offset'] *= poundsToKilogramFactor
                        signalData['min'] *= poundsToKilogramFactor
                        signalData['max'] *= poundsToKilogramFactor
                    elif temp == "gal" or temp == "gallon" or temp == "gallons":
                        signalData["postfixMetric"] = "kg"
                        signalData["postfixImperial"] = "lbs"
                        signalData['factor'] *= gallonsToLitersFactor
                        signalData['offset'] *= gallonsToLitersFactor
                        signalData['min'] *= gallonsToLitersFactor
                        signalData['max'] *= gallonsToLitersFactor
                    elif temp == "psi":
                        signalData["postfixMetric"] = "kPa"
                        signalData["postfixImperial"] = "psi"
                        signalData['factor'] *= kiloPascalToPoundPerSquareInchFactor
                        signalData['offset'] *= kiloPascalToPoundPerSquareInchFactor
                        signalData['min'] *= kiloPascalToPoundPerSquareInchFactor
                        signalData['max'] *= kiloPascalToPoundPerSquareInchFactor

                currentBo["signals"].append(signalData)
            except Exception as e:
                problems.append({"severity": "error", "line": index + 1,
                                "description": f"Can't parse multiplexer data from SG_ line, there should either be \" M \" or \" m0 \" where 0 can be any number. This will lead to incorrect data for this signal."})
        elif(line[0] == "VAL_"):
            valProblem = None
            if(len(line) % 2 != 0):

                problems.append(
                    {"severity": "warning", "line": index + 1,
                        "description": "VAL_ line does not follow DBC standard; amount of text/numbers in the line should be an even number. States/values will be incorrect, but data is unaffected."}
                )
            if(len(line) < 7):

                problems.append({"severity": "warning", "line": index + 1,
                                "description": "VAL_ line only contains one state, nothing will break but it defeats the purpose of having states/values for this signal."})

                valProblem = {"severity": "warning", "line": index + 1,
                              "description": "VAL_ line only contains one state, nothing will break but it defeats the purpose of having states/values for this signal."}
            for k, v in extractValData(line).items():
                exec("%s = %s" % (k, v))
            valList.append({"valBoLink": valBoLink, "valSgLink": valSgLink,
                           "states": states, "lineInDbc": (index + 1), "problem": valProblem})
        elif(line[0] == "SIG_VALTYPE_"):
            dataTypeProblem = None
            if(len(line) != 5):
                raise Exception(
                    f"SIG_VALTYPE_ line at {index + 1} does not follow DBC standard; should have a CAN ID, signal name and number.")
            for k, v in extractDataTypeData(line, index+1).items():
                exec("%s = %s" % (k, v))
            dataTypeList.append({
                {"dataTypeBoLink": dataTypeBoLink, "dataTypeSgLink": dataTypeSgLink,
                    "dataType": dataType, "lineInDbc": (index + 1), "problem": dataTypeProblem}
            })
        elif(line[0] == "CM_"):
            if(len(line) < 4):
                raise Exception(
                    f"CM_ line at {index + 1} does not follow DBC standard; should have one of (BU_, BO_ or SG_) type, CAN ID, signal name and comment.")
            for k, v in extractCommentData(line, index+1).items():
                exec("%s = %s" % (k, v))
        else:
            print(
                f"Skipping non implementation line that starts with {line}", line)

        if(len(currentBo) != 0):
            boList.append(currentBo)
     
        temp_boList = []
        for x in boList:
           
            if x != 0:
                temp_boList.append(x)

    

        boList = temp_boList
        if('filterDm1' in options.keys()):
            if(options["filterDm1"] == True):
                temp_boList = []
                for x in boList:
                    if x != 65226:
                        temp_boList.append(x)
                boList = temp_boList

        if(not len(boList)):
            raise Exception('Invalid DBC: Could not find any BO_ or SG_ lines')
        for val in valList:
            bo = val["valBoLink"] == boList.get('canId')
            if(not bo):
                problems.append(
                    {'severity': "warning", 'line': val['lineInDbc'],
                        'description': f"VAL_ line could not be matched to BO_ because CAN ID {val['valBoLink']} can not be found in any message. Nothing will break, and if we add the correct values/states later there won't even be any data loss."}
                )
            sg = val["valSgLink"] == bo["signals"].get('name')
            if(not sg):
                problems.append({
                    {"severity": "warning", "line": val["lineInDbc"], "description": f"VAL_ line could not be matched to SG_ because there's no signal with the name {val['valSgLink']} in the DBC file. Nothing will break, but the customer might intend to add another signal to the DBC file, so they might complain that it's missing."}
                })
            sg["stats"] = val["states"]
            if(val["problem"]):
                sg["problems"].push(val["problem"])

        for datatype in dataTypeList:
            bo = dataType["dataTypeBoLink"] == boList.get("canId")
            if(not bo):
                problems.append(
                    {"severity": "warning", "line": datatype["lineInDbc"], "description": f"SIG_VALTYPE_ line could not be matched to BO_ because CAN ID {dataType['dataTypeBoLink']} can not be found in any message. Nothing will break, but the customer might have intended to add another message to the DBC file, so they might complain that it's missing."}

                )
            sg = datatype["dataTypeSgLink"] == bo["signals"].get("name")
            if(not sg):
                problems.append(
                    {"severity": "warning", "line": datatype["lineInDbc"], "description": f"SIG_VALTYPE_ line could not be matched to SG_ because there's no signal with the name {dataType['dataTypeSgLink']} in the DBC file. Nothing will break, but the customer might have intended to add another signal to the DBC file, so they might complain that it's missing."}

                )
            sg["dataType"] = datatype["dataType"]
            if(datatype["problem"]):
                sg["problems"].push(datatype["problem"])

        for comment in commentList:
            bo = comment["commentBoLink"] == boList.get('canId')
            if(not bo):
                problems.append(
                    {"severity": "warning", "line": comment["lineInDbc"], "description": f"CM_ line could not be matched to BO_ because CAN ID {comment['dataTypeBoLink']} can not be found in any message. Nothing will break, but the customer might have intended to add another message to the DBC file, so they might complain that it's missing."}

                )
            sg = datatype["commentBoLink"] == bo["signals"].get("name")
            if(not sg):
                bo["comment"] = comment["comment"]
                if(comment["problem"]):
                    bo["problems"].append(comment["problem"])
            sg["comment"] = comment["comment"]
            if(comment["comment"]):
                sg["problems"].append(comment["problem"])

        for problem in problems:
            message = problem["line"] == boList.get("lineInDbc")

            if message:
                message["problems"].append(problem)
            for bo in boList:
                for sg in bo["signals"]:
                    signal = problem["line"] == sg.get("lineInDbc")
                    if(signal):
                        signal["problems"].append(problem)

        result = {"params": boList, "problems": problems}

        return result
