# coding=utf-8

'''
Tool Maya che date N reference te le piazza automaticamente in scena
(in base a top, side, front)
* Anche da cartella in automatico
* Devono essere locked e messe su un altro layer
* Slider per settare size e distanza
'''

import maya.cmds as cmds
from pymel.all import Callback
import re


class PlaneType(object):
    TOP = 'top'
    BOTTOM = 'bottom'
    SIDE_L = 'side_l'
    SIDE_R = 'side_r'
    FRONT = 'front'
    BACK = 'back'


planes = {}


# TEST Reset the scene to the original state
def TestResetScene():
    cmds.select(all=True)
    cmds.delete()


# TEST Reset hypeshade to the original state
def TestResetHypershade():
    materials = cmds.ls(type='shadingDependNode')
    cmds.delete(materials)


def TestResetLayers():
    layers = cmds.ls(type='displayLayer')
    cmds.delete(layers)


def LoadImagePath(planeType):
    imgFilter = 'All Image files (*.jpg *.gif *.png);;'
    imgPath = cmds.fileDialog2(fileFilter=imgFilter, dialogStyle=1, fileMode=1)
    SetImagePath(planeType, imgPath[0])
    RefreshUIImgPath(planeType, imgPath[0])


def SetImagePath(planeType, imagePath):
    global planes
    planes[planeType] = imagePath


def RefreshUIImgPath(planeType, imagePath):
    cmds.textField(planeType+'_field', edit=True, tx=str(imagePath))


def RefreshAllUIImgPath():
    for plane in planes:
        RefreshUIImgPath(plane, planes[plane])


def CreatePlane(planeType):
    global planes
    planeSize = cmds.intSliderGrp('plane_size', q=True, v=True)
    planeDistance = cmds.intSliderGrp('plane_distance', q=True, v=True)

    halfSize = (planeSize / 2.0)

    print(halfSize)

    if planeType == PlaneType.TOP:
        # Top
        plane = cmds.polyPlane(n='ref_top', w=planeSize, h=planeSize, sx=1, sy=1, ax=(0, 1, 0))
        cmds.setAttr(plane[0]+'.translate', 0, (planeSize + planeDistance), 0)

    elif planeType == PlaneType.BOTTOM:
        # Bottom
        plane = cmds.polyPlane(n='ref_bottom', w=planeSize, h=planeSize, sx=1, sy=1, ax=(0, 1, 0))
        cmds.setAttr(plane[0]+'.translate', 0, -planeDistance, 0)
        cmds.setAttr(plane[0]+'.rotate', 0, 0, 180)

    elif planeType == PlaneType.SIDE_L:
        # Left Side
        plane = cmds.polyPlane(n='ref_side_l', w=planeSize, h=planeSize, sx=1, sy=1, ax=(1, 0, 0))
        cmds.setAttr(plane[0]+'.translate', -(halfSize + planeDistance), halfSize, 0)
        cmds.setAttr(plane[0]+'.rotate', 0, 0, 180)

    elif planeType == PlaneType.SIDE_R:
        # Rignt Side
        plane = cmds.polyPlane(n='ref_side_r', w=planeSize, h=planeSize, sx=1, sy=1, ax=(1, 0, 0))
        cmds.setAttr(plane[0]+'.translate', (halfSize + planeDistance), halfSize, 0)
        cmds.setAttr(plane[0]+'.rotate', 0, 0, 0)

    elif planeType == PlaneType.FRONT:
        # Front
        plane = cmds.polyPlane(n='ref_front', w=planeSize, h=planeSize, sx=1, sy=1, ax=(0, 0, 1))
        cmds.setAttr(plane[0]+'.translate', 0, halfSize, (halfSize + planeDistance))

    elif planeType == PlaneType.BACK:
        # Back
        plane = cmds.polyPlane(n='ref_back', w=planeSize, h=planeSize, sx=1, sy=1, ax=(0, 0, 1))
        cmds.setAttr(plane[0]+'.translate', 0, halfSize, -(halfSize + planeDistance))
        cmds.setAttr(plane[0]+'.rotate', 0, 180, 0)

    return plane


def ApplyTexture(mesh, texturePath):
    material = CreateMaterialFromPath(texturePath)
    cmds.select(mesh[0])
    cmds.hyperShade(assign=material)


def CreateMaterialFromPath(texturePath):
    # Creates a new lambert
    myMaterial = cmds.shadingNode('lambert', asShader=True)
    # Creates a shading node for the file
    myFile = cmds.shadingNode('file', asTexture=True)
    # Creates a shading group
    myShadingGroup = cmds.sets(renderable=True, noSurfaceShader=True, empty=True)
    # Sets the texture path
    cmds.setAttr(myFile+'.fileTextureName', texturePath, type='string')
    # Assigns the Texture File Name to the Shading Group Shader
    cmds.connectAttr(myMaterial+'.outColor', myShadingGroup+'.surfaceShader')
    # Assigns the Texture Color to the Material Color
    cmds.connectAttr(myFile+'.outColor', myMaterial+'.color')
    # Returns the material
    return myMaterial


def SearchReferencesInFolder():
    global planes

    directory = cmds.fileDialog2(dialogStyle=1, fileMode=3)[0]
    files = cmds.getFileList(folder=directory)

    for file in files:
        if re.search(r'top', file):
            planes[PlaneType.TOP] = directory+'/'+file
        elif re.search(r'bottom', file):
            planes[PlaneType.BOTTOM] = directory+'/'+file
        elif re.search(r'left', file):
            planes[PlaneType.SIDE_L] = directory+'/'+file
        elif re.search(r'right', file):
            planes[PlaneType.SIDE_R] = directory+'/'+file
        elif re.search(r'front', file):
            planes[PlaneType.FRONT] = directory+'/'+file
        elif re.search(r'back', file):
            planes[PlaneType.BACK] = directory+'/'+file

    RefreshAllUIImgPath()


def CreateReferenceLayer():
    cmds.createDisplayLayer(n='ReferenceLayer', empty=True)
    cmds.setAttr('ReferenceLayer.displayType', 2)


def AddMeshToReferenceLayer(meshName):
    cmds.editDisplayLayerMembers('ReferenceLayer', meshName)


def GeneratePlanes():
    global planes
    CreateReferenceLayer()
    for planeType in planes:
        plane = CreatePlane(planeType)
        ApplyTexture(plane, planes[planeType])
        AddMeshToReferenceLayer(plane)


def InitUI():
    win_name = 'quick_ref_setup'

    if cmds.window(win_name, q=True, ex=True):
        cmds.deleteUI(win_name)

    cmds.window(win_name, t='Quick References Setup')
    cmds.window(win_name, e=True, height=100, width=500, sizeable=False)
    cmds.columnLayout(adj=True)

    cmds.intSliderGrp('plane_size', f=True, l='Plane Size', minValue=1, maxValue=10, value=5)
    cmds.intSliderGrp('plane_distance', f=True, l='Plane Distance', minValue=0, maxValue=10, value=1)

    cmds.rowLayout(adj=True, nc=2)
    cmds.textField('top_field')
    cmds.button(label='Select Top', w=100, c=Callback(LoadImagePath, PlaneType.TOP))
    cmds.setParent('..')

    cmds.rowLayout(adj=True, nc=2)
    cmds.textField('bottom_field')
    cmds.button(label='Select Bottom', w=100, c=Callback(LoadImagePath, PlaneType.BOTTOM))
    cmds.setParent('..')

    cmds.rowLayout(adj=True, nc=2)
    cmds.textField('side_l_field')
    cmds.button(label='Select Left Side', w=100, c=Callback(LoadImagePath, PlaneType.SIDE_L))
    cmds.setParent('..')

    cmds.rowLayout(adj=True, nc=2)
    cmds.textField('side_r_field')
    cmds.button(label='Select Right Side', w=100, c=Callback(LoadImagePath, PlaneType.SIDE_R))
    cmds.setParent('..')

    cmds.rowLayout(adj=True, nc=2)
    cmds.textField('front_field')
    cmds.button(label='Select Front', w=100, c=Callback(LoadImagePath, PlaneType.FRONT))
    cmds.setParent('..')

    cmds.rowLayout(adj=True, nc=2)
    cmds.textField('back_field')
    cmds.button(label='Select Back', w=100, c=Callback(LoadImagePath, PlaneType.BACK))
    cmds.setParent('..')

    cmds.rowLayout(nc=2)
    cmds.button(label='Load from folder', h=50, w=250, c=Callback(SearchReferencesInFolder))
    cmds.button(label='Generate', h=50, w=250, c=Callback(GeneratePlanes))
    cmds.setParent('..')
    cmds.showWindow(win_name)


# TestResetHypershade()
# TestResetScene()
# TestResetLayers()
InitUI()