from .logging_util import log_info, log_warn, log_error
import substance_painter.js as js
import json
import os
import tempfile
from .tree_item import TreeItem
from enum import Enum
from PySide2.QtWidgets import QProgressDialog
from PySide2.QtCore import Qt

from pytoshop.core import PsdFile
from pytoshop.layers import LayerRecord, LayerMask, LayerAndMaskInfo, LayerInfo, ChannelImageData
import pytoshop.enums as enums
from pytoshop.enums import ColorMode, BlendMode
from pytoshop.tagged_block import TaggedBlock, SectionDividerSetting, UnicodeLayerName
from PIL import Image
import numpy as np

class ExportResult(Enum):
    SUCCEED = 1
    CANCELED = 2

def export_channel(exportPath, tmpdir, docStruct, material_index, channel, exportConfig, parent=None):
    material = docStruct["materials"][material_index]
    materialName = material["name"]
    stackName = material["stacks"][0]["name"]
    stackPath = f'["{materialName}", "{stackName}"]'
    channelFormat = js.evaluate(f'alg.mapexport.channelFormat({stackPath}, "{channel}");')
    # override bitDepth
    if int(exportConfig["bitDepth"]) == -1:
        bitDepth = channelFormat["bitDepth"]
    else:
        bitDepth = int(exportConfig["bitDepth"])
    colorModeMap = {
        "sRGB8": ColorMode.rgb,
        "L8": ColorMode.grayscale,
        "RGB8": ColorMode.rgb,
        "L16": ColorMode.grayscale,
        "RGB16": ColorMode.rgb,
        "L16F": ColorMode.grayscale,
        "RGB16F": ColorMode.rgb,
        "L32F": ColorMode.grayscale,
        "RGB32F": ColorMode.rgb,
        }
    colorMode = colorModeMap.get(channelFormat["label"], ColorMode.rgb)
    size = exportConfig["resolution"][0]
    def convert_blending_mode(painterMode, isGroup):
        if painterMode == "Passthrough":
            if isGroup:
                blendMode = BlendMode.pass_through
            else:
                blendMode = BlendMode.normal
            return blendMode
        blendMode = {
            "Normal": BlendMode.normal,
            "Replace": BlendMode.normal,
            "Multiply": BlendMode.multiply,
            "Divide": BlendMode.divide,
            "Linear dodge (Add)": BlendMode.linear_dodge,
            "Subtract": BlendMode.subtract,
            "Difference": BlendMode.difference,
            "Exclusion": BlendMode.exclusion,
            "Overlay": BlendMode.overlay,
            "Screen": BlendMode.screen,
            "Linear burn": BlendMode.linear_burn,
            "Color burn": BlendMode.color_burn,
            "Color dodge": BlendMode.color_dodge,
            "Soft light": BlendMode.soft_light,
            "Hard light": BlendMode.hard_light,
            "Vivid light": BlendMode.vivid_light,
            "Pin Light": BlendMode.pin_light,
            "Saturation": BlendMode.saturation,
            "Color": BlendMode.color,
            "Darken (Min)": BlendMode.darken,
            "Lighten (Max)": BlendMode.lighten,
        }.get(painterMode, BlendMode.normal)
        return blendMode
    
    tmp_filename_base = os.path.join(tmpdir, materialName + "_" + stackName + "_" + channel)
    tmp_filename_base = tmp_filename_base.replace("\\", "/")
    filename_base = exportPath + materialName + "_" + stackName + "_" + channel
    filename_base = filename_base.replace("\\", "/")
    
    layer_records = []
    layer_no = 0
    def countLayer(layer):
        count = 1
        isGroup = "layers" in layer
        if isGroup:
            for childLayer in layer["layers"]:
                count += countLayer(childLayer)
        return count
    layer_count = 0
    for layer in material["stacks"][0]["layers"]:
        layer_count += countLayer(layer)
    progress = QProgressDialog(f"Exporting {materialName}_{stackName}_{channel}", "Cancel", 0, layer_count, parent)
    progress.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
    progress.resize(400,50)
    progress.setWindowTitle(f"Exporting {materialName}_{stackName}_{channel}")
    progress.setWindowModality(Qt.WindowModal)
    progress.show()

    def getMaskImage(layer):
        filename = tmp_filename_base + "_" + str(layer["uid"]) + "_mask.png"
        script = f'alg.mapexport.save([{layer["uid"]}, "mask"], "{filename}", {json.dumps(exportConfig)});'
        js.evaluate(script)
        mask_img = np.asarray(Image.open(filename, mode="r"))
        return mask_img
    
    def getLayerImage(layer):
        filename = tmp_filename_base + "_" + str(layer["uid"]) + ".png"
        script = f'alg.mapexport.save([{layer["uid"]}, "{channel}"], "{filename}", {json.dumps(exportConfig)});'
        js.evaluate(script)
        layer_img = np.asarray(Image.open(filename, mode="r", ))
        return layer_img

    def processLayer(layer):
        if progress.wasCanceled():
            return ExportResult.CANCELED
        progress.setLabelText("export " + layer["name"])
        uid = layer["uid"]
        name = layer["name"]
        isGroup = "layers" in layer
        blendModes = js.evaluate(f"alg.mapexport.layerBlendingModes({uid});")[channel]
        blendMode = convert_blending_mode(blendModes["mode"], isGroup)
        opacity = int(blendModes["opacity"]/100 * 255)
        visible = layer["enabled"]
        if isGroup:
            # layerGroup

            # append BoundingSectionDivider
            channels={
                enums.ChannelId.transparency: ChannelImageData(np.zeros((0,0), np.uint8)),
                enums.ChannelId.red: ChannelImageData(np.zeros((0,0), np.uint8)),
                enums.ChannelId.green: ChannelImageData(np.zeros((0,0), np.uint8)),
                enums.ChannelId.blue: ChannelImageData(np.zeros((0,0), np.uint8)),
            }
            layer_records.append(LayerRecord(
                opacity=0,
                visible=False,
                name="</Layer group>",
                channels=channels,
                blocks=[
                    UnicodeLayerName(name),
                    SectionDividerSetting(enums.SectionDividerSetting.bounding)
                    ]
                ))
            
            for childLayerStruct in layer["layers"]:
                result = processLayer(childLayerStruct)
                if result == ExportResult.CANCELED:
                    return ExportResult.CANCELED

            channels={
                enums.ChannelId.transparency: ChannelImageData(np.zeros((0,0), np.uint8)),
                enums.ChannelId.red: ChannelImageData(np.zeros((0,0), np.uint8)),
                enums.ChannelId.green: ChannelImageData(np.zeros((0,0), np.uint8)),
                enums.ChannelId.blue: ChannelImageData(np.zeros((0,0), np.uint8)),
            }
            if layer["hasMask"]:
                mask_image = getMaskImage(layer)
                channels[enums.ChannelId.user_layer_mask] = ChannelImageData(mask_image)
            # append SectionDivider
            layer_record = LayerRecord(
                top=0, left=0, bottom=0, right=0,
                blend_mode=blendMode, opacity=opacity, clipping=False,
                transparency_protected=False, visible=visible,
                pixel_data_irrelevant=False,
                name=name,
                channels=channels,
                blocks=[
                    UnicodeLayerName(name),
                    SectionDividerSetting(enums.SectionDividerSetting.open)
                    ],
                color_mode=colorMode
                )
            if layer["hasMask"]:
                layer_record.mask = LayerMask(0, 0, size, size)

        else:
            # leafLayer
            layer_image = getLayerImage(layer)
            channels={
                enums.ChannelId.red: ChannelImageData(layer_image[:,:,0]),
                enums.ChannelId.green: ChannelImageData(layer_image[:,:,1]),
                enums.ChannelId.blue: ChannelImageData(layer_image[:,:,2]),
            }
            if layer_image.shape[2]==4:
                channels[enums.ChannelId.transparency] = ChannelImageData(layer_image[:,:,3])
            if layer["hasMask"]:
                mask = getMaskImage(layer)
                channels[enums.ChannelId.user_layer_mask] = ChannelImageData(mask)
            layer_record = LayerRecord(
                top=0, left=0, bottom=size, right=size,
                blend_mode=blendMode, opacity=opacity, clipping=False,
                transparency_protected=False, visible=visible,
                pixel_data_irrelevant=False,
                name=str(name),
                channels=channels,
                blocks=[
                    UnicodeLayerName(name),
                ], color_mode=ColorMode
            )
            if layer["hasMask"]:
                layer_record.mask = LayerMask(0, 0, size, size)
        layer_records.append(layer_record)
        progress.setValue(progress.value() + 1)
        return ExportResult.SUCCEED

    result = ExportResult.SUCCEED
    for layer in material["stacks"][0]["layers"]:
        result = processLayer(layer)
        if result == ExportResult.CANCELED:
            break
    progress.setValue(layer_count)
    if result == ExportResult.CANCELED:
        return ExportResult.CANCELED

    layer_and_mask_info = LayerAndMaskInfo(LayerInfo(layer_records, True))
    psd = PsdFile(enums.Version.version_1, 4, size, size, bitDepth, colorMode, None, None, layer_and_mask_info, None, enums.Compression.rle)
    with open(filename_base + ".psd", "wb") as f:
        psd.write(f)
    return ExportResult.SUCCEED

def export_psd(docStruct, exportMap:TreeItem, exportDir, exportConfig, parent=None):
    with tempfile.TemporaryDirectory() as tmpdir:
        projectName = js.evaluate("alg.project.name()")
        exportPath = exportDir + "/" + projectName + "_psd_export/"
        # log_info(f"exportPath = {exportPath}")
        # log_info(docStruct)
        for material_index in range(exportMap.childCount()):
            materialItem = exportMap.child(material_index)
            materialName = materialItem.data("name")
            for channel_index in range(materialItem.childCount()):
                channelItem = materialItem.child(channel_index)
                channelName = channelItem.data("name")
                if(channelItem.getCheckState("name") == True):
                    log_info(f"export {materialName}.{channelName}")
                    export_result = export_channel(exportPath, tmpdir, docStruct, material_index, channelName, exportConfig, parent)
                    if export_result == ExportResult.CANCELED:
                        return ExportResult.CANCELED
    return ExportResult.SUCCEED
