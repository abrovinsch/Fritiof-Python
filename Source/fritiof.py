# -*- coding: utf-8 -*-
#!/usr/bin/python

from sys import argv
from random import randint
import re
import os

class FritiofObject:

    # Syntax Definitions
    __symbol_new_tag = "§"
    __symbol_pair_delimiter = "|"
    __symbol_invisible_marker = "^"
    __symbol_set_dictionary_folder = "-dictionary"
    __symbol_insert_file = "-insert"
    __symbol_inline_commment = "//"
    __unallowed_symbols = "§[]{}()¨^*|#:; \n\"\'"
    __symbol_file_ending = "fritiof"

    def __init__(self):
        self.tags = {}
        self.dictionary_directory = ""
        self.debug_mode = False
        self.filepath = ""

    # Loads a .fritiof file and adds all it's data to tags
    def load(self,path_to_load):

        # Extract the name of the file and the directory from the path
        path_to_load = os.path.expanduser(path_to_load)

        if not os.path.exists(path_to_load):
            print("Fritiof Error: No such file: %s" % path_to_load)
            return

        file_name = os.path.basename(path_to_load)
        self.dictionary_directory = os.path.dirname(path_to_load)

        # Ignore files that does not have a .fritiof extension
        if not file_name.endswith(".%s" % self.__symbol_file_ending):
            print("Fritiof Error: can only open files with the .%s extension (%s)" % (self.__symbol_file_ending, file_name))
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
            line = re.sub(self.__symbol_inline_commment + r'.*',"",line)

            # Remove whitespace delimiters
            while self.__symbol_invisible_marker in line:
                line = line.replace(self.__symbol_invisible_marker,"")

            # Ignore empty lines
            if line == "":
                continue

            # Handle pairs
            if self.__symbol_pair_delimiter in line:
                parts = line.split(self.__symbol_pair_delimiter)
                line = ""
                pair_index = 0
                for part in parts:
                    pair_index = pair_index + 1
                    line += ("[pair%d:%s]" % (pair_index, part))

            # Handle tag-separation symbols
            if line.startswith(self.__symbol_new_tag):
                current_tag_name = line[1:]
                if len(current_tag_name) == 0:
                    print ("Fritiof Syntax Error: a tag must have a name of at least 1 (%s)" % line)
                    return

                if not self.is_allowed_tag_name(current_tag_name):
                    self.tags = {}
                    return
            else:
                if current_tag_name == "":
                    print ("Fritiof Syntax Error: text is not within a tag (%s)" % line)
                    return
                self.add_tag(current_tag_name,line)

    # Adds a single string to a tag. If the key is new, a new tag is created
    def add_tag(self,tag_name, tag_contents):
        # If the tag already exists, just add it to that list
        if(tag_name in self.tags):
            self.tags[tag_name].append(tag_contents)
        # Otherwise we create that list and add the first element
        else:
            self.tags[tag_name] = list()
            self.tags[tag_name].append(tag_contents)

    # Returns a random string from a tag
    def get_string_from_tag(self,tag):

        if self.debug_mode:
            wrapper = "{%s}"
        else:
            wrapper = "%s"

        if tag in self.tags:
            index = randint(0,len(self.tags[tag])-1)
            return wrapper % self.tags[tag][index]
        else:
            print ("Fritiof Error: no such tag or variable '%s'" % tag)
            return "{%s}" % tag

    # Executes a single line of fritiof and returns the resulting string (if any)
    def execute(self, line_of_code):
        result = line_of_code

        find_var_setting_regex = r'\[[^:]+:[^\]]*\]'
        tagsearch_obj = re.search(r'#[^#]+#',result,flags=0)
        set_var_search_obj = re.search(find_var_setting_regex,result,flags=0)

        while tagsearch_obj or set_var_search_obj:

            # Determine what comes first, a variable setting or a string grab
            REALLY_HIGH_NUMBER = 9223372036854775807
            set_index = REALLY_HIGH_NUMBER
            string_index = REALLY_HIGH_NUMBER
            if set_var_search_obj :
                set_index = result.index(set_var_search_obj.group())
            if tagsearch_obj :
                string_index = result.index(tagsearch_obj.group())

            grab_value_comes_first = set_index > string_index

            # Grab the first value and replace it with something from the tag
            if grab_value_comes_first:

                tag = tagsearch_obj.group().replace("#","")
                if tag.endswith(".capitalize"):
                    s = tag.replace(".capitalize","")
                    new_string = self.get_string_from_tag(s)
                    new_string = new_string.capitalize()
                else:
                    new_string = self.get_string_from_tag(tag)

                result = result.replace("#%s#" % tag,new_string,1)
                tagsearch_obj = re.search(r'#[^#]+#',result,flags=0)
                set_var_search_obj = re.search(find_var_setting_regex,result,flags=0)

            # Set the first variable
            else:
                line = re.sub(r'[\[\]]',"",set_var_search_obj.group())
                parts = line.split(":")
                var_name = parts[0]
                value = parts[1]
                result = result.replace(set_var_search_obj.group(),"",1)
                self.tags[var_name] = list()
                self.add_tag(var_name,value)
                set_var_search_obj = re.search(find_var_setting_regex,result,flags=0)
                tagsearch_obj = re.search(r'#[^#]+#',result,flags=0)

        result = result.replace("\\\"","\"")
        return result

    # Inserts the content of any referenced files into the file
    def insert_external_files(self,source):
        result = "";

        for line in source.split("\n"):

            if line.startswith(self.__symbol_insert_file):
                if self.dictionary_directory == "":
                    print("Fritiof Error: No dictionary directory set!")
                    return source
                fileToInsert = line[8:]

                sourcefile = open(self.dictionary_directory + "/" + fileToInsert + ".fritiof")
                str = sourcefile.read()
                result += "\n" + str;
            elif line.startswith(self.__symbol_set_dictionary_folder):
                self.dictionary_directory = line[12:]
            else:
                result += "\n" + line;

        if "-insert" in result:
            result = self.insert_external_files(result)
        return result

    # Returns if the string is a valid name for a tag
    def is_allowed_tag_name(self, string):
        for l in self.__unallowed_symbols:
            if l in string:
                print("Fritiof Syntax Error: Unallowed symbol '%s' in tag name '§%s'" % (l, string))
                return False
        return True

    # Continually print the results of requested tags
    def test(self):
        command_input = "origin"
        last_command_input = ""

        while command_input != "exit":
            if command_input == "list_tags":
                print("Defined tags:")
                for tag in self.tags.keys():
                    print(tag)
                command_input = input("")
                continue
            elif command_input == "export_tracery":
                self.export_tracery()
                command_input = input("")
                continue

            self.reload_file(self.filepath)

            if command_input == "":
                command_input = last_command_input
            else:
                last_command_input = command_input

            print (self.execute("#" + command_input + "#"))
            command_input = input("")

    def reload_file(self,path_to_load):
        # Reset the object
        self.tags = {}
        self.dictionary_directory = ""
        self.load(path_to_load)

    def export_tracery(self, compact = False):

        if compact:
            joiner = '","'
            wrapper = '"%s":["%s"]'
            tag_separator = ","
        else:
            joiner = '",\n"'
            wrapper = '"%s":[\n"%s"\n]'
            tag_separator = ",\n\n"

        # Convert data to tracery format
        tagStrings = []
        for key in self.tags.keys():
            tagStrings.append(wrapper % (key, joiner.join(self.tags[key])))
        output = tag_separator.join(tagStrings) + "\n"

        # Create the path of the export file
        file_name = os.path.basename(self.filepath)
        exportDirectory = os.path.dirname(self.filepath)

        if exportDirectory == "":
            exportDirectory = os.path.expanduser("~")

        exportFileName = file_name.replace("fritiof","tracery")
        if exportFileName == "":
            exportFileName = "exported_tracery"

        exportFileName = exportFileName.replace(".", "_") + ".txt"
        exportPath = exportDirectory + "/" + exportFileName

        outputfile = open(exportPath, 'w+')
        outputfile.write(output)  # python will convert \n to os.linesep
        outputfile.close()

        print("Exported Tracery to %s" % exportPath)

def test_file(file):
    testfritiofObject = FritiofObject()
    testfritiofObject.load(file)
    testfritiofObject.test()
