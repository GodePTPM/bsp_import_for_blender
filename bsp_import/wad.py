import bpy, struct
from pathlib import Path

def retrieve_textures_from_wad_files(path, files, textures):
    for file_name in files:
        file_path = Path(path + file_name)
        if file_path.is_file():
            with open(file_path, 'rb') as file:
                file_magic = file.read(4)
                if file_magic == b'WAD2' or file_magic == b'WAD3':
                    (textures_count,offset) = struct.unpack('II', file.read(8))

                    previous_position = offset
                    
                    for index in range(textures_count):
                        file.seek(previous_position)
                        (offset, disk_size, size, type, compression, dummy) = struct.unpack('iiib?h', file.read(16))

                        texture_name = file.read(16)
                        texture_length = texture_name.find(b'\x00')
                        texture_name = texture_name[0:texture_length].decode('UTF-8')
                        
                        previous_position = file.tell()
                        
                        if texture_name.lower() in textures:
                            file.seek(offset+16) # skip texture name
                            (width, height) = struct.unpack('II', file.read(8))
                            (miptexture_offset1, miptexture_offset2, miptexture_offset4, miptexture_offset8) = struct.unpack('IIII', file.read(16))
                            
                            if miptexture_offset1 != 0:
                                texture_image_pixels = []

                                miptexture_finish = int(offset + (miptexture_offset8 + ((width/8) * (height/8))))

                                file.seek(miptexture_finish)

                                palette_size = struct.unpack('H', file.read(2))[0]
                                
                                palette = []

                                for j in range( palette_size*3 ):
                                    miptexture_data  = file.read(3)
                                    if len(miptexture_data) > 2:
                                        palette.append( struct.unpack('BBB', miptexture_data) )

                                file.seek(offset + miptexture_offset1)

                                for j in range( width*height ):
                                    (color,) = struct.unpack('B', file.read(1))
                                    
                                    texture_image_pixels.append(palette[color][0]/255)
                                    texture_image_pixels.append(palette[color][1]/255)
                                    texture_image_pixels.append(palette[color][2]/255)
                                    
                                    if palette[color][2] == 255 and palette[color][0] + palette[color][1] == 0:
                                        texture_image_pixels.append(0.0)
                                    else:
                                        texture_image_pixels.append(1.0)
                                    
                                textures[texture_name.lower()].pixels = texture_image_pixels
        else:
            pass # file not found
