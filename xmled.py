#!/usr/bin/python

from __future__ import print_function
import sys
import argparse
from lxml import etree as xml


class ExpressionNotFoundException(Exception):
    pass

class ConfusingOutputArguments(Exception):
    pass

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def parseNameValuePairs(nameValuePairStrList):
    if nameValuePairStrList is None:
        return {}

    return dict(map(lambda x: x.split("="), nameValuePairStrList))

def readfile(filepath):
    with open(filepath) as file:
        return file.read()

def main(
sourceFileName,
xPathExpression,
text=None,
destinationFileName=None,
insertBefore=False,
inPlace=False,
namespaces={},
attributes={},
siblingsToAppend=[],
childrenToAppend=[]
):
    if inPlace and destinationFileName is not None:
        raise ConfusingOutputArguments()

    parser = xml.XMLParser()

    root = xml.parse(sourceFileName, parser)

    #eprint(str.format("DEBUG: root = {0}", xml.tostring(root)))

    elements = root.xpath(xPathExpression, namespaces=namespaces)
    #eprint(str.format("DEBUG: Found {0} elements.", len(elements)))

    if len(elements) == 0:
        raise ExpressionNotFoundException()

    for element in elements:
        # Set element text
        if text is not None:
            element.text = text

        # Set element attribute values
        for key, value in attributes.iteritems():
            element.set(key, value)

        for sibling in siblingsToAppend:
            element.addnext(xml.fromstring(sibling))

        for child in childrenToAppend:
            element.append(xml.fromstring(child))

    resultXml = xml.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True)

    def openOutput():
        if inPlace:
            return open(sourceFileName, "w")
        elif destinationFileName is None:
            return sys.stdout
        else:
            return open(destinationFileName, "w")

    with openOutput() as out:
        out.write(resultXml)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set values of elements matching <XPathExpression> in a XML document.")
    parser.add_argument("source", help="The XML document to set values in.")
    parser.add_argument("xPathExpression", help="XPath expression to elements that should be modified.")
    parser.add_argument("-o", "--output", help="The output file. Default: stdout", default=None, dest="destination")
    parser.add_argument("-i", "--in-place", action='store_true', help="Overwrite source document.", dest="inplace")
    parser.add_argument("-ns, --namespace", action='append', help="Specify namespaces. Can be used multiple times. Syntax: 'a=<namespace url>'", dest="namespaces", default=[])
    parser.add_argument("-t", "--text", help="Replace the text of matched elements.", dest="text")
    parser.add_argument("-a", "--attribute", action='append', help="Set an attribute value on matched elements.", dest="attributes", default=[])
    parser.add_argument("-as", "--append-sibling", action='append', help="Append an XML fragment as siblings to matched elements.", dest="siblingsToAppend", default=[])
    parser.add_argument("-ac", "--append-children", action='append', help="Append an XML fragment as children to matched elements.", dest="childrenToAppend", default=[])
    parser.add_argument("-asf", "--append-sibling-file", action='append', help="Append an XML fragment from file as siblings to matched elements.", dest="fileSiblingsToAppend", default=[])
    parser.add_argument("-acf", "--append-children-file", action='append', help="Append an XML fragment from file as children to matched elements.", dest="fileChildrenToAppend", default=[])

    args = parser.parse_args()

    siblingsToAppend = args.siblingsToAppend + map(lambda path: readfile(path), args.fileSiblingsToAppend)
    childrenToAppend = args.childrenToAppend + map(lambda path: readfile(path), args.fileChildrenToAppend)

    try:
        main(
            args.source,
            args.xPathExpression,
            text=args.text,
            destinationFileName=args.destination,
            inPlace=args.inplace,
            namespaces=parseNameValuePairs(args.namespaces),
            attributes=parseNameValuePairs(args.attributes),
            siblingsToAppend=siblingsToAppend,
            childrenToAppend=childrenToAppend
        )

        sys.exit(0)

    except ExpressionNotFoundException:
        eprint(str.format("ERROR: No elements matching {0} found.", args.xPathExpression))
        sys.exit(1)
    except ConfusingOutputArguments:
        eprint(str.format("ERROR: Invalid options - Both --in-place and --output specified."))
        sys.exit(2)
    except xml.XPathEvalError as ex:
        eprint(str.format("ERROR: Invalid XPathExpression {0}", args.xPathExpression))
        sys.exit(3)
