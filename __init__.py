import bpy

from bpy_extras.io_utils import ImportHelper

from bpy.props import StringProperty

from bpy.types import Operator

from .rbsp import *

bl_info = {
    'name': 'Binary Space Partitioning (.bsp)',
    'author': 'gode',
    'version': (0, 0, 1),
    'blender': (2, 80, 0),
    "category": "Import-Export",
    'location': 'File > Import-Export',
    'description': 'Import .bsp files in Blender'
}

class import_rbsp(Operator, ImportHelper):
    bl_idname = 'import_rbsp.scene'
    bl_description = 'Import Raven\'s .bsp File'
    bl_label = 'RBSP'

    filename_ext = '.bsp'

    filter_glob: StringProperty(
        default='*.bsp',
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        print('Loading .bsp file {file_path}..')
        return parse_rbsp(self.filepath)

class import_menu(bpy.types.Menu):
    bl_label = 'Binary Space Partitioning (.bsp)'

    def draw(self, context):
        self.layout.operator(import_rbsp.bl_idname, text=import_rbsp.bl_label)

def menu_func_import(self, context):
    self.layout.menu('import_menu', text='Binary Space Partitioning (.bsp)')


def register():
    bpy.utils.register_class(import_rbsp)
    bpy.utils.register_class(import_menu)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(import_rbsp)
    bpy.utils.unregister_class(import_menu)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == '__main__':
    register()
    bpy.ops.import_test.some_data('INVOKE_DEFAULT')
