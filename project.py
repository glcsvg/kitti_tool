from __future__ import division
#from Tkinter import *
from tkinter.messagebox import showinfo
from tkinter import ttk
from tkinter import *
from tkinter import filedialog
from PIL import Image
from PIL import ImageTk
import os
import glob
import random
import cv2
import numpy as np
import sys
import pathlib


# colors for the bboxes
COLORS = ['red', 'blue', 'cyan', 'orange', 'magenta', 'teal', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("KittiTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.outDir = ''
        self.outVideoImageDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None
        self.currentLabelclass = ''
        self.cla_can_temp = []
        self.classcandidate_filename = 'class.txt'

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        self.checkprediction = 1
        

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        # self.label = Label(self.frame, text = "Image Dir:")
        # self.label.grid(row = 0, column = 0, sticky = E)
        # self.entry = Entry(self.frame)
        # self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.slctvideoBtn = Button(self.frame, text = "Select Video", command = self.createImageVideo,background='#bfbfbf')
        self.slctvideoBtn.grid(row = 0, column = 1,sticky = W+E)
        self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir,background='#bfbfbf')
        self.ldBtn.grid(row = 0, column = 2,sticky = W+E)
        #verification
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage)  # press 'a' to go backforward
        self.parent.bind("d", self.nextImage)  # press 'd' to go forward"""
        self.mainPanel.grid(row=1, column=1, rowspan=4, sticky=W + N)

        # choose class
        self.classname = StringVar()
        self.classcandidate = ttk.Combobox(self.frame,state='readonly',textvariable=self.classname)
        self.classcandidate.grid(row=1,column=2)
        if os.path.exists(self.classcandidate_filename):
        	with open(self.classcandidate_filename) as cf:
        		for line in cf.readlines():
        			# print line
        			self.cla_can_temp.append(line.strip('\n'))
        #print self.cla_can_temp
        self.classcandidate['values'] = self.cla_can_temp
        self.classcandidate.current(0)
        self.currentLabelclass = self.classcandidate.get() #init
        self.btnclass = Button(self.frame, text = 'ComfirmClass', command = self.setClass,background='#e6ffe6')
        self.btnclass.grid(row=2,column=2,sticky = W+E)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='Bounding Boxes:')
        self.lb1.grid(row=3, column=2, sticky=W + N)
        self.listbox = Listbox(self.frame, width=22, height=12)
        self.listbox.grid(row=4, column=2, sticky=N + S)
        self.btnDel = Button(self.frame, text='Delete', command=self.delBBox)
        self.btnDel.grid(row=5, column=2, sticky=W + E + N)
        self.btnClear = Button(self.frame, text='ClearAll', command=self.clearBBox,background='#ff6666')
        self.btnClear.grid(row=6, column=2, sticky=W + E + N)
        #verification
        self.yesBtn = Button(self.frame, text = "Yes", command = self.truePrediction, width = 8, background='#98FB98')
        self.yesBtn.grid(row = 7, column = 2,sticky = W)
        self.noBtn = Button(self.frame, text = "No ", command = self.falsePrediction, width = 8, background='#ff3333')
        self.noBtn.grid(row = 7, column = 2,sticky = E)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 7, column = 0, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<<   Prev', width = 10, command = self.prevImage,background='#bfbfbf')
        self.prevBtn.pack(side = LEFT, padx = 15, pady = 5)
        self.nextBtn = Button(self.ctrPanel, text='Next   >>', width = 10, command = self.nextImage,background='#bfbfbf')
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 5)
        self.btn_quit = Button(self.ctrPanel, text='Quit', command=self.parent.quit,background='red')
        self.btn_quit.pack(side = LEFT, padx = 5, pady = 5)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

    def truePrediction(self):
        #self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage(self.imageDir)

    def falsePrediction(self):
        self.checkprediction = 0
        self.mainPanel.unbind("<Button-1>", self.mouseClick)
        self.mainPanel.unbind("<Motion>", self.mouseMove)

    def createImageVideo(self):
        self.videoDir = filedialog.askopenfile(parent=root,initialdir = "/home/dell/Desktop/",title = "Select directory")
        videoname =(self.videoDir.name.split("/")[-1]).split('.')[0]
        self.outVideoImageDir = os.path.join(r'./kitti_images')
        print(self.outVideoImageDir)

        if not os.path.exists(self.outVideoImageDir):
            os.mkdir(self.outVideoImageDir)
        #read video
        video_cap = cv2.VideoCapture(self.videoDir.name)
        frame_width = int(video_cap.get(3))
        frame_height = int(video_cap.get(4))
        c=1
        while(True):
            # Capture frame-by-frame
            ret, frame = video_cap.read()            
            if ret == True : 
                if c%100==0:
                    #cv2.imshow('frame',gray)
                    frameId = video_cap.get(1)
                    tmp_name = str(frameId) + '.jpg'
                    img_file_name = os.path.join(self.outVideoImageDir,tmp_name)
                    cv2.imwrite(img_file_name, frame)
                c+=1
            else:
                break

        video_cap.release()
        showinfo('Son', 'Resimler oluşturuldu')


    def loadDir(self, dbg = False):

        self.outDir = os.path.join(r'./MYLABELS')        
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        self.imageDir = filedialog.askdirectory(parent=root,initialdir = "/home/dell/Desktop/p1/tkinter/resim/",title = "Select directory")
        print("Dosya ismi",self.imageDir)
        if self.imageDir == '':
            showinfo('Son', 'Bu dosyada resim bulunamadı')
            return
        else:
            for name in os.listdir(self.imageDir):
                        if name.lower().endswith(".jpg") or name.lower().endswith(".png") or name.lower().endswith(".jpeg"):
                            self.imageList.append(name)
        print("..................",self.imageList)
        if len(self.imageList) == 0:
            print('Bu dosyada resim bulunamadı!')
            return

        self.cur = 1
        self.total = len(self.imageList)
        self.loadImage(self.imageDir)

    def loadImage(self,imageDir):
        # load image
        imagepath = self.imageDir + '/' + self.imageList[self.cur - 1]
        #print("yüklenen resim",imagepath)
        self.img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as txt_file:
                for (i, line) in enumerate(txt_file):
                    # tmp = [int(t.strip()) for t in line.split()]
                    tmp = line.split()
                    #print tmp
                    self.bboxList.append(tuple(tmp))

                    print(self.bboxList)
                    
                    print(int(float(tmp[3])))
                    tmpId = self.mainPanel.create_rectangle(int(float(tmp[3])), int(float(tmp[4])), \
                                                            int(float(tmp[5])), int(float(tmp[6])), \
                                                            width = 2, \
                                                            outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' %(tmp[0],int(float(tmp[3])), int(float(tmp[4])), \
                    												  int(float(tmp[5])), int(float(tmp[6]))))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
                    
        # else:
        #     print("dosya yok")
        #   exit(1)
    
    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            print("ilk durum",self.STATE['x'], self.STATE['y'])
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            print("2.durum",self.STATE['x'], self.STATE['y'])
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.bboxList.append((self.currentLabelclass,x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' % (self.currentLabelclass, x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width=2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width=2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                          event.x, event.y, \
                                                          width=2, \
                                                          outline=COLORS[len(self.bboxList) % len(COLORS)])
    
    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []
    
    def prevImage(self, event = None):   
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage(self.imageDir)
        else:
            showinfo('Son', 'Resim bulunamdı.')

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage(self.imageDir)

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []
    
    def setClass(self):
        self.currentLabelclass = self.classcandidate.get()
        print('Sınıf etiketi :', self.currentLabelclass)
    
    def saveImage(self):
        with open(self.labelfilename, 'w') as f:

            for bbox in self.bboxList:
                print(bbox)
                classname = bbox[0]
                x1 = '{0:.2f}'.format(float(bbox[1]))
                y1 = '{0:.2f}'.format(float(bbox[2]))
                x2 = '{0:.2f}'.format(float(bbox[3]))
                y2 = '{0:.2f}'.format(float(bbox[4]))

                f.write(("{0} 0.00 0.00 {1} {2} {3} {4} 0.00 0.00 0.00 0.00 0.00 0.00 0.00\n").
                            format(classname,x1,y1,x2,y2))
                #showinfo('Dosya yazıldı')
        print('Resim. %d ksydedildi' % (self.cur))
if __name__ == '__main__':

    root = Tk()
    tool = LabelTool(root)
    root.resizable(width =  True, height = True)
    root.mainloop()
