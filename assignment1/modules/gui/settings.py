import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering


class Settings:
    UNLIT = "defaultUnlit"
    LIT = "defaultLit"
    NORMALS = "normals"
    DEPTH = "depth"

    DEFAULT_GPU_INDEX = 0

    DEFAULT_DOWNSAMPLE_FACTOR = 1

    DEFAULT_CAMERA_MODEL = "OPENCV"
    CAMERA_MODELS = [
        DEFAULT_CAMERA_MODEL, 
        'SIMPLE_PINHOLE', 'PINHOLE',
        'SIMPLE_RADIAL', 'RADIAL',
        'FULL_OPENCV',
        'SIMPLE_RADIAL_FISHEYE', 'RADIAL_FISHEYE',
        'OPENCV_FISHEYE', 
        'FOV',
        'THIN_PRISM_FISHEYE'
    ]

    DEFAULT_COLMAP_MATCHER = 'exhaustive_matcher'
    COLMAP_MATCHERS = [
        DEFAULT_COLMAP_MATCHER,
        'vocab_tree_matcher',
        'sequential_matcher'
    ]

    DEFAULT_MATERIAL_NAME = "Polished ceramic [default]"
    PREFAB = {
        DEFAULT_MATERIAL_NAME: {
            "metallic": 0.0,
            "roughness": 0.7,
            "reflectance": 0.5,
            "clearcoat": 0.2,
            "clearcoat_roughness": 0.2,
            "anisotropy": 0.0
        },
        "Metal (rougher)": {
            "metallic": 1.0,
            "roughness": 0.5,
            "reflectance": 0.9,
            "clearcoat": 0.0,
            "clearcoat_roughness": 0.0,
            "anisotropy": 0.0
        },
        "Metal (smoother)": {
            "metallic": 1.0,
            "roughness": 0.3,
            "reflectance": 0.9,
            "clearcoat": 0.0,
            "clearcoat_roughness": 0.0,
            "anisotropy": 0.0
        },
        "Plastic": {
            "metallic": 0.0,
            "roughness": 0.5,
            "reflectance": 0.5,
            "clearcoat": 0.5,
            "clearcoat_roughness": 0.2,
            "anisotropy": 0.0
        },
        "Glazed ceramic": {
            "metallic": 0.0,
            "roughness": 0.5,
            "reflectance": 0.9,
            "clearcoat": 1.0,
            "clearcoat_roughness": 0.1,
            "anisotropy": 0.0
        },
        "Clay": {
            "metallic": 0.0,
            "roughness": 1.0,
            "reflectance": 0.5,
            "clearcoat": 0.1,
            "clearcoat_roughness": 0.287,
            "anisotropy": 0.0
        },
    }

    def __init__(self):
        self.mouse_model = gui.SceneWidget.Controls.ROTATE_CAMERA

        self.bg_color = gui.Color(0, 0, 0)

        self.camera_color = gui.Color(0.784, 0.526, 0.973)
        self.camera_size = 0.3
        self.apply_camera = False

        self.image_downsample_factor = 0

        self.material = rendering.MaterialRecord()
        self.material.base_color = [0.9, 0.9, 0.9, 1.0]
        self.material.point_size = 5
        self.apply_material = False
