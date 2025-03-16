import customtkinter as ctk
from customtkinter import filedialog, CTkImage
import threading
from PIL import Image, UnidentifiedImageError
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from game_identifier import identify_games
from image_utils import download_cover
import logging

logger = logging.getLogger(__name__)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class PS2GameManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PlayStation 2 Game Manager")
        self.geometry("1200x800")
        self._create_widgets()
        self._setup_data()
        self.center_window()
        self._setup_log_colors()
        
        # Инициализация переменных
        self._image_references = {}
        self._current_image = None
        self._image_lock = threading.Lock()
        self._scan_active = False
        self._current_scan_index = 0
        self._games_to_process = []
        self._cancel_operation = False  # Новый флаг для отмены операций

    def _create_widgets(self):
        """Создание всех элементов интерфейса"""
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Панель инструментов
        self.toolbar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.toolbar.pack(fill="x", pady=5)
        self._create_toolbar_buttons()

        # Прогресс-бар
        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(fill="x", pady=5)
        self.progress.set(0)

        # Основная область контента
        self.content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content.pack(fill="both", expand=True)

        # Создаем scrollable frame для списка игр
        self.game_list = ctk.CTkScrollableFrame(self.content, width=450)
        self.game_list.pack(side="left", fill="both", expand=True, padx=5)
        
        # Область для обложки с фиксированным размером
        self.cover_frame = ctk.CTkFrame(self.content, width=300, height=300)
        self.cover_frame.pack(side="right", padx=10)
        self.cover_frame.pack_propagate(False)  # Запрещаем изменение размера фрейма
        
        # Создаем label для обложки с фиксированным размером
        self.cover_label = ctk.CTkLabel(
            self.cover_frame, 
            text="Нет обложки",
            width=300,
            height=300
        )
        self.cover_label.pack(expand=True, fill="both")

        # Панель переименования
        self.rename_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.rename_panel.pack(fill="x", pady=10)
        self._create_rename_widgets()

        # Лог и статус бар
        self.log = ctk.CTkTextbox(self.main_frame, height=150)
        self.log.pack(fill="both", expand=True)
        self.status_bar = ctk.CTkLabel(self, text="Готов к работе...", anchor="w")
        self.status_bar.pack(fill="x", padx=5)

    def _setup_data(self):
        """Инициализация структур данных"""
        self.games = {
            'paths': [],
            'serials': [],
            'titles': [],
            'buttons': []
        }
        self.current_folder = None
        self.art_folder = None

    def _setup_log_colors(self):
        """Настройка цветов лога"""
        self.log.tag_config("error", foreground="#FF4444")
        self.log.tag_config("warning", foreground="#FFB443")
        self.log.tag_config("success", foreground="#44FF44")
        self.log.tag_config("info", foreground="#FFFFFF")

    def _create_toolbar_buttons(self):
        self.scan_button = ctk.CTkButton(
            self.toolbar,
            text="🔍 Сканировать",
            command=self.start_scan,
            font=("Arial", 14),
            corner_radius=8,
            width=200
        )
        self.scan_button.pack(side="left", padx=5)

        self.refresh_button = ctk.CTkButton(
            self.toolbar,
            text="🔄 Обновить список",
            command=self.refresh_games_list,
            font=("Arial", 14),
            corner_radius=8,
            width=200,
            state="disabled"  # Изначально отключена
        )
        self.refresh_button.pack(side="left", padx=5)

        self.folder_button = ctk.CTkButton(
            self.toolbar,
            text="📁 Выбрать папку",
            command=self.select_folder,
            font=("Arial", 14),
            corner_radius=8,
            width=200
        )
        self.folder_button.pack(side="left", padx=5)

        self.covers_button = ctk.CTkButton(
            self.toolbar,
            text="🖼 Скачать обложки",
            command=self.download_all_covers,
            font=("Arial", 14),
            corner_radius=8,
            width=200
        )
        self.covers_button.pack(side="left", padx=5)

        self.clear_log_button = ctk.CTkButton(
            self.toolbar,
            text="🧹 Очистить лог",
            command=self.clear_log,
            font=("Arial", 14),
            corner_radius=8,
            width=200
        )
        self.clear_log_button.pack(side="left", padx=5)

    def _create_rename_widgets(self):
        self.rename_entry = ctk.CTkEntry(
            self.rename_panel,
            placeholder_text="Новое имя файла",
            width=400
        )
        self.rename_entry.pack(side="left", expand=True, padx=5)

        ctk.CTkButton(
            self.rename_panel,
            text="📝 Использовать название",
            command=self.suggest_name,
            font=("Arial", 12)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            self.rename_panel,
            text="🔄 Переименовать",
            command=self.rename_file,
            font=("Arial", 12)
        ).pack(side="left")

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def clear_log(self):
        self.log.delete("1.0", "end")
        self.log_message("Лог очищен", "info")

    def log_message(self, message, tag="info"):
        self.log.insert("end", f"{message}\n", tag)
        self.log.see("end")
        self.update_status(f"Статус: {message}")

    def update_status(self, message):
        self.status_bar.configure(text=message)
        self.update_idletasks()

    def select_folder(self):
        try:
            path = filedialog.askdirectory()
            if path:
                self.current_folder = Path(path)
                self.art_folder = self.current_folder / "ART"
                
                if not self.art_folder.exists():
                    self.art_folder.mkdir(parents=True)
                    self.log_message(f"Создана папка для обложек: {self.art_folder}", "success")
                
                self.log_message(f"Выбрана рабочая папка: {path}", "info")
            else:
                self.log_message("Папка не выбрана", "warning")
        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}", "error")

    def start_scan(self):
        if not self.current_folder:
            self.log_message("Сначала выберите папку!", "warning")
            return
        if self._scan_active:
            self.log_message("Сканирование уже выполняется!", "warning")
            return

        self._cancel_operation = False
        threading.Thread(target=self._initial_scan, daemon=True).start()

    def _initial_scan(self):
        """Первичное сканирование папки"""
        try:
            self._scan_active = True
            self.scan_button.configure(state="disabled")
            self.refresh_button.configure(state="disabled")
            self.log_message("Начато первичное сканирование...", "info")
            
            # Выполняем сканирование
            self.scan_folder()
            
            # После успешного сканирования
            self.scan_button.configure(state="disabled")
            self.refresh_button.configure(state="normal")
            self.log_message("Первичное сканирование завершено. Теперь доступно обновление списка.", "success")
        except Exception as e:
            self.log_message(f"Ошибка при первичном сканировании: {str(e)}", "error")
            self.scan_button.configure(state="normal")
            self.refresh_button.configure(state="disabled")
        finally:
            self._scan_active = False

    def scan_folder(self):
        try:
            self._scan_active = True
            self.log_message("Начато сканирование...", "info")
            self.progress.set(0)

            # Очищаем обложку
            try:
                self._current_image = None
                self.cover_label._image = None
                self.cover_label.configure(image=None, text="")
                self.update_idletasks()
                self._image_references.clear()
            except Exception as e:
                logger.error(f"Ошибка при очистке обложки: {str(e)}")

            # Безопасное удаление старых кнопок
            try:
                if hasattr(self, 'game_list') and self.game_list is not None:
                    for btn in self.games['buttons']:
                        try:
                            if hasattr(btn, 'destroy'):
                                btn.destroy()
                        except Exception:
                            pass
                    self.games['buttons'].clear()
                    
                    # Пересоздаем scrollable frame
                    if self.game_list.winfo_exists():
                        self.game_list.pack_forget()
                        self.game_list.destroy()
                    
                    self.game_list = ctk.CTkScrollableFrame(self.content, width=450)
                    self.game_list.pack(side="left", fill="both", expand=True, padx=5, before=self.cover_frame)
                    
                    # Очищаем данные
                    self.games = {
                        'paths': [],
                        'serials': [],
                        'titles': [],
                        'buttons': []
                    }
                    
                    self.update()
                    
            except Exception as e:
                logger.error(f"Ошибка при очистке интерфейса: {str(e)}")

            try:
                # Получение списка игр
                games = identify_games(
                    str(self.current_folder),
                    self.log_message,
                    progress_callback=self._update_scan_progress
                )
            except Exception as e:
                raise Exception(f"Ошибка при идентификации игр: {str(e)}")
            
            if self._cancel_operation:
                self.log_message("Операция отменена пользователем", "warning")
                self._scan_active = False
                return

            try:
                games.sort(key=lambda x: x[2].lower())
            except Exception as e:
                logger.error(f"Ошибка при сортировке игр: {str(e)}")
                # Продолжаем без сортировки
            
            self._games_to_process = games
            self._current_scan_index = 0
            self._total_games = len(games)
            
            # Запуск пошаговой обработки
            self.after(10, self._process_next_game)

        except Exception as e:
            self.log_message(f"Ошибка сканирования: {str(e)}", "error")
            logger.exception("Критическая ошибка при сканировании")
            self._scan_active = False

    def _update_scan_progress(self, current, total):
        """Обновление прогресса идентификации игр"""
        self.progress.set(current / total)
        self.update_status(f"Идентификация: {current}/{total}")

    def _process_next_game(self):
        """Пошаговая обработка найденных игр"""
        if self._current_scan_index >= self._total_games:
            self._scan_active = False
            self.progress.set(0)
            self.log_message(f"Найдено {self._total_games} игр", "success")
            self.update_status("Сканирование завершено")
            return

        try:
            # Проверяем существование game_list
            if not hasattr(self, 'game_list') or self.game_list is None:
                self._scan_active = False
                self.log_message("Ошибка: список игр не инициализирован", "error")
                return

            path, serial, title = self._games_to_process[self._current_scan_index]
            
            self.games['paths'].append(path)
            self.games['serials'].append(serial)
            self.games['titles'].append(title)
            
            # Создание кнопки с проверкой существования родительского виджета
            try:
                btn = ctk.CTkButton(
                    master=self.game_list,
                    text=f"🎮 {Path(path).name}\n🔢 {serial} | 📛 {title}",
                    command=lambda i=self._current_scan_index: self.select_game(i),
                    anchor="w",
                    font=("Arial", 12),
                    height=60,
                    fg_color="transparent",
                    hover_color="#2A2D2E",
                    corner_radius=8
                )
                btn.pack(fill="x", pady=2)
                self.games['buttons'].append(btn)
            except Exception as e:
                logger.error(f"Ошибка создания кнопки: {str(e)}")
            
            self.progress.set((self._current_scan_index + 1) / self._total_games)
            self.update_status(f"Обработано {self._current_scan_index + 1}/{self._total_games} игр")
            
            self._current_scan_index += 1
            
            # Планируем следующую обработку только если виджет все еще существует
            if hasattr(self, 'game_list') and self.game_list is not None:
                self.after(10, self._process_next_game)
            else:
                self._scan_active = False
                self.log_message("Сканирование прервано: список игр не существует", "warning")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке игры: {str(e)}")
            self._current_scan_index += 1
            if hasattr(self, 'game_list') and self.game_list is not None:
                self.after(10, self._process_next_game)

    def select_game(self, index):
        """Выбор игры из списка"""
        if not isinstance(index, int) or index < 0 or index >= len(self.games['buttons']):
            self.log_message("Некорректный индекс игры", "error")
            return

        for btn in self.games['buttons']:
            btn.configure(fg_color="transparent")
        
        self.games['buttons'][index].configure(
            fg_color="#1F6AA5",
            border_width=1,
            border_color="#144870"
        )
        self.show_game_details(index)

    def show_game_details(self, index):
        self.rename_entry.delete(0, "end")
        path = self.games['paths'][index]
        self.rename_entry.insert(0, Path(path).stem)
        
        serial = self.games['serials'][index]
        self.load_cover(serial)

    def load_cover(self, serial):
        """Загрузка обложки игры"""
        try:
            # Безопасная очистка изображения
            self._current_image = None
            self.cover_label._image = None
            self.cover_label.configure(image=None, text="")
            self.update_idletasks()

            # Формируем имя файла в нужном формате
            cover = f"{serial.replace('-', '_')[:-2]}.{serial[-2:]}_COV.png"
            cover_path = self.art_folder / cover
            
            if cover_path.exists():
                self.display_cover(cover_path)
            else:
                # Просто показываем сообщение об отсутствии обложки
                self.cover_label.configure(text="Нет обложки")
                self.update_idletasks()

        except Exception as e:
            logger.error(f"Ошибка при загрузке обложки: {str(e)}")
            self._handle_image_error("Ошибка загрузки")

    def display_cover(self, path):
        """Основной метод для отображения обложки"""
        try:
            if not Path(path).exists():
                raise FileNotFoundError(f"Файл не найден: {path}")

            # Проверяем, есть ли изображение в кэше
            key = str(path)
            if key in self._image_references:
                self.after(0, lambda: self._update_cover(self._image_references[key]))
                return

            # Запускаем загрузку изображения в отдельном потоке
            threading.Thread(
                target=self._async_load_image,
                args=(path,),
                daemon=True
            ).start()

        except Exception as e:
            self._handle_image_error(f"Ошибка загрузки: {str(e)}")

    def _async_load_image(self, path):
        """Асинхронная загрузка и обработка изображения"""
        try:
            # Проверка существования файла
            if not Path(path).exists():
                raise FileNotFoundError(f"Файл не найден: {path}")

            with self._image_lock:
                try:
                    with Image.open(path) as image:
                        # Проверка размера изображения
                        if image.size[0] * image.size[1] > 10000000:  # Ограничение на размер
                            raise ValueError("Изображение слишком большое")
                            
                        image = image.resize((300, 300), Image.LANCZOS)
                        ctk_image = CTkImage(image, size=(300, 300))
                except UnidentifiedImageError:
                    raise UnidentifiedImageError("Неподдерживаемый формат изображения")
                except Exception as e:
                    raise Exception(f"Ошибка при обработке изображения: {str(e)}")

            # Сохраняем изображение в кэше
            key = str(path)
            self._image_references[key] = ctk_image

            # Безопасное обновление GUI
            try:
                self.after(0, lambda: self._update_cover(ctk_image))
            except Exception as e:
                logger.error(f"Ошибка при обновлении GUI: {str(e)}")

        except FileNotFoundError as e:
            self._handle_image_error(str(e))
        except UnidentifiedImageError:
            self._handle_image_error("Неподдерживаемый формат изображения")
        except ValueError as e:
            self._handle_image_error(str(e))
        except Exception as e:
            self._handle_image_error(f"Ошибка обработки: {str(e)}")
            logger.exception("Критическая ошибка при обработке изображения")

    def _update_cover(self, ctk_image):
        """Обновление обложки в GUI"""
        try:
            if not self.winfo_exists():  # Проверка, существует ли еще окно
                return
            
            self._current_image = ctk_image  # Сохраняем ссылку на текущее изображение
            self.cover_label.configure(image=ctk_image, text="")
            
        except Exception as e:
            logger.error(f"Ошибка обновления обложки: {str(e)}")
            self._handle_image_error("Ошибка обновления")

    def _handle_image_error(self, message):
        """Обработка ошибок изображения"""
        logger.error(message)
        self.log_message(message, "error")
        try:
            # Безопасная очистка изображения
            self._current_image = None
            self.cover_label._image = None
            self.cover_label.configure(image=None, text="Ошибка загрузки")
            self.update_idletasks()
        except Exception as e:
            logger.error(f"Ошибка при обработке ошибки изображения: {str(e)}")

    def suggest_name(self):
        if (index := self.get_selected_index()) is not None:
            self.rename_entry.delete(0, "end")
            self.rename_entry.insert(0, self.games['titles'][index])

    def rename_file(self):
        if (index := self.get_selected_index()) is None:
            self.log_message("Сначала выберите игру!", "warning")
            return
        
        old_path = Path(self.games['paths'][index])
        new_name = self.rename_entry.get().strip()
        
        if not new_name:
            self.log_message("Введите новое имя!", "warning")
            return
        
        # Расширенная очистка имени файла
        new_name = new_name.replace(':', '-').replace('?', '')\
            .replace('/', '-').replace('\\', '-')\
            .replace('*', '').replace('"', '')\
            .replace('<', '').replace('>', '')\
            .replace('|', '')
        
        new_path = old_path.parent / f"{new_name}.iso"
        
        try:
            if new_path.exists():
                raise FileExistsError("Файл с таким именем уже существует")
                
            old_path.rename(new_path)
            self.games['paths'][index] = str(new_path)
            self.update_game_list(index, new_name)
            self.log_message(f"Успешно переименовано в {new_name}.iso", "success")
        except PermissionError:
            self.log_message("Нет прав доступа для переименования файла", "error")
        except FileExistsError:
            self.log_message("Файл с таким именем уже существует", "error")
        except OSError as e:
            self.log_message(f"Ошибка операционной системы: {str(e)}", "error")
        except Exception as e:
            self.log_message(f"Неизвестная ошибка: {str(e)}", "error")

    def get_selected_index(self):
        for i, btn in enumerate(self.games['buttons']):
            if btn.cget("fg_color") == "#1F6AA5":
                return i
        return None

    def update_game_list(self, index, new_name):
        btn = self.games['buttons'][index]
        new_text = f"🎮 {new_name}.iso\n🔢 {self.games['serials'][index]} | 📛 {self.games['titles'][index]}"
        btn.configure(text=new_text)

    def download_all_covers(self):
        if not self.games['serials']:
            self.log_message("Сначала выполните сканирование!", "warning")
            return

        self._cancel_operation = False  # Сброс флага отмены
        threading.Thread(target=self._download_all_covers, daemon=True).start()

    def _download_all_covers(self):
        try:
            total = len(self.games['serials'])
            self.progress.set(0)
            
            with ThreadPoolExecutor() as executor:
                futures = []
                for i in range(total):
                    if self._cancel_operation:
                        self.log_message("Загрузка обложек отменена", "warning")
                        break
                    
                    serial = self.games['serials'][i]
                    # Проверяем существование обложки в нужном формате
                    cover = f"{serial.replace('-', '_')[:-2]}.{serial[-2:]}_COV.png"
                    cover_path = self.art_folder / cover
                    
                    if not cover_path.exists():
                        futures.append(executor.submit(
                            download_cover,
                            self.games['titles'][i],
                            serial,
                            str(self.art_folder)
                        ))
                    else:
                        self.log_message(f"Обложка уже существует: {cover}", "info")
                
                for i, future in enumerate(futures):
                    if self._cancel_operation:
                        break
                    try:
                        result = future.result()
                        if result and result[0]:
                            self.log_message(f"Загружена обложка: {result[1]}", "success")
                        else:
                            self.log_message(f"Не удалось загрузить обложку для {self.games['titles'][i]}", "warning")
                    except Exception as e:
                        self.log_message(f"Ошибка при загрузке обложки: {str(e)}", "error")
                    self.progress.set((i + 1) / len(futures))
                    self.update_status(f"Загрузка обложек: {i + 1}/{len(futures)}")
                
                if not self._cancel_operation:
                    self.log_message("Загрузка обложек завершена!", "success")
        
        except Exception as e:
            self.log_message(f"Ошибка загрузки обложек: {str(e)}", "error")
        finally:
            self.progress.set(0)

    def refresh_games_list(self):
        """Обновление списка игр"""
        if not self.current_folder:
            self.log_message("Папка не выбрана!", "warning")
            return
        
        if self._scan_active:
            self.log_message("Сканирование уже выполняется!", "warning")
            return

        self._cancel_operation = False
        threading.Thread(target=self._refresh_scan, daemon=True).start()

    def _refresh_scan(self):
        """Сканирование на наличие изменений"""
        try:
            self._scan_active = True
            self.refresh_button.configure(state="disabled")
            self.log_message("Проверка изменений...", "info")
            
            # Получаем текущий список файлов
            current_files = set(self.games['paths'])
            
            # Сканируем папку на наличие всех файлов
            new_games = identify_games(
                str(self.current_folder),
                self.log_message,
                progress_callback=self._update_scan_progress
            )
            
            # Создаем множество новых путей для быстрой проверки
            new_paths = {path for path, _, _ in new_games}
            
            # Находим удаленные файлы
            removed_files = current_files - new_paths
            if removed_files:
                self.log_message(f"Обнаружено {len(removed_files)} удаленных файлов", "info")
                self._remove_missing_games(removed_files)
            
            # Находим новые файлы
            new_files = [(p, s, t) for p, s, t in new_games if p not in current_files]
            
            if new_files:
                self.log_message(f"Найдено {len(new_files)} новых игр", "success")
                self._add_new_games(new_files)
            elif not removed_files:
                self.log_message("Изменений не обнаружено", "info")
            
        except Exception as e:
            self.log_message(f"Ошибка при обновлении списка: {str(e)}", "error")
        finally:
            self._scan_active = False
            self.refresh_button.configure(state="normal")

    def _remove_missing_games(self, removed_files):
        """Удаление отсутствующих игр из списка"""
        try:
            # Создаем список индексов для удаления (в обратном порядке)
            indices_to_remove = []
            for i, path in enumerate(self.games['paths']):
                if path in removed_files:
                    indices_to_remove.append(i)
            
            # Удаляем элементы с конца списка
            for index in reversed(indices_to_remove):
                # Удаляем кнопку
                if index < len(self.games['buttons']):
                    try:
                        if self.games['buttons'][index].winfo_exists():
                            self.games['buttons'][index].destroy()
                    except Exception:
                        pass
                
                # Удаляем данные
                for key in ['paths', 'serials', 'titles', 'buttons']:
                    if index < len(self.games[key]):
                        self.games[key].pop(index)
                
                self.log_message(f"Удалена отсутствующая игра: {Path(self.games['paths'][index]).name}", "info")
            
        except Exception as e:
            self.log_message(f"Ошибка при удалении игр: {str(e)}", "error")

    def _add_new_games(self, new_files):
        """Добавление новых игр в список"""
        try:
            for path, serial, title in new_files:
                self.games['paths'].append(path)
                self.games['serials'].append(serial)
                self.games['titles'].append(title)
                
                btn = ctk.CTkButton(
                    master=self.game_list,
                    text=f"🎮 {Path(path).name}\n🔢 {serial} | 📛 {title}",
                    command=lambda i=len(self.games['buttons']): self.select_game(i),
                    anchor="w",
                    font=("Arial", 12),
                    height=60,
                    fg_color="#1F6AA5",  # Выделяем новые игры цветом
                    hover_color="#2A2D2E",
                    corner_radius=8
                )
                btn.pack(fill="x", pady=2)
                self.games['buttons'].append(btn)
                
                self.log_message(f"Добавлена новая игра: {title}", "success")
        
        except Exception as e:
            self.log_message(f"Ошибка при добавлении игр: {str(e)}", "error")

if __name__ == "__main__":
    app = PS2GameManager()
    app.mainloop()