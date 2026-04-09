def calculator_tool(query):
    try:
        return str(eval(query))
    except:
        return None

def tool_router(query):
    if any(x in query for x in ["+", "-", "*", "/"]):
        return calculator_tool(query)
    return None
