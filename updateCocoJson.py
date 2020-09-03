import json
import os

#####################################################################################################################
# README                                                                                               				#
# updateCocoJson.py updates the annotations from old json file with new annotations from yolo format                #
# output: a new json file with new annotations                                                                      #
#####################################################################################################################

YOLO_PATH = 'path/to/yolo bbox'
JSON_PATH = '/path/to/instances.json'
OUTPUT_FILE_NAME = 'new_instances.json'
THRESHOLD = 0.1

with open(JSON_PATH) as jsonFile:
    jsonData=json.load(jsonFile)

newCocoOutput={
    "categories": jsonData['categories'],
    "info": jsonData['info'],
    "annotations": [],
    "images": jsonData['images'],
    "licenses": jsonData['licenses']
}
imageInfo = jsonData['images']
annotations = jsonData['annotations']

yoloFiles = next(os.walk(YOLO_PATH))[2]

newBboxNumber = 0

annotationID = 0
for yoloFile in yoloFiles:
    if yoloFile != 'classes.txt':
        with open(YOLO_PATH + '/{}'.format(yoloFile)) as f:
            data = f.read().splitlines()
        for oneLineData in data:
            element = oneLineData.split()

            yoloData = {
                "imageName": yoloFile.replace(".txt", ""),
                "category_id": int(element[0]),
                "bbox": element[1:]
            }

            for image in imageInfo:
                imageName = image['file_name'].replace(".jpg", "")
                imageName = imageName.replace(".png", "")
                imageName = imageName.replace(".jpeg", "")

                if yoloData['imageName'] == imageName:
                    imageData = {
                        "id": image['id'],
                        "width": image['width'],
                        "height": image['height'],
                    }

                    x1 = round(image['width'] * float(yoloData['bbox'][0]) - abs(float(yoloData['bbox'][2]) * image['width']) / 2)
                    x2 = round(abs(float(yoloData['bbox'][2]) * image['width']) + x1)
                    y1 = round(image['height'] * float(yoloData['bbox'][1]) - abs(float(yoloData['bbox'][3]) * image['height']) / 2)
                    y2 = round(abs(float(yoloData['bbox'][3]) * image['height']) + y1)

                    yoloBbox = []
                    yoloBbox.append(y1)
                    yoloBbox.append(x1)
                    yoloBbox.append(y2)
                    yoloBbox.append(x2)

                    assigned = False
                    for annotation in annotations:
                        if annotation['image_id'] == imageData['id']:
                            if annotation['category_id'] == yoloData['category_id']:

                                delta_y1 = abs(annotation['bbox'][0] - yoloBbox[0])
                                delta_x1 = abs(annotation['bbox'][1] - yoloBbox[1])
                                delta_y2 = abs(annotation['bbox'][2] - yoloBbox[2])
                                delta_x2 = abs(annotation['bbox'][3] - yoloBbox[3])

                                # if bbox exactly te same
                                if delta_y1 == 0 and delta_x1 == 0 and delta_y2 == 0 and delta_x2 == 0:
                                    annotation['id'] = annotationID
                                    newCocoOutput['annotations'].append(annotation)
                                    assigned = True
                                    annotationID += 1
                                    break
                                # if bbox slightly different
                                elif delta_y1 < THRESHOLD*image['height'] and delta_x1 < THRESHOLD*image['width'] and delta_y2 < THRESHOLD*image['height'] and delta_x2 < THRESHOLD*image['width']:
                                    annotation['id'] = annotationID
                                    annotation['bbox'] = yoloBbox
                                    newCocoOutput['annotations'].append(annotation)
                                    assigned = True
                                    annotationID += 1
                                    break

                    if not assigned:
                        segment = []
                        segment.append(round(float(x1), 1))
                        segment.append(round(float(y1), 1))

                        segment.append(round(float(x2), 1))
                        segment.append(round(float(y1), 1))

                        segment.append(round(float(x2), 1))
                        segment.append(round(float(y2), 1))

                        segment.append(round(float(x1), 1))
                        segment.append(round(float(y2), 1))

                        segmentation = []
                        segmentation.append(segment)

                        newAnnotation = {
                            "id": annotationID,
                            "width": imageData['width'],
                            "height": imageData['height'],
                            "area": abs((yoloBbox[3]-yoloBbox[1]))*abs((yoloBbox[2]-yoloBbox[0])),
                            "image_id": imageData['id'],
                            "bbox": yoloBbox,
                            "category_id": yoloData['category_id'],
                            "iscrowd": 0,
                            "segmentation": segmentation
                        }
                        newCocoOutput['annotations'].append(newAnnotation)
                        annotationID += 1
                        newBboxNumber += 1
                        break

print("Number of new bbox: {}".format(newBboxNumber))

##################################
# create or update new json file #
##################################
with open(OUTPUT_FILE_NAME, 'w') as new_json_file:
    json.dump(newCocoOutput, new_json_file, indent=2)
