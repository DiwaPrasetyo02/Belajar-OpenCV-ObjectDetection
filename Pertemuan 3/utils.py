import numpy as np 
import cv2 

class Utils : 
    def draw_ped(self, img, label, x0, y0, xt, yt, font_size=0.4, color=(255,127,0), text_color=(255,255,255)):

        y0, yt = max(y0 - 15, 0) , min(yt + 15, img.shape[0])
        x0, xt = max(x0 - 15, 0) , min(xt + 15, img.shape[1])

        (w, h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_size, 1)
        cv2.rectangle(img,
                        (x0, y0 + baseline),  
                        (max(xt, x0 + w), yt), 
                        color, 
                        2)
        cv2.rectangle(img,
                        (x0, y0 - h - baseline),  
                        (x0 + w, y0 + baseline), 
                        color, 
                        -1)
        cv2.rectangle(img,
                        (x0, y0 - h - baseline),  
                        (x0 + w, y0 + baseline), 
                        color, 
                        2)  
        cv2.putText(img, 
                    label, 
                    (x0, y0),                   
                    cv2.FONT_HERSHEY_SIMPLEX,     
                    font_size,                          
                    text_color,                
                    1,
                    cv2.LINE_AA) 
        return img
    
    def postprocess_darknet(self, outs, frame, classes, 
                        confThreshold = 0.5, nmsThreshold = 0.3, font_size=0.8, 
                        color=(255,127,0), text_color=(255,255,255)):

            frame_h, frame_w, frame_c = frame.shape

            classIds = []
            confidences = []
            boxes = []
            for out in outs:
                for detection in out:
                    scores = detection[5:]

                    classId = np.argmax(scores)
                    confidence = scores[classId]
                    c_x = int(detection[0] * frame_w)
                    c_y = int(detection[1] * frame_h)
                    w = int(detection[2] * frame_w)
                    h = int(detection[3] * frame_h)
                    x = int(c_x - w / 2)
                    y = int(c_y - h / 2)
                    classIds.append(classId)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])

            indices = cv2.dnn.NMSBoxes(boxes, confidences, confThreshold, nmsThreshold)
            for i in indices:
                box = boxes[i]
                x = box[0]
                y = box[1]
                w = box[2]
                h = box[3]

                label = '%s: %.1f%%' % (classes[classIds[i]], (confidences[i]*100))
                print(label)
                frame = self.draw_ped(frame, label, x, y, x+w, y+h, color=color, text_color=text_color, font_size=font_size)
            
            return frame

    def postprocess_onnx(self, outs, frame, classes, 
                        confThreshold = 0.5, nmsThreshold = 0.3, font_size=0.8, 
                        color=(255,127,0), text_color=(255,255,255)):

            [height, width, _] = frame.shape
            length = max((height, width))
            scale = length / 640

            # Prepare output array
            outputs = np.array([cv2.transpose(outs[0])])
            rows = outputs.shape[1]

            boxes = []
            scores = []
            class_ids = []

            # Iterate through output to collect bounding boxes, confidence scores, and class IDs
            for i in range(rows):
                classes_scores = outputs[0][i][4:]
                (minScore, maxScore, minClassLoc, (x, maxClassIndex)) = cv2.minMaxLoc(classes_scores)
                if maxScore >= 0.25:
                    box = [
                        outputs[0][i][0] - (0.5 * outputs[0][i][2]),
                        outputs[0][i][1] - (0.5 * outputs[0][i][3]),
                        outputs[0][i][2],
                        outputs[0][i][3],
                    ]
                    boxes.append(box)
                    scores.append(maxScore)
                    class_ids.append(maxClassIndex)

            # Apply NMS (Non-maximum suppression)
            result_boxes = cv2.dnn.NMSBoxes(boxes, scores, 0.25, 0.45, 0.5)

            # Iterate through NMS results to draw bounding boxes and labels
            for i in range(len(result_boxes)):
                index = result_boxes[i]
                box = boxes[index]
                label = '%s: %.1f%%' % (classes[class_ids[index]], (scores[index]*100))
                x = round(box[0] * scale)
                y = round(box[1] * scale)
                w = round(box[2] * scale)
                h = round(box[3] * scale)
                print(label)
                frame = self.draw_ped(frame, label, x, y, x+w, y+h, color=color, text_color=text_color, font_size=font_size) 
            return frame