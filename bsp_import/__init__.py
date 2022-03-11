import bpy

from bpy_extras.io_utils import ImportHelper

from bpy.props import StringProperty

from bpy.types import Operator

from .bsp import *

bl_info = {
    'name': 'Binary Space Partitioning (.bsp)',
    'author': 'gode',
    'version': (0, 0, 1),
    'blender': (2, 80, 0),
    "category": "Import-Export",
    'location': 'File > Import-Export',
    'description': 'Import .bsp files in Blender'
}
    
class import_bsp(Operator, ImportHelper):
    bl_idname = 'import_bsp.scene'
    bl_description = 'Import .bsp File'
    bl_label = 'Binary Space Partitioning (.bsp)'

    filename_ext = '.bsp'

    filter_glob: StringProperty(
        default='*.bsp',
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        print('Loading .bsp file {file_path}..')
        return parse_bsp(self.filepath)

def menu_bsp_import(self, context):
    self.layout.operator(import_bsp.bl_idname, text=import_bsp.bl_label)


def register():
    bpy.utils.register_class(import_bsp)
    bpy.types.TOPBAR_MT_file_import.append(menu_bsp_import)


def unregister():
    bpy.utils.unregister_class(import_bsp)
    bpy.types.TOPBAR_MT_file_import.remove(menu_bsp_import)

if __name__ == '__main__':
    register()
    bpy.ops.import_test.some_data('INVOKE_DEFAULT')
