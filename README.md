Wadcraft
========

A dumb Doom WAD level to Minecraft map fragment converter.


Basic usage, it's extremely rough:

 - First you need to setup it. Given that it needs the NBT library, something along those lines should do the trick:

    wget 'http://bitbucket.org/ianb/virtualenv/raw/tip/virtualenv.py'
    python virtualenv.py --no-site-packages --distribute env
    source env/bin/activate
    python setup.py develop

 - Then you can run it with the main iwad. By default it extracts E1M1, so you need a doom 1 iwad, but it's trivial to change the level name in main.py

    wadcraft doom.wad 
    
 - That will generate a level.schematic file, that you can load into minecraft with various world editor. With WorldEdit, an in-game editor, you just need to move the schematic file in the right place, and then:

    //load level
    //paste
