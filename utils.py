import re
from re import sub


def snake_case(s):
    return '_'.join(
        sub('([A-Z][a-z]+)', r' \1',
            sub('([A-Z]+)', r' \1',
                s.replace('-', ' '))).split()).lower()


def splitCanId(canId):
    isExtendedFrame = canId > 0xffffd
    priority = pgn = source = None
    if isExtendedFrame:
        source = candId & 0xff
        pgn = canId >> 8 & 0xffff
        priority = canId >> 24 & 0xff
    else:
        pgn = canId
    return (isExtendedFrame, priority, pgn, source)

# SG_ speed m1 : 8|8@1+ (1,-50) [-50|150] "km/h" Vector__XXX


def extractSignalData(line, labelPrefix, index):
    isMultiplexor = multiplexerValue = category = comment = None
    if(len(line) == 9 and line[3] == ':'):
        [rawMultiplexer] = line.pop(2)
        if(rawMultiplexer) == 'M':
            isMultiplexor = True
        elif rawMultiplexer[0] == 'm':
            multiplexerValue = int(rawMultiplexer[1:])
        else:
            raise Exception(f"Can't read multiplexer {rawMultiplexer}")

    # TODO edge cases as warnings (return them as Array)
    [startBit, bitLength, littleEndian] = re.split(r'[^\d]', line[3])
    [factor, offset] = line[4][1, -1].split(',')
    const[min, max] = line[5][1, -1] .split('|')
    isSigned = line[3].endswith('-')

    # Categorizes signals based on source device. If source device has a default value, use the BO_ name
    if(line[7] != 'Vector__XXX'):
        category = line[7]
    else:
        category = labelPrefix.title()
    # Automatically sets signed 1-bit signals to unsigned versions to save headaches in business logic later
    if(bitLength == '1' and isSigned):
        isSigned = False

    return{
        "name": line[1],
        "label": f"{labelPrefix}.{snake_case(line[1])}",
        "startBit": int(startBit),
        "bitLength": int(bitLength),
        "isLittleEndian": bool(int(littleEndian)),
        "isSigned": isSigned,
        "factor": float(factor),
        "offset": float(offset),
        "min": float(min),
        "max": float(max),
        "sourceUnit":  line[6][1, -1] if line[6][1, -1] else None,
        "isMultiplexor": isMultiplexor,
        "multiplexerValue": multiplexerValue,
        "dataType": "int",
        "choking": (int(bitLength) % 8 == 0),
        "visibility": True,  # ViriCiti specifc
        "interval": 1000,  # ViriCiti specific
        "category": category,  # ViriCiti specific
        "comment": comment,
        "lineInDbc": index,
        "problems": []
    }


# VAL_ 123 signalWithValues 0 "Off" 1 "On" 255 "Ignore" 254 "This device is on fire"

def extractValData(line):
    index = 3
    value = state = None
    valArray = []
    while index != len(line)-1:
        value = int(line[index])
        index += 1
        state = line[index][1:-1]
        index += 1
        valArray.append({"value": value, "state": state})
    # Grab the CAN ID and name from indexes 1 and 2 to later link states to correct signal
        return {
            "valBoLink": int(line[1]),
            'valSgLink': line[2],
            'states': valArray
        }

# SIG_VALTYPE_ 1024 DoubleSignal0 : 2;


def extractDataTypeData(line, index):
    dataType = None
    if line[4][0, -1] == "0":
        dataType = "int"
    if line[4][0, -1] == "1":
        dataType = "float"
    if line[4][0, -1] == "2":
        dataType = "double"
    if line[4][0, -1] != "2" and line[4][0, -1] != "0" and line[4][0, -1] != "1":
        raise Exception(
            f"Can't read dataType {line[4][0,-1]} at line {index} in the .dbc file. It should either be 0 (int), 1 (float) or 2 (double). This will cause unfixable incorrect data.")

#  Grab the CAN ID and name from indexes 1 and 2 to later link states to correct signal
        return {
            "dataTypeBoLink": int(line[1]),
            "dataTypeSgLink": line[2],
            "dataType": dataType
        }


# CM_ [<BU_|BO_|SG_> [CAN-ID] [SignalName]] "<DescriptionText>";
def extractCommentData(line, index):
    comment = ""
    commentBoLink = commentSgLink = None
    if line[1] == "SG_":
        commentSgLink = line[3]
    if line[1] == 'BO_':
        commentBoLink = int(line[2])
        comment = line[len(line) - 2]
    return {
        "commentBoLink": commentBoLink,
        "commentSgLink": commentSgLink,
        "comment": comment[1:len(comment)-2]
    }

