# DungeonFaster
A simple way to spice up your DnD (or other TTRPG) campaign and be the coolest DM ever.

This is a work in progress. 

## Requirements
- Python3.10
- Kivy
- ffpyplayer
- Media files for your campaign (maps, images, and/or audio files)

## Installation
### From Source
#### Ubuntu
```
$ sudo apt install python3 pip3
$ pip install poetry
$ ./build.sh
```

#### Windows
I'm sorry to hear that. My condolences.

### From Package
```
pip install dungeonfaster-0.0.1-py3-non-any.whl
```

## Usage
### Campaign Creation
To use DungeonFaster, you first have to create a campaign using the DF GUI
- Over-world map
  - Grid adjustment
  - Hidden tiles
- (optional) Individual locations
- (optional) Background music 
  - Over-world
  - Specific locations
  - Combat

### Running a Campaign
TODO

## Roadmap
- [x] Main GUI
- [x] Campaign creation GUI
- [x] Load campaign GUI
- [x] Run campaign GUI
  - [x] Show current party icon
  - [x] Tile selection and state responses
    - [x] On select (if revealed) -> show adjacent tiles
    - [x] Click after select -> go to location
    - [x] Click adjacent after select -> move party
  - [x] Leave location
  - [x] Play location music
  - [x] Initial DM controls
- [x] `whl` Creation and deployment
- [ ] v0.1.0 Re-work campaign GUI
- [ ] Create example campaign
- [ ] v1.0.0 Add user guide and example walk-through
