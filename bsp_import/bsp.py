import bpy, struct
from pathlib import Path
from .wad import *

class rbsp_categories:
    TEXTURES = 1
    TEXTURES_FORMATS = ['.tga', '.png', '.jpg', '.jpeg']
    VERTEXES = 10
    MESHVERTS = 11
    FACES = 13
    def get():
        return (rbsp_categories.TEXTURES, rbsp_categories.VERTEXES, rbsp_categories.MESHVERTS, rbsp_categories.FACES)

class ibsp_categories:
    TEXTURES = 2
    ENTITIES = 0
    VERTEXES = 3
    TEXINFO = 6
    EDGES = 12
    SURFEDGES = 13
    FACES = 7
    def get():
        return (ibsp_categories.TEXTURES, ibsp_categories.ENTITIES, ibsp_categories.VERTEXES, ibsp_categories.TEXINFO, ibsp_categories.EDGES, ibsp_categories.SURFEDGES, ibsp_categories.FACES)

def parse_bsp(file_path):
    with open(file_path, 'rb') as file:
        file_magic = file.read(4)
        file_path_array = file_path.split('/')
        file_name = file_path_array[len(file_path_array)-1]
        file_path = file_path.replace(file_name, '', -1)

        if file_magic == b'RBSP' and struct.unpack('I', file.read(4))[0] == 0x1: # SoF2/JK2/JA/EF Version

            mesh = bpy.data.meshes.new(file_name)
            
            object = bpy.data.objects.new(file_name, mesh)

            extracted_data = {
                'Vertexes': [],
                'Meshverts': [],
            }
            
            draw_geometry = {
                "Vertexes": [],
                "Faces": [],
                "Faces_Material": [],
                "Vertexes_Color": [],
                "UVs": []
            }

            for index in rbsp_categories.get():
                file.seek(8+(8*index))
                (offset, size) = struct.unpack('II', file.read(8))
                file.seek(offset)
                
                if index == rbsp_categories.TEXTURES:
                    while file.tell() < offset+size:
                        texture_name = file.read(64).decode('UTF-8').replace('\x00', '', -1)
                        file.seek(file.tell()+8)
                        if texture_name[-4:] == "_bsp": ## Sometimes have _bsp suffix which makes texture unfindable
                            texture_name = texture_name[:len(texture_name) - 4]
                        texture_path = False
                        for extension in rbsp_categories.TEXTURES_FORMATS:
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
                        
                if index == rbsp_categories.VERTEXES:
                    while file.tell() < offset+size:
                        (position_x, position_y, position_z) = struct.unpack('fff', file.read(12))
                        (texcoords_x, texcoords_y) = struct.unpack('ff', file.read(8)) # Subtract texcoords_y from 1.0
                        file.seek(file.tell()+44)
                        (color_r, color_g, color_b, color_a) = struct.unpack('BBBB', file.read(4)) # Divide by 255 the values
                        extracted_data['Vertexes'].append( [ (position_x, position_y, position_z), (texcoords_x, 1.0-texcoords_y), (color_r/255, color_g/255, color_b/255, color_a/255) ] )
                        file.seek(file.tell()+12)

                if index == rbsp_categories.MESHVERTS:
                    while file.tell() < offset+size:
                        extracted_data['Meshverts'].append( struct.unpack('I', file.read(4))[0] )

                if index == rbsp_categories.FACES:
                    while file.tell() < offset+size:
                        (texture, effect, type, vertex, n_vertexes, index, n_indexes) = struct.unpack('IIIIIII', file.read(28))
                        
                        file.seek(file.tell()+120)
                        if type == 3 or type == 1:
                            for j in range(n_indexes):
                                if j%3 == 0:
                                    vertexes_count = len(draw_geometry["Vertexes"])
                                    
                                    draw_geometry["Faces"].append( (vertexes_count+0, vertexes_count+1, vertexes_count+2) )
                                
                                    vert_0 = vertex + extracted_data['Meshverts'][index + j + 0]
                                    draw_geometry["Vertexes"].append( extracted_data['Vertexes'][vert_0][0] )
                                    
                                    vert_1 = vertex + extracted_data['Meshverts'][index + j + 1]
                                    draw_geometry["Vertexes"].append( extracted_data['Vertexes'][vert_1][0] )
                                    
                                    vert_2 = vertex + extracted_data['Meshverts'][index + j + 2]
                                    draw_geometry["Vertexes"].append( extracted_data['Vertexes'][vert_2][0] )
                                    
                                    draw_geometry["Faces_Material"].append(texture)
                                    
                                    draw_geometry["UVs"] += [ extracted_data['Vertexes'][vert_0][1][0], extracted_data['Vertexes'][vert_0][1][1], extracted_data['Vertexes'][vert_1][1][0], extracted_data['Vertexes'][vert_1][1][1], extracted_data['Vertexes'][vert_2][1][0], extracted_data['Vertexes'][vert_2][1][1] ]

                                    draw_geometry["Vertexes_Color"].append(extracted_data['Vertexes'][vert_0][2])
                                    draw_geometry["Vertexes_Color"].append(extracted_data['Vertexes'][vert_1][2])
                                    draw_geometry["Vertexes_Color"].append(extracted_data['Vertexes'][vert_2][2])
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
            
            mesh.flip_normals()
            
            bpy.context.collection.objects.link(object)

        elif struct.unpack('i', file_magic)[0] == 0x1e:

            mesh = bpy.data.meshes.new(file_name)
            
            object = bpy.data.objects.new(file_name, mesh)

            extracted_data = {
                'Textures': {},
                'Vertices': {},
                'Faces': {},
                'Edges': {},
                'Surfedges': {},
                'Texinfo': {},
            }

            draw_geometry = {
                "Vertexes": [],
                "Edges": [],
                "Faces": [],
                "Surfedges": [],
                "Texinfo": [],
                "Faces_Material": [],
                "UVs": [],
            }
            
            textures_sizes = []
            
            wad_textures = {}

            for index in ibsp_categories.get():
                file.seek(4+(8*index))
                (offset, size) = struct.unpack('ii', file.read(8))
                file.seek(offset)

                if index == ibsp_categories.TEXTURES:

                    textures_lump_start = file.tell()

                    (textures_count,) = struct.unpack('I', file.read(4))

                    for i in range(textures_count):
                        
                        (offset,) = struct.unpack('i', file.read(4) )
                        
                        offset_start = file.tell()
                        
                        file.seek(textures_lump_start + offset)
                        
                        texture_name = file.read(16)

                        texture_length = texture_name.find(b'\x00')
                        texture_name = texture_name[0:texture_length].decode('UTF-8')
                        (width, height) = struct.unpack('II', file.read(8))
                        (miptexture_offset1, miptexture_offset2, miptexture_offset4, miptexture_offset8) = struct.unpack('IIII', file.read(16))

                        texture_image = bpy.data.images.new(texture_name, width, height)
                        
                        textures_sizes.append([width, height])
                        
                        material = bpy.data.materials.new(texture_name)
                        
                        if miptexture_offset1 != 0:
                            
                            texture_image_pixels = []

                            miptexture_finish = int(offset + (miptexture_offset8 + ((width/8) * (height/8))))

                            file.seek(textures_lump_start + miptexture_finish)

                            palette_size = struct.unpack('H', file.read(2))[0]
                            
                            palette = []

                            for j in range( palette_size*3 ):
                                miptexture_data  = file.read(3)
                                if len(miptexture_data) > 2:
                                    palette.append( struct.unpack('BBB', miptexture_data) )

                            file.seek(textures_lump_start + offset + miptexture_offset1)

                            for j in range( width*height ):
                                (color,) = struct.unpack('B', file.read(1))
                                
                                texture_image_pixels.append(palette[color][0]/255)
                                texture_image_pixels.append(palette[color][1]/255)
                                texture_image_pixels.append(palette[color][2]/255)
                                
                                if palette[color][2] == 255 and palette[color][0] + palette[color][1] == 0:
                                    texture_image_pixels.append(0.0)
                                else:
                                    texture_image_pixels.append(1.0)
                                
                            texture_image.pixels = texture_image_pixels
                        else:
                            wad_textures[texture_name.lower()] = texture_image

                        material.use_nodes = True
                        material_bsdf = material.node_tree.nodes['Principled BSDF']
                        material_texture = material.node_tree.nodes.new('ShaderNodeTexImage')
                        material_texture.image = texture_image
                        material.node_tree.nodes.active = material_texture
                        material.node_tree.links.new(material_bsdf.inputs['Base Color'], material_texture.outputs['Color'])
                        object.data.materials.append(material)

                        file.seek(offset_start)
                        
                if index == ibsp_categories.ENTITIES:
                    entities_dump = file.read(size)
                    start_wadlist_entry = entities_dump.find(b'wad')
                    end_wadlist_entry = entities_dump.find(b'\n', start_wadlist_entry)
                    wadlist_entry = entities_dump[start_wadlist_entry+6:end_wadlist_entry-1].decode('UTF-8').split(";")
                    wadlist_entry.pop()
                    current_entry = 0
                    for wad_path in wadlist_entry:
                        wad_name = wad_path[wad_path.rfind('\\', 0, len(wad_path))+1:len(wad_path)]
                        wadlist_entry[current_entry] = wad_name
                        current_entry += 1
                    retrieve_textures_from_wad_files(file_path, wadlist_entry, wad_textures)
                    
                if index == ibsp_categories.TEXINFO:
                    while file.tell() < offset+size:
                        (s_coord_x, s_coord_y, s_coord_z, s_shift, t_coord_x, t_coord_y, t_coord_z, t_shift, tex_index) = struct.unpack('ffffffffI', file.read(36))
                        draw_geometry["Texinfo"].append( (s_coord_x, s_coord_y, s_coord_z, s_shift, t_coord_x, t_coord_y, t_coord_z, t_shift, tex_index, textures_sizes[tex_index]) )
                        file.seek(file.tell()+4)
                    
                if index == ibsp_categories.VERTEXES:
                    while file.tell() < offset+size:
                        (x, y, z) = struct.unpack('fff', file.read(12))
                        draw_geometry['Vertexes'].append( (x, y, z) )

                if index == ibsp_categories.EDGES:
                    while file.tell() < offset+size:
                        (a, b) = struct.unpack('HH', file.read(4))
                        draw_geometry['Edges'].append( (a, b) )
        
                if index == ibsp_categories.SURFEDGES:
                    while file.tell() < offset+size:
                        (edge_index,) = struct.unpack('i', file.read(4))
                        draw_geometry['Surfedges'].append(edge_index)

                if index == ibsp_categories.FACES:
                    while file.tell() < offset+size:
                        (plane, planeside, first_surfedge, surfedges_count, texinfo_id) = struct.unpack('hhihH', file.read(12))
                        add_face = []
                        add_uv = []
                        for j in range(surfedges_count):
                            if draw_geometry["Surfedges"][first_surfedge+j] > 0:
                                select_edge = draw_geometry["Edges"][draw_geometry["Surfedges"][first_surfedge+j]]
                                add_face.append(select_edge[0])
                                
                                u_axis = (draw_geometry["Texinfo"][texinfo_id][0], draw_geometry["Texinfo"][texinfo_id][1], draw_geometry["Texinfo"][texinfo_id][2])
                                u_offset = draw_geometry["Texinfo"][texinfo_id][3]
                                v_axis = (draw_geometry["Texinfo"][texinfo_id][4], draw_geometry["Texinfo"][texinfo_id][5], draw_geometry["Texinfo"][texinfo_id][6])
                                v_offset = draw_geometry["Texinfo"][texinfo_id][7]
                                uv_size = draw_geometry["Texinfo"][texinfo_id][9]
                                u = (draw_geometry["Vertexes"][select_edge[0]][0] * u_axis[0] + draw_geometry["Vertexes"][select_edge[0]][1] * u_axis[1] + draw_geometry["Vertexes"][select_edge[0]][2] * u_axis[2]) + u_offset
                                v = (draw_geometry["Vertexes"][select_edge[0]][0] * v_axis[0] + draw_geometry["Vertexes"][select_edge[0]][1] * v_axis[1] + draw_geometry["Vertexes"][select_edge[0]][2] * v_axis[2]) + v_offset
                                add_uv.append(u/uv_size[0])
                                add_uv.append(v/uv_size[1])
                            else:
                                select_edge = draw_geometry["Edges"][draw_geometry["Surfedges"][first_surfedge+j]*-1]
                                add_face.append(select_edge[1])
                                
                                u_axis = (draw_geometry["Texinfo"][texinfo_id][0], draw_geometry["Texinfo"][texinfo_id][1], draw_geometry["Texinfo"][texinfo_id][2])
                                u_offset = draw_geometry["Texinfo"][texinfo_id][3]
                                v_axis = (draw_geometry["Texinfo"][texinfo_id][4], draw_geometry["Texinfo"][texinfo_id][5], draw_geometry["Texinfo"][texinfo_id][6])
                                v_offset = draw_geometry["Texinfo"][texinfo_id][7]
                                uv_size = draw_geometry["Texinfo"][texinfo_id][9]
                                u = (draw_geometry["Vertexes"][select_edge[1]][0] * u_axis[0] + draw_geometry["Vertexes"][select_edge[1]][1] * u_axis[1] + draw_geometry["Vertexes"][select_edge[1]][2] * u_axis[2]) + u_offset
                                v = (draw_geometry["Vertexes"][select_edge[1]][0] * v_axis[0] + draw_geometry["Vertexes"][select_edge[1]][1] * v_axis[1] + draw_geometry["Vertexes"][select_edge[1]][2] * v_axis[2]) + v_offset
                                add_uv.append(u/uv_size[0])
                                add_uv.append(v/uv_size[1])

                        draw_geometry["UVs"] += add_uv
                        draw_geometry["Faces"].append(tuple(add_face))
                        draw_geometry["Faces_Material"].append(draw_geometry["Texinfo"][texinfo_id][8])

                        file.seek(file.tell()+8)

            mesh.from_pydata(draw_geometry["Vertexes"], [], draw_geometry["Faces"])
            
            for i in range(len(draw_geometry["Faces_Material"])):
                object.data.polygons[i].material_index = draw_geometry["Faces_Material"][i]
            
            mesh.uv_layers.new(do_init=False, name="UVMap")
            mesh.uv_layers["UVMap"].data.foreach_set("uv", draw_geometry["UVs"])
            
            mesh.flip_normals()

            bpy.context.collection.objects.link(object)

        else:
            raise ValueError('File is not a supported format !')
        return {"FINISHED"}
