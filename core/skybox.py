import numpy as np

from OpenGL.GL import *
import glm

from .shader import ShaderProgram

class Skybox:
    def __init__(self, faces: list[str]):
        self.__loadGeometry()
        self.__loadCubemap(faces)
   
    def draw(self, shaderProgram: ShaderProgram) -> None:
        glDepthFunc(GL_LEQUAL) # change depth function so depth test passes when values are equal to depth buffer's content
         
        glBindVertexArray(self.VAO)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.textureId)
        glDrawArrays(GL_TRIANGLES, 0, 36)
   
        glDepthFunc(GL_LESS)
   
    def __loadGeometry(self) -> None:
        skyboxVertices = glm.array(np.array([
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

        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(1)
        
        glBindVertexArray(self.VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, skyboxVertices.nbytes, skyboxVertices.ptr, GL_STATIC_DRAW)
        
        # vertex position 
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * glm.sizeof(glm.float32), None)

        glBindVertexArray(0)

    def __loadCubemap(self, faces: list[str]) -> None:    
        self.textureId = glGenTextures(1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.textureId)

        from PIL import Image
        for i in range(len(faces)):
            with Image.open(faces[i]) as img:
                nrComponents = len(img.getbands())
                format = GL_RED if nrComponents == 1 else \
                         GL_RGB if nrComponents == 3 else \
                         GL_RGBA
                
                glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, format, img.width, img.height, 0, format, GL_UNSIGNED_BYTE, img.tobytes())
            
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
