# Fritiof Python - a python module for generating text with the Fritiof markup language

## Using Fritiof with Python

*Tip! If you don't know how Fritiof works, please consult the 'How fritiof works' section*.

To use Fritiof Python, start by importing this module and create a Fritiof object:
```python
import fritiof

my_fritiof_object = fritiof.FritiofObject()
```

Then we give the Fritiof object a .fritiof file and tell it to return a string.
Let's say we have a file named `my_fritiof_file.fritiof` and would like to print a random string from its `awesome_name` Tag. We could do it like this:
```python
my_fritiof_object.load("~/my_fritiof_file.fritiof")
awesome_name_result = my_fritiof_object.execute("#awesome_name#")
print(awesome_name_result)
```

The method `execute()` takes a fritiof statement, executes it and then returns the resulting string (if any). In this case, we feed it a `#grab#` statement, telling Fritiof to return a random item from the tag `awesome_name`.

### Using test() to test your fritiof
When writing Fritiof, it is very useful to coninually test the results of different statements. You can do this by using the test() method in the command line, likes so:
```python
my_fritiof_object = fritiof.FritiofObject()
my_fritiof_object.load("~/my_fritiof_file.fritiof")
my_fritiof_object.test()
```

Doing this will let you enter the name of any Tag in the fritiof and print a string from it, continually. If you leave the input blank, it will get one from the same tag as last time. Enter 'exit' when you want to stop testing.

*Tip! Test() automatically reloads your fritiof-files between runs so you can immediately see the results of your edits*

Another useful feature when using test() is to look at all the tags currently created. Enter `list_tags` and you will get a list of every tag defined in the fritiofObject.

### Testing for lazy people

An even easier way to just test one file is to run the following code:
```python
import fritiof
fritiof.test_file("~/documents/file_to_test.fritiof")
```

This will automatically load the file and do `test()` on it

## Exporting to Tracery / JSON

If you want to, you can export to tracery, which is used by, for example, the excellent service www.cheapbotsdonequick.com.

To do this, run the following code:

```python
import fritiof
my_fritiof_object = fritiof.FritiofObject()
my_fritiof_object.load("~/twitterbot/bot.fritiof")
my_fritiof_object.export_tracery()
```

This will create a file named *bot_tracery.txt* in the *~/twitterbot/* folder. It will overwrite any existing file with that name.

*Tip! When running test() you can enter `export_tracery` to immediately export the current version of your project to tracery*

# The Fritiof Markup Language
The Fritiof is a markup language is used to generate text combining many text-snippets. The main idea is that you define *tags*, which are lists of strings and then combine random items of those tags for interesting results. It is largely inspired by the language Tracery created by Kate Compton.

## How fritiof works
Let's say we wanted to create a random name generator, consisting of a first name and a last name. We would need to first create a list of first names and a list of last names. These lists are called **tags**. We can create the two new tags by typing:
```
§first_name
Carmencita
Fritiof

§last_name
Rönnerdahl
Anderson
```

The `§` symbol means *"Here comes a new tag named [whatever-comes after]"*. Every non-empty line following is an item in the tag.

Let's create a new tag named `full_name` which combines a random item from `first_name` with one from `last_name`, by using the grab functionality. The syntax for grab looks like this: `#tag_name_goes_here#`.

Example:
```
§full_name
#first_name# #last_name#
```

By writing `#first_name#`, we tell Fritiof to insert a random string from the list "first_name". The tag `#full_name#` might now return text such as "Carmencita Rönnderdahl" or "Fritiof Andersson".

You can grab strings recursively if you want to:
```
§inside_the_box
inside the box #inside_the_box#
is a treasure
```

Here, `#inside_the_box#` could return something like *"inside the box inside the box inside the box inside the box is a treasure"*

## Advanced Fritiof features

### Variables

You can create variables at any time by using the syntax `[variable_name:value]`.

```
§my_name_is
[name:Evert]My name is #name#.
```
Now, `my_name_is` will return "My name is Evert.". The variable `name` was set to "Evert" and then used using the #grab# syntax from earlier.

The value doesn't have to be a string literal but can just as well include #grab# statements. Example:
```
§i_have_a_pet
[pet:#animal#]I have a pet #pet#. It is a nice #pet#.

§animal
dog
cat
```

Now, `#i_have_a_pet#` will either return "I have a pet dog. It is a nice dog." OR "I have a pet cat. It is a nice cat."

*NOTE: The variables are dynamically created at runtime whenever the line of code is inserted in a string. Variable declarations are always executed left from right, depth-first.*

### Pairs

Sometimes it is handy to create pairs of associated words. For example, you might want to couple verbs and nouns together and use them in a sentence. You can create pairs by using the `A|B` syntax. This will assign **"A"** to the variable `pair1` and **"B"** to the `pair2` but it will *not* return any text.

Example:
```
§do_thing_with_pet
#clean_thing_pairs#I will #pair1# my #pair2#.

§clean_thing_pairs
ride|horse
walk|dog
feed|cat
```

This will return either "I will ride my horse." or "I will walk my dog." or "I will feed my cat"

Despite its name, a pair doesn't need to be made up of only two parts. You can add as many parts as you like and access them through `#pair3#`, `#pair4#`, `#pair5#` etc. This can be great when listing inflections of verbs or writing similar "tables":
```
§irregular_verbs
do|did|done
go|went|gone
eat|ate|eaten
```

### Emptiness markers

What if we wanted to add an empty line to our tag? Just leaving a line blank won't work since that will be ignored by the interpreter. Instead, we will have to explicitly add an empty line by printing an emptiness marker: `^`.

For instance, we might want to have a tag with 50% chance of returning "snoddas" and 50% chance of returning nothing. We would write that like this:

```
§maybe_snoddas
snoddas
^
```

The emptiness marker is also used for when you want to end a line with whitespace. Whitespace at the end of lines will be removed by the interpreter, so if you want to explicitly tell to end with, for instance, space, you can put an emptiness marker after the whitespace character.

Example:
```
§cow_with_space
cow ^
```

Here, `#cow_with_space#` would return "cow ".

## Inserting other files

If you want to, you can split your project across many files. Use *insert* to load the entire contents of a given file. The syntax for this insert looks like this: `-insert <path of file without file extension>`

To do this, however, you need to specify where the directory with the other .fritiof files exists. This directory is referred to as the *dictionary*. To specify where the dictionary-path, use this syntax: `-dictionary <path of dictionary folder>`

Let's say we have a *my_dictionary folder* with a *fruit.fritiof* and a *colors.fritiof* file which we would like to use. We could insert them like this:
```
-dictionary /users/abrovinsch/my_dictionary
-insert fruit
-insert colors

§i_want_a_fruit
I want a #color# #fruit#
```

Here, calling `#i_want_a_fruit#` would return something like "I want a blue banana" (assuming I had defined those Tags in the files).

*Note! If the file you insert is itself inserting files, you will insert those files as well*

# Support

This is just a hobby project for me and I don't give any promises to support this project, or any guarantees of quality. However, I might be able to help you or answer any questions if you reach out to me at my twitter **@kaptenskojare**. If you don't have twitter, send me an email at **lundqvist.oskar01@gmail.com**.

Good luck!

*By Oskar Lundqvist / Abrovinsch 2018*
