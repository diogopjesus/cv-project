import numpy as np
import pygame as pg
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLU import *
import glm

from shader import ShaderProgram
from camera import Camera
from model import Model
from skybox import Skybox
from light import LightManager
from terrain import HeightMapTerrain

def load_cubemap(faces: list[str]) -> int:
    textureId = glGenTextures(1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, textureId)

    from PIL import Image
    for i in range(len(faces)):
        with Image.open(faces[i]).transpose(Image.FLIP_TOP_BOTTOM) as img:
            glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB, img.width, img.height, 0, GL_UNSIGNED_BYTE, img.tobytes())
        
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

    return textureId

faces = [
    "skybox/right.jpg",
    "skybox/left.jpg",
    "skybox/top.jpg",
    "skybox/bottom.jpg",
    "skybox/front.jpg",
    "skybox/back.jpg"
]

faces = [
    "skybox2/right.bmp",
    "skybox2/left.bmp",
    "skybox2/top.bmp",
    "skybox2/bottom.bmp",
    "skybox2/front.bmp",
    "skybox2/back.bmp"
]

faces = [
    "skybox3/right.tga",
    "skybox3/left.tga",
    "skybox3/top.tga",
    "skybox3/bottom.tga",
    "skybox3/front.tga",
    "skybox3/back.tga"
]

grab = False
forward = left = backward = right = False
def process_events(camera: Camera, deltaTime: float) -> Camera:
    global grab, forward, left, backward, right

    pg.event.pump()
    
    running = True
    for event in pg.event.get():
        if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
            running = False

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_w:
                forward = True
            if event.key == pg.K_a:
                left = True
            if event.key == pg.K_s:
                backward = True
            if event.key == pg.K_d:
                right = True

        if event.type == pg.KEYUP:
            if event.key == pg.K_w:
                forward = False
            if event.key == pg.K_a:
                left = False
            if event.key == pg.K_s:
                backward = False
            if event.key == pg.K_d:
                right = False

    if forward:
        camera.translate(Camera.MOVE_FOWARD, deltaTime)
    if left:
        camera.translate(Camera.MOVE_LEFT, deltaTime)
    if backward:
        camera.translate(Camera.MOVE_BACKWARD, deltaTime)
    if right:
        camera.translate(Camera.MOVE_RIGHT, deltaTime)

    mov = pg.mouse.get_rel()
    click = pg.mouse.get_pressed()
    if click[0]:
        camera.rotate(-mov[0], -mov[1], constrainPitch=False)
    
    return running


# create a display
pg.init()
display = (800, 600)
screen = pg.display.set_mode(display, pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)
clock = pg.time.Clock()
running = True

camera = Camera(glm.vec3(0,0,8), glm.vec3(0,1,0), -90, 0)
pg.event.set_grab(False)

myModel = Model("models/backpack.obj")

glEnable(GL_DEPTH_TEST)
glClearColor(0.2,0.2,0.2,1)

# init shader program
vsCode = open("shaders/model.vert", "r")
fgCode = open("shaders/model.frag", "r")
shaderProgram = ShaderProgram(vsCode.read(), fgCode.read())
vsCode.close()
fgCode.close()

vsCode = open("shaders/skybox.vert", "r")
fgCode = open("shaders/skybox.frag", "r")
skyboxProgram = ShaderProgram(vsCode.read(), fgCode.read())
vsCode.close()
fgCode.close()

vsCode = open("shaders/lightSource.vert", "r")
fgCode = open("shaders/lightSource.frag", "r")
lightProgram = ShaderProgram(vsCode.read(), fgCode.read())
vsCode.close()
fgCode.close()

vsCode = open("shaders/heightMapTerrain.vert", "r")
fgCode = open("shaders/heightMapTerrain.frag", "r")
terrainProgram = ShaderProgram(vsCode.read(), fgCode.read())
vsCode.close()
fgCode.close()

skybox = Skybox(faces)

lightManager = LightManager()

pointLightPositions = [
    glm.vec3( 0.7,  0.2,  2.0),
    glm.vec3( 2.3, -3.3, -4.0),
    glm.vec3(-4.0,  2.0, -12.0),
    glm.vec3( 0.0,  0.0, -3.0)
]

lightManager.setDirLight(
    direction = glm.vec3(-0.2, -1.0, -0.3),
    ambient = glm.vec3(0.05, 0.05, 0.05),
    diffuse = glm.vec3(0.4, 0.4, 0.4),
    specular = glm.vec3(0.5, 0.5, 0.5)
)

lightManager.setSpotLight(
    ambient = camera.position,
    diffuse = glm.vec3(1.0, 1.0, 1.0),
    specular = glm.vec3(1.0, 1.0, 1.0),
    constant = 1.0,
    linear = 0.09,
    quadratic = 0.032,
    cutOff = glm.cos(glm.radians(12.5)),
    outerCutOff = glm.cos(glm.radians(15.0))
)

for i in range(len(pointLightPositions)):
    lightManager.setPointLight(
        i,
        position = pointLightPositions[i],
        ambient = glm.vec3(0.05, 0.05, 0.05),
        diffuse = glm.vec3(0.8, 0.8, 0.8),
        specular = glm.vec3(1.0, 1.0, 1.0),
        constant = 1.0,
        linear = 0.09,
        quadratic = 0.032
    )

lightManager.toggleSpotLight()

terrain = HeightMapTerrain("terrains/aveiro.png")

deltaTime = 0.0

while running:

    running = process_events(camera, deltaTime)

    # render iteration
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    projection = glm.perspective(glm.radians(camera.getZoom()), display[0]/display[1], 0.1, 100)
    view = camera.getViewMatrix()
    
    lightColor = glm.vec3(1,1,1)
    lightPos =  glm.vec3(3,3,0)

    viewPos = camera.position

    lightProgram.use()
    
    model = glm.mat4(1.0)
    model = glm.translate(model,lightPos)
    model = glm.scale(model, glm.vec3(0.2,0.2,0.2))    
    lightProgram.setMat4("model", model)
    lightProgram.setMat4("view", view)
    lightProgram.setMat4("projection", projection)

    lightManager.drawPointLights(lightProgram)

    terrainProgram.use()
    
    model = glm.mat4(1.0)
    terrainProgram.setMat4("model", model)
    terrainProgram.setMat4("view", view)
    terrainProgram.setMat4("projection", projection)

    terrain.draw(terrainProgram)

    shaderProgram.use()
    
    model = glm.mat4(1.0)
    shaderProgram.setMat4("model", model)
    shaderProgram.setMat4("view", view)
    shaderProgram.setMat4("projection", projection)

    shaderProgram.setVec3("viewPos", viewPos)

    lightManager.setUniforms(shaderProgram, camera)

    shaderProgram.setFloat("shininess", 32.0)

    myModel.draw(shaderProgram)

    skyboxProgram.use()
    
    model = glm.mat4(1.0)
    view = glm.mat4(glm.mat3(view)) # remove translation from the view matrix
    skyboxProgram.setMat4("view", view)
    skyboxProgram.setMat4("projection", projection)
    skybox.draw(skyboxProgram)
    
    pg.display.flip()

    deltaTime = clock.tick(60) / 1000

shaderProgram.delete()

pg.quit()
   