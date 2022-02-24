import bpy, struct
from pathlib import Path

## http://www.mralligator.com/q3/

lump_categories = ['Entities', 'Textures', 'Planes', 'Nodes', 'Leafs', 'Leaffaces', 'Leafbrushes', 'Models', 'Brushes', 'Brushsides', 'Vertexes', 'Meshverts', 'Effects', 'Faces', 'Lightmaps', 'Lightvols', 'Visdata']

lump_data = {}

def parse_rbsp(file_path):
    with open(file_path, 'rb') as file:
        if file.read(4) != b'RBSP' or struct.unpack('I', file.read(4))[0] != 0x1: # SoF2/JK2/JA/EF Version
            raise ValueError('File is not a supported format !')

        file_path_array = file_path.split('/')
        file_name = file_path_array[len(file_path_array)-1]
        file_path = file_path.replace(file_name, '', -1)

        extracted_data = {
            'Textures': {},
            'Vertexes': {
                'Extracted': []
            },
            'Faces': {
                'Extracted': []
            },
            'Meshverts': {
                'Extracted': []
            }
        }
        
        for i in range(len(lump_categories)):
            if lump_categories[i] in extracted_data:
                file.seek(8+(8*i))
                (offset, size) = struct.unpack('II', file.read(8))
                file.seek(offset)
                extracted_data[lump_categories[i]]['Data'] = file.read(size)
        
        mesh = bpy.data.meshes.new(file_name)
        
        object = bpy.data.objects.new(file_name, mesh)
        
        for i in range( int( len(extracted_data['Textures']['Data']) / 72 ) ):
            texture_name = extracted_data['Textures']['Data'][ 72*i : (72*i)+64 ].decode('UTF-8').replace('\x00', '', -1)
            if texture_name[-4:] == "_bsp": ## Sometimes have _bsp suffix which makes texture unfindable
                texture_name = texture_name[:len(texture_name) - 4]
            
            texture_path = False
            valid_formats = ['.tga', '.png', '.jpg', '.jpeg']
            
            for extension in valid_formats:
                if Path(file_path + texture_name + extension).exists():
                    texture_path = file_path + texture_name + extension
            
            material = bpy.data.materials.new(texture_name)
            
            material.use_nodes = True
            
            if texture_path:
                material_bsdf = material.node_tree.nodes['Principled BSDF']
                material_texture = material.node_tree.nodes.new('ShaderNodeTexImage')
                material_texture.image = bpy.data.images.load(texture_path)
                material.node_tree.nodes.active = material_texture
                material.node_tree.links.new(material_bsdf.inputs['Base Color'], material_texture.outputs['Color'])
            else:
                print(f'Texture {file_path + texture_name} not found !')
                material.diffuse_color = (0.5, 0.0, 0.5, 1.0)

            object.data.materials.append(material)

        for i in range( int( len(extracted_data['Vertexes']['Data']) / 80 ) ):
            (position_x, position_y, position_z) = struct.unpack('fff', extracted_data['Vertexes']['Data'][ 80*i : (80*i)+12 ])
            (texcoords_x, texcoords_y) = struct.unpack('ff', extracted_data['Vertexes']['Data'][ (80*i)+12 : (80*i)+20 ]) # Subtract texcoords_y from 1.0
            (color_r, color_g, color_b, color_a) = struct.unpack('BBBB', extracted_data['Vertexes']['Data'][ (80*i)+64 : (80*i)+68 ]) # Divide by 255 the values
            extracted_data['Vertexes']['Extracted'].append( [ (position_x, position_y, position_z), (texcoords_x, 1.0-texcoords_y), (color_r/255, color_g/255, color_b/255, color_a/255) ] )

        for i in range( int( len(extracted_data['Meshverts']['Data']) / 4 ) ):
            extracted_data['Meshverts']['Extracted'].append( struct.unpack('I', extracted_data['Meshverts']['Data'][ 4*i : (4*i)+4 ])[0] )

        draw_geometry = {
            "Vertexes": [],
            "Faces": [],
            "Faces_Material": [],
            "Vertexes_Color": [],
            "UVs": []
        }
        
        for i in range( int( len(extracted_data['Faces']['Data']) / 148 ) ):
            (texture, effect, type, vertex, n_vertexes, index, n_indexes) = struct.unpack('IIIIIII', extracted_data['Faces']['Data'][ 148*i : (148*i)+28 ])
            # (patch_width, patch_height) = struct.unpack('II', extracted_data['Faces']['Data'][ (148*i)+140 : (148*i)+148 ])
            if type == 3 or type == 1:
                for j in range(n_indexes):
                    if j%3 == 0:
                        vertexes_count = len(draw_geometry["Vertexes"])
                        
                        draw_geometry["Faces"].append( (vertexes_count+0, vertexes_count+1, vertexes_count+2) )
                    
                        vert_0 = vertex + extracted_data['Meshverts']['Extracted'][index + j + 0]
                        draw_geometry["Vertexes"].append( extracted_data['Vertexes']['Extracted'][vert_0][0] )
                        
                        vert_1 = vertex + extracted_data['Meshverts']['Extracted'][index + j + 1]
                        draw_geometry["Vertexes"].append( extracted_data['Vertexes']['Extracted'][vert_1][0] )
                        
                        vert_2 = vertex + extracted_data['Meshverts']['Extracted'][index + j + 2]
                        draw_geometry["Vertexes"].append( extracted_data['Vertexes']['Extracted'][vert_2][0] )
                        
                        draw_geometry["Faces_Material"].append(texture)
                        
                        draw_geometry["UVs"] += [ extracted_data['Vertexes']['Extracted'][vert_0][1][0], extracted_data['Vertexes']['Extracted'][vert_0][1][1], extracted_data['Vertexes']['Extracted'][vert_1][1][0], extracted_data['Vertexes']['Extracted'][vert_1][1][1], extracted_data['Vertexes']['Extracted'][vert_2][1][0], extracted_data['Vertexes']['Extracted'][vert_2][1][1] ]

                        draw_geometry["Vertexes_Color"].append(extracted_data['Vertexes']['Extracted'][vert_0][2])
                        draw_geometry["Vertexes_Color"].append(extracted_data['Vertexes']['Extracted'][vert_1][2])
                        draw_geometry["Vertexes_Color"].append(extracted_data['Vertexes']['Extracted'][vert_2][2])
                        
            elif type == 2:
                pass # TODO

        mesh.from_pydata(draw_geometry["Vertexes"], [], draw_geometry["Faces"])
        
        for i in range(len(draw_geometry["Faces_Material"])):
            object.data.polygons[i].material_index = draw_geometry["Faces_Material"][i]
        
        mesh.uv_layers.new(do_init=False, name="UVMap")
        
        mesh.uv_layers["UVMap"].data.foreach_set("uv", draw_geometry["UVs"])
        
        vertexes_color = mesh.vertex_colors.new(name = "Color")
        mesh.vertex_colors.active = vertexes_color
        
        for i in range(len(mesh.vertices)):
            vertexes_color.data[i].color = draw_geometry["Vertexes_Color"][i]
        
        bpy.context.collection.objects.link(object)
        return {"FINISHED"}
