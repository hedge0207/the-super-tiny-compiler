import re


def tokenizer(input):
    cur = 0
    tokens = []

    while cur < len(input):
        char = input[cur]

        if char==" ":
            cur += 1
            continue

        if char=="(":
            tokens.append({"type":"paren", "value":"("})
            cur += 1
            continue

        if char==")":
            tokens.append({"type":"paren", "value":")"})
            cur += 1
            continue
        
        if char.isdigit():
            value = ""
            while char.isdigit():
                value += char
                cur += 1
                char = input[cur]

            tokens.append({"type":"number", "value":value})
            continue

        if char == '"':
            value = ""
            cur += 1
            char = input[cur]

            while char != '"':
                value += char
                cur += 1
                char = input[cur]
            
            cur += 1
            tokens.append({"type":"string", "value":value})
            continue
        
        letters = re.compile('[a-z]')
        if letters.match(char):
            value = ""
            while letters.match(char):
                value+=char
                cur+=1
                char = input[cur]
            tokens.append({"type":"name", "value":value})
            continue

        raise TypeError("I don't know {}".format(char))
    
    return tokens


def parser(tokens):
    cur = 0

    def walk():
        nonlocal cur

        token = tokens[cur]

        if token["type"] == "number":
            cur += 1
            return {
                "type": 'NumberLiteral',
                "value": token["value"]
            }
        
        if token["type"] == "string":
            cur += 1
            return {
                "type": 'StringLiteral',
                "value": token["value"]
            }
        
        if token["type"] == "paren" and token["value"] == "(":
            cur += 1
            token = tokens[cur]

            node = {
                "type": 'CallExpression',
                "name": token["value"],
                "params": [],
            }

            cur += 1

            token = tokens[cur]

            while token["type"] != "paren" or (token["type"]=="paren" and token["value"] != ")"):
                node["params"].append(walk())
                token = tokens[cur]
            
            cur+=1
        
            return node
        raise TypeError(token["type"])
    
    ast = {
        "type":"Program",
        "body":[]
    }

    while cur < len(tokens):
        ast["body"].append(walk())
    
    return ast


def traverser(ast, visitor):
    def traverser_list(lst, parent):
        for child in lst:
            traverse_node(child, parent)

    def traverse_node(node, parent):
        methods = visitor.get(node["type"])

        if methods and methods["enter"]:
            methods["enter"](node, parent)

        node_type = node["type"]
        if node_type=="Program":
            traverser_list(node["body"], node)
        elif node_type=="CallExpression":
            traverser_list(node["params"], node)
        elif node_type == "NumberLiteral" or node_type == "StringLiteral":
            pass
        else:
            raise TypeError(node_type)
        
        if methods and methods.get("exit"):
            methods["exit"](node, parent)
    traverse_node(ast, None)


def transformer(ast):
    new_ast = {
        "type":"Program",
        "body":[]
    }

    ast["_context"] = new_ast["body"]

    def num_enter(node, parent):
        parent["_context"].append({
            "type":"NumberLiteral", 
            "value":node["value"]
            })

    def str_enter(node, parent):
        parent["_context"].append({
            "type":"StringLiteral", 
            "value":node["value"]
            })

    def call_enter(node, parent):
        expression = {
            "type":"CallExpression",
            "callee":{
                "type":"Identifier",
                "name":node["name"]
            },
            "arguments":[]
        }

        node["_context"] = expression["arguments"]

        if parent["type"] != "CallExpression":
            expression = {
                "type":"ExpressionStatement",
                "expression":expression
            }
        
        parent["_context"].append(expression)
    
    traverser(ast, {
        "NumberLiteral": {
            "enter": num_enter
        },
        "StringLiteral":{
            "enter": str_enter
        },
        "CallExpression":{
            "enter": call_enter
        }
    })
    return new_ast


def code_generator(node):
    node_type = node["type"]
    if node_type=="Program":
        return "\n".join(list(map(code_generator, node["body"])))
    elif node_type=="ExpressionStatement":
        return code_generator(node["expression"])+";"
    elif node_type=="CallExpression":
        return code_generator(node["callee"])+"("+", ".join(list(map(code_generator, node["arguments"]))) + ")"
    elif node_type=="Identifier":
        return node["name"]
    elif node_type == "NumberLiteral":
        return node["value"]
    elif node_type == "StringLiteral":
        return '"'+node["value"]+'"'
    else:
        raise TypeError(node_type)


def compiler(input_str):
    tokens = tokenizer(input_str)
    ast = parser(tokens)
    new_ast = transformer(ast)
    result = code_generator(new_ast)

    return result

result = compiler("(add 2 (subtract 4 2))")
print(result)