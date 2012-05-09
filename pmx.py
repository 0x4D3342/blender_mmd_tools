# -*- coding: utf-8 -*-
import struct

class InvalidFileError(Exception):
    pass
class UnsupportedVersionError(Exception):
    pass

class Encoding:
    _MAP = [
        (0, 'utf-16-le'),
        (1, 'utf-8'),
        ]

    def __init__(self, arg):
        self.index = 0
        self.charset = ''
        t = None
        print(arg)
        if isinstance(arg, str):
            t = list(filter(lambda x: x[1]==arg, self._MAP))
            if len(t) == 0:
                raise ValueError('invalid charset %s'%arg)
        elif isinstance(arg, int):
            t = list(filter(lambda x: x[0]==arg, self._MAP))
            if len(t) == 0:
                raise ValueError('invalid index %d'%arg)
        else:
            raise ValueError('invalid argument type')
        t = t[0]
        self.index = t[0]
        self.charset  = t[1]

    def __repr__(self):
        return '<Encoding charset %s>'%self.charset

class Coordinate:
    """ """
    def __init__(self, xAxis, zAxis):
        self.x_axis = xAxis
        self.z_axis = zAxis

class Header:
    def __init__(self):
        self.sign = ''
        self.version = 0

        self.encoding = None
        self.additional_uvs = 0

        self.vertex_index_size = 1
        self.material_index_size = 1
        self.bone_index_size = 1
        self.morph_index_size = 1
        self.rigid_index_size = 1

    def load(self, fin):
        self.sign = str(fin.read(4), 'ascii')
        if self.sign != 'PMX ':
            raise InvalidFileError
        self.version, = struct.unpack('<f', fin.read(4))
        if self.version != 2.0:
            raise UnsupportedVersionError('unsupported version: %f'%self.version)
        num, = struct.unpack('<B', fin.read(1))
        if num != 8:
            raise InvalidFileError
        self.encoding = Encoding(struct.unpack('<B', fin.read(1))[0])
        self.additional_uvs, = struct.unpack('<B', fin.read(1))
        self.vertex_index_size, = struct.unpack('<B', fin.read(1))
        self.texture_index_size, = struct.unpack('<B', fin.read(1))
        self.material_index_size, = struct.unpack('<B', fin.read(1))
        self.bone_index_size, = struct.unpack('<B', fin.read(1))
        self.morph_index_size, = struct.unpack('<B', fin.read(1))
        self.rigid_index_size, = struct.unpack('<B', fin.read(1))

    def __repr__(self):
        return '<Header encoding %s, uvs %d, vtx %d, tex %d, mat %d, bone %d, morph %d, rigid %d>'%(
            str(self.encoding),
            self.additional_uvs,
            self.vertex_index_size,
            self.texture_index_size,
            self.material_index_size,
            self.bone_index_size,
            self.morph_index_size,
            self.rigid_index_size,
            )

    def readStr(self, fin):
        length, = struct.unpack('<i', fin.read(4))
        format = '<%ds'%length
        buf, = struct.unpack(format, fin.read(length))
        return str(buf, self.encoding.charset)

    def readIndex(self, fin, size):
        index = None
        if size == 1:
            index, = struct.unpack('<b', fin.read(size))
        elif size == 2:
            index, = struct.unpack('<h', fin.read(size))
        elif size == 4:
            index, = struct.unpack('<i', fin.read(size))
        else:
            raise ValueError('invalid data size %s'%str(size))
        return index

    def readVertexIndex(self, fin):
        return self.readIndex(fin, self.vertex_index_size)

    def readBoneIndex(self, fin):
        return self.readIndex(fin, self.bone_index_size)

    def readTextureIndex(self, fin):
        return self.readIndex(fin, self.texture_index_size)

class Model:
    def __init__(self):
        self.header = None

        self.name = ''
        self.name_e = ''
        self.comment = ''
        self.comment_e = ''

        self.vertices = []
        self.faces = []
        self.textures = []
        self.materials = []
        self.bones = []
        self.morphs = []

        self.display = []

        self.rigids = []
        self.joints = []

    def load(self, header, fin):
        self.name = header.readStr(fin)
        self.name_e = header.readStr(fin)

        self.comment = header.readStr(fin)
        self.comment_e = header.readStr(fin)

        num_vertices, = struct.unpack('<i', fin.read(4))
        self.vertices = []
        for i in range(num_vertices):
            v = Vertex()
            v.load(header, fin)
            self.vertices.append(v)

        num_faces, = struct.unpack('<i', fin.read(4))
        self.faces = []
        for i in range(int(num_faces/3)):
            f1 = header.readVertexIndex(fin)
            f2 = header.readVertexIndex(fin)
            f3 = header.readVertexIndex(fin)
            self.faces.append((f1, f2, f3))

        num_textures, = struct.unpack('<i', fin.read(4))
        self.textures = []
        for i in range(num_textures):
            t = Texture()
            t.load(header, fin)
            self.textures.append(t)

        num_materials, = struct.unpack('<i', fin.read(4))
        self.materials = []
        for i in range(num_materials):
            m = Material()
            m.load(header, fin)
            self.materials.append(m)

        num_bones, = struct.unpack('<i', fin.read(4))
        self.bones = []
        for i in range(num_bones):
            b = Bone()
            b.load(header, fin)
            print(b)
            self.bones.append(b)

    def __repr__(self):
        return '<Model name %s, name_e %s, comment %s, comment_e %s, textures %s>'%(
            self.name,
            self.name_e,
            self.comment,
            self.comment_e,
            str(self.textures),
            )

class Vertex:
    def __init__(self):
        self.co = [0.0, 0.0, 0.0]
        self.normal = [0.0, 0.0, 0.0]
        self.uv = [0.0, 0.0]
        self.additional_uvs = []
        self.weight = None
        self.edge_scale = 1

    def __repr__(self):
        return '<Vertex co %s, normal %s, uv %s, additional_uvs %s, weight %s, edge_scale %s>'%(
            str(self.co),
            str(self.normal),
            str(self.uv),
            str(self.additional_uvs),
            str(self.weight),
            str(self.edge_scale),
            )

    def load(self, header, fin):
        self.co = list(struct.unpack('<fff', fin.read(4*3)))
        self.normal = list(struct.unpack('<fff', fin.read(4*3)))
        self.uv = list(struct.unpack('<ff', fin.read(4*2)))
        self.additional_uvs = []
        for i in range(header.additional_uvs):
            self.additional_uvs.append(list(struct.unpack('<ffff', fin.read(4*4))))
        self.weight = BoneWeight()
        self.weight.load(header, fin)
        self.edge_scale, = struct.unpack('<f', fin.read(4))

class BoneWeightSDEF:
    def __init__(self, weight=0, c=None, r0=None, r1=None):
        self.weight = weight
        self.c = c
        self.r0 = r0
        self.r1 = r1

class BoneWeight:
    BDEF1 = 0
    BDEF2 = 1
    BDEF4 = 2
    SDEF  = 3

    TYPES = [
        (BDEF1, 'BDEF1'),
        (BDEF2, 'BDEF2'),
        (BDEF4, 'BDEF4'),
        (SDEF, 'SDEF'),
        ]

    def __init__(self):
        self.bones = []
        self.weights = []

    def convertIdToName(self, type_id):
        t = list(filter(lambda x: x[0]==type_id, TYPES))
        if len(t) > 0:
            return t[0][1]
        else:
            return None

    def convertNameToId(self, type_name):
        t = list(filter(lambda x: x[1]==type_name, TYPES))
        if len(t) > 0:
            return t[0][0]
        else:
            return None

    def load(self, header, fin):
        self.type, = struct.unpack('<b', fin.read(1))
        self.bones = []
        self.weights = []
        if self.type == self.BDEF1:
            self.bones.append(header.readVertexIndex(fin))
        elif self.type == self.BDEF2:
            self.bones.append(header.readVertexIndex(fin))
            self.bones.append(header.readVertexIndex(fin))
            self.weights.append(struct.unpack('<f', fin.read(4))[0])
        elif self.type == self.BDEF4:
            self.bones.append(header.readVertexIndex(fin))
            self.bones.append(header.readVertexIndex(fin))
            self.bones.append(header.readVertexIndex(fin))
            self.bones.append(header.readVertexIndex(fin))
            self.weights.append(list(struct.unpack('<ffff', fin.read(4*4))))
        elif self.type == self.SDEF:
            self.bones.append(header.readVertexIndex(fin))
            self.bones.append(header.readVertexIndex(fin))
            self.weights = BoneWeightSDEF()
            self.weights.weight, = struct.unpack('<f', fin.read(4))
            self.weights.c = list(struct.unpack('<fff', fin.read(4*3)))
            self.weights.r0 = list(struct.unpack('<fff', fin.read(4*3)))
            self.weights.r1 = list(struct.unpack('<fff', fin.read(4*3)))
        else:
            raise ValueError('invalid weight type %s'%str(self.type))

class Texture:
    def __init__(self):
        self.path = ''

    def __repr__(self):
        return '<Texture path %s>'%str(self.path)

    def load(self, header, fin):
        self.path = header.readStr(fin)

class SharedTexture(Texture):
    def __init__(self):
        self.number = 0
        self.prefix = ''

class Material:
    SPHERE_MODE_OFF = 0
    SPHERE_MODE_MULT = 1
    SPHERE_MODE_ADD = 2
    SPHERE_MODE_SUB = 3

    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.diffuse = []
        self.specular = []
        self.ambient = []

        self.is_doulbe_sided = False
        self.enabled_drop_shadow = False
        self.enabled_self_shadow_map = False
        self.enabled_self_shadow = False
        self.enabled_toon_edge = False

        self.edge_color = []
        self.edge_size = 1

        self.texture = None
        self.sphere_texture = None
        self.sphere_texture_mode = 0
        self.is_shared_toon_texture = True
        self.toon_texture = None

        self.comment = ''
        self.vertex_count = 0

    def __repr__(self):
        return '<Material name %s, name_e %s, diffuse %s, specular %s, ambient %s, double_side %s, drop_shadow %s, self_shadow_map %s, self_shadow %s, toon_edge %s, edge_color %s, edge_size %s, toon_texture %s, comment %s>'%(
            self.name,
            self.name_e,
            str(self.diffuse),
            str(self.specular),
            str(self.ambient),
            str(self.is_doulbe_sided),
            str(self.enabled_drop_shadow),
            str(self.enabled_self_shadow_map),
            str(self.enabled_self_shadow),
            str(self.enabled_toon_edge),
            str(self.edge_color),
            str(self.edge_size),
            str(self.texture),
            str(self.sphere_texture),
            str(self.toon_texture),
            str(self.comment),)

    def load(self, header, fin):
        self.name = header.readStr(fin)
        print(self.name)
        self.name_e = header.readStr(fin)

        self.diffuse = list(struct.unpack('<ffff', fin.read(4*4)))
        self.specular = list(struct.unpack('<ffff', fin.read(4*4)))
        self.ambient = list(struct.unpack('<fff', fin.read(4*3)))

        flags, = struct.unpack('<b', fin.read(1))
        self.is_doulbe_sided = flags & 1
        self.enabled_drop_shadow = flags & 2
        self.enabled_self_shadow_map = flags & 4
        self.enabled_self_shadow = flags & 8
        self.enabled_toon_edge = flags & 16

        self.edge_color = list(struct.unpack('<ffff', fin.read(4*4)))
        self.edge_size, = struct.unpack('<f', fin.read(4))

        self.texture = header.readTextureIndex(fin)
        self.sphere_texture = header.readTextureIndex(fin)
        self.sphere_texture_mode, = struct.unpack('<b', fin.read(1))

        self.is_shared_toon_texture, = struct.unpack('<b', fin.read(1))
        self.is_shared_toon_texture = (self.is_shared_toon_texture == 1)
        self.toon_texture = header.readTextureIndex(fin)

        self.comment = header.readStr(fin)
        self.vertex_count, = struct.unpack('<i', fin.read(4))

class Bone:
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.location = []
        self.parent = None
        self.depth = 0

        # 接続先表示方法
        # 座標オフセット(float3)または、boneIndex(int)
        self.displayConnection = None

        self.isRotatable = True
        self.isMovable = True
        self.visible = True
        self.isControllable = True

        self.ik = False

        # 回転付与
        # (Boneオブジェクト, 付与率float)のタプル
        self.externalRotate = None

        # 移動付与
        # (Boneオブジェクト, 付与率float)のタプル
        self.externalTrans = None

        # 軸固定
        # 軸ベクトルfloat3
        self.axis = None

        # ローカル軸
        self.localCoordinate = None

        self.transAfterPhis = False

        # 外部親変形
        self.externalTransKey = None

        # 以下IKボーンのみ有効な変数
        self.target = None
        self.loopCount = 0
        # IKループ計三時の1回あたりの制限角度(ラジアン)
        self.rotationConstraint = 0

        # IKLinkオブジェクトの配列
        self.ik_links = []

    def __repr__(self):
        return '<Bone name %s, name_e %s>'%(
            self.name,
            self.name_e,)

    def load(self, header, fin):
        self.name = header.readStr(fin)
        self.name_e = header.readStr(fin)

        self.location = list(struct.unpack('<fff', fin.read(4*3)))
        self.parent = header.readBoneIndex(fin)
        self.depth, = struct.unpack('<i', fin.read(4))

        flags, = struct.unpack('<h', fin.read(2))
        if flags & 0x0001:
            self.displayConnection = header.readBoneIndex(fin)
        else:
            self.displayConnection = list(struct.unpack('<fff', fin.read(4*3)))

        self.isRotatable    = ((flags & 0x0002) != 0)
        self.isMovable      = ((flags & 0x0004) != 0)
        self.visible        = ((flags & 0x0008) != 0)
        self.isControllable = ((flags & 0x0010) != 0)

        self.ik             = ((flags & 0x0020) != 0)

        if flags & 0x0100:
            t = header.readBoneIndex(fin)
            v, = struct.unpack('<f', fin.read(4))
            self.externalRotate = (t, v)
        else:
            self.externalRotate = None

        if flags & 0x0200:
            t = header.readBoneIndex(fin)
            v, = struct.unpack('<f', fin.read(4))
            self.externalTrans = (t, v)
        else:
            self.externalTrans = None

        if flags & 0x0400:
            self.axis = list(struct.unpack('<fff', fin.read(4*3)))
        else:
            self.axis = None

        if flags & 0x0800:
            xaxis = list(struct.unpack('<fff', fin.read(4*3)))
            zaxis = list(struct.unpack('<fff', fin.read(4*3)))
            self.localCoordinate = Coordinate(xaxis, zaxis)
        else:
            self.localCoordinate = None

        self.transAfterPhis = ((flags & 0x1000) != 0)

        if flags & 0x2000:
            self.externalTransKey, = struct.unpack('<f', fin.read(4))
        else:
            self.externalTransKey = None

        if self.ik:
            self.target = header.readBoneIndex(fin)
            self.loopCount, = struct.unpack('<i', fin.read(4))
            self.rotationConstraint, = struct.unpack('<f', fin.read(4))

            iklink_num, = struct.unpack('<i', fin.read(4))
            self.ik_links = []
            for i in range(iklink_num):
                link = IKLink()
                link.load(header, fin)
                self.ik_links.append(link)

class IKLink:
    def __init__(self):
        self.target = None
        self.maximunAngle = None
        self.minimumAngle = None

    def __repr__(self):
        return '<IKLink target %s>'%(str(self.target))

    def load(self, header, fin):
        self.target = header.readBoneIndex(fin)
        flag, = struct.unpack('<b', fin.read(1))
        if flag == 1:
            self.minimumAngle = list(struct.unpack('<fff', fin.read(4*3)))
            self.maximunAngle = list(struct.unpack('<fff', fin.read(4*3)))
        else:
            self.minimumAngle = None
            self.maximunAngle = None

class Morph:
    """ """
    CATEGORY_SYSTEM = 0
    CATEGORY_EYEBROW = 1
    CATEGORY_EYE = 2
    CATEGORY_MOUTH = 3
    CATEGORY_OHTER = 4

    def __init__(self):
        self.name = ''
        self.name_e = ''

class VertexMorphData:
    def __init_(self):
        self.vertex = None
        self.offset = []

class UVMorphData:
    def __init__(self):
        self.vertex = None
        self.offset = []

class BoneMorphData:
    def __init__(self):
        self.bone = None
        self.location_offset = []
        self.rotation_offset = []

class MaterialMorphData:
    TYPE_MULT = 0
    TYPE_ADD = 1
    
    def __init__(self):
        self.material = None
        self.offset_type = TYPE_MULT
        self.diffuse_offset = []
        self.specular_offset = []
        self.ambient_offset = []
        self.edge_color_offset = []
        self.edge_size_offset = []
        self.texture_factor = []
        self.sphere_texture_factor = []
        self.toon_texture_factor = []

class GroupMorphData:
    def __init__(self):
        self.morph = None
        self.factor = 0.0

class VertexMorph(Morph):
    def __init__(self):
        Morph.__init__(self)

        self.data = []

class UVMorph(Morph):
    def __init__(self):
        Morph.__init__(self)

        self.data = []

class BoneMorph(Morph):
    def __init__(self):
        Morph.__init__(self)

        self.data = []

class MaterialMorph(Morph):
    def __init__(self):
        Morph.__init__(self)

        self.data = []

class GroupMorph(Morph):
    def __init__(self):
        Morph.__init__(self)

        self.data = []


class Display:
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.isSpecial = False

        self.data = []

class Rigid:
    TYPE_SPHERE = 0
    TYPE_BOX = 1
    TYPE_CAPSULE = 2

    MODE_STATIC = 0
    MODE_DYNAMIC = 1
    MODE_DYNAMIC_BONE = 2
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.bone = None
        self.collision_group_number = 0
        self.non_collision_group_number = 0

        self.type = TYPE_SPHERE
        self.size = []

        self.location = []
        self.rotation = []

        self.mass = 1
        self.velocity_attenuation = []
        self.rotation_attenuation = []
        self.bounce = []
        self.friction = []

        self.mode = MODE_STATIC

class Joint:
    MODE_SPRING6DOF = 0
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.mode = MODE_SPRING6DOF

        self.src_rigid = None
        self.dest_rigid = None

        self.location = []
        self.rotation = []

        self.maximum_location = []
        self.minimum_location = []
        self.maximum_rotation = []
        self.minimum_rotation = []

        self.spring_constant = []
        self.spring_rotaion_constant = []

class File:
    def __init__(self):
        self.header = Header()
        self.model = Model()

    def load(self, path):
        with open(path, 'rb') as fin:
            self.header.load(fin)
            print(self.header)
            self.model.load(self.header, fin)
            print(self.model)

if __name__ == '__main__':
    f = File()
    f.load('/Users/yoshinobu/dev/blender-scripts/import_pmx/初音ミクVer2MP2.pmx')
