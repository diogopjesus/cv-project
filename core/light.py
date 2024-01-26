import numpy as np

from OpenGL.GL import *
import glm

from .shader import ShaderProgram
from .camera import Camera

class LightManager:
    MAX_NUMBER_OF_POINT_LIGHTS = 10
    
    def __init__(self):
        self.dirLight = {
            "direction": glm.vec3(0),
            "ambient": glm.vec3(0),
            "diffuse": glm.vec3(0),
            "specular": glm.vec3(0)
        }
        self.pointLights = [None for i in range(LightManager.MAX_NUMBER_OF_POINT_LIGHTS)]
        self.numOfPointLights = 0

        self.spotLight = None

        self.enSpotLight = False
        
        self.__loadPointLightGeometry()

    def drawPointLights(self, shaderProgram: ShaderProgram) -> None:
        for i in range(LightManager.MAX_NUMBER_OF_POINT_LIGHTS):
            if self.pointLights[i] is not None:
                position = self.pointLights[i]["position"]
                model = glm.mat4(1)
                model = glm.translate(model, position)
                model = glm.scale(model, glm.vec3(0.1)) # TODO: interactive scaling
                shaderProgram.setMat4("model", model)
                
                # set color
                shaderProgram.setVec3("lightColor", self.pointLights[i]["diffuse"])
                
                glBindVertexArray(self.pointLightVAO)
                glDrawArrays(GL_TRIANGLES, 0, 36)
                glBindVertexArray(0) 
    
    def setUniforms(self, shaderProgram: ShaderProgram, camPos: glm.vec3, camFront: glm.vec3) -> None:
        shaderProgram.setVec3("dirLight.direction", self.dirLight["direction"])
        shaderProgram.setVec3("dirLight.ambient", self.dirLight["ambient"])
        shaderProgram.setVec3("dirLight.diffuse", self.dirLight["diffuse"])
        shaderProgram.setVec3("dirLight.specular", self.dirLight["specular"])

        for i in range(len(self.pointLights)):
            pl = self.pointLights[i]
            if pl is not None:  
                shaderProgram.setVec3("pointLights["+ str(i) + "].position", pl["position"])
                shaderProgram.setVec3("pointLights["+ str(i) + "].ambient", pl["ambient"])
                shaderProgram.setVec3("pointLights["+ str(i) + "].diffuse", pl["diffuse"])
                shaderProgram.setVec3("pointLights["+ str(i) + "].specular", pl["specular"])
                shaderProgram.setFloat("pointLights["+ str(i) + "].constant", pl["constant"])
                shaderProgram.setFloat("pointLights["+ str(i) + "].linear", pl["linear"])
                shaderProgram.setFloat("pointLights["+ str(i) + "].quadratic", pl["quadratic"])

        if self.enSpotLight and self.spotLight is not None:            
            shaderProgram.setVec3("spotLight.position", camPos)
            shaderProgram.setVec3("spotLight.direction", camFront)
            shaderProgram.setVec3("spotLight.ambient", self.spotLight["ambient"])
            shaderProgram.setVec3("spotLight.diffuse", self.spotLight["diffuse"])
            shaderProgram.setVec3("spotLight.specular", self.spotLight["specular"])
            shaderProgram.setFloat("spotLight.constant", self.spotLight["constant"])
            shaderProgram.setFloat("spotLight.linear", self.spotLight["linear"])
            shaderProgram.setFloat("spotLight.quadratic", self.spotLight["quadratic"])
            shaderProgram.setFloat("spotLight.cutOff", self.spotLight["cutOff"])
            shaderProgram.setFloat("spotLight.outerCutOff", self.spotLight["outerCutOff"])

        shaderProgram.setInt("numberOfPointLights", self.numOfPointLights)
        shaderProgram.setBool("enableSpotLight", self.enSpotLight)
    
    def setDirLight(self, *args, **kwargs) -> None:
        if len(args) == 4:
            for a in args:
                if not isinstance(a, glm.vec3):
                    raise ValueError("Invalid argument value! '" + str(a) + "' must be a glm.vec3")
            
            self.dirLight["direction"] = args[0]
            self.dirLight["ambient"] = args[1]
            self.dirLight["diffuse"] = args[2]
            self.dirLight["specular"] = args[3]

        elif len(args) == 12:
            for a in args:
                if not isinstance(a, float) or not isinstance(a, int):
                    raise ValueError("Invalid argument value! '" + str(a) + "' must be a float or int")
            
            self.dirLight["direction"] = glm.vec3(args[0], args[1], args[2])
            self.dirLight["ambient"] = glm.vec3(args[3], args[4], args[5])
            self.dirLight["diffuse"] = glm.vec3(args[6], args[7], args[8])
            self.dirLight["specular"] = glm.vec3(args[9], args[10], args[11])
        
        elif len(args) + len(kwargs.keys()) >= 4:
            for a in args:
                if not isinstance(a, glm.vec3):
                    raise ValueError("Invalid argument value! '" + str(a) + "' must be a glm.vec3")

            keys = ("direction", "ambient", "diffuse", "specular")
            for i in range(len(args)):
                kwargs[keys[i]] = args[i]
            
            for k in keys:
                if k not in kwargs.keys():
                    raise ValueError("Missing definition for '" + str(k) + "' value!")
                
            self.dirLight["direction"] = kwargs["direction"]
            self.dirLight["ambient"] = kwargs["ambient"]
            self.dirLight["diffuse"] = kwargs["diffuse"]
            self.dirLight["specular"] = kwargs["specular"]
                    
        else:
            raise ValueError("Invalid number of arguments: " + str(len(args) + len(kwargs.keys()))) 
    
    def setSpotLight(self, *args, **kwargs) -> None:
        if len(args) == 8:
            for i in range(len(args)):
                if i < 3 and not isinstance(args[i], glm.vec3):
                    raise ValueError("Invalid Argument value! '" + str(args[i]) + "' must be a glm.vec3")
                elif i >= 3 and (not isinstance(args[i], float) or isinstance(args[i], int)):
                    raise ValueError("Invalid Argument value! '" + str(args[i]) + "' must be a float or int")

            self.spotLight = {
                "ambient": args[0],
                "diffuse": args[1],
                "specular": args[2],
                "constant": args[3],
                "linear": args[4],
                "quadratic": args[5],
                "cutOff": args[6],
                "outerCutOff": args[7]
            }
        
        elif len(args) + len(kwargs.keys()) >= 8:
            for i in range(len(args)):
                if i < 3 and not isinstance(args[i], glm.vec3):
                    raise ValueError("Invalid Argument value! '" + str(args[i]) + "' must be a glm.vec3")
                elif i >= 3 and (not isinstance(args[i], float) or isinstance(args[i], int)):
                    raise ValueError("Invalid Argument value! '" + str(args[i]) + "' must be a float or int")
            
            keys = ("ambient", "diffuse", "specular", "constant", "linear", "quadratic", "cutOff", "outerCutOff")
            for i in range(len(args)):
                kwargs[keys[i]] = args[i]
            
            for k in keys:
                if k not in kwargs.keys():
                    raise ValueError("Missing definition for '" + str(k) + "' value!")
            
            self.spotLight = {
                "ambient": kwargs["ambient"],
                "diffuse": kwargs["diffuse"],
                "specular": kwargs["specular"],
                "constant": kwargs["constant"],
                "linear": kwargs["linear"],
                "quadratic": kwargs["quadratic"],
                "cutOff": kwargs["cutOff"],
                "outerCutOff": kwargs["outerCutOff"]
            }
            
        else: 
            raise ValueError("Invalid number of arguments: " + str(len(args) + len(kwargs.keys()))) 

    def toggleSpotLight(self) -> None:
        self.enSpotLight = not self.enSpotLight    
    
    def setPointLight(self, idx: int, *args, **kwargs) -> None:
        if idx >= LightManager.MAX_NUMBER_OF_POINT_LIGHTS:
            raise ValueError("Light manager can only support ", LightManager.MAX_NUMBER_OF_POINT_LIGHTS, " different point lights")
        
        if idx < 0:
            raise ValueError("Invalid Point Light identifier!")
        
        
        if len(args) == 7:
            for i in range(len(args)):
                if i < 4 and not isinstance(args[i], glm.vec3):
                    raise ValueError("Invalid Argument value! '" + str(args[i]) + "' must be a glm.vec3")
                elif i >= 4 and (not isinstance(args[i], float) or isinstance(args[i], int)):
                    raise ValueError("Invalid Argument value! '" + str(args[i]) + "' must be a float or int")

            if self.pointLights[idx] is None:
                self.numOfPointLights+=1

            self.pointLights[idx] = {
                "position": args[0],
                "ambient": args[1],
                "diffuse": args[2],
                "specular": args[3],
                "constant": args[4],
                "linear": args[5],
                "quadratic": args[6],
            }

        elif len(args) + len(kwargs.keys()) >= 7:
            for i in range(len(args)):
                if i < 4 and not isinstance(args[i], glm.vec3):
                    raise ValueError("Invalid Argument value! '" + str(args[i]) + "' must be a glm.vec3")
                elif i >= 4 and (not isinstance(args[i], float) or isinstance(args[i], int)):
                    raise ValueError("Invalid Argument value! '" + str(args[i]) + "' must be a float or int")
            
            keys = ("position", "ambient", "diffuse", "specular","constant","linear","quadratic")
            for i in range(len(args)):
                kwargs[keys[i]] = args[i]
            
            for k in keys:
                if k not in kwargs.keys():
                    raise ValueError("Missing definition for '" + str(k) + "' value!")
            
            if self.pointLights[idx] is None:
                self.numOfPointLights+=1

            self.pointLights[idx] = {
                "position": kwargs["position"],
                "ambient": kwargs["ambient"],
                "diffuse": kwargs["diffuse"],
                "specular": kwargs["specular"],
                "constant": kwargs["constant"],
                "linear": kwargs["linear"],
                "quadratic": kwargs["quadratic"],
            }

        else:
            raise ValueError("Invalid number of arguments: " + str(1 + len(args) + len(kwargs.keys()))) 
            
    def getPointLight(self, idx: int) -> dict:
        if idx >= LightManager.MAX_NUMBER_OF_POINT_LIGHTS:
            raise ValueError("Light manager can only support ", LightManager.MAX_NUMBER_OF_POINT_LIGHTS, " different point lights")
        
        if idx < 0:
            raise ValueError("Invalid Point Light identifier!")
        
        return self.pointLights[idx]
    
    def removePointLight(self, pos: int) -> None:
        for i in range(LightManager.MAX_NUMBER_OF_POINT_LIGHTS):
            if i == pos:
                if self.pointLights[i] is not None:
                    self.numOfPointLights -= 1
                    self.pointLights[i] = None
                break
    
    def __loadPointLightGeometry(self):
        data = glm.array(np.array([
            -1.0,  1.0, -1.0,
            -1.0, -1.0, -1.0,
            1.0, -1.0, -1.0,
            1.0, -1.0, -1.0,
            1.0,  1.0, -1.0,
            -1.0,  1.0, -1.0,

            -1.0, -1.0,  1.0,
            -1.0, -1.0, -1.0,
            -1.0,  1.0, -1.0,
            -1.0,  1.0, -1.0,
            -1.0,  1.0,  1.0,
            -1.0, -1.0,  1.0,

            1.0, -1.0, -1.0,
            1.0, -1.0,  1.0,
            1.0,  1.0,  1.0,
            1.0,  1.0,  1.0,
            1.0,  1.0, -1.0,
            1.0, -1.0, -1.0,

            -1.0, -1.0,  1.0,
            -1.0,  1.0,  1.0,
            1.0,  1.0,  1.0,
            1.0,  1.0,  1.0,
            1.0, -1.0,  1.0,
            -1.0, -1.0,  1.0,

            -1.0,  1.0, -1.0,
            1.0,  1.0, -1.0,
            1.0,  1.0,  1.0,
            1.0,  1.0,  1.0,
            -1.0,  1.0,  1.0,
            -1.0,  1.0, -1.0,

            -1.0, -1.0, -1.0,
            -1.0, -1.0,  1.0,
            1.0, -1.0, -1.0,
            1.0, -1.0, -1.0,
            -1.0, -1.0,  1.0,
            1.0, -1.0,  1.0
        ], dtype=np.float32))
        
        self.pointLightVAO = glGenVertexArrays(1)
        self.pointLightVBO = glGenBuffers(1)

        glBindVertexArray(self.pointLightVAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.pointLightVBO)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data.ptr, GL_STATIC_DRAW)
        
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * glm.sizeof(glm.float32), None)
        glEnableVertexAttribArray(0)