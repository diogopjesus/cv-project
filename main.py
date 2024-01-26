from threading import Thread
import queue

from typing import List

from OpenGL.GL import *
import glm

import numpy as np
import pygame as pg

from core import *

""" HELPER FUNCTIONS """

def READ_ASSETS(path: str) -> dict:
    import json
    import sys

    assets = {} 
    try:
        with open(path, "r") as file:
            assets = json.load(file)
    except Exception as e:
        message = "Could not load assets database: "
        print(message, e, file=sys.stderr)
        sys.exit(1)
    finally:
        return assets


""" GLOBAL VARIABLES """

ASSETS_PATH="assets.json"
ASSETS=READ_ASSETS(ASSETS_PATH)

DEFAULT_CONFIGURATION_VALUES = {
    "clearColor": [0,0,0,1],
    "fovy": 45,
    "nearPane": 0.01,
    "farPane": 100,
    "cameraXpos": 0,
    "cameraYpos": 0,
    "cameraZpos": 0,
    "cameraPitch": 0,
    "cameraYaw": 0,
    "dirLightDirection": (0,0,0),
    "dirLightAmbient": (1,1,1),
    "dirLightDiffuse": (0,0,0),
    "dirLightSpecular": (0,0,0),
    "spotLightAmbient": (0,0,0),
    "spotLightDiffuse": (0,0,0),
    "spotLightSpecular": (0,0,0),
    "spotLightConstant": 1.0,
    "spotLightLinear": 0.09,
    "spotLightQuadratic": 0.032,
    "spotLightCutOff": 12.5,
    "spotLightOuterCutOff": 15.0,
}
CONFIGURATION_VALUES = DEFAULT_CONFIGURATION_VALUES.copy()

SIMULATION_RUNNING=True

SKYBOX_QUEUE = queue.Queue()
TERRAIN_QUEUE = queue.Queue()
SPOTLIGHT_QUEUE = queue.Queue()
POINTLIGHT_QUEUE = queue.Queue()
MODEL_QUEUE = queue.Queue()

""" GUI CLASS """

class ScedGUI:
    import dearpygui.dearpygui as dpg
    
    def __init__(self):
        self.widgets = {}
        self.pointLightEnabled = [False for i in range(10)]
        self.modelCount = 0

        ScedGUI.dpg.create_context()
        ScedGUI.dpg.create_viewport(title="Configurator", width=300, height=800)
        self.__initWindow()
        ScedGUI.dpg.setup_dearpygui()
        ScedGUI.dpg.show_viewport()
        ScedGUI.dpg.set_primary_window("Primary window", True)

    def __initWindow(self):
        with ScedGUI.dpg.handler_registry():
            ScedGUI.dpg.add_key_down_handler(ScedGUI.dpg.mvKey_Escape, callback=ScedGUI.__escape_callback)
        
        with ScedGUI.dpg.window(tag="Primary window") as pw:
            self.widgets["clearColor"] = ScedGUI.dpg.add_color_picker(label="Clear Color", default_value=[0,0,0,1], display_type=ScedGUI.dpg.mvColorEdit_float, display_rgb=True, callback=ScedGUI.__clearColor_callback)
            
            with ScedGUI.dpg.collapsing_header(label="Perpective"):
                self.widgets["fovy"] = ScedGUI.dpg.add_slider_int(label="Fovy", default_value=45, min_value=1, max_value=179, callback=ScedGUI.__fovy_callback)
                self.widgets["nearPane"] = ScedGUI.dpg.add_slider_float(label="Near Pane", default_value=0.01, min_value=0.01, max_value=1000, callback=ScedGUI.__nearPane_callback)
                self.widgets["farPane"] = ScedGUI.dpg.add_slider_float(label="Far Pane", default_value=100, min_value=0.01, max_value=1000, callback=ScedGUI.__farPane_callback)
                
            with ScedGUI.dpg.collapsing_header(label="Camera"):
                minv = -10
                maxv = 10
                ScedGUI.dpg.add_3d_slider(label="Position", default_value=(0,0,0), min_x=minv, max_x=maxv, min_y=minv, max_y=maxv, min_z=minv, max_z=maxv, callback=ScedGUI.__cameraPos_callback)
                
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_float(label="X-Pos", default_value=0, callback=ScedGUI.__cameraXpos_callback)
                    ScedGUI.dpg.add_slider_float(source=flatSource, default_value=0, min_value=-20, max_value=20, callback=ScedGUI.__cameraXpos_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_float(label="Y-Pos", default_value=0, callback=ScedGUI.__cameraYpos_callback)
                    ScedGUI.dpg.add_slider_float(source=flatSource, default_value=0, min_value=-20, max_value=20, callback=ScedGUI.__cameraYpos_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_float(label="Z-Pos", default_value=0, callback=ScedGUI.__cameraZpos_callback)
                    ScedGUI.dpg.add_slider_float(source=flatSource, default_value=0, min_value=-20, max_value=20, callback=ScedGUI.__cameraZpos_callback)
                
                ScedGUI.dpg.add_slider_int(label="Pitch", default_value=0, min_value=-90, max_value=90, format="%d deg", callback=ScedGUI.__cameraPitch_callback)
                ScedGUI.dpg.add_slider_int(label="Yaw", default_value=0, min_value=-180, max_value=180, format="%d deg", callback=ScedGUI.__cameraYaw_callback)
            
            ScedGUI.dpg.add_combo(label="Skybox", items=[""]+self.__get_skybox_ids(), callback=self.__skybox_callback)
            
            ScedGUI.dpg.add_combo(label="Terrain", items=[""]+self.__get_terrain_ids(), callback=self.__terrain_callback)

            with ScedGUI.dpg.collapsing_header(label="Directional Light"):
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_floatx(label="Direction", size=3, default_value=[0,0,0], min_value=0, max_value=1, min_clamped=True, max_clamped=True, callback=ScedGUI.__dirLightDirection_callback)
                    ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=1, default_value=[0,0,0], callback=ScedGUI.__dirLightDirection_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_floatx(label="Ambient", size=3, default_value=[1,1,1], min_value=0, max_value=1, min_clamped=True, max_clamped=True, callback=ScedGUI.__dirLightAmbient_callback)
                    ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=1, default_value=[1,1,1], callback=ScedGUI.__dirLightAmbient_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_floatx(label="Diffuse", size=3, default_value=[0,0,0], min_value=0, max_value=1, min_clamped=True, max_clamped=True, callback=ScedGUI.__dirLightDiffuse_callback)
                    ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=1, default_value=[0,0,0])
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_floatx(label="Specular", size=3, default_value=[0,0,0], min_value=0, max_value=1, min_clamped=True, max_clamped=True, callback=ScedGUI.__dirLightSpecular_callback)
                    ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=1, default_value=[0,0,0])
                
            with ScedGUI.dpg.collapsing_header(label="Spot Light"):
                ScedGUI.dpg.add_checkbox(label="Toggle", default_value=False, callback=ScedGUI.__toggleSpotLight_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_floatx(label="Ambient", size=3, default_value=[0,0,0], min_value=0, max_value=1, min_clamped=True, max_clamped=True, callback=ScedGUI.__spotLightAmbient_callback)
                    ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=1, default_value=[0,0,0], callback=ScedGUI.__spotLightAmbient_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_floatx(label="Diffuse", size=3, default_value=[0,0,0], min_value=0, max_value=1, min_clamped=True, max_clamped=True, callback=ScedGUI.__spotLightDiffuse_callback)
                    ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=1, default_value=[0,0,0], callback=ScedGUI.__spotLightDiffuse_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_floatx(label="Specular", size=3, default_value=[0,0,0], min_value=0, max_value=1, min_clamped=True, max_clamped=True, callback=ScedGUI.__spotLightSpecular_callback)
                    ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=1, default_value=[0,0,0], callback=ScedGUI.__spotLightSpecular_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_float(label="Constant", default_value=1.0, min_value=0, max_value=10, min_clamped=True, max_clamped=True, callback=ScedGUI.__spotLightConstant_callback)
                    ScedGUI.dpg.add_slider_float(source=flatSource, default_value=1.0, min_value=0, max_value=10, callback=ScedGUI.__spotLightConstant_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_float(label="Linear", default_value=0.09, min_value=0, max_value=1, min_clamped=True, max_clamped=True, callback=ScedGUI.__spotLightLinear_callback)
                    ScedGUI.dpg.add_slider_float(source=flatSource, default_value=0.09, min_value=0, max_value=1, callback=ScedGUI.__spotLightLinear_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_float(label="Quadratic", default_value=0.032, min_value=0, max_value=1, min_clamped=True, max_clamped=True, callback=ScedGUI.__spotLightQuadratic_callback)
                    ScedGUI.dpg.add_slider_float(source=flatSource, default_value=0.032, min_value=0, max_value=1, callback=ScedGUI.__spotLightQuadratic_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_float(label="CutOff", default_value=12.5, min_value=0, max_value=90, min_clamped=True, max_clamped=True, callback=ScedGUI.__spotLightCutOff_callback)
                    ScedGUI.dpg.add_slider_float(source=flatSource, default_value=12.5, min_value=0, max_value=90, callback=ScedGUI.__spotLightCutOff_callback)
                with ScedGUI.dpg.group():
                    flatSource = ScedGUI.dpg.add_input_float(label="OuterCutOff", default_value=15.0, min_value=0, max_value=90, min_clamped=True, max_clamped=True, callback=ScedGUI.__spotLightOuterCutOff_callback)
                    ScedGUI.dpg.add_slider_float(source=flatSource, default_value=15.0, min_value=0, max_value=90, callback=ScedGUI.__spotLightOuterCutOff_callback)

            ScedGUI.dpg.add_button(label="Add Point Light", user_data=pw, callback=self.__addPointLight_callback)

            modelTag = "ModelSelect"
            ScedGUI.dpg.add_combo(tag=modelTag, label="Select Model", items=self.__get_model_ids())
            ScedGUI.dpg.add_button(label="Add Model", user_data=(pw,modelTag), callback=self.__addModel_callback)
                    
    def loop(self):
        global SIMULATION_RUNNING

        while ScedGUI.dpg.is_dearpygui_running() and SIMULATION_RUNNING:
            ScedGUI.dpg.render_dearpygui_frame()
        ScedGUI.dpg.destroy_context() 
        
        SIMULATION_RUNNING = False

    def __get_skybox_ids(self) -> list[str]:
        global ASSETS
        if ASSETS.get("skyboxes") is not None:
            return list(ASSETS["skyboxes"].keys())
        return [] 

    def __get_terrain_ids(self) -> list[str]:
        global ASSETS
        if ASSETS.get("heightmaps") is not None:
            return list(ASSETS["heightmaps"].keys())    
        return []

    def __get_model_ids(self) -> list[str]:
        global ASSETS
        if ASSETS.get("models") is not None:
            return list(ASSETS["models"].keys())
        return []

    """"CALLBACK FUNCTIONS"""
    
    @staticmethod
    def __escape_callback(sender, app_data) -> None:
        global SIMULATION_RUNNING
        SIMULATION_RUNNING = False
    
    @staticmethod
    def __clearColor_callback(sendr, app_data: tuple[int,int,int]) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["clearColor"] = app_data
        
    @staticmethod
    def __fovy_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["fovy"] = app_data

    @staticmethod
    def __nearPane_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["nearPane"] = app_data

    @staticmethod
    def __farPane_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["farPane"] = app_data

    @staticmethod
    def __cameraPos_callback(sender, app_data: tuple[float,float,float]) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["cameraXpos"] = app_data[0]
        CONFIGURATION_VALUES["cameraYpos"] = app_data[1]
        CONFIGURATION_VALUES["cameraZpos"] = app_data[2]
    
    @staticmethod
    def __cameraXpos_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["cameraXpos"] = app_data

    @staticmethod
    def __cameraYpos_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["cameraYpos"] = app_data
    
    @staticmethod
    def __cameraZpos_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["cameraZpos"] = app_data
    
    @staticmethod
    def __cameraPitch_callback(sender, app_data: int) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["cameraPitch"] = app_data

    @staticmethod
    def __cameraYaw_callback(sender, app_data: int) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["cameraYaw"] = app_data

    @staticmethod
    def __skybox_callback(sender, app_data: str) -> None:
        global SKYBOX_QUEUE
        SKYBOX_QUEUE.put(app_data)

    @staticmethod
    def __terrain_callback(sender, app_data: str) -> None:
        global TERRAIN_QUEUE
        TERRAIN_QUEUE.put(app_data)

    @staticmethod
    def __dirLightDirection_callback(sender, app_data: list[float]) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["dirLightDirection"] = app_data
    
    @staticmethod
    def __dirLightAmbient_callback(sender, app_data: list[float]) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["dirLightAmbient"] = app_data
    
    @staticmethod
    def __dirLightDiffuse_callback(sender, app_data: list[float]) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["dirLightDiffuse"] = app_data
        
    @staticmethod
    def __dirLightSpecular_callback(sender, app_data: list[float]) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["dirLightSpecular"] = app_data

    @staticmethod
    def __toggleSpotLight_callback(sender, app_data: bool) -> None:
        global SPOTLIGHT_QUEUE
        SPOTLIGHT_QUEUE.put(1)

    @staticmethod
    def __spotLightAmbient_callback(sender, app_data: list[float]) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["spotLightAmbient"] = app_data
    
    @staticmethod
    def __spotLightDiffuse_callback(sender, app_data: list[float]) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["spotLightDiffuse"] = app_data
    
    @staticmethod
    def __spotLightSpecular_callback(sender, app_data: list[float]) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["spotLightSpecular"] = app_data
    
    @staticmethod
    def __spotLightConstant_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["spotLightConstant"] = app_data
    
    @staticmethod
    def __spotLightLinear_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["spotLightLinear"] = app_data
    
    @staticmethod
    def __spotLightQuadratic_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["spotLightQuadratic"] = app_data
    
    @staticmethod
    def __spotLightCutOff_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["spotLightCutOff"] = app_data
    
    @staticmethod
    def __spotLightOuterCutOff_callback(sender, app_data: float) -> None:
        global CONFIGURATION_VALUES
        CONFIGURATION_VALUES["spotLightOuterCutOff"] = app_data
   
    def __addPointLight_callback(self, sender, app_data: bool, user_data: int) -> None:
        for i in range(10):
            if not self.pointLightEnabled[i]:
                self.pointLightEnabled[i] = True
                lightNum = i
                break
        else:
            return
        
        name="pointLight"+str(lightNum)
        with ScedGUI.dpg.collapsing_header(tag=name, label="Point Light "+str(lightNum), parent=user_data):
            with ScedGUI.dpg.group():
                flatSource = ScedGUI.dpg.add_input_floatx(label="Position", size=3, default_value=[0,0,0], user_data=lightNum, callback=ScedGUI.__pointLightPosition_callback)
                ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=-1, max_value=1, default_value=[0,0,0], user_data=lightNum, callback=ScedGUI.__pointLightPosition_callback)        
            with ScedGUI.dpg.group():
                flatSource = ScedGUI.dpg.add_input_floatx(label="Ambient", size=3, default_value=[0,0,0], min_value=0, max_value=1, min_clamped=True, max_clamped=True, user_data=lightNum, callback=ScedGUI.__pointLightAmbient_callback)
                ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=1, default_value=[0,0,0], user_data=lightNum, callback=ScedGUI.__pointLightAmbient_callback)
            with ScedGUI.dpg.group():
                flatSource = ScedGUI.dpg.add_input_floatx(label="Diffuse", size=3, default_value=[1,1,1], min_value=0, max_value=1, min_clamped=True, max_clamped=True, user_data=lightNum, callback=ScedGUI.__pointLightDiffuse_callback)
                ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=1, default_value=[1,1,1], user_data=lightNum, callback=ScedGUI.__pointLightDiffuse_callback)
            with ScedGUI.dpg.group():
                flatSource = ScedGUI.dpg.add_input_floatx(label="Specular", size=3, default_value=[0,0,0], min_value=0, max_value=1, min_clamped=True, max_clamped=True, user_data=lightNum, callback=ScedGUI.__pointLightSpecular_callback)
                ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=1, default_value=[0,0,0], user_data=lightNum, callback=ScedGUI.__pointLightSpecular_callback)
            with ScedGUI.dpg.group():
                flatSource = ScedGUI.dpg.add_input_float(label="Constant", default_value=1.0, min_value=0, max_value=10, min_clamped=True, max_clamped=True, user_data=lightNum, callback=ScedGUI.__pointLightConstant_callback)
                ScedGUI.dpg.add_slider_float(source=flatSource, default_value=1.0, min_value=0, max_value=10, user_data=lightNum, callback=ScedGUI.__pointLightConstant_callback)
            with ScedGUI.dpg.group():
                flatSource = ScedGUI.dpg.add_input_float(label="Linear", default_value=0.09, min_value=0, max_value=1, min_clamped=True, max_clamped=True, user_data=lightNum, callback=ScedGUI.__pointLightLinear_callback)
                ScedGUI.dpg.add_slider_float(source=flatSource, default_value=0.09, min_value=0, max_value=1, user_data=lightNum, callback=ScedGUI.__pointLightLinear_callback)
            with ScedGUI.dpg.group():
                flatSource = ScedGUI.dpg.add_input_float(label="Quadratic", default_value=0.032, min_value=0, max_value=1, min_clamped=True, max_clamped=True, user_data=lightNum, callback=ScedGUI.__pointLightQuadratic_callback)
                ScedGUI.dpg.add_slider_float(source=flatSource, default_value=0.032, min_value=0, max_value=1, user_data=lightNum, callback=ScedGUI.__pointLightQuadratic_callback)
            
            ScedGUI.dpg.add_button(label="Remove", user_data=(name,lightNum), callback=self.__removePointLight_callback)
        
    @staticmethod
    def __pointLightPosition_callback(sender, app_data: list[float], user_data: int) -> None:
        global POINTLIGHT_QUEUE
        POINTLIGHT_QUEUE.put((user_data, "position", app_data))
    
    @staticmethod
    def __pointLightAmbient_callback(sender, app_data: list[float], user_data: int) -> None:
        global POINTLIGHT_QUEUE
        POINTLIGHT_QUEUE.put((user_data, "ambient", app_data))
    
    @staticmethod
    def __pointLightDiffuse_callback(sender, app_data: list[float], user_data: int) -> None:
        global POINTLIGHT_QUEUE
        POINTLIGHT_QUEUE.put((user_data, "diffuse", app_data))
    
    @staticmethod
    def __pointLightSpecular_callback(sender, app_data: list[float], user_data: int) -> None:
        global POINTLIGHT_QUEUE
        POINTLIGHT_QUEUE.put((user_data, "specular", app_data))
    
    @staticmethod
    def __pointLightConstant_callback(sender, app_data: float, user_data: int) -> None:
        global POINTLIGHT_QUEUE
        POINTLIGHT_QUEUE.put((user_data, "constant", app_data))
    
    @staticmethod
    def __pointLightLinear_callback(sender, app_data: float, user_data: int) -> None:
        global POINTLIGHT_QUEUE
        POINTLIGHT_QUEUE.put((user_data, "linear", app_data))
    
    @staticmethod
    def __pointLightQuadratic_callback(sender, app_data: float, user_data: int) -> None:
        global POINTLIGHT_QUEUE
        POINTLIGHT_QUEUE.put((user_data, "quadratic", app_data))

    def __removePointLight_callback(self, sender, app_data: int, user_data: tuple[str,int]) -> None:
        global POINTLIGHT_QUEUE
        ScedGUI.dpg.delete_item(user_data[0])
        self.pointLightEnabled[user_data[1]] = False
        POINTLIGHT_QUEUE.put((user_data[1], "remove", None))

    def __addModel_callback(self, sender, app_data: str, user_data: tuple[int,str]) -> None:
        global MODEL_QUEUE

        modelName = ScedGUI.dpg.get_value(user_data[1])

        if modelName == "":
            return
        
        ScedGUI.dpg.set_value(user_data[1], "")
        
        self.modelCount += 1
        modelId = self.modelCount

        MODEL_QUEUE.put((modelName, modelId, "add"))

        with ScedGUI.dpg.collapsing_header(tag=modelName+str(modelId), label="Model " + str(modelId) + " (" + modelName + ")", parent=user_data[0]):
            with ScedGUI.dpg.group():
                flatSource = ScedGUI.dpg.add_input_floatx(label="Position", size=3, default_value=[0,0,0], user_data=(modelName,modelId), callback=ScedGUI.__modelPosition_callback)
                ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=-10, max_value=10, default_value=[0,0,0], user_data=(modelName,modelId), callback=ScedGUI.__modelPosition_callback)
            with ScedGUI.dpg.group():
                flatSource = ScedGUI.dpg.add_input_floatx(label="Scale", size=3, default_value=[1,1,1], user_data=(modelName,modelId), callback=ScedGUI.__modelScale_callback)
                ScedGUI.dpg.add_slider_floatx(source=flatSource, size=3, min_value=0, max_value=10, default_value=[1,1,1], user_data=(modelName,modelId), callback=ScedGUI.__modelScale_callback)
            with ScedGUI.dpg.group():
                flatSource = ScedGUI.dpg.add_input_intx(label="Rotation", size=3, default_value=[0,0,0], user_data=(modelName,modelId), callback=ScedGUI.__modelRotation_callback)
                ScedGUI.dpg.add_slider_intx(source=flatSource, size=3, min_value=-180, max_value=180, default_value=[0,0,0], user_data=(modelName,modelId), callback=ScedGUI.__modelRotation_callback)
            
            ScedGUI.dpg.add_button(label="Remove", user_data=(modelName,modelId), callback=self.__removeModel_callback)
    
    @staticmethod
    def __removeModel_callback(sender, app_data: bool, user_data: tuple[str,int]) -> None:
        global MODEL_QUEUE
        ScedGUI.dpg.delete_item(user_data[0] + str(user_data[1]))
        MODEL_QUEUE.put((user_data[0], user_data[1], "remove"))
    
    @staticmethod
    def __modelPosition_callback(sender, app_data: list[float], user_data: tuple[str, int]) -> None:
        global MODEL_QUEUE
        MODEL_QUEUE.put((user_data[0], user_data[1], "position", app_data))
    
    @staticmethod
    def __modelScale_callback(sender, app_data: list[float], user_data: tuple[str, int]) -> None:
        global MODEL_QUEUE
        MODEL_QUEUE.put((user_data[0], user_data[1], "scale", app_data))
    
    @staticmethod
    def __modelRotation_callback(sender, app_data: list[int], user_data: tuple[str, int]) -> None:
        global MODEL_QUEUE
        MODEL_QUEUE.put((user_data[0], user_data[1], "rotation", app_data)) 
    


""" Main context class """

class Sced:
    def __init__(self, display: tuple[int,int]):
        self.display = display
        
        pg.init()
        pg.display.set_mode(display, pg.OPENGL | pg.DOUBLEBUF)
        pg.display.set_caption("Sced")
        self.clock = pg.time.Clock()
       
        self.__loadAssets() 

        self.lightManager = LightManager()
        self.currSkybox = None
        self.currTerrain = None
        self.cameraPos = glm.vec3(0)

        self.currModels = {}

        self.running = True

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(*self.__getClearColor())

        projection = self.__getProjectionMatrix()
        view = self.__getViewMatrix()

        self.__loadTerrain()
        if self.currTerrain is not None:
            self.currTerrain[1].use()
            model = glm.mat4(1.0)    
            self.currTerrain[1].setMat4("model", model)
            self.currTerrain[1].setMat4("view", view)
            self.currTerrain[1].setMat4("projection", projection)
            self.currTerrain[0].draw(self.currTerrain[1])

        self.__loadDirLight()
        self.__loadSpotLight()
        self.__loadPointLights()
        
        shaderProgram = self._loadedAssets["pointLightShader"]
        shaderProgram.use()
        model = glm.mat4(1)
        shaderProgram.setMat4("model", model)
        shaderProgram.setMat4("view", view)
        shaderProgram.setMat4("projection", projection)
        self.lightManager.drawPointLights(shaderProgram) 

        self.__loadModels()

        for rep in self.currModels.values():
            objModel, program = rep["object"]
            position = rep["position"]
            scale = rep["scale"]
            rotation = rep["rotation"]
            
            model = glm.mat4(1.0)            
            model = glm.translate(model, glm.vec3(*position))
            model = glm.scale(model, glm.vec3(*scale))
            model = glm.rotate(model, glm.radians(rotation[0]), glm.vec3(1,0,0))
            model = glm.rotate(model, glm.radians(rotation[1]), glm.vec3(0,1,0))
            model = glm.rotate(model, glm.radians(rotation[2]), glm.vec3(0,0,1))

            program.use()
            program.setFloat("shininess", 32.0)
            self.lightManager.setUniforms(program, self.cameraPos, self.cameraFront)
            program.setMat4("model", model)
            program.setMat4("view", view)
            program.setMat4("projection", projection)
            objModel.draw(program)

        self.__loadSkybox()
        if self.currSkybox is not None:
            self.currSkybox[1].use()
            model = glm.mat4(1.0)
            skyboxView = glm.mat4(glm.mat3(view)) # remove translation
            self.currSkybox[1].setMat4("model", model)
            self.currSkybox[1].setMat4("view", skyboxView)
            self.currSkybox[1].setMat4("projection", projection)
            self.currSkybox[0].draw(self.currSkybox[1])


    def loop(self):
        global SIMULATION_RUNNING
 
        glEnable(GL_DEPTH_TEST)

        deltaTime = 0
        while self.running and SIMULATION_RUNNING:
            self.__check_events()
            try:
                self.render()
            except Exception as e:
                message = "An error occured while rendering the scene!\n" + str(e)
                import sys
                print(message, file=sys.stderr)
                SIMULATION_RUNNING = False
                
            pg.display.flip()
            deltaTime = self.clock.tick(60) / 1000
        
        SIMULATION_RUNNING = False
        
    def __check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.running = False

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s:
                    self.__saveScene()

    def __getClearColor(self):
        global CONFIGURATION_VALUES
        return CONFIGURATION_VALUES["clearColor"]
        
    def __getProjectionMatrix(self):
        global CONFIGURATION_VALUES
        fovy = glm.radians(CONFIGURATION_VALUES["fovy"])
        ratio = pg.display.Info().current_w / pg.display.Info().current_h
        nearPane = CONFIGURATION_VALUES["nearPane"]
        farPane = CONFIGURATION_VALUES["farPane"]
        return glm.perspective(fovy, ratio, nearPane, farPane)

    def __getViewMatrix(self):
        global CONFIGURATION_VALUES

        worldUp = glm.vec3(0,1,0)
        
        position = glm.vec3(
            CONFIGURATION_VALUES["cameraXpos"],
            CONFIGURATION_VALUES["cameraYpos"],
            CONFIGURATION_VALUES["cameraZpos"],
        )

        self.cameraPos = position

        yaw = CONFIGURATION_VALUES["cameraYaw"]
        pitch = CONFIGURATION_VALUES["cameraPitch"]
        
        front = glm.vec3(
            glm.cos(glm.radians(yaw)) * glm.cos(glm.radians(pitch)),
            glm.sin(glm.radians(pitch)),
            glm.sin(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
        )
        front = glm.normalize(front)

        self.cameraFront = front

        right = glm.normalize(glm.cross(front, worldUp))
        up = glm.normalize(glm.cross(right,front))
        
        return glm.lookAt(
            position,
            position + front,
            up
        )

    def __loadAssets(self):
        global ASSETS
        
        from os import listdir
        from os.path import isfile, join

        print("Loading assets...")
        self._loadedAssets = {}

        progress = 0
        self.__drawProgressBar(progress)
        
        # load skyboxes
        maxProgress = 20
        if ASSETS.get("skyboxes") is not None:
            progressStep = maxProgress / len(ASSETS["skyboxes"].keys())
            loadedSkyboxes = {}
            
            for skyboxName in ASSETS["skyboxes"].keys():
                path = ASSETS["skyboxes"][skyboxName]["path"]
                vsPath = ASSETS["skyboxes"][skyboxName]["shaders"]["vertex"]
                fgPath = ASSETS["skyboxes"][skyboxName]["shaders"]["fragment"]
                
                filesInDir = [f for f in listdir(path) if isfile(join(path, f))]
                extension = filesInDir[0].split(".")[-1]
                keyNames = ("right", "left", "top", "bottom", "front", "back")
                
                for kn in keyNames:
                    fn = kn+"."+extension
                    if fn not in filesInDir:
                        message = "Skybox '" + str(skyboxName) + "' does not have valid face names!"
                        raise RuntimeError(message)
                
                faces = [join(path, kn+"."+extension) for kn in keyNames]
                skybox = Skybox(faces)
                
                # Create Shader Program
                vsCode = open(vsPath, "r")
                fgCode = open(fgPath, "r")         
                program = ShaderProgram(vsCode.read(), fgCode.read())
                vsCode.close()
                fgCode.close()

                loadedSkyboxes[skyboxName] = (skybox, program)
                
                progress += progressStep
                self.__drawProgressBar(progress)
                
            self._loadedAssets["skyboxes"] = loadedSkyboxes
          
        progress = maxProgress
        self.__drawProgressBar(progress)
          
        maxProgress += 40
        if ASSETS.get("heightmaps") is not None:
            progressStep = maxProgress / len(ASSETS["heightmaps"].keys())
            loadedTerrains = {}
            
            for heightmapName in ASSETS["heightmaps"].keys():
                path = ASSETS["heightmaps"][heightmapName]["path"]
                vsPath = ASSETS["heightmaps"][heightmapName]["shaders"]["vertex"]
                fgPath = ASSETS["heightmaps"][heightmapName]["shaders"]["fragment"]
                
                if not isfile(path):
                    message = "Height Map path for '" + heightmapName + "' is not a file!"
                    raise RuntimeError(message)
                
                terrain = HeightMapTerrain(path)

                # Create Shader Program
                vsCode = open(vsPath, "r")
                fgCode = open(fgPath, "r")
                program = ShaderProgram(vsCode.read(), fgCode.read())
                vsCode.close()
                fgCode.close()

                loadedTerrains[heightmapName] = (terrain, program)

                progress += progressStep
                self.__drawProgressBar(progress)
            
            self._loadedAssets["terrains"] = loadedTerrains
        
        progress = maxProgress
        self.__drawProgressBar(progress)

        maxProgress += 10
        if ASSETS.get("pointLight") is not None:
            vsPath = ASSETS["pointLight"]["shaders"]["vertex"]
            fgPath = ASSETS["pointLight"]["shaders"]["fragment"]

            # Create Shader Program
            vsCode = open(vsPath, "r")
            fgCode = open(fgPath, "r")     
            program = ShaderProgram(vsCode.read(), fgCode.read())
            vsCode.close()
            fgCode.close()

            self._loadedAssets["pointLightShader"] = program 
        
        progress = maxProgress
        self.__drawProgressBar(maxProgress)

        maxProgress += 30
        if ASSETS.get("models") is not None:
            progressStep = maxProgress / len(ASSETS["models"].keys())
            loadedModels = {}
            
            for modelName in ASSETS["models"].keys():
                path = ASSETS["models"][modelName]["path"]
                vsPath = ASSETS["models"][modelName]["shaders"]["vertex"]
                fgPath = ASSETS["models"][modelName]["shaders"]["fragment"]
                
                if not isfile(path):
                    message = "Model path for '" + modelName + "' is not a file!"
                    raise RuntimeError(message)
                
                model = Model(path)
                
                # Create Shader Program
                vsCode = open(vsPath, "r")
                fgCode = open(fgPath, "r")
                program = ShaderProgram(vsCode.read(), fgCode.read())
                vsCode.close()
                fgCode.close()
                
                loadedModels[modelName] = (model, program)

                progress += progressStep
                self.__drawProgressBar(progress)
            
            self._loadedAssets["models"] = loadedModels
                
        progress = maxProgress
        self.__drawProgressBar(progress)
        
        print("Assets Loaded")


    def __loadSkybox(self) -> None:
        global SKYBOX_QUEUEcontext
        
        if not SKYBOX_QUEUE.empty():
            name = SKYBOX_QUEUE.get()
            try:
                self.currSkybox = self._loadedAssets["skyboxes"][name]
            except KeyError:
                if name != "":
                    print("Invalid terrain Key: ", name)
                self.currSkybox = None
       
    def __loadTerrain(self) -> None:
        global TERRAIN_QUEUE
        
        if not TERRAIN_QUEUE.empty():
            name = TERRAIN_QUEUE.get()
            try:
                self.currTerrain = self._loadedAssets["terrains"][name]
            except:
                if name != "":
                    print("Invalid terrain Key: ", name)
                self.currTerrain = None

    def __loadDirLight(self) -> None:
        global CONFIGURATION_VALUES

        self.lightManager.setDirLight(
            direction = glm.vec3(CONFIGURATION_VALUES["dirLightDirection"]),
            ambient = glm.vec3(CONFIGURATION_VALUES["dirLightAmbient"]),
            diffuse = glm.vec3(CONFIGURATION_VALUES["dirLightDiffuse"]),
            specular = glm.vec3(CONFIGURATION_VALUES["dirLightSpecular"])
        )
    
    def __loadSpotLight(self) -> None:
        global CONFIGURATION_VALUES, SPOTLIGHT_QUEUE

        self.lightManager.setSpotLight(
            ambient = glm.vec3(CONFIGURATION_VALUES["spotLightAmbient"]),
            diffuse = glm.vec3(CONFIGURATION_VALUES["spotLightDiffuse"]),
            specular = glm.vec3(CONFIGURATION_VALUES["spotLightSpecular"]),
            constant = CONFIGURATION_VALUES["spotLightConstant"],
            linear = CONFIGURATION_VALUES["spotLightLinear"],
            quadratic = CONFIGURATION_VALUES["spotLightQuadratic"],
            cutOff = glm.cos(glm.radians(CONFIGURATION_VALUES["spotLightCutOff"])),
            outerCutOff = glm.cos(glm.radians(CONFIGURATION_VALUES["spotLightOuterCutOff"]))
        )

        if not SPOTLIGHT_QUEUE.empty():
            SPOTLIGHT_QUEUE.get()
            self.lightManager.toggleSpotLight()
            
    def __loadPointLights(self) -> None:
        global POINTLIGHT_QUEUE
        
        while not POINTLIGHT_QUEUE.empty():
            lightNum, lightType, value = POINTLIGHT_QUEUE.get()
            
            currPointLight = self.lightManager.getPointLight(lightNum)
            if currPointLight is None:
                currPointLight = {
                    "position": glm.vec3(0,0,0),
                    "ambient": glm.vec3(0,0,0),
                    "diffuse": glm.vec3(1,1,1),
                    "specular": glm.vec3(0,0,0),
                    "constant": 1.0,
                    "linear": 0.09,
                    "quadratic": 0.032
                }
            
            if lightType == "position":
                currPointLight[lightType] = glm.vec3(value)
            elif lightType == "ambient":
                currPointLight[lightType] = glm.vec3(value)
            elif lightType == "diffuse":
                currPointLight[lightType] = glm.vec3(value)
            elif lightType == "specular":
                currPointLight[lightType] = glm.vec3(value)
            elif lightType == "constant":
                currPointLight[lightType] = value
            elif lightType == "linear":
                currPointLight[lightType] = value
            elif lightType == "quadratic":
                currPointLight[lightType] = value
            elif lightType == "remove":
                self.lightManager.removePointLight(lightNum)
                continue
            else:
                print("Invalid Point Light Type: ", lightType)
                return
        
            self.lightManager.setPointLight(lightNum, **currPointLight)

    def __loadModels(self) -> None:
        global MODEL_QUEUE
        
        while not MODEL_QUEUE.empty():
            info = MODEL_QUEUE.get()
            if len(info) <= 3:
                modelName, modelId, action = info
                if action == "add":
                    self.currModels[modelName+str(modelId)] = {}
                    self.currModels[modelName+str(modelId)]["object"] = self._loadedAssets["models"][modelName]
                    self.currModels[modelName+str(modelId)]["position"] = glm.vec3(0)
                    self.currModels[modelName+str(modelId)]["scale"] = glm.vec3(1)
                    self.currModels[modelName+str(modelId)]["rotation"] = glm.vec3(0)
                elif action == "remove":
                    del self.currModels[modelName+str(modelId)]
                else:
                    print("Invalid Model Action: ", action)
                    return
            else:
                modelName, modelId, action, value = info
                
                if modelName+str(modelId) not in self.currModels.keys():
                    message = "Invalid Model: " + modelName + str(modelId)
                    raise ValueError(message)
                
                if action == "position":
                    self.currModels[modelName+str(modelId)]["position"] = glm.vec3(value)
                elif action == "scale":
                    self.currModels[modelName+str(modelId)]["scale"] = glm.vec3(value)
                elif action == "rotation":
                    self.currModels[modelName+str(modelId)]["rotation"] = glm.vec3(value)
                else:
                    print("Invalid Model Action: ", action)
                    return

    def __drawProgressBar(self, percentage: float) -> None:
        # represent percentage as a float between [0,1]
        percentage /= 100
        percentage = min(max(percentage,0),1)
        
        glDisable(GL_DEPTH_TEST)
        glClear(GL_COLOR_BUFFER_BIT)
        
        # x and y are the bottom left screen coordinates
        width,height = (1,0.1)
        x,y = (-0.5, -0.05)
        
        # draw background
        
        glColor3f(1.0,1.0,1.0) # background color
        glBegin(GL_QUADS)
        glVertex2f(x,y)
        glVertex2f(x+width,y)
        glVertex2f(x+width,y+height)
        glVertex2f(x,y+height)
        glEnd()

        # draw rectangle
        progress = width * percentage
        
        glColor3f(0.4, 0.8, 0.0) # progress bar color
        glBegin(GL_QUADS)
        glVertex2f(x,y)
        glVertex2f(x+progress, y)
        glVertex2f(x+progress, y+height)
        glVertex2f(x, y+height)
        glEnd()

        pg.display.flip()

    def __saveScene(self) -> None:
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        data = glReadPixels(0, 0, self.display[0], self.display[1], GL_RGBA, GL_UNSIGNED_BYTE)
        
        from PIL import Image, ImageOps
        
        image = Image.frombytes("RGBA", self.display, data)
        image = ImageOps.flip(image)
        
        import datetime
        fname = "sced " + datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + ".png"
        image.save(fname, "PNG")
        print("Saved render as:", fname)
        

def create_gui():
    gui = ScedGUI()
    gui.loop()

if __name__ == "__main__":
    thread = Thread(target=create_gui)
    thread.start()
    
    display = (720, 720)
    try:
        sced = Sced(display)
        sced.loop()
    except Exception as e:
        message = "An unexpected error occured while running Sced!\n" + str(e)
        import sys
        print(message, file=sys.stderr)
        SIMULATION_RUNNING = False
    except KeyboardInterrupt:
        SIMULATION_RUNNING = False
    
    thread.join()