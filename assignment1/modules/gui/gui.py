# ----------------------------------------------------------------------------
# -                        Open3D: www.open3d.org                            -
# ----------------------------------------------------------------------------
# Copyright (c) 2018-2023 www.open3d.org
# SPDX-License-Identifier: MIT
# ----------------------------------------------------------------------------

import glob
import time
import numpy as np
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import os
import os.path as osp
import platform
import sys

from modules.colmap.api import ColmapAPI
from modules.gui.settings import Settings
from utils.thread_utils import run_on_thread

isMacOS = (platform.system() == "Darwin")


class AppWindow:
    MENU_OPEN_EXISTING = 11
    MENU_OPEN_IMAGE_FOLDER = 12
    MENU_OPEN_VIDEO = 13
    MENU_EXPORT = 14
    MENU_QUIT = 15
    MENU_SHOW_SETTINGS = 21
    MENU_ABOUT = 31

    DEFAULT_IBL = "default"

    def __init__(self, width, height):
        self.settings = Settings()

        # COLMAP API
        self.colmap_api = ColmapAPI(
            gpu_index=self.settings.DEFAULT_GPU_INDEX,
            camera_model=self.settings.DEFAULT_CAMERA_MODEL,
            matcher=self.settings.DEFAULT_COLMAP_MATCHER,
        )

        self.window = gui.Application.instance.create_window(
            "Open3D", width, height)
        w = self.window  # to make the code more concise

        # 3D widget
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(w.renderer)

        # Sizing
        em = w.theme.font_size
        separation_height = int(round(0.5 * em))

        # Setting panel
        self._settings_panel = gui.Vert(
            0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em))

        # GUI Control
        gui_ctrls = gui.CollapsableVert(
            "GUI settings", 0.25 * em,
            gui.Margins(em, 0, 0, 0)
        )
        self._bg_color = gui.ColorEdit()
        self._bg_color.set_on_value_changed(self._on_bg_color)
        grid = gui.VGrid(2, 0.25 * em)
        grid.add_child(gui.Label("BG Color"))
        grid.add_child(self._bg_color)
        gui_ctrls.add_child(grid)

        self._camera_color = gui.ColorEdit()
        self._camera_color.set_on_value_changed(self._on_camera_color)
        grid = gui.VGrid(2, 0.25 * em)
        grid.add_child(gui.Label("Cam Color"))
        grid.add_child(self._camera_color)
        gui_ctrls.add_child(grid)

        self._camera_size = gui.Slider(gui.Slider.DOUBLE)
        self._camera_size.set_limits(0.1, 1)
        self._camera_size.set_on_value_changed(self._on_camera_size)

        self._point_size = gui.Slider(gui.Slider.INT)
        self._point_size.set_limits(1, 10)
        self._point_size.set_on_value_changed(self._on_point_size)

        grid = gui.VGrid(2, 0.25 * em)
        grid.add_child(gui.Label("Cam Size"))
        grid.add_child(self._camera_size)
        grid.add_child(gui.Label("Point Size"))
        grid.add_child(self._point_size)
        gui_ctrls.add_child(grid)

        self._settings_panel.add_child(gui_ctrls)

        # COLMAP Control
        colmap_ctrls = gui.CollapsableVert("COLMAP settings", 0.25 * em,
                                         gui.Margins(em, 0, 0, 0))

        self._camera_models = gui.Combobox()
        for name in Settings.CAMERA_MODELS:
            self._camera_models.add_item(name)
        self._camera_models.set_on_selection_changed(self._on_colmap_camera_model_change)
        
        self._colmap_matchers = gui.Combobox()
        for name in Settings.COLMAP_MATCHERS:
            self._colmap_matchers.add_item(name)
        self._colmap_matchers.set_on_selection_changed(self._on_colmap_matcher_change)

        grid = gui.VGrid(2, 0.25 * em)
        grid.add_child(gui.Label("Camera"))
        grid.add_child(self._camera_models)
        grid.add_child(gui.Label("Matchers"))
        grid.add_child(self._colmap_matchers)
        colmap_ctrls.add_child(grid)

        h = gui.Horiz(0.25 * em)  # row 2
        self._fit_colmap_button = gui.Button("Fit Colmap")
        self._fit_colmap_button.horizontal_padding_em = 0.2
        self._fit_colmap_button.enabled = False
        self._fit_colmap_button.set_on_clicked(self._on_fit_colmap_button)
        h.add_stretch()
        h.add_child(self._fit_colmap_button)
        h.add_stretch()
        colmap_ctrls.add_child(h)

        self.colmap_ctrls = colmap_ctrls
        self._settings_panel.add_fixed(separation_height)
        self._settings_panel.add_child(self.colmap_ctrls)
        # ----

        # Normally our user interface can be children of all one layout (usually
        # a vertical layout), which is then the only child of the window. In our
        # case we want the scene to take up all the space and the settings panel
        # to go above it. We can do this custom layout by providing an on_layout
        # callback. The on_layout callback should set the frame
        # (position + size) of every child correctly. After the callback is
        # done the window will layout the grandchildren.
        w.set_on_layout(self._on_layout)
        w.add_child(self._scene)
        w.add_child(self._settings_panel)

        # ---- Menu ----
        # The menu is global (because the macOS menu is global), so only create
        # it once, no matter how many windows are created
        if gui.Application.instance.menubar is None:
            if isMacOS:
                app_menu = gui.Menu()
                app_menu.add_item("About", AppWindow.MENU_ABOUT)
                app_menu.add_separator()
                app_menu.add_item("Quit", AppWindow.MENU_QUIT)

            file_menu = gui.Menu()
            file_menu.add_item("Open existing result...", AppWindow.MENU_OPEN_EXISTING)
            file_menu.add_item("Open image folder...", AppWindow.MENU_OPEN_IMAGE_FOLDER)
            file_menu.add_item("Export Current Image...", AppWindow.MENU_EXPORT)

            if not isMacOS:
                file_menu.add_separator()
                file_menu.add_item("Quit", AppWindow.MENU_QUIT)

            settings_menu = gui.Menu()
            settings_menu.add_item("3D Reconstruction",
                                   AppWindow.MENU_SHOW_SETTINGS)
            settings_menu.set_checked(AppWindow.MENU_SHOW_SETTINGS, True)
            help_menu = gui.Menu()
            help_menu.add_item("About", AppWindow.MENU_ABOUT)

            menu = gui.Menu()
            if isMacOS:
                # macOS will name the first menu item for the running application
                # (in our case, probably "Python"), regardless of what we call
                # it. This is the application menu, and it is where the
                # About..., Preferences..., and Quit menu items typically go.
                menu.add_menu("Example", app_menu)
                menu.add_menu("File", file_menu)
                menu.add_menu("Settings", settings_menu)
                # Don't include help menu unless it has something more than
                # About...
            else:
                menu.add_menu("File", file_menu)
                menu.add_menu("Settings", settings_menu)
                menu.add_menu("Help", help_menu)
            gui.Application.instance.menubar = menu

        # The menubar is global, but we need to connect the menu items to the
        # window, so that the window can call the appropriate function when the
        # menu item is activated.
        w.set_on_menu_item_activated(AppWindow.MENU_OPEN_EXISTING, self._on_menu_open_existing)
        w.set_on_menu_item_activated(AppWindow.MENU_OPEN_IMAGE_FOLDER, self._on_menu_open_image_folder)
        w.set_on_menu_item_activated(AppWindow.MENU_EXPORT,
                                     self._on_menu_export)
        w.set_on_menu_item_activated(AppWindow.MENU_QUIT, self._on_menu_quit)
        w.set_on_menu_item_activated(AppWindow.MENU_SHOW_SETTINGS,
                                     self._on_menu_toggle_settings_panel)
        w.set_on_menu_item_activated(AppWindow.MENU_ABOUT, self._on_menu_about)
        # ----

        self._apply_settings()

    def _on_point_size(self, size):
        self.settings.material.point_size = int(size)
        self.settings.apply_material = True
        self._apply_settings()

    def _on_camera_size(self, size):
        self.settings.camera_size = size
        self.settings.apply_camera = True
        self._apply_settings()

    def _on_fit_colmap_button(self):
        self.colmap_api.estimate_cameras()

        em = self.window.theme.font_size
        dlg = gui.Dialog("Error")

        # Add the text
        dlg_layout = gui.Vert(em / 2, gui.Margins(em, em, em, em))
        self._colmap_running_label = gui.Label("Running COLMAP. Please wait ...")
        dlg_layout.add_child(self._colmap_running_label)

        self._fit_colmap_ok_button = gui.Button("Close")
        self._fit_colmap_ok_button.set_on_clicked(self._on_info_ok)
        self._fit_colmap_ok_button.enabled = False

        h = gui.Horiz()
        h.add_stretch()
        h.add_child(self._fit_colmap_ok_button)
        h.add_stretch()
        dlg_layout.add_child(h)

        dlg.add_child(dlg_layout)
        self.window.show_dialog(dlg)

        self._enable_colmap_ok_button_when_done()

    def _enable_colmap_ok_button_when_done(self):
        w = self.window
        if self.colmap_api.estimate_done():
            self._add_geometries_from_colmap()
            self._colmap_running_label.text = 'Done!'
            self._fit_colmap_ok_button.enabled = True
            w.post_redraw()
        else:
            gui.Application.instance.post_to_main_thread(w, self._enable_colmap_ok_button_when_done)

    def _on_colmap_matcher_change(self, name, index):
        self.colmap_api.matcher = name

    def _on_colmap_camera_model_change(self, name, index):
        self.colmap_api.camera_model = name

    def _apply_settings(self):
        bg_color = [
            self.settings.bg_color.red, self.settings.bg_color.green,
            self.settings.bg_color.blue, self.settings.bg_color.alpha
        ]
        self._scene.scene.set_background(bg_color)

        self._bg_color.color_value = self.settings.bg_color
        self._camera_color.color_value = self.settings.camera_color

        if self.settings.apply_material:
            self._scene.scene.update_material(self.settings.material)
            self.settings.apply_material = False

        if self.settings.apply_camera:
            self._visualize_cameras()
            self.settings.apply_camera = False

        self._point_size.double_value = self.settings.material.point_size
        self._camera_size.double_value = self.settings.camera_size

    def _on_layout(self, layout_context):
        # The on_layout callback should set the frame (position + size) of every
        # child correctly. After the callback is done the window will layout
        # the grandchildren.
        r = self.window.content_rect
        self._scene.frame = r
        width = 17 * layout_context.theme.font_size
        height = min(
            r.height,
            self._settings_panel.calc_preferred_size(
                layout_context, gui.Widget.Constraints()).height)
        self._settings_panel.frame = gui.Rect(r.get_right() - width, r.y, width,
                                              height)

    def _set_mouse_mode_rotate(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_CAMERA)

    def _set_mouse_mode_fly(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.FLY)

    def _set_mouse_mode_sun(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_SUN)

    def _set_mouse_mode_ibl(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_IBL)

    def _set_mouse_mode_model(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_MODEL)

    def _on_bg_color(self, new_color):
        self.settings.bg_color = new_color
        self._apply_settings()

    def _on_camera_color(self, new_color):
        self.settings.camera_color = new_color
        self.settings.apply_camera = True
        self._apply_settings()

    def _on_menu_open_existing(self):
        dlg = gui.FileDialog(
            gui.FileDialog.OPEN_DIR,
            "Choose result folder to load",
            self.window.theme
        )

        # A file dialog MUST define on_cancel and on_done functions
        dlg.set_on_cancel(self._on_file_dialog_cancel)
        dlg.set_on_done(self._on_load_existing_dialog_done)
        self.window.show_dialog(dlg)

    def _on_menu_open_image_folder(self):
        dlg = gui.FileDialog(
            gui.FileDialog.OPEN_DIR,
            "Choose image folder to load",
            self.window.theme
        )

        # A file dialog MUST define on_cancel and on_done functions
        dlg.set_on_cancel(self._on_file_dialog_cancel)
        dlg.set_on_done(self._on_load_image_folder_dialog_done)
        self.window.show_dialog(dlg)

    def _on_file_dialog_cancel(self):
        self.window.close_dialog()

    def _on_load_existing_dialog_done(self, filename):
        self.window.close_dialog()
        self.load_existing_result(filename)

    def _on_load_image_folder_dialog_done(self, data_path):
        self.window.close_dialog()

        self.colmap_api.data_path = data_path

        # Verify if there is any image in this folder
        if len(self.colmap_api._list_images_in_folder(self.colmap_api.image_dir)) == 0:
            self.colmap_api.data_path = None
            em = self.window.theme.font_size
            dlg = gui.Dialog("Error")

            # Add the text
            dlg_layout = gui.Vert(em / 2, gui.Margins(em, em, em, em))
            dlg_layout.add_child(gui.Label("There is no image in this folder! Choose another one."))

            ok = gui.Button("OK")
            ok.set_on_clicked(self._on_error_ok)

            h = gui.Horiz()
            h.add_stretch()
            h.add_child(ok)
            h.add_stretch()
            dlg_layout.add_child(h)

            dlg.add_child(dlg_layout)
            self.window.show_dialog(dlg)

        self._fit_colmap_button.enabled = True

    def _on_menu_export(self):
        dlg = gui.FileDialog(gui.FileDialog.SAVE, "Choose file to save",
                             self.window.theme)
        dlg.add_filter(".png", "PNG files (.png)")
        dlg.set_on_cancel(self._on_file_dialog_cancel)
        dlg.set_on_done(self._on_export_dialog_done)
        self.window.show_dialog(dlg)

    def _on_export_dialog_done(self, filename):
        self.window.close_dialog()
        frame = self._scene.frame
        self.export_image(filename, frame.width, frame.height)

    def _on_menu_quit(self):
        gui.Application.instance.quit()

    def _on_menu_toggle_settings_panel(self):
        self._settings_panel.visible = not self._settings_panel.visible
        gui.Application.instance.menubar.set_checked(
            AppWindow.MENU_SHOW_SETTINGS, self._settings_panel.visible)

    def _on_menu_about(self):
        # Show a simple dialog. Although the Dialog is actually a widget, you can
        # treat it similar to a Window for layout and put all the widgets in a
        # layout which you make the only child of the Dialog.
        em = self.window.theme.font_size
        dlg = gui.Dialog("About")

        # Add the text
        dlg_layout = gui.Vert(em / 2, gui.Margins(em, em, em, em))
        dlg_layout.add_child(gui.Label("Code framework for the lecture: CV802: Advanced 3D Computer Vision"))
        dlg_layout.add_child(gui.Label("Instructor: Hao Li"))
        dlg_layout.add_child(gui.Label("Co-Instructure: Paul"))
        dlg_layout.add_child(gui.Label("TAs: Phong Tran, Nhat Ho"))
        dlg_layout.add_child(gui.Label("Copyright (C) 2024 by Metaverse Lab, MBZUAI"))
        dlg_layout.add_child(gui.Label("License:"))
        dlg_layout.add_child(gui.Label(
            (
                "This program is free software; you can redistribute it and/or modify "
                "it under the terms of the GNU General Public Licenseas published by the Free Software Foundation; either version 2 "
                "of the License, or (at your option) any later version."
            )
        ))
        dlg_layout.add_child(gui.Label(
            (
                "This program is distributed in the hope that it will be useful, "
                "but WITHOUT ANY WARRANTY; without even the implied warranty of "
                "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the "
                "GNU General Public License for more details."
            )
        ))
        dlg_layout.add_child(gui.Label(
            (
                "You should have received a copy of the GNU General Public License "
                "along with this program; if not, write to the Free Software "
                "Foundation, Inc., 51 Franklin Street, Fifth Floor, "
                "Boston, MA  02110-1301, USA."
            )
        ))

        # Add the Ok button. We need to define a callback function to handle
        # the click.
        ok = gui.Button("OK")
        ok.set_on_clicked(self._on_about_ok)

        # We want the Ok button to be an the right side, so we need to add
        # a stretch item to the layout, otherwise the button will be the size
        # of the entire row. A stretch item takes up as much space as it can,
        # which forces the button to be its minimum size.
        h = gui.Horiz()
        h.add_stretch()
        h.add_child(ok)
        h.add_stretch()
        dlg_layout.add_child(h)

        dlg.add_child(dlg_layout)
        self.window.show_dialog(dlg)

    def _on_about_ok(self):
        self.window.close_dialog()

    def _on_error_ok(self):
        self.window.close_dialog()

    def _on_info_ok(self):
        self.window.close_dialog()

    def _on_camera_list_change(self, name, index):
        self.colmap_api.activate_camera_name = name
        self._update_camera()

    def load_existing_result(self, data_path):
        self._scene.scene.clear_geometry()

        self.colmap_api.data_path = data_path
        if self.colmap_api.check_colmap_folder_valid():
            self.colmap_api.estimate_cameras(recompute=False)
            self._add_geometries_from_colmap()
        else:
            self.colmap_api.data_path = None
            em = self.window.theme.font_size
            dlg = gui.Dialog("Error")

            # Add the text
            dlg_layout = gui.Vert(em / 2, gui.Margins(em, em, em, em))
            dlg_layout.add_child(gui.Label("Picked folder does not contain precomputed COLMAP data!"))

            ok = gui.Button("OK")
            ok.set_on_clicked(self._on_error_ok)

            h = gui.Horiz()
            h.add_stretch()
            h.add_child(ok)
            h.add_stretch()
            dlg_layout.add_child(h)

            dlg.add_child(dlg_layout)
            self.window.show_dialog(dlg)

    def _add_geometries_from_colmap(self):
        w = self.window
        if self.colmap_api.estimate_done():
            self._scene.scene.add_geometry("__model__", self.colmap_api.pcd, self.settings.material)

            # Update camera list in GUI
            if not hasattr(self, '_camera_list'):
                self.colmap_ctrls.add_child(gui.Label("Camera list"))
                self._camera_list = gui.Combobox()
                self.colmap_ctrls.add_child(self._camera_list)
                self._camera_list.set_on_selection_changed(self._on_camera_list_change)

            self._camera_list.clear_items()
            for camera_name in self.colmap_api.camera_names:
                self._camera_list.add_item(camera_name)

            self._visualize_cameras()
            self._update_camera()

            w = self.window  # to make the code more concise
            w.set_needs_layout()
        else:
            gui.Application.instance.post_to_main_thread(w, self._add_geometries_from_colmap)

    def _update_camera(self):
        bounds = self._scene.scene.bounding_box
        # self._scene.setup_camera(60, bounds, bounds.get_center())

        intrinsics, extrinsics = self.colmap_api.extract_camera_parameters(self.colmap_api.activate_camera_name)
        self._scene.setup_camera(intrinsics, extrinsics, bounds)

    def _visualize_cameras(self):
        for camera_name in self.colmap_api.camera_names:
            intrinsics, extrinsics = self.colmap_api.extract_camera_parameters(camera_name)
            camera_lines = o3d.geometry.LineSet.create_camera_visualization(
                view_width_px=intrinsics.width,
                view_height_px=intrinsics.height,
                intrinsic=intrinsics.intrinsic_matrix,
                extrinsic=extrinsics,
                scale=self.settings.camera_size
            )
            r = self.settings.camera_color.red
            g = self.settings.camera_color.green
            b = self.settings.camera_color.blue
            camera_lines.colors = o3d.utility.Vector3dVector(
                [np.array([r, g, b]),] * 8
            )
            self._scene.scene.remove_geometry(f"__cam{camera_name}__")
            self._scene.scene.add_geometry(f"__cam{camera_name}__", camera_lines, self.settings.material)

    def export_image(self, path, width, height):
        def on_image(image):
            img = image

            quality = 9  # png
            if path.endswith(".jpg"):
                quality = 100
            o3d.io.write_image(path, img, quality)

        self._scene.scene.scene.render_to_image(on_image)
