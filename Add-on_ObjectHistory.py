# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Object History",
    "author": "TkSakai",
    "version": (0, 1),
    "blender": (2, 79, 0),
    "location": "Property > Object ",
    "description": "Storing history of object",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
    }

import bpy
import datetime,time

#OPERATOR

class OBJECT_OT_ObjectHistorySave(bpy.types.Operator):
    bl_idname = "objecthistory.save"
    bl_label = "Save"
    bl_description = "Save Object History"
    
    @classmethod
    def poll(cls,context):
        return context.object.mode == "OBJECT" and context.object.type in ("MESH","CURVE")
    
    def execute(self,context):
                        
        original_object = context.active_object
        original_object_name = original_object.name
        history = original_object.history
        index = len(history)
        
        timestamp = datetime.datetime.now().strftime("%m-%d-%H-%M-%S-%f")
        
        history_name =  "{}_{}".format(original_object_name,timestamp)
        
        his = history.add()
        his.name = original_object_name
        
        original_object.history_index = len(history)-1
        
        
        
        history_object = original_object.copy()
        history_object.data = original_object.data.copy()

        history_object.is_history = True
        history_object.name = history_name
        history_object.use_fake_user = True

        history_object.history_original = original_object
        
        his.ob = history_object
        his.timestamp = timestamp
        
        context.scene.objects.active = original_object
        
        original_object.select = True
        
        print (original_object.users)
        
        print ("SUCCESS")
        return {"FINISHED"}

class OBJECT_OT_ObjectHistoryDelete(bpy.types.Operator):
    bl_idname = "objecthistory.delete"
    bl_label = "Delete"
    bl_description = "Delete history from list"
    
    @classmethod
    def poll(cls,context):
        return len(context.object.history)
    
    def execute(self,context):
        
        original_object = context.active_object
        history = original_object.history
        index = original_object.history_index
        
        his_name = history[index].name
        his_ob = history[index].ob
        
        history.remove(index)
        
        if len(history) > 0:
            context.object.history_index = index - 1
            if context.object.history_index < 0:
                context.object.history_index = 0
        
        his_ob.is_history = False                    
        his_ob.use_fake_user = False
        his_ob.history.clear()
        
        #also remove history from other history
        for his in history:
            his.ob.history.remove(index)
            
        return {"FINISHED"}


class OBJECT_OT_ObjectHistoryRevert(bpy.types.Operator):
    bl_idname = "objecthistory.revert"
    bl_label = "Revert"
    bl_description = "Revert history object selected in list"
    
    @classmethod
    def poll(cls,context):
        return len(context.object.history) > 0 and context.object.mode == "OBJECT" and context.object.type in ("MESH","CURVE")
    
    def execute(self,context):
                
        
        scene = context.scene
        
        original_object = context.object
        original_loc = original_object.location.copy()
        original_rot_euler = original_object.rotation_euler.copy()
        original_rot_mode = original_object.rotation_mode
        original_rot_quat = original_object.rotation_quaternion.copy()
        original_scale = original_object.scale.copy()
        
        history = original_object.history
        index = original_object.history_index
        
        history_name = history[index].name
        
        history_object = history[index].ob.copy()
        history_object.data=history_object.data.copy()
        
        if original_object.type != history_object.type:
            bpy.ops.object.convert(target=history_object.type)        
                    
        
        excludes = ("name","select","as_pointer","use_fake_user")
        attrs = [attr for attr in dir(original_object) if not attr.startswith(excludes)]
        
        for attr in attrs:
            try:
                setattr(original_object,attr,getattr(history_object,attr))
                    
            except AttributeError:
                pass

        
        if (scene.history_inheritance_loc):
            original_object.location = original_loc
            
        if (scene.history_inheritance_rot):            
            original_object.rotation_mode = original_rot_mode
            original_object.rotation_euler = original_rot_euler
            original_object.rotation_quaternion = original_rot_quat
            
        if (scene.history_inheritance_scale):       
            original_object.scale = original_scale
            
        return {"FINISHED"}

class OBJECT_OT_ObjectHistoryRevertPrevious(bpy.types.Operator):
    bl_idname = "objecthistory.revertprev"
    bl_label = "Revert"
    bl_description = "Revert to previous history"
    
    destination = (("prev","Previous",""),("next","Next",""),("first","First",""),("last","Last",""))
    
    whereTo = bpy.props.EnumProperty(items=destination)
    
    @classmethod
    def poll(cls,context):
        return len(context.object.history) > 0 and context.object.mode == "OBJECT" and context.object.type in ("MESH","CURVE")
   
    def execute(self,context):
        #bpy.ops.objecthistory.revert()
        ob = context.object
        
        if self.whereTo == "prev":
            ob.history_index -= 1
            if (ob.history_index < 0):
                ob.history_index = 0
                self.report({"INFO"},"Already at the first history")
            
        elif self.whereTo == "next":
            ob.history_index += 1
            if (ob.history_index > len(ob.history)-1):                
                ob.history_index = len(ob.history)-1
                self.report({"INFO"},"Already at the last history")
            
        elif self.whereTo == "first":
            context.object.history_index = 0
            self.report({"INFO"},"First Commit")
            
        elif self.whereTo == "last":
            context.object.history_index = len(context.object.history)-1
            self.report({"INFO"},"Last Commit")
            
            
        bpy.ops.objecthistory.revert()

        
                
        return {"FINISHED"}

class OBJECT_OT_ObjectHistoryCleanUp(bpy.types.Operator):
    bl_idname = "objecthistory.clean"
    bl_label = "Clean Up"
    bl_description = "Clean unused histories up from file"
    
    @classmethod
    def poll(cls,context):
        return True
    
    def execute(self,context):
        
        count = 0
        original_objects = list(set([ob.history_original for ob in bpy.data.objects if ob.history_original is not None]))
        removed_original_objects = [ob for ob in original_objects if not ob.users_scene]
        
        #Tracking history objects through histories of removed_original_objects.
        for ob in removed_original_objects:            
            for history in ob.history:
                history.ob.history_original = None
                history.ob.use_fake_user = False
                history.ob.history.clear()
                count += 1
                        
            #In some case(idk exactly when this happens),history_original of original object is itself.                      
            if ob.history_original == ob:
                ob.history_original = None
            
            
            ob.history.clear()
        
        
        
        self.report({"INFO"},"{} unused repositries will be discarded when closing Blender".format(count))
        
        return {"FINISHED"}
   
#GUI

class ObjectHistoryList(bpy.types.UIList):
        
    def draw_item(self,context,layout,data,item,icon,active_data,active_propname,index):
        split = layout.split(0.1)
        split.label(str(index+1))
        split.prop(item,"name",icon = "MESH_CUBE",text="",emboss=False)
        split.label(item.timestamp[0:5],icon = "SORTTIME")
        split.label(item.timestamp[6:14],icon = "TIME")
        
    
class OBJECT_PT_ObjectHistoryPanel(bpy.types.Panel):
    bl_label = "Object History"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    
    @classmethod
    def poll(cls,context):
        return len(context.selected_objects) != 0 and context.object.type in ("MESH","CURVE")
    
    def draw(self,context):
        scene = context.scene
        object = context.active_object
        layout = self.layout
        
        row = layout.row()      
        row.template_list("ObjectHistoryList","historylist",object,"history",object,"history_index",rows=3)        
        
        col = row.column(align=True)

        col.operator("objecthistory.save",text="",icon="ZOOMIN")
        col.operator("objecthistory.delete",text="",icon="ZOOMOUT")
        #col.operator("objecthistory.pull",text="Pull")
        #col.operator("objecthistory.preview",text="Preview")
        col.operator("objecthistory.revert",text="",icon="LOOP_BACK")
        col = col.column(align =False)
        
        row = layout.row(align = True)
        row.label(text="Inheritance :")
        row.prop(scene,"history_inheritance_loc",text = "Location")
        row.prop(scene,"history_inheritance_rot",text = "Rotation")
        row.prop(scene,"history_inheritance_scale",text = "Scale")
        
        layout.operator("objecthistory.clean",text="Clean Up",icon="RADIO")
        
        #col = layout.column()
        #col.prop(scene,"history_safety",text = "Safe")
        #col.operator("objecthistory.cleanup",text="CleanUp")
        
        
class OBJECT_MT_ObjectHistoryMenu(bpy.types.Menu):
    bl_idname = "OBJECT_OT_ObjectHistoryMenu"
    bl_label = "Object History"
    bl_description = "Object History Menu"
    
    @classmethod
    def poll(cls,context):
        return 
    
    def draw(self,context):
        layout = self.layout
        layout.operator("objecthistory.save",text="Save History",icon="ZOOMIN")
        layout.separator()
        layout.operator("objecthistory.revertprev",text="Revert Previous",icon="LOOP_BACK").whereTo = "prev"
        layout.operator("objecthistory.revertprev",text="Revert Next",icon="LOOP_FORWARDS").whereTo = "next"
        layout.separator()
        layout.operator("objecthistory.revertprev",text="Revert First",icon="BACK").whereTo = "first"
        layout.operator("objecthistory.revertprev",text="Revert Last",icon="FORWARD").whereTo = "last"
        
def ObjectHistory_menu_draw(self,context):
    
    if context.object.type not in ("MESH","CURVE"):
        return
    layout = self.layout
    layout.menu("OBJECT_OT_ObjectHistoryMenu")

#PROPERTIES

class ObjectHistory(bpy.types.PropertyGroup):
        
    name = bpy.props.StringProperty(name = "name")
    timestamp = bpy.props.StringProperty(name="timestamp")
    ob = bpy.props.PointerProperty(name="object",type=bpy.types.Object)


#REGISTER

    
clss= [OBJECT_OT_ObjectHistoryCleanUp,OBJECT_OT_ObjectHistoryRevertPrevious,OBJECT_OT_ObjectHistorySave,OBJECT_OT_ObjectHistoryDelete,OBJECT_OT_ObjectHistoryRevert,OBJECT_PT_ObjectHistoryPanel,OBJECT_MT_ObjectHistoryMenu,ObjectHistoryList,ObjectHistory]
    
def register():
    
    for cls in clss:
        bpy.utils.register_class(cls)
    
    bpy.types.VIEW3D_MT_object_specials.prepend(ObjectHistory_menu_draw)
      
    bpy.types.Object.history_index = bpy.props.IntProperty(default=0)
    bpy.types.Object.history = bpy.props.CollectionProperty(type = ObjectHistory)
    bpy.types.Object.is_history = bpy.props.BoolProperty(default=False)
    bpy.types.Object.history_original = bpy.props.PointerProperty(type=bpy.types.Object)

    bpy.types.Scene.history_inheritance_loc = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.history_inheritance_rot = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.history_inheritance_scale = bpy.props.BoolProperty(default=True)
    
def unregister():
    
    for cls in clss:
        bpy.utils.unregister_class(cls)
    
    bpy.types.VIEW3D_MT_object_specials.remove(ObjectHistory_menu_draw)

if __name__=="__main__":
    register()