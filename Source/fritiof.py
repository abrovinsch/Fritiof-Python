# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
'Fritiof for Python'
by Oskar Lundqvist /
Abrovinsch (c) 2018

This module interprets the
Fritiof markup language,
made for generating procedural text.

Information about how to use it can be found at:
https://github.com/abrovinsch/Fritiof-Python/blob/master/readme.md
"""

import random
import re
import os

# --- Syntax Definitions ---
SYNTAX_NEW_TAG = "§"
SYNTAX_PAIR_DELIMITER = "|"
SYNTAX_INVISIBLE_MARKER = "^"
SYNTAX_SET_DICTIONARY_FOLDER = "-dictionary"
SYNTAX_INSERT_FILE = "-insert"
SYNTAX_INLINE_COMMENT = "//"
SYNTAX_FILE_ENDING = "fritiof"

REPLACEMENTS = {
    "\\\#":"<HASH>",
    "\\n":"<nl>",
    "\\[":"<open_square_bracket>",
    "\\]":"<close_square_bracket>"
}

UNALLOWED_SYMBOLS = "§[]{}()¨^*|#.,:; \n\"\'<>\t"
SYS_MAX_INT = 2147483647

class FritiofObject:
    """
    A FritiofObject contains
    defintions of tags and variables.
    """

    def __init__(self):
        self.tags = {}
        self.dictionary_directory = ""
        self.debug_mode = False
        self.filepath = ""
        self.usage_freqs = {}
        self.gather_stats = False

    def load(self, path_to_load):
        """Loads a .fritiof file and adds all it's data to tags."""

        # Extract the name of the file and the directory from the path
        path_to_load = os.path.expanduser(path_to_load)

        if not os.path.exists(path_to_load):
            fritiof_error("No such file: %s" % path_to_load)
            return

        file_name = os.path.basename(path_to_load)
        self.dictionary_directory = os.path.dirname(path_to_load)

        # Ignore files that does not have a .fritiof extension
        if not file_name.endswith(".%s" % SYNTAX_FILE_ENDING):
            fritiof_error("Can only open files with the .%s extension (%s)"
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

            # Ignore empty lines
            if not line:
                continue

            # Remove whitespace delimiters
            while SYNTAX_INVISIBLE_MARKER in line:
                line = line.replace(SYNTAX_INVISIBLE_MARKER, "")



            # Handle tag-separation symbols
            if line.startswith(SYNTAX_NEW_TAG):
                current_tag_name = line[1:].rstrip()
                if not is_allowed_tag_name(current_tag_name):
                    self.tags = {}
                    return
            else:
                if not current_tag_name:
                    fritiof_syntax_error("Text is not within a tag (%s)" % line)
                    return
                self.add_tag(current_tag_name, line)

    def add_tag(self, tag_name, tag_contents):
        """Adds a single string to a tag.
        If the key is new, a new tag is created."""

        strings_to_add = []
        if isinstance(tag_contents, str) and "\n" in tag_contents:
            strings_to_add = tag_contents.split("\n")
        elif isinstance(tag_contents, list):
            strings_to_add = tag_contents
        else:
            strings_to_add.append(tag_contents)

        cleaned_strings = []
        for string in strings_to_add:

            # Handle fractional chances
            find_frac_chance_regex = r'(\d+)/(\d+)\{([^\}]+)\}'
            frac_chance_match = re.search(find_frac_chance_regex,
                                           string,
                                           flags=0)
            if frac_chance_match:
                try:
                    denominator = int(frac_chance_match.group(1))
                except:
                    fritiof_syntax_error("Denominator '%s' is not a valid integer" % frac_chance_match.group(1))

                try:
                    nominator = int(frac_chance_match.group(2))
                except:
                    fritiof_syntax_error("Nominator '%s' is not a valid integer" % frac_chance_match.group(2))

                tag_content = frac_chance_match.group(3)

                if denominator > nominator:
                    fritiof_syntax_error("The denominator must not be larger than the nominator in change tag '%s'" % string)
                    return False

                frac_chance_tag = "%s_in_%s" % (denominator, nominator)

                if not frac_chance_tag in self.tags:
                    l = []
                    for i in range(denominator):
                        l.append("#v#")

                    for i in range(nominator - denominator):
                        l.append("")

                    self.add_tag(frac_chance_tag, l)
                    string = "[v:%s]#%s#" % (tag_content, frac_chance_tag)

            # Replace reserved symbols
            for key in REPLACEMENTS.keys():
                string = string.replace(key, REPLACEMENTS[key])

            # Handle pairs
            if SYNTAX_PAIR_DELIMITER in string:
                parts = string.split(SYNTAX_PAIR_DELIMITER)
                string = ""
                pair_index = 0
                for part in parts:
                    pair_index = pair_index + 1
                    string += ("[pair%d:%s]" % (pair_index, part))

            cleaned_strings.append(string)

        # If the tag already exists, just add our contents to that list
        if tag_name in self.tags:
            for string in cleaned_strings:
                self.tags[tag_name].append(string)

        # Otherwise we create that list and add the first element
        else:
            self.tags[tag_name] = list()
            for string in cleaned_strings:
                self.tags[tag_name].append(string)

    def get_string_from_tag(self, tag):
        """Returns a random string from a tag."""

        if self.debug_mode:
            wrapper = "{%s}"
        else:
            wrapper = "%s"

        if tag in self.tags:
            if self.gather_stats and tag in self.usage_freqs.keys():
                self.usage_freqs[tag] += 1
            return wrapper % random.choice(self.tags[tag])

        fritiof_error("No such tag or variable '%s'" % tag)
        return "{%s}" % tag

    def execute(self, line_of_code):
        """Executes a single line of fritiof and
        returns the resulting string (if any)."""
        result = line_of_code

        find_var_setting_regex = r'\[[^:]+:[^\]]*\]'

        tagsearch_obj = re.search(r'#[^#]+#', result, flags=0)
        set_var_search_obj = re.search(find_var_setting_regex,
                                       result,
                                       flags=0)

        while tagsearch_obj or set_var_search_obj:
            # Determine what comes first,
            # a variable setting or a string grab
            set_index = SYS_MAX_INT
            string_index = SYS_MAX_INT
            if set_var_search_obj:
                set_index = result.index(set_var_search_obj.group())
            if tagsearch_obj:
                string_index = result.index(tagsearch_obj.group())

            # Grab the first value and
            # replace it with something from the tag
            if set_index > string_index:
                tag = tagsearch_obj.group().replace("#", "")
                if tag.endswith(".capitalize"):
                    fixed_tag = tag.replace(".capitalize", "")
                    new_string = self.get_string_from_tag(fixed_tag)
                    new_string = new_string.capitalize()
                else:
                    new_string = self.get_string_from_tag(tag)

                result = result.replace("#%s#" % tag, new_string, 1)

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
        """Inserts the content of any
        referenced files into the file."""

        result = ""

        for line in source.split("\n"):
            if line.startswith(SYNTAX_INSERT_FILE):
                if not self.dictionary_directory:
                    fritiof_error("No dictionary directory set!")
                    return source
                file_to_insert = line[8:]

                file_path = "%s/%s.%s" % (self.dictionary_directory,
                                          file_to_insert, SYNTAX_FILE_ENDING)
                file_path = os.path.expanduser(file_path)

                if not os.path.exists(file_path):
                    fritiof_error("Can't insert non-existing file: %s" %
                                  file_path)
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
        """Continually print the results of requested tags."""
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
            elif command_input.startswith("tagstats"):
                if " " in command_input:
                    tags_to_test = command_input.split(" ")[1]
                else:
                    tags_to_test = "origin"

                self.print_usage_stats(tags_to_test,5000)
                command_input = input("")
                continue

            # Reset this object and reload the file
            if not command_input:
                command_input = last_command_input
            else:
                last_command_input = command_input

            print(remove_replacements(self.execute("#%s#" % command_input)))

            command_input = input("")

            self.tags = {}
            self.dictionary_directory = ""
            self.load(self.filepath)

    def export_tracery(self, compact=False, open_on_export=True):
        """Converts this Fritiof to tracery
        and exports it as a file."""
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
            # Escape all quote symbols
            tag = self.tags[key]
            tag = [w.replace('"', '\\"') for w in tag]
            tag_strings.append(wrapper % (key, joiner.join(tag)))

        output = tag_separator.join(tag_strings) + "\n"
        output = "{\n%s\n}\n" % remove_replacements(output)
        output = output.replace("\\[", "[")
        output = output.replace("\\]", "]")

        # Create the path of the export file
        file_name = os.path.basename(self.filepath)
        export_directory = os.path.dirname(self.filepath)

        if not export_directory:
            export_directory = os.path.expanduser("~")

        export_filename = file_name.replace("fritiof", "tracery")
        if not export_filename:
            export_filename = "exported_tracery"

        export_filename = export_filename.replace(".", "_") + ".txt"
        export_path = os.path.join(export_directory, export_filename)

        outputfile = open(export_path, 'w+')
        outputfile.write(output)  # python will convert \n to os.linesep
        outputfile.close()

        fritiof_msg("Exported Tracery to %s" % export_path)

        if open_on_export:
            os.system('open -a TextEdit "%s"' % export_path)

        return output

    def print_usage_stats(self, tag, tests):
        """Executes a tag [tests] times and
         see which tags it uses most"""

        # Check parameters
        if not tag in self.tags or tests < 1:
            return False

        self.usage_freqs = {el:0 for el in list(self.tags.keys())}
        self.gather_stats = True

        # Gather usage statistics data
        for _ in range(tests):
            self.execute("#%s#" % tag)

        # Reset the stats when done
        self.gather_stats = False

        # Create a table with data
        table = {}
        for key in self.usage_freqs:
            amount = len(self.tags[key])
            freq = self.usage_freqs[key]
            table[key] = (freq, amount, freq/amount/tests)

        table_items = sorted(list(table.keys()), key=lambda x: table[x][0])
        table_items.reverse()

        # Print the table
        left_margin = 30
        print("\n" + " " * left_margin + "   FREQ  SIZE  REL FREQ")

        for item in table_items:
            # Ignore tags which are percentage functions
            # or tags with less than 3 items
            if table[item][0] < 1 or table[item][2] == 1 or "_in_" in item or table[item][1] < 3:
                continue

            rel_frequency = table[item][2] * 100

            col = "\033[96m"
            if rel_frequency > 1:
                col = "\033[91m"
            elif rel_frequency >= 0.5:
                col = "\033[93m"
            elif rel_frequency >= 0.1:
                col = "\033[92m"

            cell_rel_frequency = "{0}{1}%{2}".format(col, "%4.2f" % (rel_frequency), "\033[0m")
            cell_frequency = "%3.0d" % (table[item][0] / (tests) * 100) + "%"
            cell_tags_size = "%4d" % table[item][1]

            line = " " * (left_margin - len(item)) + item
            line += " | {0} |{1} | {2}".format(cell_frequency,
                                               cell_tags_size,
                                               cell_rel_frequency)
            print(line)

        self.usage_freqs = {} # Reset the usage statistics table
        return table

def test_file(file):
    """Continually tests a file."""

    print("Testing %s..." % file)
    test_fritiofobject = FritiofObject()
    test_fritiofobject.load(file)
    test_fritiofobject.test()

def is_allowed_tag_name(string):
    """Returns if the string is a valid name for a tag."""
    if not string:
        fritiof_syntax_error("A tag must have a name of at least 1 (%s)" % string)
        return False

    for symbol in UNALLOWED_SYMBOLS:
        if symbol in string:
            fritiof_syntax_error("Unallowed symbol '%s' in tag name '§%s'" % (symbol, string))
            return False
    return True

def remove_replacements(string):
    """Returns the given string without any replacements"""
    for key, val in REPLACEMENTS.items():
        string = string.replace(val, key)
    return string

def fritiof_error(msg):
    """Print an error"""
    print("\033[93mFritiof Error:\033[0m %s" % msg)

def fritiof_syntax_error(msg):
    """Print a syntax error"""
    print("\033[91mFritiof Syntax Error:\033[0m %s " % msg)

def fritiof_msg(msg):
    """Print a message"""
    print("\033[92m%s\033[0m" % msg)
