# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
'Fritiof for Python'
by Oskar Lundqvist / Abrovinsch (c) 2018

This module interprets the Fritiof markup language,
made for generating procedural text.

Information about how to use it can be found at:
https://github.com/abrovinsch/Fritiof-Python/blob/master/readme.md
"""

from random import randint
import re
import os

# Syntax Definitions
SYNTAX_NEW_TAG = "§"
SYNTAX_PAIR_DELIMITER = "|"
SYNTAX_INVISIBLE_MARKER = "^"
SYNTAX_SET_DICTIONARY_FOLDER = "-dictionary"
SYNTAX_INSERT_FILE = "-insert"
SYNTAX_INLINE_COMMENT = "//"
SYNTAX_FILE_ENDING = "fritiof"

UNALLOWED_SYMBOLS = "§[]{}()¨^*|#:; \n\"\'"
SYS_MAX_INT = 2147483647

class FritiofObject:
    """
    A FritiofObject contains defintions of tags and variables.
    """

    def __init__(self):
        self.tags = {}
        self.dictionary_directory = ""
        self.debug_mode = False
        self.filepath = ""

    def load(self, path_to_load):
        """Loads a .fritiof file and adds all it's data to tags"""

        # Extract the name of the file and the directory from the path
        path_to_load = os.path.expanduser(path_to_load)

        if not os.path.exists(path_to_load):
            print("Fritiof Error: No such file: %s" % path_to_load)
            return

        file_name = os.path.basename(path_to_load)
        self.dictionary_directory = os.path.dirname(path_to_load)

        # Ignore files that does not have a .fritiof extension
        if not file_name.endswith(".%s" % SYNTAX_FILE_ENDING):
            print("Fritiof Error: can only open files with the .%s extension (%s)"
                  % (SYNTAX_FILE_ENDING, file_name))
            return

        # Load the contents of the original file
        sourcefile = open(path_to_load)
        file_content = sourcefile.read()
        sourcefile.close()
        self.filepath = path_to_load

        # Insert any referenced files
        file_content = self.insert_external_files(file_content)

        # This is whatever tag we are working with
        current_tag_name = ""

        # Go through line for line
        for line in file_content.split("\n"):

            # Remove inline comments
            line = re.sub(SYNTAX_INLINE_COMMENT + r'.*', "", line)

            # Remove whitespace delimiters
            while SYNTAX_INVISIBLE_MARKER in line:
                line = line.replace(SYNTAX_INVISIBLE_MARKER, "")

            # Ignore empty lines
            if line == "":
                continue

            # Handle pairs
            if SYNTAX_PAIR_DELIMITER in line:
                parts = line.split(SYNTAX_PAIR_DELIMITER)
                line = ""
                pair_index = 0
                for part in parts:
                    pair_index = pair_index + 1
                    line += ("[pair%d:%s]" % (pair_index, part))

            # Handle tag-separation symbols
            if line.startswith(SYNTAX_NEW_TAG):
                current_tag_name = line[1:]
                if current_tag_name == "":
                    print("Fritiof Syntax Error: a tag must have a name of at least 1 (%s)" % line)
                    return

                if not is_allowed_tag_name(current_tag_name):
                    self.tags = {}
                    return
            else:
                if current_tag_name == "":
                    print("Fritiof Syntax Error: text is not within a tag (%s)" % line)
                    return
                self.add_tag(current_tag_name, line)

    def add_tag(self, tag_name, tag_contents):
        """Adds a single string to a tag. If the key is new, a new tag is created"""

        # If the tag already exists, just add it to that list
        if tag_name in self.tags:
            self.tags[tag_name].append(tag_contents)
        # Otherwise we create that list and add the first element
        else:
            self.tags[tag_name] = list()
            self.tags[tag_name].append(tag_contents)

    def get_string_from_tag(self, tag):
        """Returns a random string from a tag"""

        if self.debug_mode:
            wrapper = "{%s}"
        else:
            wrapper = "%s"

        if tag in self.tags:
            index = randint(0, len(self.tags[tag])-1)
            return wrapper % self.tags[tag][index]

        print("Fritiof Error: no such tag or variable '%s'" % tag)
        return "{%s}" % tag

    def execute(self, line_of_code):
        """Executes a single line of fritiof and returns the resulting string (if any)"""
        result = line_of_code

        find_var_setting_regex = r'\[[^:]+:[^\]]*\]'
        tagsearch_obj = re.search(r'#[^#]+#', result, flags=0)
        set_var_search_obj = re.search(find_var_setting_regex, result, flags=0)

        while tagsearch_obj or set_var_search_obj:

            # Determine what comes first, a variable setting or a string grab
            set_index = SYS_MAX_INT
            string_index = SYS_MAX_INT
            if set_var_search_obj:
                set_index = result.index(set_var_search_obj.group())
            if tagsearch_obj:
                string_index = result.index(tagsearch_obj.group())

            # Grab the first value and replace it with something from the tag
            if set_index > string_index:
                tag = tagsearch_obj.group().replace("#", "")
                if tag.endswith(".capitalize"):
                    tag = tag.replace(".capitalize", "")
                    new_string = self.get_string_from_tag(tag)
                    new_string = new_string.capitalize()
                else:
                    new_string = self.get_string_from_tag(tag)

                result = result.replace("#%s#" % tag, new_string, 1)
                tagsearch_obj = re.search(r'#[^#]+#', result, flags=0)
                set_var_search_obj = re.search(find_var_setting_regex, result, flags=0)

            # Set the first variable
            else:
                line = re.sub(r'[\[\]]', "", set_var_search_obj.group())
                parts = line.split(":")
                var_name = parts[0]
                value = parts[1]
                result = result.replace(set_var_search_obj.group(), "", 1)
                self.tags[var_name] = list()
                self.add_tag(var_name, value)
                set_var_search_obj = re.search(find_var_setting_regex, result, flags=0)
                tagsearch_obj = re.search(r'#[^#]+#', result, flags=0)

        result = result.replace("\\\"", "\"")
        return result

    def insert_external_files(self, source):
        """Inserts the content of any referenced files into the file"""
        result = ""

        for line in source.split("\n"):

            if line.startswith(SYNTAX_INSERT_FILE):
                if self.dictionary_directory == "":
                    print("Fritiof Error: No dictionary directory set!")
                    return source
                file_to_insert = line[8:]

                file_path = "%s/%s.%s" % (self.dictionary_directory,
                                          file_to_insert, SYNTAX_FILE_ENDING)
                file_path = os.path.expanduser(file_path)

                if not os.path.exists(file_path):
                    print("Fritiof Error: Cant insert non-existing file: %s" % file_path)
                    return

                sourcefile = open(file_path)
                file_contents = sourcefile.read()
                sourcefile.close()
                result += "\n" + file_contents
            elif line.startswith(SYNTAX_SET_DICTIONARY_FOLDER):
                self.dictionary_directory = line[12:]
            else:
                result += "\n" + line

        if "-insert" in result:
            result = self.insert_external_files(result)
        return result

    def test(self):
        """Continually print the results of requested tags"""
        command_input = "origin"
        last_command_input = ""

        while command_input != "exit":
            if command_input == "list_tags":
                print("Defined tags:")
                for tag in self.tags:
                    print(tag)
                command_input = input("")
                continue
            elif command_input == "export_tracery":
                self.export_tracery()
                command_input = input("")
                continue

            # Reset this object and reload the file
            self.tags = {}
            self.dictionary_directory = ""
            self.load(self.filepath)

            if command_input == "":
                command_input = last_command_input
            else:
                last_command_input = command_input

            print(self.execute("#" + command_input + "#"))
            command_input = input("")

    def export_tracery(self, compact=False):
        """Converts this Fritiof to tracery and exports it as a file"""
        if compact:
            joiner = '","'
            wrapper = '"%s":["%s"]'
            tag_separator = ","
        else:
            joiner = '",\n"'
            wrapper = '"%s":[\n"%s"\n]'
            tag_separator = ",\n\n"

        # Convert data to tracery format
        tag_strings = []
        for key in self.tags:
            tag_strings.append(wrapper % (key, joiner.join(self.tags[key])))
        output = tag_separator.join(tag_strings) + "\n"

        # Create the path of the export file
        file_name = os.path.basename(self.filepath)
        export_directory = os.path.dirname(self.filepath)

        if export_directory == "":
            export_directory = os.path.expanduser("~")

        export_filename = file_name.replace("fritiof", "tracery")
        if export_filename == "":
            export_filename = "exported_tracery"

        export_filename = export_filename.replace(".", "_") + ".txt"
        export_path = export_directory + "/" + export_filename

        outputfile = open(export_path, 'w+')
        outputfile.write(output)  # python will convert \n to os.linesep
        outputfile.close()

        print("Exported Tracery to %s" % export_path)

def test_file(file):
    """Continually tests a file"""

    test_fritiofobject = FritiofObject()
    test_fritiofobject.load(file)
    test_fritiofobject.test()

def is_allowed_tag_name(string):
    """Returns if the string is a valid name for a tag"""

    for symbol in UNALLOWED_SYMBOLS:
        if symbol in string:
            print("Fritiof Syntax Error: Unallowed symbol '%s' in tag name '§%s'"
                  % (symbol, string))
            return False
    return True
