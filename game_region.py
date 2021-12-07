import numpy

import data

class GameRegion(object):

    SCALE_TYPE_TEMPLATE = 0
    SCALE_TYPE_BOUNDING_BOX = 1

    # to prevent unforseen consequences, game_size should be 16:9 aspect ratio
    def __init__(self, screen_loc, game_resolution, template_source_resolution, template_infos, bounding_box_source_resolution, bounding_box_infos):
        self.screen_loc = screen_loc
        self.game_resolution = game_resolution
        self.template_source_resolution = template_source_resolution
        self.template_scale = [dest_res / src_res for dest_res, src_res in zip(game_resolution, template_source_resolution)]
        self.bounding_box_source_resolution = bounding_box_source_resolution
        self.bounding_box_scale = [dest_res / src_res for dest_res, src_res in zip(game_resolution, bounding_box_source_resolution)]
        self.init_bounding_boxes(bounding_box_infos)
        self.init_templates(template_infos)

    def init_bounding_boxes(self, bounding_box_infos):
        tmp_list = []
        for _, bounding_box_info in bounding_box_infos.items():
            tmp_list.append(data.BoundingBox(bounding_box_info, self))
        self.bounding_boxes = {}
        for i in tmp_list:
            self.bounding_boxes[i.name] = i

    def init_templates(self, template_infos):
        tmp_list = []
        for _, template_info in template_infos.items():
            tmp_list.append(data.Template.create_from_template_info(template_info, self))
        self.templates = {}
        for i in tmp_list:
            self.templates[i.name] = i

    def resolve_scale_type(self, scale_type):
        scaler = None
        if scale_type == GameRegion.SCALE_TYPE_TEMPLATE:
            scaler = self.template_scale
        if scale_type == GameRegion.SCALE_TYPE_BOUNDING_BOX:
            scaler = self.bounding_box_scale
        return scaler

    def transform_coords(self, coords, scale_type):
        scaler = self.resolve_scale_type(scale_type)
        return [screen_loc + int(round(in_coord * scale)) for screen_loc, in_coord, scale in zip(self.screen_loc, coords, scaler)]

    def transform_size(self, size, scale_type):
        scaler = self.resolve_scale_type(scale_type)
        return [int(round(in_size * scale)) for in_size, scale in zip(size, scaler)]

    # bounding boxes are 4 elements, not 2
    def transform_bounding_box(self, bounding_box, scale_type):
        return self.transform_coords(bounding_box[:2], scale_type) + self.transform_coords(bounding_box[2:], scale_type)

    def crop_screenshot(self, screenshot):
        im = screenshot.copy()
        bb = [self.screen_loc[0], self.screen_loc[1], self.screen_loc[0] +  self.game_resolution[0], self.screen_loc[1] + self.game_resolution[1]]
        im = im.crop(bb)
        return numpy.array(im.convert("L"))