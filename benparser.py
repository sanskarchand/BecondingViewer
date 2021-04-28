from enum import Enum
import inspect

REPLACEMENT_STRING = "<omitting non-UTF-8 bytes>"

class TokenType(Enum):
    T_BYTESTRING = 1,
    T_INTEGER = 2,
    T_LIST = 3,
    T_DICTIONARY = 4,
    T_INVALID = 5,

def _identify_token(torrDataString, runIndex):
    
    f = torrDataString[runIndex]
    map_ = {
        "123456789".encode(): TokenType.T_BYTESTRING,
        "i".encode(): TokenType.T_INTEGER,
        "d".encode(): TokenType.T_DICTIONARY,
        "l".encode(): TokenType.T_LIST
    }

    for key in map_:
        if f in key:
            return map_[key]

    return TokenType.T_INVALID


def _crunch_automatic(torrDataString, runIndex):
    map_ = {
        TokenType.T_BYTESTRING: _crunch_bytestring,
        TokenType.T_INTEGER: _crunch_integer,
        TokenType.T_DICTIONARY: _crunch_dict,
        TokenType.T_LIST: _crunch_list,
    }
    
    tokenType = _identify_token(torrDataString, runIndex) 
    for key in map_:
        if key == tokenType:
            crunchingFunc = map_[key]
            return crunchingFunc(torrDataString, runIndex)

    return None



def _crunch_bytestring(torrDataString, idx):
    colIndex = torrDataString.find(":".encode(), idx)
    try:
        #e.g. "8:abcdefgh", '8' is the length
        #breakpoint()
        strLen = int(torrDataString[idx:colIndex])
        return colIndex + strLen + 1
    except Exception as e:
        print(f"{inspect.stack()[0][3]}: error: {str(e)}")
        return None


def _crunch_integer(torrDataString, idx):
    endIndex = torrDataString.find("e".encode(), idx)
    return endIndex + 1


def _crunch_list(torrDataString, idx):
    finalIndex = idx + 1
    checkChar = torrDataString[finalIndex]

    while (checkChar != "e".encode()[0]):
        finalIndex = _crunch_automatic(torrDataString, finalIndex)
        checkChar = torrDataString[finalIndex]

    
    return finalIndex + 1


def _crunch_dict(torrDataString, idx):
    finalIndex = idx + 1
    checkChar = torrDataString[finalIndex]

    while (checkChar != "e".encode()[0]):

        finalIndex = _crunch_bytestring(torrDataString, finalIndex)
        finalIndex = _crunch_automatic(torrDataString, finalIndex)
        checkChar = torrDataString[finalIndex]
    
    return finalIndex + 1

# will return a string
def _parse_automatic(torrDataString, runIndex):
    map_ = {
        TokenType.T_BYTESTRING: _parse_bytestring,
        TokenType.T_INTEGER: _parse_integer,
        TokenType.T_DICTIONARY: _parse_dict,
        TokenType.T_LIST: _parse_list,
    }
    
    tokenType = _identify_token(torrDataString, runIndex) 
    for key in map_:
        if key == tokenType:
            parsingFunc = map_[key]
            return parsingFunc(torrDataString, runIndex)

    return None


def _parse_bytestring(torrDataString, idx):
    #breakpoint()
    colIndex = torrDataString.find(":".encode(), idx)
    
    # risky operations (IndexError et cetera)
    try:
        strLenString = torrDataString[idx:colIndex]
        strLen = int(strLenString)
        byteStr = torrDataString[colIndex+1:colIndex+1+strLen]
        return byteStr.decode()
    except UnicodeDecodeError as e:
        print(f"{inspect.stack()[0][3]}: warning: {str(e)}   (idx={idx})")
        return byteStr                  # pieces cannot be decoded, of course
    except Exception as e:
        print(f"{inspect.stack()[0][3]}: error: {str(e)}")
        return None

def _parse_integer(torrDataString, idx):
    if torrDataString[idx] != "i".encode()[0]:
        return None
    
    # e.g. i42e -> the integer 42
    fIndex = torrDataString.find("e".encode(), idx)
    try:
        integerString = torrDataString[idx+1:fIndex]
        value = int(integerString)
        return value
    except Exception as e:
        print(f"{inspect.stack()[0][3]}: error: {str(e)}")
        return None

def _parse_list(torrDataString, idx):
    parsedList = []

    #breakpoint() 
    if torrDataString[idx] != "l".encode()[0]:
        return None

    runIndex = idx + 1
    checkChar = torrDataString[runIndex]

    while checkChar != "e".encode()[0]:
        item = _parse_automatic(torrDataString, runIndex)
        runIndex = _crunch_automatic(torrDataString, runIndex)

        #NOTE: use some kind of caching so that _identify_token's result is re-used?
        # assume subsequent calls

        parsedList.append(item) 
        checkChar = torrDataString[runIndex]
    
    return parsedList
    
def _parse_dict(torrDataString, idx):

    parsedDict = dict()
    
    #NOTE:  Indexing a bytes object gives an int, not a byte object
    if torrDataString[idx] != "d".encode()[0]:
        return None

    runIndex = idx + 1
    checkChar = torrDataString[runIndex]

    while checkChar != "e".encode()[0]:
        if _identify_token(torrDataString, runIndex) != TokenType.T_BYTESTRING:
            return None
        #dictKey = _parse_bytestring(torrDataString, runIndex)
        dictKey = _parse_automatic(torrDataString, runIndex)
        if not dictKey:
            return None

        runIndex = _crunch_bytestring(torrDataString, runIndex)

        # Parse and crunch the value
        dictVal = _parse_automatic(torrDataString, runIndex)
        runIndex = _crunch_automatic(torrDataString, runIndex)

        parsedDict[dictKey] = dictVal
        checkChar = torrDataString[runIndex]
    
    return parsedDict

# helper func
def get_printable_torrent(parsedTorrent):
    printableCopy = parsedTorrent.copy()
    return get_printable_torrent_helper(printableCopy)

def get_printable_torrent_helper(torrentDict):
    for key in torrentDict:
        if type(torrentDict[key]) == bytes:
            torrentDict[key] = REPLACEMENT_STRING
        elif type(torrentDict[key]) == dict:
            torrentDict[key] = get_printable_torrent_helper(torrentDict[key])

    
    return torrentDict


# --- this is the part that should be used by importers ---
def parse_torrent(torrentDataBytes):
    #breakpoint()
    parsedDict = _parse_dict(torrentDataBytes, 0)
    return parsedDict
