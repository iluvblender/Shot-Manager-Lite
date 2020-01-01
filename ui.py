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

import bpy
from bpy.types import Panel



class SM_PT_shot_manager(Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Shot Manager"
    bl_idname = "SCENE_PT_shotmanager"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
   
    def draw_header(self, context):
        self.layout.prop(context.scene, "sm_use",text="")

    def draw(self, context):

        scene = context.scene
        chapters = scene.timeline_markers.items()
        layout = self.layout
        layout.active = scene.sm_use
        
        row = layout.row(align=True)
        row.operator('my_list.update', text='',icon = 'ADD').Add = True
        row.label( text = 'Add New')
        #row.prop(scene,'sm_enable_all')

        row = layout.row()
        row.template_list("SM_UL_List", "chapter_list", scene,"sm_prop_grp",scene, "sm_list_index")

        #Shot Details
        col = layout.column(align=False)
        row = layout.column(align=False)
        split = layout.split(factor = 0.5)


        if len(scene.sm_prop_grp) > 0:
            index = scene.sm_list_index
            shot = scene.sm_prop_grp[index]
            link_text_start = shot.start_marker.name
            link_text_end = shot.end_marker.name
            #Start Frame

            #col = split.column(align=False)
            col = split.column(align=False)
            if shot.start_marker.index == 9999:
                col.operator('sm.link', text=link_text_start,icon = 'UNLINKED').StartEnd = 1
                col.prop(shot, "start_frameALT",text= 'Start')
            else:
                try:
                    sf = str(scene.timeline_markers[link_text_start].frame)  
                except KeyError:
                    sf = '0'
                col.operator('sm.link', text= link_text_start,icon = 'LINK_BLEND').StartEnd = 3
                col.label(text ='Start: '+ sf)

            
            #End Frame
            col = split.column(align=False)
            if shot.end_marker.index == 9999:
                col.operator('sm.link', text=link_text_end,icon = 'UNLINKED').StartEnd = 2
                col.prop(shot, "end_frameALT",text= 'End')
            else:
                try:
                    sf = str(scene.timeline_markers[link_text_end].frame)
                except KeyError:
                    sf = '0' 
                col.operator('sm.link', text= link_text_end,icon = 'LINK_BLEND').StartEnd = 4
                col.label(text ='End: '+ sf)
                

            row = layout.row()
            duration = scene.frame_end - scene.frame_start
            duration_formatted = 'Duration: ' +str(duration) +' frames,  '+ format(duration / scene.render.fps, '.2f')+' seconds'
            row.label(text = duration_formatted,icon = 'MOD_TIME')

            row = layout.row()
            row.prop(shot, "name")
            row = layout.row()
            row.prop(shot, "custom_camera")
            row = layout.row()
            row.prop(shot, "notes")
            row = layout.row()
            row.label(text = 'Primary Layer:')
            row.operator('sm.mainlayer',text = shot.main)
            row = layout.row()
            row.label(text = 'Transparent Background:')
            row.prop(shot, "alpha",text='',)
            row = layout.row()
            row.label(text = 'View Layers:')
            if shot.view_layers == '*True':
                row.label(text = 'None saved')
            else:
                s = row.operator('sm.save_layers', text = 'Clear', icon = 'UGLYPACKAGE')
                s.clear=True ; s.context_ = index
            if scene.sm_warning =='Outdated-Update':
                row.alert = True
                s = row.operator('sm.save_layers', text = scene.sm_warning, icon = 'ERROR')
                s.clear=False ; s.context_ = index
                row.alert = False
            else:
                s = row.operator('sm.save_layers', text = 'Save', icon = 'PACKAGE')
                s.clear=False ; s.context_ = index


            

            
class SM_PT_settings(Panel):
    bl_label = "Settings"
    bl_parent_id = "SCENE_PT_shotmanager"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False 
        col = layout.column(align=True)
        col.prop(scene,"sm_mainLayer", text = 'Switch to Primary')
        col.prop(scene, "sm_frame")
        col.prop(scene,'sm_view_layers_default')
        col = layout.split(factor = 0.5)
        col.separator(factor=1.0)
        col.operator('my_list.delete', text='Delete all shots',icon = 'TRASH').delete_all=True
        col = layout.split(factor = 0.5)
        col.operator('sm.savejson', text= 'Export shots to .json')
        col.operator('sm.openjson', text= 'Import shots from .json')

class SM_PT_Footer(Panel):
    bl_label = "Data"
    bl_parent_id = "SCENE_PT_shotmanager"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout= self.layout
        col = layout.column()
        
        col = col.split()
        col.label(text='Shots to Json')
        col.operator('sm.savejson', text= 'Export')
        col.operator('sm.openjson', text= 'Import')
        col = layout.column()
        col = layout.split(factor= 0.9)
        #col.separator(factor=1.0)
        col.label(text='Remove all shots')
        col.operator('my_list.delete',text='',icon = 'TRASH').delete_all=True

class SM_PT_output(Panel):
    bl_label = "Output Summary"
    bl_parent_id = "SCENE_PT_shotmanager"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    
    #bl_options = {'HIDE_HEADER'}


    def draw(self, context):

        scene = context.scene
        layout = self.layout
        #layout.use_property_decorate = False  # No animation.
        
        
        window = context.window
        
        layout.template_ID(window, "scene")

        row = layout.row(align=False)
        row.prop(scene, "sm_path")
        row = layout.row()
        row.label(text="RENDER PATH:  " + scene.render.filepath)

        #View Layers
        layout.label(text="View Layers:")
        
        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align= True)
        layers = bpy.context.scene.view_layers.items()


        for a,b in layers:

            using = b.use
            row = flow.row(align=True)
            
            if using == True:
                row.prop(b, "use", text=a,icon='RESTRICT_RENDER_OFF')
            else:
                row.prop(b, "use", text=a,icon='RESTRICT_RENDER_ON')


            row.separator()
        #Output
        eevee = scene.eevee
        cycles = scene.cycles

        row = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align= True)
        row.scale_x=0.75
        row.label(text='Transparency: '+ str(scene.render.film_transparent))
        row.label(text='Render Engine: '+ scene.render.engine)
        row.label(text='Cycles Device: '+ scene.cycles.device)
        row.label(text='Format: '+ scene.render.file_extension)
        row = layout.row(align=True)
        row=row.split(factor=0.7)
        row.label(text='Eevee Render Samples:')
        row.prop(eevee, "taa_render_samples",text='')
        row = layout.row(align=True)
        row=row.split(factor=0.7)
        row.label(text='Cycles Render Samples:')
        row.prop(cycles, "samples",text='')
        



class SM_PT_QuickPanel(Panel):
    """Creates a Panel in the Timeline"""
    bl_label = "Keep in range"
    bl_idname = "SCENE_PT_SMQuickPanel"
    bl_space_type =  'DOPESHEET_EDITOR'
    bl_region_type = 'UI'

    
    #bl_options = {'HIDE_HEADER'}
    def draw_header(self,context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(scene, "sm_frame",text='')


    def draw(self, context):

        scene = context.scene
        layout = self.layout
        shots = scene.sm_prop_grp
        
        #layout.prop(scene, "sm_frame")
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align= True) 
        flow.scale_x = 0.6
        for index, shot in enumerate(shots):
            if index == scene.sm_list_index:
                flow.operator('sm.quickpick', text= shot.name, depress=True).ind = index

            else:

                flow.operator('sm.quickpick', text= shot.name).ind = index


#draw UI LIST
class SM_UL_List(bpy.types.UIList):
    

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        fps = scene.render.fps
        markers = scene.timeline_markers.items()
        layout = layout.row(align = True)
        #layout.use_property_split=True
        #layout.use_property_decorate = False
        layout.scale_x = 0.8
        #layout.prop(item, 'enable',text= '', toggle = -1)

        if index > 0:
            i = layout.operator('my_list.update', text='',icon = "TRIA_UP")
            i.index = index
            i.Move = 'UP'
        
        if index < len(scene.sm_prop_grp)-1:
            i = layout.operator('my_list.update', text='',icon = "TRIA_DOWN")
            i.index = index
            i.Move = 'DOWN'
            
        else:
            layout.separator(factor=2)

        if index == 0:
            layout.separator(factor=2)

        layout.scale_x = 1

        layout.label(text=item.name)
        
        
        if item.custom_camera != None:
            layout.label(text = item.custom_camera.name, icon ="OUTLINER_OB_CAMERA")
        else:
            layout.label(text = '', icon ="OUTLINER_DATA_CAMERA")

        layout.operator('my_list.delete', text='',icon = 'REMOVE').index = index





