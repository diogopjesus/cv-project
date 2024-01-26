import numpy as np

from OpenGL.GL import *
import glm

from PIL import Image

from .shader import ShaderProgram

class HeightMapTerrain:
    def __init__(self, path: str):
        self.__loadHeightMap(path)

    def draw(self, shaderProgram: ShaderProgram) -> None:
        glBindVertexArray(self.terrainVAO)
        for strip in range(self.numStrips):
            glDrawElements(GL_TRIANGLE_STRIP,
                           self.numTrisPerStrip+2,
                           GL_UNSIGNED_INT,
                           ctypes.c_void_p(4 * (self.numTrisPerStrip+2) * strip)
                        )
        glBindVertexArray(0)
    
    def __loadHeightMap(self,path :str) -> None:
        vertices = []
        indices = []

        yScale = 64.0 / 256.0
        yShift = 10.0
        rez = 1
        
        with Image.open(path) as img:
            bytesPerPixel = len(img.getbands())
            height = img.height
            width = img.width

            for i in range(height):
               for j in range(width):
                    texel = img.getpixel((j,i))
                    if img.mode in ["RGB", "RGBA"]:
                        y = texel[0]
                    else:
                        message = "HeightMapTerrain does not support '" + img.mode + "' type!"
                        raise ValueError(message)
                    

                    vx = -height/2.0 + i
                    vy = y * yScale - yShift
                    vz = -width/2.0 + j

                    vertices.extend([vx,vy,vz])
        
        for i in range(0, height-1, rez): 
            for j in range(0, width, rez):
                for k in range(2):
                    indices.append(j + width * (i + k*rez))
                    
        self.numStrips = int((height-1)/rez)
        self.numTrisPerStrip = int((width/rez)*2)-2
        
        vertices = glm.array(np.array(vertices, dtype=np.float32))
        indices = glm.array(np.array(indices, dtype=np.uint32))
        
        self.terrainVAO = glGenVertexArrays(1)
        self.terrainVBO = glGenBuffers(1)                 
        self.terrainEBO = glGenBuffers(1)
        
        glBindVertexArray(self.terrainVAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.terrainVBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * glm.sizeof(glm.float32), None)
        glEnableVertexAttribArray(0)
        
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.terrainEBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices.ptr, GL_STATIC_DRAW)

        glBindVertexArray(0)
