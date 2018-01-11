# 'Fritiof for Python'
*by Oskar Lundqvist / Abrovinsch (c) 2018*

This module interprets the Fritiof markup language,
made for generating procedural text.

Information about how to use it can be found at:
https://github.com/abrovinsch/Fritiof-Python/blob/master/readme.md*

## Functions:
### is_allowed_tag_name(string)
Returns if the string is a valid name for a tag

### test_file(file)
Continually tests a file


## Data
SYNTAX_FILE_ENDING = 'fritiof'
SYNTAX_INLINE_COMMENT = '//'
SYNTAX_INSERT_FILE = '-insert'
SYNTAX_INVISIBLE_MARKER = '^'
SYNTAX_NEW_TAG = '\xc2\xa7'
SYNTAX_PAIR_DELIMITER = '|'
SYNTAX_SET_DICTIONARY_FOLDER = '-dictionary'

# class FritiofObject
A FritiofObject contains defintions of tags and variables.

## Methods:
#### __init__(self)

### add_tag(self, tag_name, tag_contents)
Adds a single string to a tag. If the key is new, a new tag is created

### execute(self, line_of_code)
Executes a single line of fritiof and returns the resulting string (if any)

### export_tracery(self, compact=False)
Converts this Fritiof to tracery and exports it as a file

### get_string_from_tag(self, tag)
Returns a random string from a tag

### insert_external_files(self, source)
Inserts the content of any referenced files into the file

### load(self, path_to_load)
Loads a .fritiof file and adds all it's data to tags

### test(self)
Continually print the results of requested tags
