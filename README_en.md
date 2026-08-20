# Terminal Viewer
[中](README_zh.md) | [En](README_en.md)

Terminal Viewer is a Python module for displaying images in a specific format in the terminal.

## How does it work?

Terminal Viewer uses ANSI escape sequences to set both the foreground color and background color of the single character `▄` (lower half block) at the same time in the terminal. This creates the effect of a single character displaying two independent pixels. By assigning different foreground and background colors to `▄` and combining them, a complete image can be formed.

## How to use it?
- Install dependencies
```text
pip install -r requirements.txt
```

- View an image

```python
from tv import *  # Import functions
show_photo(load("your_photo.pic"))  # Load and view; the format must be an image, otherwise an error will be raised
```

- Play a video

```python
from tv import *  # Import functions
play_video(load("your_video.vid"))  # Load and play; the format must be a video, otherwise an error will be raised
# You can also specify the frame rate: play_video(load("your_video.vid"),fps=60)
```

- Parse first, then play

```python
from tv import *  # Import functions
data = parse_frames(load("your_video.vid"))  # Load and parse; the format must be a video, otherwise an error will be raised
play_parsed_video(data)
# You can also specify the frame rate: play_parsed_video(data,fps=60)
```

- Parse first, then view

```python
from tv import *  # Import functions
data = parse(load("your_photo.pic"))  # Load and parse; the format must be an image, otherwise an error will be raised
show_parsed_photo(data)
```

## Functions

| Function Name | Parameters | Description | Return Type |
|:------:|:------:|:------:|:------:|
|**transform**|ur:**int**, ug:**int**, ub:**int**, lr:**int**, lg:**int**, lb:**int**, char:**str** = **_char**|`ur/g/b` correspond to the RGB values of the upper half-block, and `lr/g/b` correspond to the RGB values of the lower half-block. Returns a single half-block character with both foreground and background colors set (two pixels stacked vertically).|**str**|
|**parse**|lst:**tuple[tuple[tuple[int,int,int,int,int,int]]]**, char:**str** = **_char**|`lst` corresponds to a single-frame image and returns a processed image (a string-based image that can be displayed directly).|**str**|
|**play_video**|lst:**tuple[tuple[tuple[tuple[int,int,int,int,int,int]]]]**, char:**str** = **_char**, fps:**int** = **30**|`lst` corresponds to a multi-frame image, and `fps` is the frame rate. Default is 30 fps. No return value.|**NoneType**|
|**show_photo**|lst:**tuple[tuple[tuple[int,int,int,int,int,int]]]**, char:**str** = **_char**|Same as the `parse` function.|**NoneType**|
|**save**|lst:**tuple[tuple[tuple[int,int,int,int,int,int]]]** \| **tuple[tuple[tuple[tuple[int,int,int,int,int,int]]]]**, path:**str**, level:**int** = **3**|Serializes `lst` and saves it to `path` after compression at level `level`.|**NoneType**|
|**load**|path:**str**|Opens the file at `path`, validates it, and if validation succeeds, returns the deserialized decompressed data; otherwise raises an error. (Do not load data from untrusted sources.)|**tuple[tuple[tuple[int,int,int,int,int,int]]]** \| **tuple[tuple[tuple[tuple[int,int,int,int,int,int]]]]**|
|**myprint**|text:**str**|Writes `text` to the buffer and flushes immediately.|**NoneType**|
|**show_parsed_photo**|data:**str**, char:**str** = **_char**|Same as `show_photo`, but accepts already parsed data.|**NoneType**|
|**play_parsed_video**|lst:**tuple[str]**, char:**str** = **_char**, fps:**int** = **30**|Same as `play_video`, but accepts already parsed data.|**NoneType**|
|**parse_frames**|lst:**tuple[tuple[tuple[tuple[int,int,int,int,int,int]]]]**, char:**str** = **_char**|Converts a video tuple into a tuple of strings for use with `play_parsed_video`.|**tuple[str]**|

## Where do the image data come from?

- You can feed [`tv.py`](tv.py) and [`prompt_zh.md`](prompt_zh.md) to an AI and describe the image or video you want to generate, for example:

```text
Generate a picture of the sun rising over a hill, save the file to the current directory automatically, do not preview it, use the .pic suffix, 512x512 pixels
```

- Or:

```text
Generate an aurora video, 100x50, 60fps, 60 seconds, save the file to the current directory automatically, do not preview it, set the compression level to 22, and ignore memory usage concerns
```

> The AI-generated data may not always look perfect...

- You can also write your own image processing script and convert the image to the format required by [`tv.py`](tv.py). In that case, the result will usually look much better.

## Effect

- Video

![Aurora 1](image/video1.png)
![Aurora 2](image/video2.png)

---

- Image

![Sunrise](image/pic.png)

# License

[Mozilla Public License, v. 2.0.](LICENSE)