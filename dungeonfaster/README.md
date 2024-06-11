# DungeonFaster

This is the main directory for the application. The `__main__.py` file is the entrypoint for 
the application. The sub-directories are broken down as follows:

## [Campaigns](campaigns)
This is the default directory for saving and loading campaigns. Campaigns are stored here as
`.json` files with absolute paths to the resource files they use on disk. Currently, the maps,
music, and other files are not copied, only referenced, so if they are moved, it can cause the 
campaign to fail to load.

## [GUI](gui)
This directory contains python files for components of the graphical user interface written in 
[kivy](https://kivy.org/).

## [Model](model)
This directory contains classes which represent the logical core of the application. Code in 
this directory should remain as independent as possible from whatever higher library is used
for the GUI ([kivy](https://kivy.org/) currently).
