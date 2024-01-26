from enum import Enum
import glm

# Default camera values
YAW         = -90.0
PITCH       =  0.0
SPEED       =  2.5
SENSITIVITY =  0.1
ZOOM        =  45.0

class Camera:
    class Movement(int):
        """ Movement description """

    MOVE_FOWARD = Movement(1)
    MOVE_BACKWARD = Movement(2)
    MOVE_LEFT = Movement(3)
    MOVE_RIGHT = Movement(4)
    
    DEFAULT_SPEED = 2.5
    DEFAULT_SENSITIVITY = 0.1
    DEFAULT_ZOOM = 45.0
    
    def __init__(self, position: glm.vec3, worldUp: glm.vec3, yaw: float, pitch: float):
        self.position = position
        self.worldUp = worldUp
        self.yaw = yaw
        self.pitch = pitch
        
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.up = glm.vec3()
        self.right = glm.vec3()
        self.movementSpeed = Camera.DEFAULT_SPEED
        self.mouseSensitivity = Camera.DEFAULT_SENSITIVITY
        self.zoom = Camera.DEFAULT_ZOOM

        self.__updateCameraVectors()

    def __updateCameraVectors(self) -> None:
        # calculate the new front vector
        front = glm.vec3()
        front.x = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        front.y = glm.sin(glm.radians(self.pitch))
        front.z = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        self.front = glm.normalize(front)

        # re-calculate the right and up vector
        self.right = glm.normalize(glm.cross(self.front, self.worldUp))  # normalize the vectors, because their length gets closer to 0 the more you look up or down which results in slower movement.
        self.up    = glm.normalize(glm.cross(self.right, self.front))

    def getViewMatrix(self) -> glm.mat4:
        return glm.lookAt(self.position, self.position + self.front, self.up)

    def translate(self, direction: Movement, deltaTime: float) -> None:
        velocity = self.movementSpeed * deltaTime
        if (direction == Camera.MOVE_FOWARD):
            self.position += self.front * velocity
        if (direction == Camera.MOVE_BACKWARD):
            self.position -= self.front * velocity
        if (direction == Camera.MOVE_LEFT):
            self.position -= self.right * velocity
        if (direction == Camera.MOVE_RIGHT):
            self.position += self.right * velocity
    
    def rotate(self, xoffset: float, yoffset: float, constrainPitch: bool = True) -> None:
        xoffset *= self.mouseSensitivity
        yoffset *= self.mouseSensitivity
        
        self.yaw += xoffset
        self.pitch -= yoffset
        
        if constrainPitch:
            if self.pitch > 89.0:
                self.pitch = 89.0
            if self.pitch < -89.0:
                self.pitch = -89.0

        self.__updateCameraVectors()

    def updateZoom(self, offset: float) -> None:
        self.zoom -= offset
        if self.zoom < 1.0:
            self.zoom = 1.0
        if self.zoom > 45.0:
            self.zoom = 45.0

    def getZoom(self) -> float:
        return self.zoom