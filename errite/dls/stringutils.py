

def removeByteString(input:str):
    start_id = input.find("'") +1
    end_id = input.find("'", start_id)
    return input[start_id :end_id]