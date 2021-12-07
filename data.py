import os
import PIL.Image
import numpy
import cv2
import threading
import datetime

import config
import game_region as game_region_module

class BoundingBoxInfo(object):

    def __init__(self, name, source_coords):
        self.name = name
        self.source_coords = source_coords



class BoundingBox(object):

    def __init__(self, bounding_box_info, game_region):
        self.name = bounding_box_info.name
        self.coords = game_region.transform_bounding_box(bounding_box_info.source_coords, game_region.SCALE_TYPE_BOUNDING_BOX)
        self.dimensions = [self.coords[2] - self.coords[0], self.coords[3] - self.coords[1]]



class TemplateInfo(object):

    def __init__(self, name, input_image, threshold = 0):
        self.name = name
        self.input_image = input_image
        self.threshold = threshold

    @classmethod
    def create_and_fetch_positional_image(cls, name: str, resolution: list[int], threshold: float = 0):
        path = os.path.join(
            "res",
            "templates",
            str(resolution[0]) + "x" + str(resolution[1]),
            name + ".png")
        im = PIL.Image.open(path)
        return TemplateInfo(name, im, threshold)




class Template(object):

    def __init__(self, name, template_image, search_region, threshold = 0):
        self.name = name
        self.image = template_image
        self.search_region = search_region
        self.threshold = threshold

    # A "positional image" is a screenshot with all irrelevant data deleted
    # (set to alpha). It simplifies things, as we now know where in the 
    # game screen to look for the template.
    @classmethod
    def create_from_template_info(cls, template_info, game_region):
        im = template_info.input_image.copy()
        im_total_size = im.size
        for i in range(2):
            if im_total_size[i] != game_region.template_source_resolution[i]:
                raise Exception("Floating templates currently not supported. "
                        "Input template image size must be equal to the source "
                        "resolution.")
        old_bb = im.getbbox()
        im = im.crop(old_bb)
        old_size = im.size
        new_size = tuple(game_region.transform_size(old_size, game_region.SCALE_TYPE_TEMPLATE))
        im = im.resize(new_size, PIL.Image.LANCZOS)
        im = im.convert("L")
        im = numpy.array(im) # converts to OpenCV format
        # the reason we use transform_size here is because, when we get a 
        # comparison image, it will simply be a cropped image of the game 
        # region, and transform_size does not add the screen-space offset,
        # whereas transform_coords does
        new_bb = game_region.transform_size([old_bb[0], old_bb[1]], game_region.SCALE_TYPE_TEMPLATE)
        new_bb += [new_bb[0] + new_size[0], new_bb[1] + new_size[1]]
        new_bb[0] -= 3
        new_bb[1] -= 3
        new_bb[2] += 3
        new_bb[3] += 3
        return Template(template_info.name, im, tuple(new_bb), template_info.threshold)

    def get_response(self, image):
        cropped = image[self.search_region[1] : self.search_region[3], self.search_region[0] : self.search_region[2]]
        r = cv2.minMaxLoc(cv2.matchTemplate(cropped, self.image, cv2.TM_CCOEFF_NORMED))[1]
        if config.debug:
            if self.name == "menu-main-modes" or \
                    self.name == "menu-modes-header" or \
                    self.name == "menu-modes-bg":
                print("template response: " + str(r))
            #timestamp = datetime.datetime.now()
            #cv2.imwrite(str(timestamp) + "_screen.png", cropped)
            #cv2.imwrite(str(timestamp) + "_template.png", self.image)
        return r

    def threshold_reached(self, image):
        return self.get_response(image) > self.threshold



def create_bounding_box_infos():
    tmp_list = []
    tmp_list.append(BoundingBoxInfo("play",           [1342,  836, 1457,  942]))
    tmp_list.append(BoundingBoxInfo("end-turn",       [1506,  475, 1615,  511]))
    tmp_list.append(BoundingBoxInfo("hero-power",     [1090,  780, 1185,  871]))
    tmp_list.append(BoundingBoxInfo("menu-dead-zone", [1665,   47, 1892, 1010]))
    tmp_list.append(BoundingBoxInfo("concede",        [880,   367, 1044,  399]))
    tmp_list.append(BoundingBoxInfo("options",        [1858, 1042, 1896, 1070]))
    tmp_list.append(BoundingBoxInfo("bg-refresh",     [1093,  166, 1166,  241]))
    result = {}
    for i in tmp_list:
        result[i.name] = i
    return result



def create_template_infos():
    tmp_list = []
    tmp_list.append(TemplateInfo.create_and_fetch_positional_image("game-over-defeat",          0.78))
    tmp_list.append(TemplateInfo.create_and_fetch_positional_image("game-over-victory",         0.78))
    tmp_list.append(TemplateInfo.create_and_fetch_positional_image("your-turn-something-to-do", 0.88))
    tmp_list.append(TemplateInfo.create_and_fetch_positional_image("play-standard",             0.88))
    tmp_list.append(TemplateInfo.create_and_fetch_positional_image("turn-start",                0.8))
    result = {}
    for i in tmp_list:
        result[i.name] = i
    return result



mouse_lock = threading.Lock()