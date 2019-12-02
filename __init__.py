#Shot Manager Addon
#Copyright (C) 2019 Pablo Tochez Anderson, Other Realms
#contact@pablotochez.com
#Licensed under GNU GPL-3.0-or-later
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Shot Manager",
    "author" : "Pablo TA.",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 5, 6),
    "location" : "Properties > Scene",
    "warning" : "",
    "category" : "Render",
    "wiki_url" : "https://otherrealms.site/shot-manager-addon"
}

import bpy,os

from .ui import (SM_PT_shot_manager, SM_UL_List, SM_PT_output,SM_PT_QuickPanel,SM_PT_settings)
from .operators import*

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty
                       )

#----------------------------------------------------------------------------------------


bpy.app.handlers.render_pre.clear()

def render_pre(self):
    updateList(self,bpy.context)

bpy.app.handlers.render_pre.append(render_pre)


def get_from_marker_start(self):
    return get_marker_check(self,'start')

def get_from_marker_end(self):
    return get_marker_check(self,'end')

def get_marker_check(self,start):
    scene = bpy.context.scene
    markers = scene.timeline_markers
    names = markers.keys()
    marker_frame = 0
    #Is shot manager being used?
    if  scene.sm_use == True:
        
        if self.index < 9999 and self.index < len(markers):
            if names.count(self.name) >1:
                markers[self.index].name += ':Duplicate'
                self.name = markers[self.index].name

            #check names
            if self.name != markers[self.index].name:
                marker_frame = fixMarkers(self,start,'NameError')
            else:
                #Match
                self.name = markers[self.index].name
                marker_frame = markers[self.index].frame
                if start == 'start':
                    scene.frame_start = marker_frame
                else:
                    scene.frame_end = marker_frame
            
        else:
            marker_frame = fixMarkers(self,start,'IndexError')


    return marker_frame


def fixMarkers(self,start,err):
    scene = bpy.context.scene
    markers = scene.timeline_markers
    index = scene.sm_list_index
    value = 0
    
    if 'start' in start:
        link = scene.sm_prop_grp[index].start_marker
    else:
        link = scene.sm_prop_grp[index].end_marker
        

    if err == 'IndexError':
        print(err)
        #try name
        i= markers.find(link.name)
        if i > -1:
            link.index= i
            return markers[i].frame

        else:
            print('name not found')
            link.index = 9999
            link.name = 'Marker Not Found' 
            if start == 'start':
                scene.sm_prop_grp[index].start_frameALT = scene.frame_start
            else:
                scene.sm_prop_grp[index].end_frameALT = scene.frame_end
            return 0

    elif err == 'NameError':
        print(err)
        #try name
        i= markers.find(link.name)
        if i > -1:
            link.index= i
            return markers[i].frame

        elif markers[link.index].select== True:
            #Renamed
            print('A Marker was re-named')
            #batch re-name
            for shot in scene.sm_prop_grp:
                if shot.start_marker.name == link.name: 
                    shot.start_marker.name =  markers[link.index].name
                if shot.end_marker.name == link.name:
                    shot.end_marker.name =  markers[link.index].name

            return markers[link.index].frame

        else:
            print('A Marker was deleted')
            link.index = 9999
            link.name = 'Marker Missing' 
            if start == 'start':
                scene.sm_prop_grp[index].start_frameALT = scene.frame_start
            else:
                scene.sm_prop_grp[index].end_frameALT = scene.frame_end
            return 0
            
    else:
        print(err)
        return 0

def poll(self,value):
    
    return bpy.context.scene.sm_use

def scene_mychosenobject_poll(self, object):
    return object.type == 'CAMERA'

    
def enableAll(self,context):
    scene=context.scene

    if scene.sm_enable_all:
        False
    else:
        True
    
    for shot in context.scene.sm_prop_grp:
        if scene.sm_enable_all== False:
            shot.enable = False
        else:
            shot.enable = True



class SM_Start_Marker_grp(bpy.types.PropertyGroup):

    name: StringProperty(
        name="Name",
        description="A name for this item",
        default = 'Marker',
        )

    index: IntProperty(
        name = "Marker Index",
        default = 100
        )

    frame: IntProperty(
        name = "Marker Frame",
        description = "Linked start frame",
        get = get_from_marker_start,
        )


class SM_End_Marker_grp(bpy.types.PropertyGroup):

    name: StringProperty(
        name="Name",
        description="A name for this item",
        default = 'Marker',
        )

    index: IntProperty(
        name = "Marker Index",
        default = 9999
        )

    frame: IntProperty(
        name = "Marker Frame",
        description = "Linked start frame",
        get = get_from_marker_end,
        )

class SM_PropertyGroup(bpy.types.PropertyGroup):
    @classmethod
    def poll(self,context):
        return bpy.context.scene.sm_use


    name: StringProperty(
        name="Name",
        description="A name for this item",
        default = 'New Shot',
        update = updateList
        )
    

    start_frameALT: IntProperty(
        name = "Start Frame",
        description = "Set start frame",
        default = 0,
        min =0,
        update = shotChange
        )

    start_marker: PointerProperty(
        name = "Markers",
        type = SM_Start_Marker_grp,
        
        )
    end_marker: PointerProperty(
        name = "Markers",
        type = SM_End_Marker_grp,
        )

    end_frameALT: IntProperty(
        name = "End Frame",
        description = "Set end frame",
        default = 250,
        min = 0,
        update = shotChange
        )

    custom_camera: PointerProperty(
        name = 'Camera',
        type = bpy.types.Object,
        poll = scene_mychosenobject_poll,
        update = updateList
    
        )

    notes: StringProperty(
        name="Notes",
        description="Notes",
        default = ''
        )


    view_layers: StringProperty(
        name="View Layer",
        description="ViewLayers",
        default = '*True'

        )
    enable: BoolProperty(
        name="Queue",
        description="Queue Shot",
        default = False,
        update = updateList

        )
    main: StringProperty(name ="Primary", default = 'None')

    alpha: BoolProperty(name="Transparency",update= updateList)


classes = (
SM_End_Marker_grp, SM_Start_Marker_grp,SM_UL_List, SM_PropertyGroup, SM_OT_Link,
SM_OT_Qpick, SM_OT_save, SM_OT_mainLayer, SM_OT_saveJSON, SM_OT_openJSON, LIST_OT_sort,LIST_OT_delete,
SM_PT_shot_manager,SM_PT_settings, SM_PT_output, SM_PT_QuickPanel, 

    )



def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.sm_prop_grp = CollectionProperty(type=SM_PropertyGroup)
    bpy.types.Scene.sm_list_index = IntProperty(name = "Index for my_list", default = 0,update = shotChange)
    bpy.types.Scene.sm_layer_settings = BoolProperty(name='Setting',default=False)


    bpy.types.Scene.sm_mainLayer = BoolProperty \
        (
        name= "Use primary layer", 
        description = "Automatically switch to your 'Primary' View Layer when going between shots",
        default = True
        ) 
    bpy.types.Scene.sm_warning = StringProperty \
        (
        name = "Warning",
        description = "Set parent folder for render path",
        default = "Save View Layers"
        )

    bpy.types.Scene.sm_path = StringProperty \
        (
        name = "Root Folder",
        description = "link to marker",
        default = "//Output",
        subtype = "DIR_PATH",
        update = updateList
        )
    bpy.types.Scene.sm_use = BoolProperty \
        (
        name = "Use",
        description = "Set parent folder for render path",
        default =True,
        update = updateList

        )
    bpy.types.Scene.sm_frame = BoolProperty \
        (
        name = "keep in range",
        description = "Set view to frame range when switching shots",
        default =False,
        )

    bpy.types.Scene.sm_enable_all = BoolProperty \
        (
        name = "Queue All",
        description = "Queue all shots for batch output",
        default =False,
        update= enableAll
        )
    bpy.types.Scene.sm_view_layers_default = EnumProperty \
        (
        name = "Unsaved layers default",
        description = "Select a default state for unsaved View Layers",
        default ='None',
        items= {('None','None','None'),('Off','Off','Off'),('On','On','On')}

        )
    
    

    try:
        from .Pro.__init__ import pro_register
        pro_register()
    except ModuleNotFoundError:
        pass


def unregister():
    try:
        from .Pro.__init__ import pro_unregister
        pro_unregister()
    except ModuleNotFoundError:
        pass

    
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.sm_view_layers_default
    del bpy.types.Scene.sm_enable_all
    del bpy.types.Scene.sm_frame
    del bpy.types.Scene.sm_use
    del bpy.types.Scene.sm_path
    del bpy.types.Scene.sm_warning
    del bpy.types.Scene.sm_list_index
    del bpy.types.Scene.sm_mainLayer



