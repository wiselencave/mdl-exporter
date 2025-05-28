from typing import List, Dict

import bpy
from bpy.app.handlers import persistent

from ..properties.War3SequenceProperties import War3SequenceProperties

IGNORED_MARKERS = ["MRF", "MRF_START"] # upper case
IGNORED_MARK = "(not exported)"


def set_current_sequence(prop: 'War3SequencesProperties', context: bpy.types.Context):
    sequences = prop.mdl_sequences
    index = prop.mdl_sequence_index

    if 0 <= index < len(sequences):
        context.scene.frame_start = sequences[index].start
        context.scene.frame_end = sequences[index].end


class War3SequencesProperties(bpy.types.PropertyGroup):
    mdl_sequences: bpy.props.CollectionProperty(
        type=War3SequenceProperties,
        options={'HIDDEN'})
    mdl_sequence_index: bpy.props.IntProperty(
        name="Sequence index",
        description="",
        default=0,
        update=set_current_sequence,
        options={'HIDDEN'})

    @classmethod
    def register(cls):
        print("Register \"War3SequencesProperties\"")
        bpy.types.Scene.war3_mdl_sequences = bpy.props.PointerProperty(
            type=War3SequencesProperties,
            options={'HIDDEN'})
        print("Register \"mdl_sequence_refreshing\"")
        bpy.types.WindowManager.mdl_sequence_refreshing = bpy.props.BoolProperty(
            name="sequence refreshing",
            description="",
            default=False,
            options={'HIDDEN'})

        if sequence_changed_handler not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(sequence_changed_handler)

    @classmethod
    def unregister(cls):
        if sequence_changed_handler in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(sequence_changed_handler)

        del bpy.types.WindowManager.mdl_sequence_refreshing
        del bpy.types.Scene.war3_mdl_sequences


@persistent
def sequence_changed_handler(self):
    # print("sequence_changed_handler\n\n")
    context = bpy.context
    # Prevent recursion
    if context.window_manager.mdl_sequence_refreshing:
        return

    context.window_manager.mdl_sequence_refreshing = True

    war3_mdl_sequences = context.scene.war3_mdl_sequences
    sequences = war3_mdl_sequences.mdl_sequences

    markers: Dict[str, List[int]] = {}
    for tlm in context.scene.timeline_markers:
        marker_instances = markers.get(tlm.name, [])
        marker_instances.append(tlm.frame)
        markers[tlm.name] = marker_instances

    for marker, frames in markers.items():
        if len(frames) == 2 and marker not in sequences:
            s = sequences.add()
            s.seq_name = marker
            s.name = marker
            if any(tag in s.seq_name.lower() for tag in ['attack', 'death', 'decay']):
                s.non_looping = True

    for sequence in sequences.values():
        if sequence.seq_name not in markers or len(markers[sequence.seq_name]) != 2:
            index = sequences.find(sequence.seq_name)
            if index <= war3_mdl_sequences.mdl_sequence_index:
                war3_mdl_sequences.mdl_sequence_index = max(index - 1, 0)
            sequences.remove(index)

    context.window_manager.mdl_sequence_refreshing = False
