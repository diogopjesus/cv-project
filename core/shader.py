from OpenGL.GL import *
from OpenGL.GL import shaders

import glm

class ShaderProgram:
    def __init__(self, vertexShaderCode: str, fragmentShaderCode: str, geometryShaderCode: str = None):
        """Object representation of a shader program.

        Args:
            vertexShaderCode (str): String of vertex shader code.
            fragmentShaderCode (str): String of fragment shader code.
            geometryShaderCode (str, optional): String of geometry shader code. Defaults to None.
        """
        if geometryShaderCode:
            self.Id = shaders.compileProgram(
                shaders.compileShader(vertexShaderCode, GL_VERTEX_SHADER),
                shaders.compileShader(geometryShaderCode, GL_GEOMETRY_SHADER),
                shaders.compileShader(fragmentShaderCode, GL_FRAGMENT_SHADER)
            )

        else:
            self.Id = shaders.compileProgram(
                shaders.compileShader(vertexShaderCode, GL_VERTEX_SHADER),
                shaders.compileShader(fragmentShaderCode, GL_FRAGMENT_SHADER)
            )

    def use(self) -> None:
        """Use shader program.
        """
        glUseProgram(self.Id)       

    def delete(self) -> None:
        """Delete shader program.
        """
        glDeleteProgram(self.Id)

    def setBool(self, name: str, value: bool) -> None:
        """Specify boolean value to a uniform variable.

        Args:
            name (str): Name of the variable.
            value (bool): Value to be specified.
        """
        glUniform1i(glGetUniformLocation(self.Id, name), int(value))
    
    def setInt(self, name: str, value: int) -> None:
        """Specify integer value to a uniform variable.

        Args:
            name (str): Name of the variable.
            value (int): Value to be specified.
        """
        glUniform1i(glGetUniformLocation(self.Id, name), value)
    
    def setFloat(self, name: str, value: float) -> None:
        """Specify float value to a uniform variable.

        Args:
            name (str): Name of the variable.
            value (float): Value to be specified.
        """
        glUniform1f(glGetUniformLocation(self.Id, name), value)

    def setVec2(self, name: str, *args) -> None:
        """Specify a 2D vector to a uniform variable.

        Args:
            name (str): Name of the variable.
            args : Value to be specified.
        """
        # args is a glm object
        if (len(args) == 1 and type(args[0]) == glm.vec2):
            glUniform2fv(glGetUniformLocation(self.Id, name), 1, glm.value_ptr(args[0]))

        elif (len(args) == 2 and all(map(lambda x: type(x) == float, args))):
            glUniform2f(glGetUniformLocation(self.Id, name), *args)

    def setVec3(self, name: str, *args) -> None:
        """Specify a 3D vector to a uniform variable.

        Args:
            name (str): Name of the variable.
            args : Value to be specified.
        """
        # args is a glm object
        if (len(args) == 1 and type(args[0]) == glm.vec3):
            glUniform3fv(glGetUniformLocation(self.Id, name), 1, glm.value_ptr(args[0]))

        elif (len(args) == 3 and all(map(lambda x: type(x) == float, args))):
            glUniform3f(glGetUniformLocation(self.Id, name), *args)

    def setVec4(self, name: str, *args) -> None:
        """Specify a 4D vector to a uniform variable.

        Args:
            name (str): Name of the variable.
            args : Value to be specified.
        """
        # args is a glm object
        if (len(args) == 1 and type(args[0]) == glm.vec4):
            glUniform4fv(glGetUniformLocation(self.Id, name), 1, glm.value_ptr(args[0]))
        
        elif (len(args) == 3 and all(map(lambda x: type(x) == float, args))):
            glUniform4f(glGetUniformLocation(self.Id, name), *args)
    
    def setMat2(self, name: str, mat: glm.mat2) -> None:
        """Specify a Matrix 2x2 to a uniform variable.

        Args:
            name (str): Name of the variable.
            mat (glm.mat2): Value to be specified.
        """
        glUniformMatrix2fv(glGetUniformLocation(self.Id, name), 1, GL_FALSE, glm.value_ptr(mat))

    def setMat3(self, name: str, mat: glm.mat3) -> None:
        """Specify a Matrix 3x3 to a uniform variable.

        Args:
            name (str): Name of the variable.
            mat (glm.mat3): Value to be specified.
        """
        glUniformMatrix3fv(glGetUniformLocation(self.Id, name), 1, GL_FALSE, glm.value_ptr(mat))

    def setMat4(self, name: str, mat: glm.mat4) -> None:
        """Specify a Matrix 4x4 to a uniform variable.

        Args:
            name (str): Name of the variable.
            mat (glm.mat4): Value to be specified.
        """
        glUniformMatrix4fv(glGetUniformLocation(self.Id, name), 1, GL_FALSE, glm.value_ptr(mat))

    # NOTE: DEPRECATED FUNCTION. Useless because the OpenGL.GL.shaders helper function already check for shader and program health status.
    # @staticmethod
    # def __checkCompileErrors(shader: int, type: str) -> None:
    #     if type != "PROGRAM":
    #         ret = glGetShaderiv(shader, GL_COMPILE_STATUS)
    #         if not ret:
    #             raise RuntimeError(glGetProgramInfoLog(shader))
    #     else:
    #         ret = glGetProgramiv(shader, GL_LINK_STATUS)
    #         if not ret:
    #             raise RuntimeError(glGetProgramInfoLog(shader))
