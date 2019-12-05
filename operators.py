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

import bpy,os,json

from .ui import (SM_PT_shot_manager, SM_UL_List, SM_PT_output,SM_PT_QuickPanel,SM_PT_settings)

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

def shotChange(self,context):
    scene = context.scene
    index = scene.sm_list_index

    #set frames
    if len(scene.sm_prop_grp) !=0:
        shot = scene.sm_prop_grp[index]
        
        #only on shot change, not all updates
        if shot.start_marker.index == 9999:
            scene.frame_start = shot.start_frameALT
        else:
            shot.start_marker.frame

        if shot.end_marker.index == 9999:
            scene.frame_end = shot.end_frameALT
        else:
            shot.end_marker.frame

        #scene.frame_current = min(scene.frame_current,scene.frame_end)
        #scene.frame_current = max(scene.frame_current,scene.frame_start)
        scene.frame_current = scene.frame_start

        #frame to playhead
        if scene.sm_frame:
            window = context.window
            for area in window.screen.areas:
                if area.type == 'DOPESHEET_EDITOR':
                    screen = window.screen
                    #spaces= area.spaces[1]
                    region = area.regions[3]
                    override = {'window': window, 'screen': screen,'region':region, 'area': area}
                    bpy.ops.action.view_frame(override)

                    
        #Update View layer to 'Primary
        if shot.main in scene.view_layers.keys():
            context.window.view_layer = scene.view_layers[shot.main]

        updateList(self,context)

def updateList(self,context):
    
    scene = context.scene
    path = scene.sm_path
    
    if scene.sm_use == True and len(scene.sm_prop_grp) !=0 :
        index = scene.sm_list_index
        shot = scene.sm_prop_grp[index]
        name = shot.name.strip()
        render_path = os.path.join(path, name , name + '_')

        if shot.custom_camera != None:
            scene.camera = shot.custom_camera
        scene.render.film_transparent= shot.alpha

        #view layer Defaults 
        if scene.sm_view_layers_default == 'On':
            for layer in scene.view_layers:
                layer.use = True
        elif scene.sm_view_layers_default == 'Off':
            for layer in scene.view_layers:
                layer.use = False

        #Check view Layers
        if shot.view_layers !='*True':
            #set view layers
            layers = shot.view_layers.split('*')
            layers.pop(0)

            for index, v_layer in enumerate(layers):
                v_layer = v_layer.split('^^')
                layers[index] = v_layer

                #safe
                if v_layer[0] in scene.view_layers.keys():
                    scene.sm_warning = "Save View Layers"
                    #sucess
                    if v_layer[1] == 'True':
                        scene.view_layers[v_layer[0]].use = True
                    else:
                        scene.view_layers[v_layer[0]].use = False
                #catch, False doesn't matter
                else:
                    scene.sm_warning = 'Outdated-Update'
                    #print('Saved View Layers Name Mismatch')
                    break
                
        else:
            scene.sm_warning = "Save View Layers"

        #Primary layer
        if shot.main not in scene.view_layers.keys():
            shot.main = 'None'

        #Update file path
        if scene.use_nodes == True and 'Shot List' in scene.node_tree.nodes.keys():


            for node in scene.node_tree.nodes:
                if 'ShotList' in node.bl_idname:
                    #Update Shot List Node----------
                    node.backup_path = render_path
                    node.update()
                    node.separateLayers()

                    break
                else:
                    scene.render.filepath = render_path

                    
        else:
            scene.render.filepath = render_path

def poll(self,value):
    
    return bpy.context.scene.sm_use

def view_layers_enum(self,context):
    main_layers = ('None','none','none')
    main = []
    main.clear()
    main.append(main_layers)

    for name in bpy.context.scene.view_layers.keys():
        main.append((name,name,name))

    return  main
     

class SM_OT_save(bpy.types.Operator):
    bl_idname = "sm.save_layers" 
    bl_label = "Save View Layer states"
    bl_description = "Save View Layer states" 

    clear: BoolProperty()
    context_: IntProperty()

    def execute(self,context):
        scene = context.scene
        #index = scene.sm_list_index
        shot = scene.sm_prop_grp[self.context_]

        L ='' 
        if self.clear == False:
            for v in bpy.context.scene.view_layers:
                L +=  '*'+ v.name +'^^' + str(v.use)
                shot.view_layers = L
                self.report({'INFO'},'View Layer State Saved')
        else:
            shot.view_layers = '*True'
            self.report({'INFO'},'View Layers Cleared')


        
        updateList(self,context)
        return {'FINISHED'}

class SM_OT_mainLayer(bpy.types.Operator):
    bl_idname = "sm.mainlayer" 
    bl_label = "Primary Layer"
    bl_description = "Save a view layer as the primary workspace" 

    V_layers : EnumProperty(items = view_layers_enum)

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self,height= 100,width = 200)

    def execute(self,context):
        scene = context.scene
        index = scene.sm_list_index
        shot = scene.sm_prop_grp[index]

        shot.main = self.V_layers
        #print(self.V_layers)

        return {'FINISHED'}

class LIST_OT_delete(bpy.types.Operator):
    bl_idname = "my_list.delete" 
    bl_label = "Delete shot" 
    bl_description = 'Delete shot'

    index: IntProperty()
    delete_all:BoolProperty(default=False)

    def invoke(self,context,event):
        wm=context.window_manager
        return wm.invoke_confirm(self,event)
    
    def execute(self, context): 
        prop_grp  = context.scene.sm_prop_grp
        index = self.index
        if self.delete_all==True:
            self.delete_all=False
            context.scene.sm_list_index=0
            prop_grp.clear()
        else:
            prop_grp.remove(index)
            context.scene.sm_list_index = max(0,index-1)
            updateList(self,context)

        return {'FINISHED'}
class LIST_OT_sort(bpy.types.Operator):
    bl_idname = "my_list.update" 
    bl_label = "Shot" 
    bl_description = 'Shot'

    index: IntProperty()
    Add: BoolProperty()
    Move: StringProperty()

    def execute(self, context): 
        
        prop_grp  = context.scene.sm_prop_grp
        index = self.index

        if self.Add == True:
            new = prop_grp.add()
            new.start_frameALT = context.scene.frame_start
            new.end_frameALT = context.scene.frame_end
            self.Add = False

        elif self.Move == 'UP':
            neighbor = index -1
            prop_grp.move(neighbor, index) 
            

            self.Move = 'none'

        elif self.Move == 'DOWN':
            neighbor = index+1
            prop_grp.move(neighbor, index) 
            
            self.Move = 'none'

        updateList(self,context)

        return {'FINISHED'}

class SM_OT_Qpick(bpy.types.Operator):
    bl_idname = "sm.quickpick" 
    bl_label = "Quick Select"
    bl_description = "Quick Select shot"

    ind: IntProperty()
    def execute(self,context):
        context.scene.sm_list_index = self.ind

        return{'FINISHED'}

class SM_OT_Link(bpy.types.Operator):
    bl_idname = "sm.link" 
    bl_label = "Link to selected marker" 
    bl_description = "Link to selected marker" 

    StartEnd: IntProperty()

    activeMarker = None

    @classmethod
    def poll(self,context):
        for m in context.scene.timeline_markers:
            if m.select == True:
                self.activeMarker = m
                return m != False
                break
 
    def execute(self, context): 
        scene = context.scene
        index = scene.sm_list_index
        shot = scene.sm_prop_grp[index]
 
        markers = list(scene.timeline_markers)

        #set Start marker
        if self.StartEnd == 1:
            f= markers.index(self.activeMarker)
            shot.start_marker.index = f
            shot.start_marker.name = self.activeMarker.name
            self.StartEnd = 0
            self.report({'INFO'},str('linked ' + str(shot.name)+' to: ' + self.activeMarker.name))

        #clear Start marker
        if self.StartEnd == 3:
            shot.start_marker.index = 9999
            shot.start_marker.name = "UNLINKED"
            #(shot.start_marker.index)
            self.StartEnd = 0
            self.report({'INFO'},'unlinked start marker ')

        #set End marker
        if self.StartEnd == 2:
            f= markers.index(self.activeMarker)
            shot.end_marker.index = f
            shot.end_marker.name = self.activeMarker.name
            self.StartEnd = 0
            self.report({'INFO'},str('linked ' + str(shot.name)+' to: ' + self.activeMarker.name))

        #clear End marker
        if self.StartEnd == 4:
            shot.end_marker.index = 9999
            shot.end_marker.name = "UNLINKED"
            #print(shot.end_marker.index)
            self.StartEnd = 0
            self.report({'INFO'},'unlinked start marker ')
         

        shotChange(self,context)
        return {'FINISHED'}       

class SM_OT_saveJSON(bpy.types.Operator):
    bl_idname = "sm.savejson" 
    bl_label = "Save json"
    bl_description = "Save shots into json" 


    filepath : bpy.props.StringProperty(subtype="DIR_PATH")
    @classmethod
    def poll(self,context):
        return len(context.scene.sm_prop_grp) != 0

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        scene = context.scene
        index = scene.sm_list_index
        shot = scene.sm_prop_grp[index]
        from .__init__ import bl_info

        filepath = os.path.splitext(self.filepath)[0]
        json_file = open(bpy.path.abspath(filepath)+'.json',"w+")

        version = bl_info['version']
 
        dictionary = {'version': version}

        for index,shot in enumerate(scene.sm_prop_grp):
            
            items = {}

            for prop in shot.keys():
                if prop == 'start_marker' or prop =='end_marker':
                    items_list = shot[prop].items()
                    try:
                        i = scene.sm_prop_grp[index].start_marker.frame
                        items_list.append(('frame',i))
                    except:
                        pass
                    try:
                        i = scene.sm_prop_grp[index].end_marker.frame
                        items_list.append(('frame',i))
                    except:
                        pass

                    items[prop] = dict(items_list)

                elif prop == 'custom_camera':
                    if shot[prop] != None:
                        items[prop] = shot[prop].name
                    else:
                        items[prop] = 'None'

                else:
                    items[prop] = shot[prop]

            dictionary[str(index)] = items

        save = json.dumps(dictionary, indent=4)
        json_file.write(save)
        json_file.close()

        self.report({'INFO'},'wrote .json at '+ bpy.path.abspath(self.filepath))

        #print(items)
        #print(dictionary)

        return {'FINISHED'}
        

class SM_OT_openJSON(bpy.types.Operator):
    bl_idname = "sm.openjson" 
    bl_label = "Open json"
    bl_description = "Load shots from json" 


    filepath : bpy.props.StringProperty(subtype="DIR_PATH")
    ignore: bpy.props.BoolProperty(name="Ignore existing shots",default = True)


    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    #def draw(self,context):

    def execute(self, context):
        scene = context.scene
        op = False
        

        try:
            with open(self.filepath, 'r') as json_file:
                json_parsed = json.load(json_file)
                op = True

        except:
            self.report({'ERROR'},'Not a valid JSON file')
            return {'FINISHED'}
        
        if op == True:
            try: 
                version = json_parsed['version']
                #print('version:',json_parsed['version'])

            except:
                self.report({'ERROR'},'Not a valid JSON file')
                return {'FINISHED'}

            for index in json_parsed:
                #Add shots
                if index != 'version':
                    props = json_parsed.get(index)
                    if self.ignore == True and props.get('name') in scene.sm_prop_grp.keys():
                        pass
                    else:
                        custom_camera = props.get('custom_camera','None')
                        end_frameALT = props.get('end_frameALT',250)
                        start_frameALT = props.get('start_frameALT',0)
                        view_layers = props.get('view_layers',"*True")
                        enable = props.get('enable', False)
                        main = props.get('main','None')
                        name = props.get('name','New Shot')
                        notes = props.get('notes','')
                        alpha= props.get('alpha',False)
                        
                        start_marker_name = props.get('start_marker',"").get('name',"")
                        start_marker_index = props.get('start_marker',"").get('index',9999)
                        start_marker_frame = props.get('start_marker',"").get('frame',0)
                    
                        end_marker_name = props.get('end_marker',"").get('name',"")
                        end_marker_index = props.get('end_marker',"").get('index',9999)
                        end_marker_frame = props.get('end_marker',"").get('frame',0)
                        

                        #print(json_parsed[index])
                        new = scene.sm_prop_grp.add()
                        new.name = name

                        if custom_camera in scene.objects.keys():
                            new.custom_camera = scene.objects[custom_camera] 
                        
                        if start_marker_index != 9999:
                            new.start_frameALT = start_marker_frame
                        else:
                            new.start_frameALT = start_frameALT

                        if end_marker_index != 9999:
                            new.start_frameALT = end_marker_frame
                        else:
                            new.end_frameALT = end_frameALT

                        new.view_layers = view_layers
                        if enable == 1:
                            new.enable = True
                        new.main = main
                        new.notes = notes
                        new.alpha = alpha

                        new.start_marker.name = start_marker_name
                        new.start_marker.index = start_marker_index
                        new.end_marker.name = end_marker_name
                        new.end_marker.index = end_marker_index


                
            self.report({'INFO'},'Loaded Shots sucessfully')

            

        return {'FINISHED'}



