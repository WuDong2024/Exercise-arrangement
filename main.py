import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, scrolledtext
import os
import json
import datetime
from PIL import Image, ImageTk, ImageFont
import shutil
import zipfile
import threading
import sys
import tempfile

class EnhancedMistakeManager:
    def __init__(self, root):
        self.root = root
        self.root.title("学霸错题本 - 高效学习助手（本软件为免费软件，如果你是付费获得的，那证明你被骗了awa）")
        self.root.geometry("1100x700")
        self.root.configure(bg='#f5f7fa')

        # 设置最小窗口尺寸
        self.root.minsize(800, 600)

        # 创建数据文件夹
        self.data_dir = "mistakes_data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # 创建图片文件夹
        self.image_dir = os.path.join(self.data_dir, "images")
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

        # 加载字体
        self.load_fonts()

        # 加载数据
        self.subjects = self.load_subjects()
        self.chapters = self.load_chapters()
        self.mistakes = self.load_mistakes()

        # 当前选择的错题
        self.current_mistake = None
        self.current_image_index = 0

        # 创建现代UI
        self.create_modern_ui()

        # 加载初始数据
        self.update_subject_dropdown()
        self.update_chapter_dropdown()

    def load_fonts(self):
        """加载字体"""
        self.default_font = ("DejaVu Sans", 10)
        self.title_font = ("DejaVu Sans", 12, "bold")

        # 尝试加载Noto Sans CJK字体
        try:
            # 检查系统是否已安装Noto Sans CJK
            test_font = ImageFont.truetype("NotoSansCJK-Regular.ttc", 10)
            self.default_font = ("Noto Sans CJK SC", 10)
            self.title_font = ("Noto Sans CJK SC", 12, "bold")
        except:
            try:
                # 尝试加载Source Han Sans（思源黑体）
                test_font = ImageFont.truetype("SourceHanSansSC-Regular.otf", 10)
                self.default_font = ("Source Han Sans SC", 10)
                self.title_font = ("Source Han Sans SC", 12, "bold")
            except:
                # 使用DejaVu Sans作为后备
                pass

        # 设置全局字体
        self.root.option_add("*Font", self.default_font)

    def create_modern_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 创建左侧面板
        left_frame = ttk.LabelFrame(main_frame, text="学科与章节", padding=(10, 5))
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 创建右侧面板
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 左侧面板内容
        subject_frame = ttk.Frame(left_frame)
        subject_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(subject_frame, text="学科:", font=self.title_font).pack(anchor=tk.W)
        self.subject_combobox = ttk.Combobox(subject_frame, state="readonly", width=20)
        self.subject_combobox.pack(fill=tk.X, pady=5)
        self.subject_combobox.bind('<<ComboboxSelected>>', self.subject_selected)

        btn_frame = ttk.Frame(subject_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="添加学科", command=self.add_subject, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="删除学科", command=self.delete_subject, width=10).pack(side=tk.LEFT)

        ttk.Separator(subject_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(subject_frame, text="章节:", font=self.title_font).pack(anchor=tk.W)
        self.chapter_combobox = ttk.Combobox(subject_frame, state="readonly", width=20)
        self.chapter_combobox.pack(fill=tk.X, pady=5)

        btn_frame2 = ttk.Frame(subject_frame)
        btn_frame2.pack(fill=tk.X)
        ttk.Button(btn_frame2, text="添加章节", command=self.add_chapter, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame2, text="删除章节", command=self.delete_chapter, width=10).pack(side=tk.LEFT)

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # 错题列表
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(list_frame, text="错题列表", font=self.title_font).pack(anchor=tk.W)

        # 创建带滚动条的错题列表框
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.mistake_listbox = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            bg="white",
            fg="#333333",
            selectbackground="#4da6ff",
            selectforeground="white",
            font=self.default_font,
            height=15,
            borderwidth=2,
            relief="groove"
        )
        self.mistake_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.mistake_listbox.yview)

        self.mistake_listbox.bind('<<ListboxSelect>>', self.mistake_selected)

        # 右侧面板内容
        # 创建带滚动条的主容器
        right_container = ttk.Frame(right_frame)
        right_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(right_container, bg='#f5f7fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 错题详情框架
        detail_frame = ttk.LabelFrame(scrollable_frame, text="错题详情", padding=(15, 10))
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 错题标题
        title_frame = ttk.Frame(detail_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(title_frame, text="标题:", width=8).pack(side=tk.LEFT)
        self.title_entry = ttk.Entry(title_frame, width=50, font=self.default_font)
        self.title_entry.pack(fill=tk.X, expand=True, padx=(0, 10))

        # 学科和章节信息
        info_frame = ttk.Frame(detail_frame)
        info_frame.pack(fill=tk.X, pady=5)

        ttk.Label(info_frame, text="学科:", width=8).pack(side=tk.LEFT)
        self.subject_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.subject_var, width=20, font=self.default_font,
                  background="#f0f5ff", relief="groove").pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(info_frame, text="章节:", width=8).pack(side=tk.LEFT)
        self.chapter_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.chapter_var, width=20, font=self.default_font,
                  background="#f0f5ff", relief="groove").pack(side=tk.LEFT)

        # 错题描述和答案
        notebook = ttk.Notebook(detail_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # 题目描述标签页
        desc_frame = ttk.Frame(notebook, padding=5)
        notebook.add(desc_frame, text="题目描述")

        self.description_text = scrolledtext.ScrolledText(
            desc_frame,
            wrap=tk.WORD,
            font=self.default_font,
            padx=10,
            pady=10,
            bg="#f8f9fa",
            height=8
        )
        self.description_text.pack(fill=tk.BOTH, expand=True)

        # 正确答案标签页
        answer_frame = ttk.Frame(notebook, padding=5)
        notebook.add(answer_frame, text="正确答案")

        self.answer_text = scrolledtext.ScrolledText(
            answer_frame,
            wrap=tk.WORD,
            font=self.default_font,
            padx=10,
            pady=10,
            bg="#f8f9fa",
            height=8
        )
        self.answer_text.pack(fill=tk.BOTH, expand=True)

        # 图片区域 - 使用独立的框架确保在小窗口下也能显示按钮
        image_container = ttk.Frame(detail_frame)
        image_container.pack(fill=tk.BOTH, pady=(10, 0), expand=True)

        image_frame = ttk.LabelFrame(image_container, text="题目图片", padding=(10, 5))
        image_frame.pack(fill=tk.BOTH, expand=True)

        # 图片显示区域
        img_display_frame = ttk.Frame(image_frame)
        img_display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.image_label = ttk.Label(img_display_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)

        # 图片导航
        nav_frame = ttk.Frame(image_frame)
        nav_frame.pack(fill=tk.X, pady=5)

        self.image_nav_label = ttk.Label(nav_frame, text="0/0")
        self.image_nav_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(nav_frame, text="上一张", command=self.prev_image, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="下一张", command=self.next_image, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="添加图片", command=self.upload_image, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="删除图片", command=self.delete_image, width=8).pack(side=tk.LEFT, padx=5)

        # 底部按钮区域
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, pady=(15, 5))

        ttk.Button(button_frame, text="添加错题", command=self.add_mistake, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="更新错题", command=self.update_mistake).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除错题", command=self.delete_mistake).pack(side=tk.LEFT, padx=5)

        ttk.Separator(button_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        ttk.Button(button_frame, text="导出数据", command=self.export_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导入数据", command=self.import_data).pack(side=tk.LEFT, padx=5)

        ttk.Separator(button_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        ttk.Button(button_frame, text="使用帮助", command=self.show_help).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关于软件", command=self.show_about).pack(side=tk.LEFT, padx=5)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(10, 5),
            font=self.default_font
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 设置样式
        self.setup_styles()

        # 绑定鼠标滚轮事件实现滚动
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def setup_styles(self):
        # 创建自定义样式
        style = ttk.Style()
        style.theme_use("clam")

        # 配置主颜色
        style.configure("TFrame", background="#f5f7fa")
        style.configure("TLabel", background="#f5f7fa", foreground="#333333", font=self.default_font)
        style.configure("TLabelframe", background="#f5f7fa", foreground="#333333", font=self.title_font)
        style.configure("TLabelframe.Label", background="#f5f7fa", foreground="#1a73e8", font=self.title_font)

        # 按钮样式
        style.configure("TButton",
                        background="#4da6ff",
                        foreground="white",
                        font=self.default_font,
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor="#4da6ff")
        style.map("TButton",
                  background=[('active', '#3d8de0'), ('pressed', '#2c7dd6')])

        # 强调按钮样式
        style.configure("Accent.TButton",
                        background="#32a852",
                        foreground="white",
                        font=self.default_font)
        style.map("Accent.TButton",
                  background=[('active', '#2a8f46'), ('pressed', '#217639')])

        # 列表框样式
        style.configure("TListbox", background="white", foreground="#333333", font=self.default_font)

        # 组合框样式
        style.configure("TCombobox", fieldbackground="white", background="white", font=self.default_font)

    def load_subjects(self):
        file_path = os.path.join(self.data_dir, "subjects.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return ["数学", "物理", "化学", "生物", "英语", "语文"]

    def save_subjects(self):
        file_path = os.path.join(self.data_dir, "subjects.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.subjects, f, ensure_ascii=False)

    def load_chapters(self):
        file_path = os.path.join(self.data_dir, "chapters.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "数学": ["代数", "几何", "函数", "概率统计"],
            "物理": ["力学", "电磁学", "光学", "热学"],
            "化学": ["无机化学", "有机化学", "物理化学", "分析化学"],
            "生物": ["细胞生物学", "遗传学", "生态学", "生理学"],
            "英语": ["语法", "阅读理解", "写作", "听力"],
            "语文": ["文言文", "现代文阅读", "作文", "基础知识"]
        }

    def save_chapters(self):
        file_path = os.path.join(self.data_dir, "chapters.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.chapters, f, ensure_ascii=False)

    def load_mistakes(self):
        file_path = os.path.join(self.data_dir, "mistakes.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for mistake in data:
                    if "images" not in mistake:
                        if "image" in mistake:
                            mistake["images"] = [mistake["image"]]
                            del mistake["image"]
                        else:
                            mistake["images"] = []
                return data
        return []

    def save_mistakes(self):
        file_path = os.path.join(self.data_dir, "mistakes.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.mistakes, f, ensure_ascii=False, indent=2)

    def update_subject_dropdown(self):
        self.subject_combobox['values'] = self.subjects
        if self.subjects:
            self.subject_combobox.current(0)
            self.subject_selected()

    def update_chapter_dropdown(self):
        subject = self.subject_combobox.get()
        if subject and subject in self.chapters:
            chapters = self.chapters[subject]
            self.chapter_combobox['values'] = chapters
            if chapters:
                self.chapter_combobox.current(0)

    def subject_selected(self, event=None):
        self.update_chapter_dropdown()
        self.update_mistake_list()

    def update_mistake_list(self):
        self.mistake_listbox.delete(0, tk.END)
        subject = self.subject_combobox.get()
        chapter = self.chapter_combobox.get()

        if subject and chapter:
            for mistake in self.mistakes:
                if mistake['subject'] == subject and mistake['chapter'] == chapter:
                    self.mistake_listbox.insert(tk.END, mistake['title'])

    def mistake_selected(self, event):
        selection = self.mistake_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        subject = self.subject_combobox.get()
        chapter = self.chapter_combobox.get()

        # 查找选中的错题
        self.current_mistake = None
        for mistake in self.mistakes:
            if mistake['subject'] == subject and mistake['chapter'] == chapter:
                if index == 0:
                    self.current_mistake = mistake
                    break
                index -= 1

        if self.current_mistake:
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, self.current_mistake['title'])
            self.subject_var.set(self.current_mistake['subject'])
            self.chapter_var.set(self.current_mistake['chapter'])
            self.description_text.delete(1.0, tk.END)
            self.description_text.insert(tk.END, self.current_mistake['description'])
            self.answer_text.delete(1.0, tk.END)
            self.answer_text.insert(tk.END, self.current_mistake['answer'])

            # 显示图片
            self.current_image_index = 0
            self.show_image()

    def show_image(self):
        if self.current_mistake and 'images' in self.current_mistake and self.current_mistake['images']:
            images = self.current_mistake['images']
            total_images = len(images)

            if total_images > 0 and self.current_image_index < total_images:
                image_path = images[self.current_image_index]
                if os.path.exists(image_path):
                    try:
                        img = Image.open(image_path)

                        # 动态调整图片大小以适应窗口
                        max_width = 500
                        max_height = 300

                        # 计算缩放比例
                        width_ratio = max_width / img.width
                        height_ratio = max_height / img.height
                        scale = min(width_ratio, height_ratio)

                        new_width = int(img.width * scale)
                        new_height = int(img.height * scale)

                        img = img.resize((new_width, new_height), Image.LANCZOS)

                        photo = ImageTk.PhotoImage(img)
                        self.image_label.configure(image=photo)
                        self.image_label.image = photo
                        self.image_nav_label.configure(text=f"{self.current_image_index+1}/{total_images}")
                        return
                    except Exception as e:
                        self.status_var.set(f"图片加载错误: {str(e)}")

        # 如果没有图片或加载失败，显示占位符
        self.image_label.configure(image='')
        self.image_label.image = None
        self.image_nav_label.configure(text="0/0")

    def prev_image(self):
        if self.current_mistake and 'images' in self.current_mistake:
            images = self.current_mistake['images']
            if images:
                self.current_image_index = (self.current_image_index - 1) % len(images)
                self.show_image()

    def next_image(self):
        if self.current_mistake and 'images' in self.current_mistake:
            images = self.current_mistake['images']
            if images:
                self.current_image_index = (self.current_image_index + 1) % len(images)
                self.show_image()

    def add_subject(self):
        subject = simpledialog.askstring("添加学科", "请输入学科名称:", parent=self.root)
        if subject and subject not in self.subjects:
            self.subjects.append(subject)
            self.chapters[subject] = []
            self.save_subjects()
            self.save_chapters()
            self.update_subject_dropdown()
            self.status_var.set(f"已添加学科: {subject}")

    def delete_subject(self):
        subject = self.subject_combobox.get()
        if subject and subject in self.subjects:
            if messagebox.askyesno("确认删除", f"确定要删除学科 '{subject}' 及其所有章节和错题吗？", parent=self.root):
                # 删除学科
                self.subjects.remove(subject)
                del self.chapters[subject]

                # 删除该学科下的所有错题
                self.mistakes = [m for m in self.mistakes if m['subject'] != subject]

                self.save_subjects()
                self.save_chapters()
                self.save_mistakes()
                self.update_subject_dropdown()
                self.update_mistake_list()
                self.status_var.set(f"已删除学科: {subject}")

    def add_chapter(self):
        subject = self.subject_combobox.get()
        if not subject:
            messagebox.showwarning("警告", "请先选择一个学科", parent=self.root)
            return

        chapter = simpledialog.askstring("添加章节", f"请输入 {subject} 的章节名称:", parent=self.root)
        if chapter and chapter not in self.chapters[subject]:
            self.chapters[subject].append(chapter)
            self.save_chapters()
            self.update_chapter_dropdown()
            self.status_var.set(f"已添加章节: {chapter}")

    def delete_chapter(self):
        subject = self.subject_combobox.get()
        chapter = self.chapter_combobox.get()

        if subject and chapter:
            if messagebox.askyesno("确认删除", f"确定要删除章节 '{chapter}' 及其所有错题吗？", parent=self.root):
                # 删除章节
                self.chapters[subject].remove(chapter)

                # 删除该章节下的所有错题
                self.mistakes = [m for m in self.mistakes if not (m['subject'] == subject and m['chapter'] == chapter)]

                self.save_chapters()
                self.save_mistakes()
                self.update_chapter_dropdown()
                self.update_mistake_list()
                self.status_var.set(f"已删除章节: {chapter}")

    def add_mistake(self):
        subject = self.subject_combobox.get()
        chapter = self.chapter_combobox.get()

        if not subject or not chapter:
            messagebox.showwarning("警告", "请先选择学科和章节", parent=self.root)
            return

        title = self.title_entry.get()
        description = self.description_text.get("1.0", tk.END).strip()
        answer = self.answer_text.get("1.0", tk.END).strip()

        if not title or not description:
            messagebox.showwarning("警告", "标题和题目描述不能为空", parent=self.root)
            return

        # 创建新错题
        new_mistake = {
            "id": datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "subject": subject,
            "chapter": chapter,
            "title": title,
            "description": description,
            "answer": answer,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "images": []
        }

        self.mistakes.append(new_mistake)
        self.save_mistakes()
        self.update_mistake_list()

        # 清空输入框
        self.title_entry.delete(0, tk.END)
        self.description_text.delete(1.0, tk.END)
        self.answer_text.delete(1.0, tk.END)
        self.current_mistake = None
        self.show_image()

        self.status_var.set(f"已添加错题: {title}")

    def update_mistake(self):
        if not self.current_mistake:
            messagebox.showwarning("警告", "请先选择一个错题", parent=self.root)
            return

        title = self.title_entry.get()
        description = self.description_text.get("1.0", tk.END).strip()
        answer = self.answer_text.get("1.0", tk.END).strip()

        if not title or not description:
            messagebox.showwarning("警告", "标题和题目描述不能为空", parent=self.root)
            return

        # 更新错题
        self.current_mistake['title'] = title
        self.current_mistake['description'] = description
        self.current_mistake['answer'] = answer
        self.current_mistake['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.save_mistakes()
        self.update_mistake_list()
        self.status_var.set(f"已更新错题: {title}")

    def delete_mistake(self):
        if not self.current_mistake:
            messagebox.showwarning("警告", "请先选择一个错题", parent=self.root)
            return

        if messagebox.askyesno("确认删除", "确定要删除这个错题吗？", parent=self.root):
            title = self.current_mistake['title']
            self.mistakes.remove(self.current_mistake)
            self.save_mistakes()
            self.update_mistake_list()

            # 清空详情
            self.title_entry.delete(0, tk.END)
            self.description_text.delete(1.0, tk.END)
            self.answer_text.delete(1.0, tk.END)
            self.current_mistake = None
            self.show_image()

            self.status_var.set(f"已删除错题: {title}")

    def upload_image(self):
        if not self.current_mistake:
            messagebox.showwarning("警告", "请先选择一个错题", parent=self.root)
            return

        file_paths = filedialog.askopenfilenames(
            title="选择错题图片",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )

        if file_paths:
            for file_path in file_paths:
                # 复制图片到数据目录
                file_name = f"{self.current_mistake['id']}_{os.path.basename(file_path)}"
                dest_path = os.path.join(self.image_dir, file_name)
                shutil.copyfile(file_path, dest_path)

                # 更新错题记录
                if 'images' not in self.current_mistake:
                    self.current_mistake['images'] = []
                self.current_mistake['images'].append(dest_path)

            self.save_mistakes()
            self.current_image_index = len(self.current_mistake['images']) - 1
            self.show_image()
            self.status_var.set(f"已添加 {len(file_paths)} 张图片")

    def delete_image(self):
        if not self.current_mistake or not self.current_mistake.get('images'):
            return

        images = self.current_mistake['images']
        if not images:
            return

        if self.current_image_index < len(images):
            # 删除图片文件
            img_path = images[self.current_image_index]
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except Exception as e:
                self.status_var.set(f"删除图片失败: {str(e)}")

            # 从列表中移除
            del images[self.current_image_index]

            # 更新索引
            if self.current_image_index >= len(images) and len(images) > 0:
                self.current_image_index = len(images) - 1

            self.save_mistakes()
            self.show_image()
            self.status_var.set("已删除当前图片")

    def export_data(self):
        export_path = filedialog.asksaveasfilename(
            title="导出数据",
            filetypes=[("ZIP 压缩包", "*.zip")],
            defaultextension=".zip"
        )

        if not export_path:
            return

        # 在后台执行导出操作
        threading.Thread(target=self._perform_export, args=(export_path,), daemon=True).start()

    def _perform_export(self, export_path):
        self.status_var.set("正在导出数据，请稍候...")

        try:
            with zipfile.ZipFile(export_path, 'w') as zipf:
                # 添加数据文件
                data_files = ["subjects.json", "chapters.json", "mistakes.json"]
                for file in data_files:
                    file_path = os.path.join(self.data_dir, file)
                    if os.path.exists(file_path):
                        zipf.write(file_path, arcname=file)

                # 添加图片
                if os.path.exists(self.image_dir):
                    for root, dirs, files in os.walk(self.image_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.data_dir)
                            zipf.write(file_path, arcname=arcname)

            self.status_var.set(f"数据已成功导出到: {export_path}")
            messagebox.showinfo("导出成功", f"数据已成功导出到:\n{export_path}", parent=self.root)
        except Exception as e:
            self.status_var.set(f"导出失败: {str(e)}")
            messagebox.showerror("导出失败", f"导出数据时出错:\n{str(e)}", parent=self.root)

    def import_data(self):
        import_path = filedialog.askopenfilename(
            title="导入数据",
            filetypes=[("ZIP 压缩包", "*.zip")]
        )

        if not import_path:
            return

        # 在后台执行导入操作
        threading.Thread(target=self._perform_import, args=(import_path,), daemon=True).start()

    def _perform_import(self, import_path):
        self.status_var.set("正在导入数据，请稍候...")

        try:
            # 备份当前数据
            backup_dir = os.path.join(self.data_dir, "backup")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # 创建备份
            for file in ["subjects.json", "chapters.json", "mistakes.json"]:
                src = os.path.join(self.data_dir, file)
                if os.path.exists(src):
                    shutil.copy(src, backup_dir)

            # 清空当前图片目录
            if os.path.exists(self.image_dir):
                shutil.rmtree(self.image_dir)
                os.makedirs(self.image_dir)

            # 解压ZIP文件
            with zipfile.ZipFile(import_path, 'r') as zipf:
                zipf.extractall(self.data_dir)

            # 重新加载数据
            self.subjects = self.load_subjects()
            self.chapters = self.load_chapters()
            self.mistakes = self.load_mistakes()

            # 更新UI
            self.root.after(0, self.update_subject_dropdown)
            self.root.after(0, self.update_mistake_list)

            self.status_var.set(f"数据已成功从 {import_path} 导入")
            messagebox.showinfo("导入成功", "数据导入成功！", parent=self.root)
        except Exception as e:
            # 恢复备份
            for file in ["subjects.json", "chapters.json", "mistakes.json"]:
                src = os.path.join(backup_dir, file)
                if os.path.exists(src):
                    shutil.copy(src, self.data_dir)

            self.status_var.set(f"导入失败: {str(e)}")
            messagebox.showerror("导入失败", f"导入数据时出错:\n{str(e)}", parent=self.root)

    def show_help(self):
        help_text = """
        【学霸错题本使用指南】
        
        1. 学科管理
          - 添加学科：点击"添加学科"按钮
          - 删除学科：选择学科后点击"删除学科"按钮
        
        2. 章节管理
          - 添加章节：先选择学科，再点击"添加章节"按钮
          - 删除章节：先选择学科和章节，再点击"删除章节"按钮
        
        3. 错题管理
          - 添加错题：填写标题、题目描述和正确答案后点击"添加错题"
          - 更新错题：修改内容后点击"更新错题"
          - 删除错题：选择错题后点击"删除错题"
        
        4. 图片管理
          - 添加图片：选择错题后点击"添加图片"按钮
          - 删除图片：在图片显示时点击"删除图片"按钮
          - 切换图片：使用"上一张"和"下一张"按钮
        
        5. 数据管理
          - 导出数据：将所有错题导出为ZIP文件
          - 导入数据：从ZIP文件导入错题数据
        
        提示：定期导出数据以防丢失！
        """
        messagebox.showinfo("使用帮助", help_text, parent=self.root)

    def show_about(self):
        about_text = """
        学霸错题本 v2.2
        
        一款高效整理学习错题的工具
        支持多学科分类、多图片管理
        
        主要功能：
        - 按学科/章节分类管理错题
        - 支持题目描述和正确答案
        - 支持多张题目图片
        - 数据导入导出功能

        
        开发：wudong_awa
        发布日期：2025年7月12日
        """
        messagebox.showinfo("关于软件", about_text, parent=self.root)

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedMistakeManager(root)
    root.mainloop()