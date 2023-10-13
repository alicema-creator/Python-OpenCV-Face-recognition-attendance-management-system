import random
import cv2
import numpy
import wx
import wx.grid
import datetime
import os
import time
import cv2 as cv
import numpy as np
import threading
import sqlite3
from PIL import Image, ImageFont, ImageDraw


# 继承wx库里面的Frame类来使用
class MainFrame(wx.Frame):
    def __init__(self):
        # 初始化窗体数据
        wx.Frame.__init__(self, None, -1, '人脸识别考勤系统', pos=(100, 100), size=(1337, 600))
        panel = wx.Panel(self, -1)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(15, wx.ROMAN, wx.NORMAL, wx.BOLD)

        # 设置窗口以及托盘图标
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap(wx.Image((zsc_circle_file_path), wx.BITMAP_TYPE_JPEG)))
        self.SetIcon(icon)

        # 设置左边背景学院logo
        image = wx.Image(zsc_rectangle_file_path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.background = wx.StaticBitmap(panel, -1, bitmap=image, style=wx.ALIGN_CENTER)
        sizer1.Add(self.background, proportion=10, flag=wx.ALIGN_CENTER, border=10)

        # 设置采集人脸按钮
        self.command1 = wx.Button(panel, -1, '采集人脸')
        self.command1.SetFont(font)
        self.command1.SetBackgroundColour('#3299CC')
        sizer1.Add(self.command1, proportion=5, flag=wx.ALL | wx.EXPAND, border=10)

        # 设置训练数据按钮
        self.command2 = wx.Button(panel, -1, '训练数据')
        self.command2.SetFont(font)
        self.command2.SetBackgroundColour('#DBDB70')
        sizer1.Add(self.command2, proportion=5, flag=wx.ALL | wx.EXPAND, border=10)

        # 设置人脸识别按钮
        self.command3 = wx.Button(panel, -1, '识别打卡')
        self.command3.SetFont(font)
        self.command3.SetBackgroundColour('#32CC32')
        sizer1.Add(self.command3, proportion=5, flag=wx.ALL | wx.EXPAND, border=10)

        # 设置退出系统按钮
        self.command4 = wx.Button(panel, -1, '关闭摄像头')
        self.command4.SetFont(font)
        self.command4.SetBackgroundColour((random.randint(1, 255), random.randint(0, 255), random.randint(0, 255)))
        sizer1.Add(self.command4, proportion=5, flag=wx.ALL | wx.EXPAND, border=10)

        # 设置消息提示文本
        self.text5 = wx.StaticText(panel, -1, '\n\n', style=wx.ALIGN_CENTER)
        self.text5.SetFont(font)
        self.text5.SetForegroundColour('Red')
        sizer1.Add(self.text5, proportion=15, flag=wx.ALL | wx.EXPAND, border=10)

        # 设置个人信息文本
        self.text6 = wx.StaticText(panel, -1, '姓名：')
        self.text7 = wx.StaticText(panel, -1, '学号：')
        self.text8 = wx.StaticText(panel, -1, '学院：')
        sizer1.Add(self.text6, proportion=3, flag=wx.LEFT, border=0)
        sizer1.Add(self.text7, proportion=3, flag=wx.LEFT, border=0)
        sizer1.Add(self.text8, proportion=3, flag=wx.LEFT, border=0)

        # 把分布局全部加入整体顶级布局
        sizer.Add(sizer1, flag=wx.EXPAND | wx.ALL, border=20)


        # 设置右上边消息提示文本
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        font = wx.Font(12, wx.ROMAN, wx.NORMAL, wx.BOLD)
        self.text9 = wx.StaticText(panel, -1, '', style=wx.ALIGN_LEFT)
        self.text9.SetFont(font)
        self.text9.SetForegroundColour('brown')
        self.text9.SetLabel(u''+'您好，欢迎使用人脸考勤系统！')

        self.text10 = wx.StaticText(panel, -1, '', style=wx.ALIGN_RIGHT)
        self.text10.SetFont(font)
        self.text10.SetForegroundColour('Blue')
        self.data_num = 0
        self.updateSumData()
        sizer3.Add(self.text9, proportion=1, flag= wx.ALL|wx.EXPAND, border=10)
        sizer3.Add(self.text10, proportion=1, flag= wx.ALL|wx.EXPAND, border=10)

        sizer2.Add(sizer3, proportion=1, flag=wx.EXPAND | wx.ALL, border=0)

        # 封面图片
        self.image_cover = wx.Image(zsc_circle_file_path, wx.BITMAP_TYPE_ANY).Scale(575, 460)
        self.bmp = wx.StaticBitmap(panel, -1, wx.Bitmap(self.image_cover))
        sizer2.Add(self.bmp, proportion=1, flag=wx.ALL|wx.EXPAND ,border=0)


        # 加入顶级布局
        sizer.Add(sizer2, flag=wx.EXPAND | wx.ALL, border=10)

        # 实例化数据库操作对象
        self.mySqlDao = MySQLDao(self)
        self.grid = MyGrid(panel, self.mySqlDao)
        self.grid.updateGrid()
        # 打卡记录表
        sizer.Add(self.grid, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)


        panel.SetSizer(sizer)

        # 四个按钮对应的事件
        self.command1.Bind(wx.EVT_BUTTON, self.command1_event)
        self.command4.Bind(wx.EVT_BUTTON, self.command4_event)
        self.command3.Bind(wx.EVT_BUTTON, self.command3_event)
        self.command2.Bind(wx.EVT_BUTTON, self.command2_event)

        # 关闭事件
        self.Bind(wx.EVT_CLOSE,self.onClose)

        # 窗口居中，显示
        self.Center()
        self.Show()

        # 控制摄像头的开启与关闭
        self.recognition = False
        self.collected = False

    '''
        主窗体关闭事件
    '''
    def onClose(self,event):
        self.command4_event(event)
        # 等待子线程完成 再关闭，防止不正常退出
        time.sleep(1)
        self.Destroy()

    '''
        采集数据按钮的响应事件
    '''
    def command1_event(self, event):
        self.text6.SetLabel('姓名：')
        self.text7.SetLabel('学号：')
        self.text8.SetLabel('学院：')
        self.text5.SetLabel(u'\n温馨提示：\n' + '⚪正在进学生信息录入...')
        self.text5.Update()

        collectFrame = CollectFrame(self,self.mySqlDao)
        collectFrame.Show()

    '''
        训练数据按钮的响应事件
    '''
    def command2_event(self, event):
        self.trainData()

    '''
        识别打卡按钮的响应事件
    '''
    def command3_event(self, event):
        self.text5.SetLabel(u'')
        self.recognition = False
        t1 = threading.Thread(target=self.recognitionFace)
        t1.start()

    '''
        关闭摄像头按钮的响应事件
    '''
    def command4_event(self, event):
        if self.collected == False:
            self.collected = True
        if self.recognition == False:
            self.recognition = True




    def updateSumData(self):
        self.data_num = 0
        for list in os.listdir(picture_dir_path):
            if len(os.listdir(picture_dir_path + '/' + list)) >= 200:
                self.data_num += 1
        self.text10.SetLabel(u'当前已采集人脸数据的人数：' + str(self.data_num))
        self.text10.Update()


    '''
        @Author：Himit_ZH
        @Function：处理收集人脸每一帧生成图片存入对应文件夹
    '''
    def collect(self,face_id):

        self.text5.SetLabel(u'\n温馨提示：\n' + '请看向摄像头\n准备采集200张人脸图片...')

        count = 0  # 统计照片数量
        path = picture_dir_path+"/Stu_" + str(face_id)  # 人脸图片数据的储存路径
        # 读取视频
        cap = cv.VideoCapture(capture_opt)
        print(cap.isOpened())
        if cap.isOpened() == False:
            self.text5.SetLabel(u'\n错误提示：\n' + '×采集人脸数据失败！\n原因：未能成功打开摄像头')
            return

        # 加载特征数据
        face_detector = cv.CascadeClassifier(haarcascade_frontalface_file_path)
        if not os.path.exists(path):  # 如果没有对应文件夹，自动生成
            os.makedirs(path)
        while self.collected == False:
            flag, frame = cap.read()
            # print('flag:',flag,'frame.shape:',frame.shape)
            if not flag:
                break
            # 将图片灰度
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.1, 3)
            if len(faces) > 1:  # 一帧出现两张照片丢弃，原因：有人乱入，也有可能人脸识别出现差错
                continue
            # 框选人脸，for循环保证一个能检测的实时动态视频流
            for x, y, w, h in faces:
                cv.rectangle(frame, (x, y), (x + w, y + h), color=(0, 255, 0), thickness=2)
                count += 1
                cv.imwrite(path + '/' + str(count) + '.png', gray[y:y + h, x:x + w])
                # # 显示图片
                # cv.imshow('Camera', frame)
                # 将一帧帧图片显示在UI中
                image1 = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image2 = cv2.resize(image1, (575, 460))
                height, width = image2.shape[:2]
                pic = wx.Bitmap.FromBuffer(width, height, image2)
                # 显示图片在panel上
                self.bmp.SetBitmap(pic)
                self.bmp.Update()

            self.text9.SetLabel(u'温馨提示：\n' + '已采集'+ str(count)+'张人脸照片')
            if count >= 200:  #默认采集200张照片
                break
        # 关闭资源
        if count >=200:
            self.text5.SetLabel(u'\n温馨提示：\n' + '✔已成功采集到人脸数据！')
            self.updateSumData()
        else:
            self.text5.SetLabel(u'\n错误提示：\n' + '×采集人脸数据失败!\n未能收集到200张人脸数据！')
            # 删除该文件夹下的所有数据
            ls = os.listdir(path)
            for file_path in ls:
                f_path = os.path.join(path, file_path)
                os.remove(f_path)
            os.rmdir(path)

        cv.destroyAllWindows()
        cap.release()
        self.bmp.SetBitmap(wx.Bitmap(self.image_cover))

    '''
        @Author：Himit_ZH
        @Function：遍历指定文件夹里面的人脸数据，根据文件夹名字，训练对应数据
    '''
    def trainData(self):
        self.text5.SetLabel(u'\n温馨提示：\n' + '⚪正在整合训练的人脸数据\n请稍后...')
        # 图片路径
        path = picture_dir_path
        facesSamples = []
        imageFiles = []
        ids = []
        for root, dirs, files in os.walk(path):
            # root 表示当前正在访问的文件夹路径
            # dirs 表示该文件夹下的子目录名list
            # files 表示该文件夹下的文件list
            # 遍历文件
            for file in files:
                imageFiles.append(os.path.join(root, file))
        # 检测人脸的模型数据
        face_detector = cv2.CascadeClassifier(haarcascade_frontalface_file_path)
        # 遍历列表中的图片
        stu_map =  self.mySqlDao.getIdfromSql()
        for imagefile in imageFiles:  # 获得所有文件名字
            imagefile = imagefile.replace('\\', '/')
            sno = imagefile.split('/')[3].split('_')[1]
            if stu_map.get(sno):
                PIL_img = Image.open(imagefile).convert('L')  # 打开图片并且转为灰度图片
                # 将图像转换为数组
                img_numpy = np.array(PIL_img, 'uint8')
                faces = face_detector.detectMultiScale(img_numpy)
                for x, y, w, h in faces:
                    facesSamples.append(img_numpy[y:y + h, x:x + w])
                    ids.append(int(stu_map.get(sno)))

        self.text5.SetLabel(u'\n温馨提示：\n' + '⚪整合数据结束\n训练数据中...')
        self.text5.Update()
        # 获取训练对象
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(facesSamples, np.array(ids))
        # 保存文件
        recognizer.write(trainer_file_path)

        # 停顿0.5秒 防止卡顿
        time.sleep(0.5)
        self.text5.SetLabel(u'\n温馨提示：\n' + '✔训练人脸数据成功！')
        self.text5.Update()

    '''
        @Author：Himit_ZH
        @Function：读取Tranier文件夹下训练好的人脸数据，跟摄像头读取的人脸数据进行对比，进行识别操作
    '''
    def recognitionFace(self):
        self.text9.SetLabel(u'温馨提示：\n' + '识别过程中尽量不要多人在识别范围内，\n否则可能识别为他人！')
        self.text9.Update()
        recogizer = cv2.face.LBPHFaceRecognizer_create()
        # 加载训练数据集文件
        recogizer.read(trainer_file_path)
        # 准备人脸特征数据
        face_detector = cv2.CascadeClassifier(haarcascade_frontalface_file_path)
        all_stu_map = self.mySqlDao.getDataFromSql()  # 获取数据库对应数据
        cam = cv2.VideoCapture(capture_opt)  # 开启默认摄像头，其他外接摄像头参数可换为1，2....
        if cam.isOpened() == False:
            self.text5.SetLabel(u'\n错误提示：\n' + '×采集人脸数据失败！\n原因：未能成功打开摄像头')
            return
        minW = 0.1 * cam.get(3)
        minH = 0.1 * cam.get(4)
        font = cv2.FONT_HERSHEY_SIMPLEX  # 字体格式

        # 记录识别的学生图片数，达到24张则表示可识别
        stu_count={}
        while self.recognition == False:
            ret, img = cam.read()  # 读取每一帧图片
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 设置成灰度图片
            faces = face_detector.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(int(minW), int(minH))
            )
            stu_id = 0
            stu_name = ''
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                id_num, confidence = recogizer.predict(gray[y:y + h, x:x + w])
                idname = '正在识别...'
                if confidence <= 70: # 置信度55以下表示可以
                    if stu_count.get(id_num):
                        stu_count[id_num] += 1
                    else:
                        stu_count[id_num] = 1
                    if stu_count[id_num] >= 24:
                        idname = all_stu_map[id_num].get('name')
                        stu_name = idname
                        stu_id = all_stu_map[id_num].get('id')
                        self.text5.SetLabel(u'\n识别成功：\n' + '✔欢迎您\n亲爱的'+idname+'')
                        self.text6.SetLabel('姓名：'+all_stu_map[id_num].get('name'))
                        self.text7.SetLabel('学号：'+all_stu_map[id_num].get('num'))
                        self.text8.SetLabel('学院：'+all_stu_map[id_num].get('college'))
                        self.text5.Update()
                        self.text6.Update()
                        self.text7.Update()
                        self.text8.Update()
                        self.recognition = True
                        break
                confidence = "置信度:%.2f"%confidence
                # 将名字和相似度显示在图片上 显示中文
                img = self.cv2ImgAddText(img, idname, x, (y - 30), (0, 255, 0), 30)
                # cv2.putText(img, str(idname), (x+5, y-5), font, 1, (0, 0, 255), 2)
                img = self.cv2ImgAddText(img, str(confidence), x + 5, y + h - 5,  (0, 0, 255), 30)
            # cv2.imshow('Camera', img)
            # 将一帧帧图片显示在UI中

            image1 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            image2 = cv2.resize(image1, (575, 460))
            height, width = image2.shape[:2]
            pic = wx.Bitmap.FromBuffer(width, height, image2)
            # 显示图片在panel上
            self.bmp.SetBitmap(pic)
            if self.recognition and stu_name != '':
                self.text9.SetLabel(u'温馨提示：识别成功！')
                self.mySqlDao.addCheckData(stu_id)
                self.Message = wx.MessageDialog(self, '亲爱的'+stu_name+'打卡成功！', '成功',
                                                          wx.ICON_MASK)
                self.Message.ShowModal()
                self.Message.Destroy()


        cam.release()



class CollectFrame(wx.Frame):
    def __init__(self,mainFrame,mySqlDao):
        self.mainFrame = mainFrame
        self.mySqlDao = mySqlDao
        wx.Frame.__init__(self, None, -1, '数据采集 - 人脸识别系统', pos=(100, 100), size=(350, 350))
        panel = wx.Panel(self, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(15, wx.ROMAN, wx.NORMAL, wx.BOLD)

        # 设置窗口以及托盘图标
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap(wx.Image((zsc_circle_file_path), wx.BITMAP_TYPE_JPEG)))
        self.SetIcon(icon)

        # 设置静态‘姓名'
        self.text1 = wx.StaticText(panel, -1, '姓名：', style=wx.ALIGN_LEFT)
        self.text1.SetFont(font)
        sizer.Add(self.text1, proportion=1, flag=wx.ALIGN_LEFT | wx.EXPAND, border=10)

        # 姓名输入框
        self.text2 = wx.TextCtrl(panel, -1, size=(200, -1), style=wx.TE_LEFT)
        self.text2.SetFont(font)
        sizer.Add(self.text2, proportion=0, flag=wx.ALL | wx.EXPAND, border=15)

        # 设置静态'学号'
        self.text3 = wx.StaticText(panel, -1, '学号：', style=wx.ALIGN_LEFT)
        self.text3.SetFont(font)
        sizer.Add(self.text3, proportion=1, flag=wx.ALIGN_LEFT | wx.EXPAND, border=10)


        # 设置采集人脸数据按钮
        self.startCollect = wx.Button(panel, -1, '开始采集人脸数据')
        self.startCollect.SetFont(font)
        self.startCollect.SetBackgroundColour('#3299CC')
        sizer.Add(self.startCollect, proportion=2, flag=wx.ALL | wx.EXPAND, border=10)

        panel.SetSizer(sizer)


        result = self.mySqlDao.PutDatatoSql(face_name, face_num,face_college)
        flag = 0 # 是否成功
        if result == 1:
            flag = 1
        elif result == 2:
            # 可能存在数据库有记录 但是图像资源被删掉了，这种情况重新录入
            if not os.path.exists(picture_dir_path+'/Stu_' + str(face_num)):  # 文件夹是否存在
                flag = 1
            elif not os.listdir(picture_dir_path+'/Stu_' + str(face_num)):  # 文件夹里面是否有文件
                flag = 1
            else:
                self.Message = wx.MessageDialog(self, '该信息已录入！请重新输入！', '错误', wx.ICON_ERROR)
                self.Message.ShowModal()
                self.Message.Destroy()
        else:
            self.Message = wx.MessageDialog(self, '数据库连接失败！', '错误', wx.ICON_ERROR)
            self.Message.ShowModal()
            self.Message.Destroy()



    def onClose(self,event):
        self.mainFrame.text5.SetLabel(u'')
        self.mainFrame.text9.SetLabel(u'温馨提示：' + '您好，欢迎使用人脸考勤系统！')
        self.Destroy()


class MyGrid(wx.grid.Grid):
    def __init__(self, parent,mySqlDao):
        wx.grid.Grid.__init__(self, parent=parent, id=-1)
        #self.CreateGrid(0, 7)
        self.SetDefaultCellBackgroundColour('#BFD8D8')#parent.BackgroundColour
        self.SetDefaultCellTextColour("#000000")
        self.CreateGrid(0, 5) #设置初始化时的行数和列数
        #为列定义初始化名字
        self.SetColLabelValue(0,'学号')
        self.SetColLabelValue(1,'姓名')
        self.SetColLabelValue(2,'学院')
        self.SetColLabelValue(3,'打卡时间')
        self.SetColLabelValue(4,'是否迟到')
        self.mySqlDao = mySqlDao


'''
操作数据库的类
'''
class MySQLDao():

    '''
    数据库初始化操作
    '''
    def __init__(self,mainFrame):
        self.mainFrame = mainFrame
        con = sqlite3.connect(database_file_path)
        # 创建游标对象
        cur = con.cursor()
        #判断是否存在库
        #判断是否存在表 无则自动创建

            con.commit()
        except Exception as e:
            self.mainFrame.Message = wx.MessageDialog(self.mainFrame, '数据库初始化失败！请检查数据库是否正常创建或链接！', 'ERROR', wx.ICON_ERROR)
            self.mainFrame.Message.ShowModal()
            self.mainFrame.Message.Destroy()
        finally:
            cur.close()
            con.close()
    '''
    @Function：将对应的学生数据存入数据库
    '''
    def PutDatatoSql(self,sname, sno,college):
        flag = 1
        con = sqlite3.connect(database_file_path)
        # 创建游标对象
        cur = con.cursor()

        sql2 = 'select * from t_stu where sname=? and sno=?'
        try:
            cur.execute(sql2,(sname, sno))
            con.commit()
            # 处理结果集
            student = cur.fetchall()
            if student:
                cur.close()
                con.close()
                flag = 2
                return flag
        except Exception as e:
            print(e)
            flag = 0
            return flag
        # 编写插入数据的sql
        sql3= 'insert into t_stu(sname,sno,college,created_time) values(?,?,?,?)'
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # 执行sql
            cur.execute(sql3, (sname, sno,college, dt))
            # 提交事务
            con.commit()
            return flag
        except Exception as e:
            con.rollback()
            flag = 0
            return flag
        finally:
            # 关闭连接
            cur.close()
            con.close()

    '''
    @Function：根据学生学号获取指定id
    '''
    def getIdfromSql(self):
        stu_map = {}
        con = sqlite3.connect(database_file_path)
        # 创建游标对象
        cur = con.cursor()
        # 编写查询的sql
        sql = 'select sno,id from t_stu'
        # 执行sql
        try:
            cur.execute(sql)
            # 处理结果集
            students = cur.fetchall()
            for stu in students:
                stu_map[str(stu[0])] = stu[1]
            return stu_map
        except Exception as e:
            self.mainFrame.Message = wx.MessageDialog(self.mainFrame, '查询数据库错误！请检查数据库链接！', 'ERROR',
                                                      wx.ICON_ERROR)
            self.mainFrame.Message.ShowModal()
            self.mainFrame.Message.Destroy()
        finally:
            cur.close()
            con.close()

    '''
    @Function：获取全部学生的信息
    '''
    def getDataFromSql(self):
        all_stu_map = {}
        # 创建连接
        con = sqlite3.connect(database_file_path)
        # 创建游标对象
        cur = con.cursor()
        # 编写查询的sql
        sql = 'select * from t_stu'
        # 执行sql
        try:
            cur.execute(sql)
            # 处理结果集
            students = cur.fetchall()
            for student in students:
                id = student[0]
                sname = student[1]
                sno = student[2]
                college = student[3]
                all_stu_map[int(id)] = {'id':id,'name': sname, 'num': sno, 'college': college}
        except Exception as e:
            self.mainFrame.Message = wx.MessageDialog(self.mainFrame, '查询数据库错误！请检查数据库链接！', 'ERROR',
                                                      wx.ICON_ERROR)
            self.mainFrame.Message.ShowModal()
            self.mainFrame.Message.Destroy()
        finally:
            # 关闭连接
            cur.close()
            con.close()
            return all_stu_map


    '''
    @Function：获取全部打卡信息
    '''
    def getCheckData(self):
        # 创建连接
        con = sqlite3.connect(database_file_path)
        # 创建游标对象
        cur = con.cursor()
        # 编写查询的sql
        sql = 'select s.sno,s.sname,s.college,c.check_time,c.late from t_stu s,t_check c where s.id = c.uid order by c.check_time, c.late desc'
        print("aa")
        # 执行sql
        try:
            cur.execute(sql)
            # 处理结果集
            students = cur.fetchall()
            return students
        except Exception as e:
            self.mainFrame.Message = wx.MessageDialog(self.mainFrame, '查询数据库错误！请检查数据库链接！', 'ERROR',
                                                      wx.ICON_ERROR)
            self.mainFrame.Message.ShowModal()
            self.mainFrame.Message.Destroy()
        finally:
            # 关闭连接
            cur.close()
            con.close()

    '''
    '''

if __name__ == '__main__':
    app = wx.App()
    app.locale = wx.Locale(wx.LANGUAGE_CHINESE_SIMPLIFIED)
    frame = MainFrame()
    app.MainLoop()
