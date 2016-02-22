# MCML
A HTML/XML for creating Minecraft command block structures

#### NOTE
This script is just a first proof of concept.
It will be compacted in the future.

#### What is this?
This scipt provides an interpreter of a small HTML/XML like language I designed: MCML
With easy to use tags you can design complicated command block structures in a text file and later clone them into your world.

## Documentation
  1. Setup
  2. Basic file layout/ a new project
  3. Markup tags
  4. Special syntax
  5. Bug tracking
  6. Compiling/exporting to a world
  

#### 1: Setup
Setup of MCML is quite easy. First of all, you'll need a Minecraft server. 
Second, you'll also need Python. MCML was designed for python 3, (I wrote it using Python 3.5). It may work on Python 2, although I cannot guarantee it. You can download Python from python.org.
The third and final step is setting up MCML. Download mcml.py and put in a folder (preferably your server folder)

#### 2: Basic file layout/ a new project
To start a new project, just simply create a new text file and open it in your favourite editor.
It's a good practice to start your project with a comment describing it. Comments can be made using Python style `#` or C style `//`

After that, you should write something similar to the following:
```
<start>
    <x>X</x>
    <y>Y</y>
    <z>Z</z>
</start>
```

On the places of the X, Y and Z you should write the coordinates your structure will be placed on.

After that, you add a `direction` tag:
```
<direction></direction>
```

This indicates the direction the command blocks will be placed in. The content should be any of `x`, `+x`, `-x`, `z`, `+z` or `-z`.
    
Now you should start making your setup logic. This is a line of command blocks which creates all scoreboard objectives, teams, sets gamerules, etc.
The blocks of the setup logic will be placed starting from the point given in the `start` tag in the direction of the `direction` tag.

To create the setup, just write your commands between some `setup` tags:
```
<setup>
    /somecommand
    /anothercommand
    etc...
</setup>
```
Besides the `setup` tag, you should also provides the following tags in a similar way (you should at least provide an empty implementation):
  1. `teardown`: The opposite of setup. Should remove scoreboard objectives, reset gamerule, etc. Usually not implemented.
  2. `spawning`: Handle player spawning.
  3. `startup`: When making a minigame, these command blocks should start the game.
  4. `reset`: When making a minigame or something like that, these command blocks should reset everything.
  
Note that all tags should be placed in the order stated above. All the command block sections from those tags will be stacked on top of eachother, with a one block space between the sections, starting from the initial given starting coordinates.

Now you can start the real work!
The final top-level tag is the `blocks` tag. It contains sections with command blocks.
The basic layout of the `blocks` tag is as follows:
```
<blocks>
    <start>
        <relative></relative>
        <x></x>
        <y></y>
        <z></z>
    </start>
    sections...
</blocks>
```
The `x`, `y` and `z` again indicate the starting point of the command blocks. 
The `relative` tag, which contains either a `0` or a `1`, indicates if the coordinates are relative from the original starting point (in the first `start` tag)

The rest of the `blocks` tags should be filled with `section`s.
The definition of a section if as follows:
```
<section>
    <name></name>
    <start>
        <relative></relative>
        <x></x>
        <y></y>
        <z></z<
    </start>
    commands...
</section>
```
Most of the tags are explained earlier and are pretty straightforward, except for the `relative` tag.
When the `relative` tag is `0`, the section will be placed relative of the starting coordinates of the `blocks` section. If it is `1`, the section will be placed relative of the previous section. (When no section has been placed yet, it will be placed relative from the `start` tag of the `blocks` tag)

Also, the name tag is just an identifier. It will be covered in more detail in part 4.

To summarize everything we've covered, here is a small example script:
```
# A small example MCML script.
<start>
    <x>0</x>
    <y>90</y>
    <z>90</z>
</start>

<direction>x</direction>

<setup>
    # The impulse tag will be covered in the next chapter
    <impulse> 
        /scoreboard objectives add Times dummy
    </impulse>
</setup>

# For the sake of not repeating too much, I'll skip the 'teardown', 'spawning', 'startup' and 'reset' tags.
# However, they have the same base-layout as the 'setup' tag.

<blocks>
    <start>
        <relative>1</relative>
        <x>0</x>
        <y>0</y>
        <z>2</z>
    </start>
    <section>
        <name>CommandBlocks</name>
        <start>
            <relative>1</relative>
            <x>0</x>
            <y>0</y>
            <z>0</z>
        </start>
        /tellraw @a[score_Times=10] {"text":"Hello!"}
        /scoreboard players add @a[score_Times=10] Times 1
    </section>
</blocks>
```

#### 3: Markup tags
The language featues some markup tags:
  1. `auto`
  2. `conditional`
  3. `impulse`
  4. `chain`
  5. `repeating`
    
The `chain`, `impulse` and `repeating` tags determine the command block type. A type tag cannot contain another type tag.
When no type tag is given, the first command block is considered a `repeating` command block. The others will be considered `chain` command blocks.

The `auto` tag indicates the command blocks should not require redstone. This is generally what you would want to use when making command block chains.

The `conditional` tag indicates that command blocks should be conditional.

Each tag affects the command blocks until it is closed. A tag can contain multiple command blocks and also other takes. The order of the tag doesn't matter. If you don't close a tag, it will affect all command blocks until the end of the `section`.

These markup tags can both be used in `setup` tags and in `section` tags.

#### 4: Special syntax

###### Referencing other sections
As mentioned before, each `section` has a name. (Even the setup section gets automaticly assigned the name 'setup').
You can reference section by their name using the `$<name>` syntax. This field will later be replaced by a setblock command with the coordinates of the specified section.

For instance, when you would have the following script:
```
# We don't write the start, direction and setup tags, too much work :)
<blocks>
    <section>
        <name>SectionA</name>
        <impulse>
            $<SectionB> redstone_block
        </impulse>
    </section>
    <section>
        <name>SectionB</name>
        <impulse>
            /say Hello!
        </impulse>
    </section?
</blocks>
```
Note that you still have to specify which block you want to place.

Also note the inserted coordinates are actually the starting coordinates of the section minus 2 in the opposite of the block direction: A repeater will be placed in front of the section. The placed redstone block will thus power the repeater, and not the first command block in the section directly.

#### 5: Bug tracking
Everytime an error occurs while parsing your script. an error message in the form
`filename: line n: message` will appear. Using these messages you should be able to debug your script.

When something goes seriously wrong because of a bug in the interpreter, you will see a traceback, something like this:
```
>>> 1 / 0
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ZeroDivisionError: division by zero
```
But of course with an other error. If you ever encounter such an error, please report it, **with traceback/ error message and your script** on the Github page of the project (on the bug tracker)

#### 6: Compiling/ exporting to a world
**NOTE: This example assumes you have python added to your PATH**

To export the command blocks to your world, you must use the command line.
The most basic command to export your command blocks is:
```
python mcml.py -f myproject.txt
```
The arguments you can supply are:
  1. -jar: The path to your server. Defaults to 'minecraft_server.jar'
  2. -f, --files: A list of the files to be interpreted
  3. -c, --close-server: Flag indicating your server should be closed after the command blocks are placed.
  
    



