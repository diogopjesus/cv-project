from dataclasses import dataclass

from OpenGL.GL import *
import glm

import numpy as np

from .shader import ShaderProgram

@dataclass
class Vertex:
    position: glm.vec3
    normal: glm.vec3
    texCoords: glm.vec2
    
    @property
    def array(self) -> glm.array:
        return glm.array(glm.float32,
            self.position.x, self.position.y, self.position.z,
            self.normal.x, self.normal.y, self.normal.z,
            self.texCoords.x, self.texCoords.y,
        )
   
    @staticmethod
    def positionOffset() -> ctypes.c_void_p:
        return ctypes.c_void_p(0)
   
    @staticmethod
    def normalOffset() -> ctypes.c_void_p:
        return ctypes.c_void_p(glm.sizeof(glm.vec3)) 

    @staticmethod
    def texCoordsOffset() -> ctypes.c_void_p:
        return ctypes.c_void_p(Vertex.normalOffset().value + glm.sizeof(glm.vec3))
    
    @staticmethod
    def size() -> int:
        return Vertex.texCoordsOffset().value + glm.sizeof(glm.vec2) 
    
@dataclass
class Texture:
    id: int
    type: str
    path: str
    
class Mesh:
    def __init__(self, vertices: list[Vertex], indices: list[int], textures: list[Texture]):
        self.vertices = []
        for v in vertices:
            self.vertices.extend(v.array.to_list())

        self.vertices = glm.array(np.array(self.vertices, dtype=np.float32))

        self.indices = glm.array.from_numbers(glm.uint32, *indices)

        self.textures = textures

        self.__setupMesh()
    
    def __setupMesh(self) -> None:
        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(1)
        self.EBO = glGenBuffers(1)

        glBindVertexArray(self.VAO)

        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices.ptr, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices.ptr, GL_STATIC_DRAW)

        # vertex position
        glEnableVertexAttribArray(0)	
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, Vertex.size(), None)
        
        # vertex normals
        glEnableVertexAttribArray(1)	
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, Vertex.size(), Vertex.normalOffset())
        
        # vertex texture coords
        glEnableVertexAttribArray(2)	
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, Vertex.size(), Vertex.texCoordsOffset())
        
        glBindVertexArray(0)

    def draw(self, shaderProgram: ShaderProgram) -> None:
        # bind appropriate textures
        diffuseNr  = 1
        specularNr = 1
        normalNr   = 1
        heightNr   = 1

        for i in range(len(self.textures)):
            glActiveTexture(GL_TEXTURE0 + i)

            number = None
            name = self.textures[i].type
            
            if name == "texture_diffuse":
                number = str(diffuseNr)
                diffuseNr += 1
            elif name == "texture_specular":
                number = str(specularNr)
                specularNr += 1
            elif(name == "texture_normal"):
                number = str(normalNr)
                normalNr += 1
            elif(name == "texture_height"):
                number = str(heightNr)
                heightNr += 1

            glUniform1i(glGetUniformLocation(shaderProgram.Id, name+number), i)
            glBindTexture(GL_TEXTURE_2D, self.textures[i].id)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, 0)
