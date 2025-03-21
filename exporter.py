
# Scene organizer with export options
# Made by Michael Kato in the year of 2013 #
# Thanks to James Kyle @ jameskyle.net for some good ideas and a few lines of code (FBX export stuff)

#import myScripts.boundingBox as BB
import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm
import os

# TODO: Move objects to 0,0,0 on export, then move them back
# TODO: What happens if an object's name changes? How will it update in the textScrollList?
# TODO: change "scrollListName" to either "attrName" or just "scrollList"

try:
    # Get path to scene, including scene name
    rawPath = cmds.file(query=True, sceneName=True)
    # Split scene name from directory and store them in separate variables
    scenePath, sceneName = rawPath.rsplit('/', 1)
except:
    print("Must save your scene first!")
    scenePath = cmds.internalVar(userWorkspaceDir=True)
    sceneName = 'Unknown'

# UI color pallette
darkGreen = [0.2,0.3,0.2]
lightGreen = [0.3,0.3,0.2]
darkBlue = [0.2,0.2,0.3]
lightBlue = [0.2,0.3,0.3]
darkRed = [0.4,0.3,0.3]
lightRed = [0.3,0.3,0.2]


def getAttribute(scrollListName, objects=None):
    mObjNames, mAttrNames, mAttrData = [],[],[]
    allObjects = cmds.ls()
    # To get the attribute of just the specified object
    if objects:
        print("Getting attributes from specific object(s)")
        # Use function arg input instead of cmds.ls()
        allObjects = objects

    for objName in allObjects:
        # if attribute exists on object
        if cmds.attributeQuery(scrollListName, node=objName, exists=True):

            # Only needs to find one object (presumably)
            if scrollListName == 'animList':
                attrName = objName+'.'+scrollListName
                rawString = cmds.getAttr(attrName)
                try:
                    # try to evaluate data from attribute
                    attrData = eval(rawString)
                except:
                    print("No data found in attribute.")
                    attrData = []
                # returns both the object where data is stored, its attribute name, and the data itself in that order
                return objName, attrName, attrData
                
            # Needs to find many objects in scene, all with the same attr name, then later return the compiled lists, outside this loop
            if scrollListName == 'modelList':
                mAttrNames.append( objName+'.'+scrollListName )
                rawString = cmds.getAttr(mAttrNames[-1])
                try:
                    # try to evaluate data from attribute
                    mObjNames.append(objName)
                    mAttrData.append( eval(rawString) )
                except:
                    print("No data found in attribute.")
                    mAttrData.append(None)
                    
    # Return data outside the loop, so it can process everything
    if scrollListName == 'modelList':
        return mObjNames, mAttrNames, mAttrData
        
    # Script needs to return something to avoid errors in case it finds nothing at all
    return None, None, None

        
def setAttribute(scrollListName, attrName='', data='', mode=''):
    # need to make sure there's an object set to store data
    if mode == 'SetData':
        for attr in data:
            print(attr)
            try:
                # Make sure attr is unlocked before edit:
                cmds.setAttr(attrName, edit=True, lock=False)
                # Set attr to string value:
                cmds.setAttr(attrName, attr, type='string')
                # And lock it for safety:
                cmds.setAttr(attrName, edit=True, lock=True)
                # Add new anim name to textScrollList
                updateTextList(scrollListName, mode='RefreshAll')
            except:
                print("Error adding attribute to object")
    
    if mode == 'PickDataObject':
        objName = cmds.ls(sl=True)[0]
        # check if attribute exists, if not, initialize it
        if not cmds.attributeQuery( scrollListName, node=objName, exists=True):
            attrName = objName+'.'+scrollListName
            print("Attribute does not exist, adding to:", objName, 'as', scrollListName)
            cmds.addAttr(objName, longName=scrollListName, dataType='string')
            # update button text to reflect what object is being used to store data
            cmds.button('selectControl', edit=True, label='Data Node: %s' %objName)


def editAttribute(scrollListName, mode='', newItem=None):
    # This is going to have to change
    if scrollListName != 'textureList':
        selectedListItems = cmds.textScrollList(scrollListName, query=True, si=True)
        selectedSceneObjects = cmds.ls(sl=True)
    
    if scrollListName == 'animList':
        # Find object where data is stored, it's attribute, and get attr data
        dataObject, attrName, attrData = getAttribute(scrollListName)
        # Save min and max of current time range
        timeRange = [ cmds.playbackOptions(query=True, min=True), cmds.playbackOptions(query=True, max=True) ]
        if mode == 'AddRange':
            # user names the animation
            animName = raw_input("Name the animation")
            # check if user gave a name
            if animName:
                attrData.append([animName,timeRange])
                setAttribute(scrollListName, attrName=attrName, data=attrData, mode='SetData')    
        if mode == 'RestoreRange':
            # get frame range of selected animation, and apply it
            frameRange = eval(attrData[selectedListItems[0]])
            cmds.playbackOptions(min=frameRange[0], max=frameRange[1])
        if mode == 'DeleteRange':
            # Go through selection in case of multiple simultaneous deletions
            for animName in selectedListItems:
                # Iterate though list, find match for animName and delete it
                for index, value in enumerate(attrData):
                    if value[0] == animName:
                        attrData.remove(value)
                        cmds.textScrollList(scrollListName, edit=True, removeItem=animName)
            # Set attribute with new data
            setAttribute(scrollListName, attrName=attrName, data=attrData, mode='SetData')
        # NOT USED
        if mode == 'RefreshAll':
            cmds.textScrollList(scrollListName, edit=True, removeAll=True)
            updateTextList(scrollListName, mode='RefreshAll')
            
    if scrollListName == 'modelList':
        # Used to initialize new object into list
        if mode == 'Add':
            # Create empty dictionary to pass many objects and their attributes to the setAttribute() function
            attrData = []
            for object in selectedSceneObjects:
                # Create attribute name for object
                attrName = object +'.'+ scrollListName
                # Check if attribute exists, if not, initialize it
                if not cmds.objExists(attrName):
                    cmds.addAttr(object, longName=scrollListName, dataType='string')
                    # Add new entry to list
                    attrData.append( [scenePath,attrName] )
            # Create attributes
            setAttribute(scrollListName, attrName=attrName, data=attrData, mode='SetData')
            
        # Delete object from list and it's attribute
        if mode == 'Delete':
            deleteAttribute(scrollListName)

    if scrollListName == 'textureList':
        print("Texture list stuff goes here")
        if mode == 'Add':
            print("Add material to list")
            mat = cmds.ls(sl=True)[0]
            cmds.swatchDisplayPort(scrollListName, edit=True, shadingNode=mat, borderWidth=2)
        if mode == 'Delete':
            print("Deleting material from list")


def deleteAttribute(scrollListName):
    objects = cmds.textScrollList(scrollListName, q=True, si=True)
    print(objects)
    for object in objects:
        attrName = object+'.'+scrollListName
        # Unlock attribute, so it can be deleted
        cmds.setAttr(attrName, edit=True, lock=False)
        cmds.deleteAttr(object, at=scrollListName)
        # Remove reference from UI fields, this will affect
        cmds.textFieldGrp('animNameField', edit=True, text='None')
        cmds.intFieldGrp('animFrameField', edit=True, value1=0, value2=0)
    updateTextFields(scrollListName, mode='RefreshAll')


def selectObject(scrollListName, object='', mode=''):
    # When user double clicks an item in scrollList, this gets called
    if scrollListName=='modelList':
        item = cmds.textScrollList(scrollListName, query=True, si=True)
        cmds.select(item)
    if mode=='MasterControl':
        try:
            dataObject = getAttribute(scrollListName)[0]
            cmds.select(dataObject)
        except:
            print("DIDNT WORK")


def updateTextList(scrollListName, mode='', newItem='', oldItem='', range=None):
    if mode == 'RefreshAll':
        if scrollListName == 'animList':
            # Get objects and attributes
            dataObject, attrName, attrData = getAttribute(scrollListName)
            # Clear textList
            cmds.textScrollList(scrollListName, edit=True, removeAll=True)
            try:
                cmds.textScrollList(scrollListName, edit=True, append=attrData[0])
            except:
                print("No data in attribute: %s" %attrName)
            cmds.button('selectControl', edit=True, label="Data Node: %s" %dataObject)
            
        if scrollListName == 'modelList':
            # Get objects and attributes
            mObjNames, mAttrNames, mAttrData = getAttribute(scrollListName)
            # Clear textList 
            cmds.textScrollList(scrollListName, edit=True, removeAll=True)
            for index, objName in enumerate(mObjNames):
                try:
                    cmds.textScrollList(scrollListName, edit=True, append=objName)
                except:
                    print("No data in attribute: %s" %mAttrNames[index])


def updateTextFields(scrollListName, mode='', field='', browsing=False, newDirectory='', aRangeMin=0.0, aRangeMax=0.0):
    """ Updates text fields based on user selections, and updates data based on user changes"""

    # For updating fields when a text item is selected
    if scrollListName=='animList':
        # Gget attr object and data
        object, attrName, attrData = getAttribute(scrollListName)
        # Get name of selected animation
        aName = cmds.textScrollList(scrollListName, query=True, si=True)[0]

        # If user selects object in list
        if mode == 'Select':
            aRangeMin, aRangeMax = attrData[1]
            # Update fields with info
            cmds.textFieldGrp('animNameField', edit=True, text=aName)
            cmds.intFieldGrp('animFrameField', edit=True, value1=aRangeMin, value2=aRangeMax )
        
        # If user is editing fields and didn't just select anything
        if mode == 'Edit':
            # Apply animation name edits as user types them
            if field == 'animNameField':
                # Get user's new, edited name
                aNewName = cmds.textFieldGrp('animNameField', query=True, text=True)
                listPos = cmds.textScrollList(scrollListName, query=True, selectIndexedItem=True)
                cmds.textScrollList(scrollListName, edit=True, removeIndexedItem=listPos[0])
                cmds.textScrollList(scrollListName, edit=True, appendPosition=[listPos[0],aNewName])
                
                # Find and change name 
                for index, aData in enumerate(attrData):
                    if aData[0] == aName:
                        attrData[index] = [aNewName, aData[1]]
                
                setAttribute(scrollListName, attrName=attrName, data=attrData, mode='SetData')
                
                # Keep item selected, after being deleted and re-added
                cmds.textScrollList(scrollListName, edit=True, selectItem=aNewName)
                
            # Apply frame range edits as user types them
            if field == 'animFrameField':
                # Consider making frame edits actually move keyframes around
                aNewRange = cmds.intFieldGrp('animFrameField', query=True, value=True)
                print(aNewRange, aName)
                for index, aData in enumerate(attrData):
                    if aData[0] == aName:
                        attrData[index][1] = aNewRange
                setAttribute(scrollListName, attrName=attrName, data=attrData, mode='SetData')
          
    # Currently only used for updating the displayed directory      
    if scrollListName == 'modelList' and mode == 'Select':
        # Get name of selected object
        selectedObj = cmds.textScrollList(scrollListName, query=True, selectItem=True)
        # Object's attributes
        objName, attrName, attrData = getAttribute(scrollListName, objects=selectedObj) 
        '''
        TODO: Need to NOT hardcode the directory
        '''
        cmds.textFieldButtonGrp('setModelDir', edit=True, text=str(attrData[0][0]) )
        
    # Applies edits to the export path to the object's attribute 
    if mode == 'EditFilePath':
        # Get name of selected object
        selectedObj = cmds.textScrollList(scrollListName, query=True, selectItem=True)
        # Object's attributes
        objName, attrName, attrData = getAttribute(scrollListName, objects=selectedObj)
        # If user manuually edits directory field, grab the changes
        if not browsing:
            # Get modified directory
            newDirectory = cmds.textFieldButtonGrp(field, query=True, text=True)
        # Replace old directory with new one
        attrData[0][0] = newDirectory
        # Do it!
        setAttribute(scrollListName, attrName=attrName[0], data=attrData[0], mode='SetData')
        # Reselect item in list
        cmds.textScrollList(scrollListName, edit=True, selectItem=selectedObj[0])
        # Then refresh the directory to apply changes
        updateTextFields(scrollListName, mode='Select')


# Not used currently     
def copyToClipBoard(texDir=''):
    command = 'echo ' + texDir.strip() + '| clip'
    os.system(command)


""" All the functitons below are for building the UI modularly """

def makeListButtons(scrollListName, buttons=None, bColor=[]):
    cmds.columnLayout(columnAttach=('both', 5), columnAlign='center', rowSpacing=10, adjustableColumn=True)
    if scrollListName=='animList':
        # these are for storing and deleting the animation meta-data on an object
        cmds.frameLayout(label='Set Data Container', marginHeight=10, marginWidth=2, borderStyle='in', collapsable=True, collapse=True )#, bgc=bColor
        cmds.text(label="Use your rigs' master control, preferably")
        cmds.button(label='Set Data Object', 
            command=lambda *args: setAttribute(scrollListName, mode='PickDataObject'),
            ann="Select the object you wish to store animation data on, then click this button")#, bgc=bColor
        cmds.button('selectControl', label='Data Node: None', 
            command=lambda *args: selectObject(scrollListName, mode='MasterControl'),
            ann="This is the object you've used to store animation data, click button to select it")#, bgc=bColor
        cmds.button(label='Delete Data From Object(s)',
            command=lambda *args: deleteAttribute(scrollListName),
            ann="Select object and click this button to remove animation data")#, bgc=bColor
        cmds.setParent('..')
        
    if scrollListName=='animList':
        cmds.frameLayout( width=100, marginHeight=5, marginWidth=5, labelVisible=False, borderStyle='etchedIn' )
        cmds.textFieldGrp('animNameField', label='Animation Name -->', text='None', columnAlign2=['left','left'], adjustableColumn=2, 
            changeCommand=lambda *args:updateTextFields(scrollListName, field='animNameField', mode='Edit') )
        cmds.intFieldGrp('animFrameField', label='Frame Range -->',columnAlign3=['left','center','right'], columnAttach3=['left','left','both'], 
            columnWidth3=[0,50,50], columnOffset2=[0,0], numberOfFields=2, value1=0.0, value2=0.0, adjustableColumn=True,
            changeCommand=lambda *args:updateTextFields(scrollListName, field='animFrameField', mode='Edit') )
        cmds.setParent('..')
        
    if scrollListName=='textureList':
        pass 
    # create variable amount of buttons with different commands going to editAttribute()
    # used pymel for the Callback function (lambda wont work in a for loop)
    for buttonInfo in buttons:
        bName, bCommand, bAnnotation = buttonInfo
        cmds.button(bName,
            label= bName, 
            annotation=bAnnotation,
            command=pm.Callback( editAttribute, scrollListName, mode=bCommand ))#, bgc=bColor
    cmds.setParent('..')
    
    
def makeExportButtons( scrollListName, buttons=None, bColor=[] ):
    cmds.columnLayout( columnAttach=('both', 5), rowSpacing=10, columnWidth=250 )
    for buttonInfo in buttons:
        # More PyMEL
        cmds.button(buttonInfo[0],
                    label = buttonInfo[0],
                    command = pm.Callback(exportInit, scrollListName, exportMode=buttonInfo[1]))#, bgc=bColor
    cmds.setParent('..')
    
    
def makeTextList( scrollListName, description='' ):
    """Creates the GUI list that contains scene and animation references"""
    """this list gets referenced all the time and is very important"""
    
    cmds.text(label= description )
    cmds.separator(style='in') 
    cmds.paneLayout( configuration='vertical2' )
    
    # Use different GUI object depending on if the tab is anim, model, or texture
    if scrollListName=='animList' or 'modelList':
        cmds.textScrollList(scrollListName, 
            allowMultiSelection=True,
            doubleClickCommand=lambda *args:selectObject( scrollListName ),
            deleteKeyCommand=lambda *args:editAttribute( scrollListName, mode='Delete' ),
            selectCommand=lambda *args:updateTextFields( scrollListName, mode='Select' ),
            bgc=[0.0,0.1,0.0],
            annotation="Double click to select object"
        )
    # For textures
    else:
        cmds.columnLayout('textureSwatches')
        cmds.swatchDisplayPort(scrollListName, wh=(300, 500), backgroundColor=[0.1, 0.1, 0.1])
        cmds.setParent('..')


def makeDropDown( scrollListName ):
    """Creates file type selector"""
    cmds.optionMenuGrp(scrollListName+'TypeSelect', label='File Type  ' )#, changeCommand= lambda *args:changeFileType(), bgc=[1.0,1.0,0.0]
    cmds.menuItem(label='FBX')
    cmds.menuItem(label='OBJexport')
    cmds.menuItem(label='mayaAscii')
    cmds.menuItem(label='mayaBinary')


def getExportDir( scrollListName ):
    fPath = cmds.fileDialog2(dialogStyle=2, fileMode=2, caption="Select directoy to export to" )[0]
    print(fPath)
    updateTextFields(scrollListName, mode='EditFilePath', browsing=True, newDirectory=fPath)
    
    
def mkToolsUI():
    
    animListName = 'animList'
    modelListName = 'modelList'
    textureListName = 'textureList'
    
    # if window exists, delete and make a new one
    if cmds.window("mk_toolsWindow", exists=True):
        cmds.deleteUI("mk_toolsWindow", window=True)
    cmds.window("mk_toolsWindow", t="MK Tools", menuBar = True)
    cmds.frameLayout( width=520, height=700, labelVisible=False, marginHeight=10, marginWidth=2, borderStyle='etchedIn' )
    cmds.image( image='%MAYA_APP_DIR%/prefs/icons/mkTools.bmp', annotation='Even I use this tool!' )
    tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5)

    # ANIMATION TAB
    animMainFrame = cmds.frameLayout( label='Animation Options', 
        marginHeight=10, marginWidth=2, 
        borderStyle='in',
        collapsable=True )#, bgc=bColor
    # textScrollList function, pass the name of textScrollList, and some description
    makeTextList(scrollListName=animListName, description="Save a frame range here to make working with multiple animations easier")
    # Create buttons, pass makeTextList name, then list of tuples with button info
    makeListButtons( scrollListName = animListName,
                            buttons = [('Add Frame Range', 'AddRange', 'Name the current frame range, so you can come back to it later'), 
                                       ('Restore Frame Range', 'RestoreRange', 'Restore a saved frame range, to edit those frames'), 
                                       ('Delete Frame Range', 'DeleteRange', 'Remove your saved frame range')])
    cmds.setParent( '..' )
    # create browse directory elements
    cmds.frameLayout( label='Export Options', marginHeight=5, marginWidth=5, borderStyle='in', collapsable=True )#, bgc = darkGreen
    cmds.textFieldButtonGrp( 'setAnimDir', label='Directory to export to:    ',
        text=scenePath, 
        buttonLabel='Browse', 
        buttonCommand=lambda *args:getExportDir('animDir'),
        changeCommand=lambda *args:updateTextFields( animListName, mode='EditFilePath', field='setAnimDir'))
    cmds.separator( style='in' ) 
    # create export options buttons and drop down menu
    cmds.rowLayout( numberOfColumns=2, adjustableColumn=1 )
    cmds.columnLayout( adj=True )
    makeDropDown( animListName )
    cmds.checkBox( 'unityNames', label='Use @animName convention?' )
    cmds.setParent('..') # column layout
    makeExportButtons( scrollListName = animListName,
                              buttons = [('Export Selected', 'listSelected'),
                                         ('Export All', 'listAll')])
    cmds.setParent( '..' ) # row layout  

    cmds.setParent( '..' )
    # footer image Copyright
    cmds.image( image='%MAYA_APP_DIR%/prefs/icons/mkToolsFooter.bmp', annotation='At least give me credit!' )
    cmds.setParent( '..' )# main frame
    updateTextList(scrollListName = animListName, mode='RefreshAll')
    
    
    # MODEL TAB
    modelMainFrame = cmds.frameLayout( label='Model Options', 
        marginHeight=10, marginWidth=2, 
        borderStyle='in',
        collapsable=True )#bgc = darkBlue
    makeTextList(scrollListName=modelListName, 
                 description="Save selected models/groups here to make exporting them easier")
    # Create makeTextList buttons, pass makeTextList name, then list of tuples with button info
    makeListButtons(scrollListName = modelListName,
                    bColor = lightBlue,
                    buttons = [('Add To List', 'Add', 'Add a reference to an object, to export later or to make selecting easier'), 
                              ('Delete from List', 'Delete', 'Deletes a saved object reference from list, not the entire scene')])
    cmds.setParent( '..' )
    # create browse directory elements
    cmds.frameLayout( label='Export Options', marginHeight=5, marginWidth=5, borderStyle='in' )
    cmds.textFieldButtonGrp( 'setModelDir', label='Directory to export to:    ',
        text=scenePath, 
        buttonLabel='Browse', 
        buttonCommand=lambda *args: getExportDir(modelListName),
        changeCommand=lambda *args: updateTextFields(modelListName, mode='EditFilePath', field='setModelDir'))
    cmds.separator(style='in')
    cmds.rowLayout( numberOfColumns=2, adjustableColumn=1 )#, bgc=[1.0,0.0,0.0]
    # create export options buttons
    makeDropDown(modelListName)
    makeExportButtons(scrollListName = modelListName,
                      buttons=[('Export Selected', 'listSelected'),
                               ('Export All', 'listAll'),
                               ('Export By Name', 'listByName')])
    cmds.setParent( '..' ) # row layout  
    cmds.setParent( '..' )# Export options frame
    # footer image Copyright
    cmds.image( image='%MAYA_APP_DIR%/prefs/icons/mkToolsFooter.bmp', annotation='At least give me credit!' )
    cmds.setParent( '..' )# main frame
    updateTextList(scrollListName='modelList', mode='RefreshAll')


    # Textures Tab
    texMainFrame = cmds.frameLayout( label='Texture Options', 
        height=300, width=500, 
        marginHeight=10, marginWidth=2, 
        borderStyle='in')
    makeTextList(scrollListName=textureListName, description="Set working textures")
    # Create makeTextList buttons, pass makeTextList name, then list of tuples with button info
    makeListButtons(scrollListName=textureListName,
                    buttons=[('Add To List', 'Add', 'Add a reference to an object, to export later or to make selecting easier'), 
                             ('Refresh', 'Refresh', 'Refresh selected textures and update view'),
                             ('Delete from List', 'Delete', 'Deletes a saved object reference from list, not the entire scene')])
    cmds.setParent( '..' )

    cmds.textFieldButtonGrp( 'textureDir', label='Texture Location',
        text=scenePath, 
        buttonLabel='Copy to Clipboard', 
        buttonCommand=lambda *args: copyToClipboard())
    cmds.image( image='%MAYA_APP_DIR%/prefs/icons/mkToolsFooter.bmp', annotation='At least give me credit!' )
    cmds.setParent( '..' )# main frame
    updateTextList(scrollListName=textureListName, mode='RefreshAll')


    # MISC TOOLS TAB
    child3 = cmds.rowColumnLayout( numberOfColumns=1 )
    # Split edges function I made years ago
    def splitEdges( SUBDIVS ):
        object = cmds.ls(sl=True, fl=True)
        name = []
        component = [] # Edges, verts, faces...
        for i in object:
            name.append(i.split('.')[0])
            component.append(i.split('.')[1])
        vertsInObj = cmds.polyEvaluate(v=True) # Get's number of verts in object
        print(vertsInObj)
        # Divides edges and querries number of divisions, querried result is a float apparently, which doesn't make sense to me
        
        subEdge = cmds.polySubdivideEdge(n='Subdivide Edges (evenly)', dv = SUBDIVS, ch=True)
        divisions = cmds.polySubdivideEdge(subEdge, query=True, dv=True)
        vert1 = vertsInObj 
        vert2 = vert1 + int(divisions)
        # Connects the verticies
        for i in range(divisions * (len(component) - 1)): # Calculates how many times to loop in order to connect all verts. This number = number of new edges created
            cmds.polyConnectComponents( name[0]+'.vtx['+str(vert1)+']', name[0]+'.vtx['+str(vert2)+']', n='Subdivide Edges (evenly)', name="spgay" , ch=True, cch=False )
            print(vert1)
            print(vert2)
            vert1 += 1
            vert2 += 1
    
    cmds.frameLayout( label='Split Edges (evenly)', marginHeight=5, marginWidth=5, borderStyle='in' )
    subDivSlider = cmds.intSliderGrp( label = 'Number of Divisions', field=True, minValue=1, value=1, changeCommand=lambda *args:ChangeSubDivs())
    subDivs = cmds.intSliderGrp(subDivSlider, query=True, value=True)
    cmds.button( label='Split Edges', command=lambda *args:splitEdges(subDivs) )
    cmds.setParent( '..' )
    # footer image Copyright
    cmds.image( image='%MAYA_APP_DIR%/prefs/icons/mkToolsFooter.bmp', annotation='At least give me credit!' )
    cmds.setParent( '..' )
    
    cmds.tabLayout( tabs, edit=True, tabLabel=((animMainFrame,'Animations'), (modelMainFrame,'Models'), (texMainFrame,'Textures'), (child3,'Other')) )

    cmds.showWindow( 'mk_toolsWindow' )


def exportInit(scrollListName, exportMode=''):
    '''This function is needed... for a reason I can't rememeber! But I made a thread about it on CGSociety'''
    print(exportMode)
    # Get selected objects
    selectedObjects = cmds.textScrollList(scrollListName, query=True, selectItem=True)
    # Pass selected objects to get their attr data, and thus their current export directories
    objectNames, attrNames, attrData = getAttribute(scrollListName, objects=selectedObjects)
    # export objects
    exportStuff(scrollListName, objects=objectNames, objectAttributes=attrData)


def exportStuff(scrollListName, objects=None, objectAttributes=None): 
    """Handles actual export of data"""
    mel.eval("FBXExportSmoothingGroups -v true")
    mel.eval("FBXExportHardEdges -v false")
    mel.eval("FBXExportTangents -v false")
    mel.eval("FBXExportSmoothMesh -v true")
    mel.eval("FBXExportInstances -v false")
    mel.eval("FBXExportReferencedContainersContent -v false")
    # mm.eval("FBXExportBakeResampleAll -v true")
    mel.eval("FBXExportUseSceneName -v false")
    mel.eval("FBXExportQuaternion -v euler")
    mel.eval("FBXExportShapes -v true")
    mel.eval("FBXExportSkins -v true")
    # Constraints
    mel.eval("FBXExportConstraints -v false")
    # Cameras
    mel.eval("FBXExportCameras -v false")
    # Lights
    mel.eval("FBXExportLights -v false")
    # Embed Media
    mel.eval("FBXExportEmbeddedTextures -v false")
    # Connections
    mel.eval("FBXExportInputConnections -v false")
    # Axis Conversion
    mel.eval("FBXExportUpAxis y")
    
    # Get the current file type selection
    fileType = cmds.optionMenuGrp(scrollListName+'TypeSelect', query=True, value=True)

    if scrollListName == 'modelList':
        # Exports all selected objects
        for index, obj in enumerate(objects):
            cmds.select(obj)
            # Apprently maya doesn't just let you use the file command to export FBX. Oh well. 
            if fileType == 'FBX':
                print("Exporting as" , fileType)
                mel.eval('FBXExport -f "' + objectAttributes[index][0] + '/' + obj + '.' + fileType + '" -s')
            else:
                print("Exporting as, not FBX", fileType)
                cmds.file(rename=obj)
                cmds.file(force=True, exportSelected=True, type=fileType)
                cmds.file(rename=sceneName)
                
    if scrollListName == 'animList':
        # get checkbox booealn status
        forUnity = cmds.checkBox( 'unityNames', query=True, value=True )
        for object in objects:
            # take stored string and get integers back
            rangeMin = eval(attrData[object])[0]
            rangeMax = eval(attrData[object])[1]
            mel.eval("FBXExportBakeComplexAnimation -v true")
            mel.eval("FBXExportBakeComplexStart -v "+str(rangeMin) ) 
            mel.eval("FBXExportBakeComplexEnd -v "+str(rangeMax) ) 
            mel.eval("FBXExportBakeComplexStep -v 1")
            if forUnity:
                # add @ in anim names for Unity to recognize it
                mel.eval('FBXExport -f "'+ animDir + '/' + sceneName + '@' + object + '.fbx"-s')
            else:
                # else just add an underscore
                mel.eval('FBXExport -f "'+ animDir + '/' + sceneName + '_' + object + '.fbx"-s')


mkToolsUI()
