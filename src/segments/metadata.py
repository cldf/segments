# coding: utf8
from __future__ import unicode_literals, print_function, division


MD = {
    "dc:author": "",
    "dc:language": "",
    "tables": [
        {
            "dc:conformsTo": "OrthographyProfile",
            "url": "",
            "null": "NULL",
            "dialect": {
                "delimiter": "\t",
                "header": True,
                "encoding": "utf-8"
            },
            "tableSchema": {
                "columns": [
                    {
                        "name": "Grapheme",
                        "datatype": "string",
                        "required": True
                    },
                    {
                        "propertyUrl": "transliterationCol",
                        "separator": " ",
                    },
                    {
                        "name": "Left",
                        "datatype": "..."
                    }
                ],
                "primaryKey": "Grapheme"
            }
        }
    ]
}
