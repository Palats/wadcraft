Wadcraft
========

A useless-but-fun Doom level to Minecraft automatic converter.                                                                                                                                     
                                                                                                                                                                                                                                             
See [E1M1: Hangar](http://www.youtube.com/watch?v=TRsFcjgq6_U) for an example of the result.
                                                                                                                                                                                                                                             
Features:                                                                                                                                                                                                                                    

  - Render floor, ceiling, walls and so on                                                                                                                                                                                                   
  - Generate standard minecraft .schematic                                                                                                                                                                                                   
  - If pasted with the WorldEdit minecraft plugin, the player will automatically be at player 1 start for a better experience :)                                                                                                             
  - Sector with visible sky are using minecraft sky                                                                                                                                                                                          
  - Door are rendered open as much as possible                                                                                                                                                                                               
  - All textures and flats are rendered using wool blocks with the color closest to the texture as possible. Given minecraft granularity, it's not always visible, but slime will be properly green, water blue and so on.                   
  - Lighting more or less based on doom sectors light levels, but lighting model are too different between the games.                                                                                                                        
  - Should be able to render any Doom/Doom2/Ultimate doom levels and probably more with tiny adjustements.                                                                                                                                   
                                                                                                                                                                                                                                             

Basic usage:

 - First you need to setup it. Given that it needs the [NBT library](https://github.com/twoolie/NBT) and [python colormap](http://code.google.com/p/python-colormath/), something along those lines should do the trick:

        wget 'http://bitbucket.org/ianb/virtualenv/raw/tip/virtualenv.py'
        python virtualenv.py --no-site-packages --distribute env
        source env/bin/activate
        python setup.py develop

   It basically create a python virtual environment where we can easily install any dependency we need.

 - You need to generate extra information about level geometry with [glbsp](http://glbsp.sourceforge.net/):
        
        glbsp -v5 doom.wad

   glbsp creates geometry information suitable for opengl, such as convex sector with clockwise segment, which is useful for wadcraft too.

 - Then you can run it with the main iwad: 

        wadcraft --iwad doom.wad --level E1M1
    
 - That will generate a level.schematic file, that you can load into minecraft with various world editor. With WorldEdit, an in-game editor, you just need to move the schematic file in the right place, and then:

        //load level
        //paste

   By default, Wadcraft generates WorldEdit offset information in the schematic, so when pasting it you will be directly on player 1 start.
