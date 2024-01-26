import pyassimp
from pyassimp.material import *
from pyassimp.postprocess import *

from PIL import Image

from OpenGL.GL import *
import glm

from .mesh import Mesh, Vertex, Texture
from .shader import ShaderProgram

class Model:
    def __init__(self, path: str):
        self.meshes = []
        self.texturesLoaded = []
        self.__loadModel(path)
    
    def draw(self, shaderProgram: ShaderProgram) -> None:
        for mesh in self.meshes:
           mesh.draw(shaderProgram)
    
    def __loadModel(self, path: str) -> None:
        processingFlags = aiProcess_Triangulate | aiProcess_GenNormals | aiProcess_FlipUVs
        with pyassimp.load(path, processing=processingFlags) as scene:
            assert scene.rootnode
            self.directory = "/".join(path.split("/")[:-1])
            self.__processNode(scene.rootnode, scene)
            
    def __processNode(self, node, scene) -> None:
        for mesh in node.meshes:
            self.meshes.append(self.__processMesh(mesh, scene))
        
        for child in node.children:
            self.__processNode(child, scene)
        
    def __processMesh(self, mesh, scene) -> Mesh:
        vertices = []
        indices = []
        textures = []
        
        for i in range(len(mesh.vertices)):
            position = glm.vec3(mesh.vertices[i][0], mesh.vertices[i][1], mesh.vertices[i][2])

            normal = glm.vec3(0,0,0)
            if len(mesh.normals) > 0:
                normal = glm.vec3(mesh.normals[i][0], mesh.normals[i][1], mesh.normals[i][2])

            texCoord = glm.vec2(0,0)
            if len(mesh.texturecoords) > 0 and mesh.texturecoords[0] is not None:
                texCoord = glm.vec2(mesh.texturecoords[0][i][0], mesh.texturecoords[0][i][1])

            vertices.append(Vertex(position,normal,texCoord))
        
        for face in mesh.faces:
            for i in face:
                indices.append(i)

        if mesh.materialindex:
            material = scene.materials[mesh.materialindex]
            
            diffuseMaps = self.__loadMaterialTextures(material, aiTextureType_DIFFUSE, "texture_diffuse")
            textures += diffuseMaps
            
            specularMaps = self.__loadMaterialTextures(material, aiTextureType_SPECULAR, "texture_specular")
            textures += specularMaps
            
            normalMaps = self.__loadMaterialTextures(material, aiTextureType_HEIGHT, "texture_normal")
            textures += normalMaps
            
            heightMaps = self.__loadMaterialTextures(material, aiTextureType_AMBIENT, "texture_height")
            textures += heightMaps

        return Mesh(vertices,indices,textures)
            
    def __loadMaterialTextures(self, mat, type, typeName: str) -> list[Texture]:
        textures = []
        
        files = mat.properties.get(("file", type))
        
        if not files:
            return textures
        
        if not isinstance(files,list): # TODO: check if when there is more than 1 file for the same category it converts to a list or adds another key to the dict
            files = [files]

        for path in files:
            skip = False
            for tex in self.texturesLoaded:
                if tex.path == path:
                    textures.append(tex)
                    skip = True
                    break
            
            if not skip:
                textureId = TextureFromFile(path, self.directory)
                texture = Texture(textureId, typeName, path)
                textures.append(texture)
                self.texturesLoaded.append(texture)
        
        return textures

def TextureFromFile(path: str, directory: str):
    filename = directory + "/" + path
    textureId = glGenTextures(1)
   
    with Image.open(filename).transpose(Image.FLIP_TOP_BOTTOM) as img:
        nrComponents = len(img.getbands())
        format = GL_RED if nrComponents == 1 else \
                 GL_RGB if nrComponents == 3 else \
                 GL_RGBA
        
        glBindTexture(GL_TEXTURE_2D, textureId)
        glTexImage2D(GL_TEXTURE_2D, 0, format, img.width, img.height, 0, format, GL_UNSIGNED_BYTE, img.tobytes())
        glGenerateMipmap(GL_TEXTURE_2D)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glBindTexture(GL_TEXTURE_2D, 0)
    
    return textureId
