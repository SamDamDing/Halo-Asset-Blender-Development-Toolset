# ##### BEGIN MIT LICENSE BLOCK #####
#
# MIT License
#
# Copyright (c) 2022 Steven Garcia
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# ##### END MIT LICENSE BLOCK #####

from .format import JMAAsset
from ..global_functions import mesh_processing, global_functions

def process_scene(context, version, generate_checksum, game_version, extension, custom_scale, biped_controller, fix_rotations):
    JMA = JMAAsset()

    collections = []
    layer_collections = list(context.view_layer.layer_collection.children)

    while len(layer_collections) > 0:
        collection_batch = layer_collections
        layer_collections = []
        for collection in collection_batch:
            collections.append(collection)
            for collection_child in collection.children:
                layer_collections.append(collection_child)

    object_properties = []
    object_list = list(context.scene.objects)
    node_list = []
    armature = []
    armature_count = 0
    first_frame = context.scene.frame_start
    last_frame = context.scene.frame_end + 1
    total_frame_count = context.scene.frame_end - first_frame + 1
    for obj in object_list:
        object_properties.append([obj.hide_get(), obj.hide_viewport])
        if obj.type == 'ARMATURE' and mesh_processing.set_ignore(collections, obj) == False:
            mesh_processing.unhide_object(collections, obj)
            armature_count += 1
            armature = obj
            mesh_processing.select_object(context, obj)
            node_list = list(obj.data.bones)

    JMA.transform_count = total_frame_count
    JMA.node_count = len(node_list)

    sorted_list = global_functions.sort_list(node_list, armature, game_version, version, False)
    joined_list = sorted_list[0]
    reversed_joined_list = sorted_list[1]

    blend_scene = global_functions.BlendScene(0, armature_count, 0, 0, 0, 0, armature, node_list, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
    global_functions.validate_halo_jma_scene(game_version, version, blend_scene, object_list, extension)

    JMA.node_checksum = 0
    for node in joined_list:
        name = node.name
        find_child_node = global_functions.get_child(node, reversed_joined_list)
        find_sibling_node = global_functions.get_sibling(armature, node, reversed_joined_list)
        first_child_node = -1
        first_sibling_node = -1
        parent_node = -1
        if not find_child_node == None:
            first_child_node = joined_list.index(find_child_node)

        if not find_sibling_node == None:
            first_sibling_node = joined_list.index(find_sibling_node)

        if not node.parent == None:
            parent_node = joined_list.index(node.parent)

        JMA.nodes.append(JMA.Node(name, parent_node, first_child_node, first_sibling_node))

    if generate_checksum:
        JMA.node_checksum = global_functions.node_hierarchy_checksum(JMA.nodes, JMA.nodes[0], JMA.node_checksum)

    for frame in range(first_frame, last_frame):
        transforms_for_frame = []
        for node in joined_list:
            context.scene.frame_set(frame)
            is_bone = False
            if armature:
                is_bone = True

            bone_matrix = global_functions.get_matrix(node, node, True, armature, joined_list, True, version, 'JMA', False, custom_scale, fix_rotations)
            mesh_dimensions = global_functions.get_dimensions(bone_matrix, node, version, is_bone, 'JMA', custom_scale)
            rotation = (mesh_dimensions.quaternion[0], mesh_dimensions.quaternion[1], mesh_dimensions.quaternion[2], mesh_dimensions.quaternion[3])
            translation = (mesh_dimensions.position[0], mesh_dimensions.position[1], mesh_dimensions.position[2])
            scale = (mesh_dimensions.scale[0])

            transforms_for_frame.append(JMA.Transform(translation, rotation, scale))

        JMA.transforms.append(transforms_for_frame)

    if version > 16394 and biped_controller:
        for frame in range(JMA.transform_count):
            context.scene.frame_set(frame)
            armature_matrix = global_functions.get_matrix(armature, armature, True, None, joined_list, False, version, 'JMA', False, custom_scale, fix_rotations)
            mesh_dimensions = global_functions.get_dimensions(armature_matrix, armature, version, False, 'JMA', custom_scale)

            rotation = (mesh_dimensions.quaternion[0], mesh_dimensions.quaternion[1], mesh_dimensions.quaternion[2], mesh_dimensions.quaternion[3])
            translation = (mesh_dimensions.position[0], mesh_dimensions.position[1], mesh_dimensions.position[2])
            scale = (mesh_dimensions.scale[0])

            JMA.biped_controller_transforms.append(JMA.Transform(translation, rotation, scale))

    context.scene.frame_set(1)
    for idx, obj in enumerate(object_list):
        property_value = object_properties[idx]
        obj.hide_set(property_value[0])
        obj.hide_viewport = property_value[1]

    return JMA
