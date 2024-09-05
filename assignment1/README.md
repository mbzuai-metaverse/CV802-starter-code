# Assignment #1: Structure from Motion
## Introduction
This assignment aims to give you a hands-on experience with Structure from Motion (Sfm) and Multi-view Stereo applications.
Specifically, your task in this assignment is to build an application that can reconstruct the camera parameters and a coarse point cloud
from multi-view images or a monocular video, visualize and interact with them. 

To make your life easier, in this repo, we provide a starter code that has already implemented the basic GUI functionalities. After completing the assignment,
your application should like the above example:

![colmap_example](./assets/examples/colmap.gif)


## Installing Dependencies
This assignment is tested on Ubuntu and MacOS. If you use other operator systems, please get in touch with the TAs if you need help installing the starter code.

We recommend using Conda to install the starter code. You can create a conda environment using:
```
conda create -n cv802 python=3.10
```

Then use pip to install the dependencies:
```
pip install -r requirements.txt
```

**Important notice:** If you use numpy version later than `2.0.0`, open3d will give segmentation faults without any error. Therefore, remember to downsample it to, for example, `1.26.1` first.

## Running the Code and Preparing the Data
To start the application, run:
```
python main.py
```

Preparing the data to run the application is fairly simple. Your data folder should have the following format:
```plaintext
your_data_name/
├── images/
│   └── *.[png|jpeg|jpg|webp]
```

## GUI Basics
#### Data Loading
- `File/Open Existing Results`: Load a folder that contains precomputed results. Please check the preparing data section.
- `File/Open Image Folder`: Load a folder that contains the images to run SfM. Please check the preparing data section.

#### GUI settings
- BG Color: Pick the background color.
- Cam Color: Pick the camera visualizer color.
- Cam size: Set the sizes of camera visualizers.
- Point size: Size of the points in the point cloud.

#### COLMAP settings
- Camera: [Camera models](https://colmap.github.io/cameras.html)
- Matcher: [Feature matchers](https://colmap.github.io/tutorial.html#feature-matching-and-geometric-verification)

#### Interaction
- Pointcloud interactions: You can use your mouse to rotate (left click), translate (left and right clicks at the same time), and zoom in/out (mouse wheel) the point cloud
- After fitting COLMAP, the camera list will appear in the panel. You can choose any camera from that list to view the point cloud from that camera's viewpoint.


## Tasks
Your only task is to complete the method `_estimate_cameras` in `modules/colmap/api.py`. Please follow the instructions given in the comments in the code.

## Free tips
- There are many tricks to speed up COLMAP (e.g., use vocab or sequential matcher, limit the number of feature points, downsample images, etc).
If your machine does not have a GPU, consider using them.
- There is a Python binding for COLMAP called [Pycolmap](https://github.com/colmap/pycolmap). You can use this to make your code cleaner instead 
of calling colmap commands using `subprocess` or `os.system`.
- If your COLMAP runs too slow, double-check if it was compiled with CUDA.
- Remember to cache your results as instructed in the code comments. Otherwise, you will have to wait for a long time every time running the code
- To extract frames from your video, use `ffmpeg`.
- Contact TAs (Building 1A, second floor) if you have any issues.

## Grading

You will get up to 20 extra credits for this assignment if you implement any of the following:
- Reimplement any step of SfM without using COLMAP or any similar external library.
- Implement new features for the GUI. For example, adding new matches beside the provided matchers, loading video directly, adding other 
COLMAP parameters, etc. You need to discuss with the TAs first.
